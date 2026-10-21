-- Did the market change in 2026, or is it just the time of year?
-- Compare each 2026 month with the SAME month of 2025 (year over year),
-- so seasonal effects such as Ramadan and summer appear in both years.
-- Volume and price are compared separately: a shock to confidence usually
-- hits the number of sales first, and prices later, or not at all.
WITH m AS (
    SELECT month, reg_type, count(*) AS sales, median(price_per_sqm) AS aed_per_sqm
    FROM sales_clean
    WHERE month >= DATE '2025-01-01'
    GROUP BY ALL
)
SELECT strftime(a.month, '%m') AS month_of_year, a.reg_type,
       b.sales AS sales_2025, a.sales AS sales_2026,
       round(100.0 * (a.sales - b.sales) / b.sales, 1)                AS sales_yoy_pct,
       round(b.aed_per_sqm) AS aed_sqm_2025, round(a.aed_per_sqm) AS aed_sqm_2026,
       round(100.0 * (a.aed_per_sqm - b.aed_per_sqm) / b.aed_per_sqm, 1) AS price_yoy_pct
FROM m a
JOIN m b ON b.month = a.month - INTERVAL 1 YEAR AND b.reg_type = a.reg_type
ORDER BY a.reg_type, a.month;
