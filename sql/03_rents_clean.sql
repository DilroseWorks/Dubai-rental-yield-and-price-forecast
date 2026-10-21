-- Step 2b: clean rents (2026, official DLD export).
-- Identical rows sit in the SAME file (step 1c), so they are DLD's own rows,
-- mostly bulk registrations (one labour camp: 484 identical rows).
-- We collapse each identical group to ONE row and keep the count in `copies`.
-- Why this is safe either way: if they are separate contracts, one bulk deal
-- should not outvote hundreds of individual tenants in a median; if they are
-- an export glitch, they should go anyway.

CREATE OR REPLACE TABLE rents_flagged AS
WITH collapsed AS (
    SELECT COLUMNS(* EXCLUDE (filename)), count(*) AS copies
    FROM raw_rents
    GROUP BY ALL
),
typed AS (
    SELECT
        try_strptime(REGISTRATION_DATE, '%Y-%m-%d %H:%M:%S')::DATE   AS reg_date,
        try_strptime(START_DATE, '%Y-%m-%d %H:%M:%S')::DATE          AS start_date,
        try_strptime(END_DATE, '%Y-%m-%d %H:%M:%S')::DATE            AS end_date,
        VERSION_EN                                                   AS version,       -- New / Renewed
        upper(trim(AREA_EN))                                         AS area,
        IS_FREE_HOLD_EN = 'Free Hold'                                AS is_freehold,
        PROP_TYPE_EN                                                 AS property_type,
        trim(PROP_SUB_TYPE_EN)                                       AS property_sub_type,  -- 'Studio ' has a trailing space
        TRY_CAST(ANNUAL_AMOUNT AS DOUBLE)                            AS annual_rent,
        TRY_CAST(CONTRACT_AMOUNT AS DOUBLE)                          AS contract_amount,
        TRY_CAST(ACTUAL_AREA AS DOUBLE)                              AS size_sqm,
        TRY_CAST(trim(TOTAL_PROPERTIES) AS INTEGER)                  AS total_properties,
        PROJECT_EN                                                   AS project_name,
        copies,
        CASE
            WHEN PROP_TYPE_EN = 'Villa' OR trim(PROP_SUB_TYPE_EN) IN ('Villa', 'Complex Villas') THEN 'Villa'
            WHEN PROP_TYPE_EN = 'Unit'  AND trim(PROP_SUB_TYPE_EN) IN ('Flat', 'Studio', 'Penthouse') THEN 'Flat'
        END                                                          AS segment
    FROM collapsed
),
first_pass AS (
    SELECT *,
        date_trunc('month', reg_date)          AS month,
        end_date - start_date                  AS duration_days,
        annual_rent / NULLIF(size_sqm, 0)      AS rent_per_sqm,
        CASE
            WHEN segment IS NULL                              THEN '1 not a flat or villa (labour camp, staff housing...)'
            WHEN total_properties IS DISTINCT FROM 1          THEN '2 contract covers several properties'
            WHEN annual_rent IS NULL OR annual_rent <= 0      THEN '3 no rent amount'
            WHEN size_sqm IS NULL OR size_sqm NOT BETWEEN 15 AND 2000 THEN '4 implausible size'
            -- v2: 1- AND 2-year leases are kept. Step 3 showed dropped leases were mostly
            -- 730-day contracts with the same rent per sqm as 1-year ones, which means
            -- ANNUAL_AMOUNT is already annualised. Very short and very long leases stay out.
            WHEN (end_date - start_date) NOT BETWEEN 330 AND 760
              OR start_date IS NULL OR end_date IS NULL        THEN '5 not a 1- or 2-year lease'
            WHEN reg_date >= DATE '2026-10-01'                THEN '6 partial month (Oct 2026)'
        END AS reason
    FROM typed
),
-- Rent per sqm cut-offs per segment, computed only on rows that passed so far.
bounds AS (
    SELECT segment,
           quantile_cont(rent_per_sqm, 0.01) AS p01,
           quantile_cont(rent_per_sqm, 0.99) AS p99
    FROM first_pass WHERE reason IS NULL GROUP BY segment
)
SELECT f.* EXCLUDE (reason),
    coalesce(f.reason,
             CASE WHEN f.rent_per_sqm < b.p01 OR f.rent_per_sqm > b.p99
                  THEN '7 extreme rent per sqm (bottom/top 1%)' END) AS exclude_reason
FROM first_pass f LEFT JOIN bounds b USING (segment);

CREATE OR REPLACE TABLE rents_clean AS
SELECT * EXCLUDE (exclude_reason)
FROM rents_flagged
WHERE exclude_reason IS NULL;
