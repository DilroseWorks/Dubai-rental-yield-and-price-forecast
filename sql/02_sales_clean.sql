-- Step 2a: clean sales.
-- Source: raw_sales_mirror only (2010 to Sep 2026). One source for the whole history,
-- so the series never jumps because two sources define a "sale" differently.
-- Every row is kept in sales_flagged with the FIRST rule it fails, so the
-- exclusion waterfall can be reported and every removed row can be traced.

CREATE OR REPLACE TABLE sales_flagged AS
WITH typed AS (
    SELECT
        transaction_id,
        CAST(instance_date AS DATE)                              AS sale_date,
        reg_type_label                                           AS reg_type,      -- Ready / Off-Plan
        upper(trim(area_name_en))                                AS area,
        project_name,
        building_name,
        property_type_label                                      AS property_type,
        property_sub_type,
        usage_label,
        procedure_name_en                                        AS procedure_name,
        TRY_CAST(rooms_bucket AS INTEGER)                        AS rooms,         -- 0 = studio
        TRY_CAST(area_sqm AS DOUBLE)                             AS size_sqm,
        TRY_CAST(price_aed AS DOUBLE)                            AS price_aed,
        quality_flags,
        -- Flat or Villa. Everything else (land, whole buildings, offices, shops,
        -- hotel apartments) is a different market and is excluded.
        CASE
            WHEN property_type_label = 'Villa'
              OR property_sub_type IN ('Villa', 'Residential / Villas', 'Residential / Attached Villas',
                                       'Residential / Residential Villa', 'Stacked Townhouses') THEN 'Villa'
            WHEN property_type_label = 'Unit'
             AND coalesce(property_sub_type, 'Flat') IN ('Flat', 'Residential Flats') THEN 'Flat'
        END                                                      AS segment,
        property_sub_type IS NULL AND property_type_label = 'Unit' AS sub_type_assumed_flat,
        procedure_name_en IS NULL                                AS procedure_missing
    FROM raw_sales_mirror
)
SELECT
    *,
    date_trunc('month', sale_date)  AS month,
    price_aed / NULLIF(size_sqm, 0) AS price_per_sqm,
    CASE
        WHEN quality_flags <> '0'                       THEN '1 failed the mirror''s quality checks'
        WHEN usage_label <> 'Residential'               THEN '2 not residential'
        -- NULL procedure is NOT treated as "not a sale": in v1 that silently dropped most
        -- 2026 Ready sales, which arrive in the mirror without a procedure name.
        -- They are kept and marked with procedure_missing instead.
        WHEN procedure_name IS NOT NULL
         AND procedure_name NOT IN ('Sell', 'Sell - Pre registration', 'Delayed Sell', 'Sale On Payment Plan')
                                                        THEN '3 not a market sale (lease-to-own, developer registration...)'
        WHEN segment IS NULL                            THEN '4 not a flat or villa'
        WHEN sale_date < DATE '2010-01-01'              THEN '5 before 2010 (thin data, 2009 backlog)'
        WHEN sale_date >= DATE '2026-10-01'             THEN '6 partial month (Oct 2026)'
    END AS exclude_reason
FROM typed;

CREATE OR REPLACE TABLE sales_clean AS
SELECT * EXCLUDE (exclude_reason, quality_flags, usage_label)
FROM sales_flagged
WHERE exclude_reason IS NULL;
