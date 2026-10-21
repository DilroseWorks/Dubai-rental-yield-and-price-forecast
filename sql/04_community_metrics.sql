-- Step 3: rental yield and price momentum per community.
-- Window for yield: Jan to Sep 2026, the full months we have rents for.
-- Sales prices come from the same months, so rent and price describe the same market.

-- Size bands. Comparing rent per sqm with price per sqm inside the same band
-- stops a community full of small studios being compared against big apartments.
CREATE OR REPLACE MACRO size_band(seg, sqm) AS
    CASE WHEN seg = 'Flat' THEN
         CASE WHEN sqm < 50 THEN 'F1 <50' WHEN sqm < 80 THEN 'F2 50-80' WHEN sqm < 120 THEN 'F3 80-120'
              WHEN sqm < 180 THEN 'F4 120-180' ELSE 'F5 180+' END
    ELSE CASE WHEN sqm < 200 THEN 'V1 <200' WHEN sqm < 300 THEN 'V2 200-300'
              WHEN sqm < 450 THEN 'V3 300-450' ELSE 'V4 450+' END
    END;

-- 1. Yield per community x segment x size band.
--    Rents: NEW contracts only (renewals are capped by the RERA index and lag the market).
--    Prices: READY sales only (you can't rent out a unit that isn't built).
--    A cell needs at least 20 rents and 20 sales, or its median is too noisy.
CREATE OR REPLACE TABLE yield_cells AS
WITH r AS (
    SELECT area, segment, size_band(segment, size_sqm) AS band,
           count(*) AS n_rents, median(rent_per_sqm) AS rent_per_sqm
    FROM rents_clean
    WHERE version = 'New' AND month BETWEEN DATE '2026-01-01' AND DATE '2026-09-01'
    GROUP BY ALL),
s AS (
    SELECT area, segment, size_band(segment, size_sqm) AS band,
           count(*) AS n_sales, median(price_per_sqm) AS price_per_sqm
    FROM sales_clean
    WHERE reg_type = 'Ready' AND month BETWEEN DATE '2026-01-01' AND DATE '2026-09-01'
    GROUP BY ALL)
SELECT r.area, r.segment, r.band, n_rents, n_sales, rent_per_sqm, price_per_sqm,
       rent_per_sqm / price_per_sqm AS gross_yield
FROM r JOIN s USING (area, segment, band)
WHERE n_rents >= 20 AND n_sales >= 20;

-- 2. Roll cells up to community x segment, weighting each band by its number of
--    new leases (bands where more people actually rent count more).
--    The naive yield (median rent / median price for the whole community) is kept
--    next to it, to show how much the like-for-like method changes the answer.
CREATE OR REPLACE TABLE community_yield AS
WITH lfl AS (
    SELECT area, segment, count(*) AS n_bands, sum(n_rents) AS n_rents, sum(n_sales) AS n_sales,
           sum(gross_yield * n_rents) / sum(n_rents) AS yield_like_for_like
    FROM yield_cells GROUP BY ALL),
naive AS (
    SELECT r.area, r.segment, r.med_rent / s.med_price AS yield_naive,
           r.n_all_rents
    FROM (SELECT area, segment, median(annual_rent) AS med_rent, count(*) AS n_all_rents FROM rents_clean
          WHERE version = 'New' AND month BETWEEN DATE '2026-01-01' AND DATE '2026-09-01' GROUP BY ALL) r
    JOIN (SELECT area, segment, median(price_aed) AS med_price FROM sales_clean
          WHERE reg_type = 'Ready' AND month BETWEEN DATE '2026-01-01' AND DATE '2026-09-01' GROUP BY ALL) s
      USING (area, segment))
SELECT lfl.*, naive.yield_naive,
       lfl.n_rents / naive.n_all_rents AS rent_coverage   -- share of the community's new leases inside qualifying bands
FROM lfl JOIN naive USING (area, segment)
WHERE lfl.n_rents >= 50 AND lfl.n_sales >= 50;

-- 3. Price momentum: median price per sqm, year over year, two windows.
--    6 months (Apr-Sep 2026 vs Apr-Sep 2025): shows the post-March 2026 market.
--    12 months (Oct 2025-Sep 2026 vs Oct 2024-Sep 2025): steadier, but mixes before and after the break.
--    Each period needs at least 30 sales, otherwise the change is left empty.
CREATE OR REPLACE TABLE community_momentum AS
WITH p AS (
    SELECT area, segment, reg_type,
        count(*)                   FILTER (WHERE month BETWEEN DATE '2026-04-01' AND DATE '2026-09-01') AS n_6m,
        median(price_per_sqm)      FILTER (WHERE month BETWEEN DATE '2026-04-01' AND DATE '2026-09-01') AS psqm_6m,
        count(*)                   FILTER (WHERE month BETWEEN DATE '2025-04-01' AND DATE '2025-09-01') AS n_6m_ly,
        median(price_per_sqm)      FILTER (WHERE month BETWEEN DATE '2025-04-01' AND DATE '2025-09-01') AS psqm_6m_ly,
        count(*)                   FILTER (WHERE month BETWEEN DATE '2025-10-01' AND DATE '2026-09-01') AS n_12m,
        median(price_per_sqm)      FILTER (WHERE month BETWEEN DATE '2025-10-01' AND DATE '2026-09-01') AS psqm_12m,
        count(*)                   FILTER (WHERE month BETWEEN DATE '2024-10-01' AND DATE '2025-09-01') AS n_12m_ly,
        median(price_per_sqm)      FILTER (WHERE month BETWEEN DATE '2024-10-01' AND DATE '2025-09-01') AS psqm_12m_ly
    FROM sales_clean GROUP BY ALL)
SELECT *,
    CASE WHEN n_6m  >= 30 AND n_6m_ly  >= 30 THEN psqm_6m  / psqm_6m_ly  - 1 END AS price_yoy_6m,
    CASE WHEN n_12m >= 30 AND n_12m_ly >= 30 THEN psqm_12m / psqm_12m_ly - 1 END AS price_yoy_12m,
    CASE WHEN n_6m_ly >= 30 THEN n_6m / n_6m_ly - 1 END                          AS volume_yoy_6m
FROM p;

-- 3b. Same-project momentum.
--    Plain community momentum is distorted when NEW projects start selling: a premium
--    tower handing over in a community lifts its median price per sqm, although no
--    existing home got more expensive. Here each project is compared only with ITSELF
--    a year earlier, then the community's change is the average of its projects'
--    changes (weighted by matched sales, averaged on a log scale).
--    v2: matched on PROJECT (falling back to building name), not building: single
--    buildings rarely have 5 sales in both periods, which left most communities blank.
--    A project needs >= 5 sales in both periods; a community needs >= 3 such projects.
CREATE OR REPLACE TABLE project_changes AS
SELECT area, segment, reg_type, coalesce(project_name, building_name) AS project,
    median(price_per_sqm) FILTER (WHERE month BETWEEN DATE '2026-04-01' AND DATE '2026-09-01') AS p_6m,
    count(*)              FILTER (WHERE month BETWEEN DATE '2026-04-01' AND DATE '2026-09-01') AS n_6m,
    median(price_per_sqm) FILTER (WHERE month BETWEEN DATE '2025-04-01' AND DATE '2025-09-01') AS p_6m_ly,
    count(*)              FILTER (WHERE month BETWEEN DATE '2025-04-01' AND DATE '2025-09-01') AS n_6m_ly,
    median(price_per_sqm) FILTER (WHERE month BETWEEN DATE '2025-10-01' AND DATE '2026-09-01') AS p_12m,
    count(*)              FILTER (WHERE month BETWEEN DATE '2025-10-01' AND DATE '2026-09-01') AS n_12m,
    median(price_per_sqm) FILTER (WHERE month BETWEEN DATE '2024-10-01' AND DATE '2025-09-01') AS p_12m_ly,
    count(*)              FILTER (WHERE month BETWEEN DATE '2024-10-01' AND DATE '2025-09-01') AS n_12m_ly
FROM sales_clean
WHERE coalesce(project_name, building_name) IS NOT NULL
GROUP BY ALL;

CREATE OR REPLACE TABLE community_momentum_same_project AS
WITH w AS (
    SELECT area, segment, reg_type,
        CASE WHEN n_6m >= 5 AND n_6m_ly >= 5 THEN least(n_6m, n_6m_ly) END        AS w6,
        CASE WHEN n_6m >= 5 AND n_6m_ly >= 5 THEN ln(p_6m / p_6m_ly) END          AS c6,
        CASE WHEN n_12m >= 5 AND n_12m_ly >= 5 THEN least(n_12m, n_12m_ly) END    AS w12,
        CASE WHEN n_12m >= 5 AND n_12m_ly >= 5 THEN ln(p_12m / p_12m_ly) END      AS c12
    FROM project_changes)
SELECT area, segment, reg_type,
    count(c6)  AS projects_6m,
    count(c12) AS projects_12m,
    CASE WHEN count(c6)  >= 3 THEN exp(sum(w6 * c6)   / sum(w6))  - 1 END AS price_yoy_6m_same_project,
    CASE WHEN count(c12) >= 3 THEN exp(sum(w12 * c12) / sum(w12)) - 1 END AS price_yoy_12m_same_project
FROM w GROUP BY ALL;

-- 4. Investor scorecard: yield next to READY momentum for the same community and segment.
--    No combined score on purpose: any weighting of yield vs growth would be our opinion.
--    The dashboard shows them as two axes and lets the reader decide.
CREATE OR REPLACE TABLE community_scorecard AS
SELECT y.area, y.segment,
       round(100 * y.yield_like_for_like, 2) AS gross_yield_pct,
       round(100 * y.yield_naive, 2)         AS naive_yield_pct,
       round(100 * b.price_yoy_6m_same_project, 1)  AS price_yoy_6m_pct,       -- same-project (main measure)
       round(100 * b.price_yoy_12m_same_project, 1) AS price_yoy_12m_pct,
       round(100 * m.price_yoy_6m, 1)        AS raw_price_yoy_6m_pct,         -- all sales (affected by new projects)
       b.projects_6m,
       round(100 * m.volume_yoy_6m, 1)       AS volume_yoy_6m_pct,
       round(m.psqm_6m)                      AS ready_aed_per_sqm_6m,
       y.n_rents, y.n_sales, y.n_bands, round(100 * y.rent_coverage, 1) AS rent_coverage_pct
FROM community_yield y
LEFT JOIN community_momentum m ON m.area = y.area AND m.segment = y.segment AND m.reg_type = 'Ready'
LEFT JOIN community_momentum_same_project b ON b.area = y.area AND b.segment = y.segment AND b.reg_type = 'Ready';

-- 4b. Naming help: DLD uses cadastral names (AL BARSHA SOUTH FOURTH), people use
--     marketing names (JVC). The top projects per area show which is which.
CREATE OR REPLACE TABLE area_top_projects AS
SELECT area, string_agg(project_name || ' (' || n || ')', '; ' ORDER BY n DESC) AS top_projects
FROM (
    SELECT area, project_name, count(*) AS n,
           row_number() OVER (PARTITION BY area ORDER BY count(*) DESC) AS rk
    FROM sales_clean
    WHERE project_name IS NOT NULL AND sale_date >= DATE '2024-01-01'
      AND area IN (SELECT area FROM community_yield UNION SELECT area FROM community_momentum)
    GROUP BY area, project_name)
WHERE rk <= 4
GROUP BY area;

-- 5. Check on cleaning rule 5 (only 1- and 2-year leases kept).
--    If some communities lose far more short leases than others, and those short
--    leases are priced differently, the rule shifts their yield relative to others.
CREATE OR REPLACE TABLE rule5_check AS
SELECT area, segment,
       count(*) AS new_leases,
       count(*) FILTER (WHERE exclude_reason LIKE '5%') AS dropped_not_1yr,
       round(100.0 * count(*) FILTER (WHERE exclude_reason LIKE '5%') / count(*), 1) AS pct_dropped,
       round(median(rent_per_sqm) FILTER (WHERE exclude_reason IS NULL)) AS rent_sqm_kept,
       round(median(rent_per_sqm) FILTER (WHERE exclude_reason LIKE '5%')) AS rent_sqm_dropped,
       round(median(duration_days) FILTER (WHERE exclude_reason LIKE '5%')) AS median_days_dropped
FROM rents_flagged
WHERE version = 'New' AND segment IS NOT NULL
  AND (exclude_reason IS NULL OR exclude_reason LIKE '5%')
  AND month BETWEEN DATE '2026-01-01' AND DATE '2026-09-01'
GROUP BY ALL
HAVING count(*) >= 200;
