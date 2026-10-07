-- Question 1: why do clinical trials fail?
-- "Failed" = TERMINATED or WITHDRAWN, compared with COMPLETED (see the `finished` view in 00_views.sql).

-- @output: failure_by_phase
SELECT
    phase,
    COUNT(*) AS trials,
    COUNT(*) FILTER (WHERE failed) AS failed,
    ROUND(100.0 * COUNT(*) FILTER (WHERE failed) / COUNT(*), 1) AS failure_rate_pct
FROM finished
GROUP BY phase
ORDER BY failure_rate_pct DESC;

-- @output: failure_by_sponsor
SELECT
    s.sponsor_type,
    COUNT(*) AS trials,
    COUNT(*) FILTER (WHERE f.failed) AS failed,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.failed) / COUNT(*), 1) AS failure_rate_pct
FROM finished f
JOIN lead_sponsor s USING (nct_id)
GROUP BY s.sponsor_type
ORDER BY failure_rate_pct DESC;

-- @output: failure_by_year
-- Only trials started 2000-2018: more recent trials are still running, so the ones
-- already "finished" are biased towards the ones that stopped early.
SELECT
    start_year,
    COUNT(*) AS trials,
    ROUND(100.0 * COUNT(*) FILTER (WHERE failed) / COUNT(*), 1) AS failure_rate_pct
FROM finished
WHERE start_year BETWEEN 2000 AND 2018
GROUP BY start_year
ORDER BY start_year;

-- @output: failure_by_area
-- A trial can belong to several disease areas (e.g. a cancer trial in the brain).
WITH areas AS (
    SELECT DISTINCT nct_id, mesh_term AS area
    FROM browse_conditions
    WHERE mesh_term IN ('Neoplasms', 'Cardiovascular Diseases', 'Nervous System Diseases', 'Mental Disorders',
                        'Infections', 'Nutritional and Metabolic Diseases', 'Respiratory Tract Diseases',
                        'Digestive System Diseases', 'Immune System Diseases', 'Musculoskeletal Diseases',
                        'Skin and Connective Tissue Diseases')
)
SELECT
    a.area,
    COUNT(*) AS trials,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.failed) / COUNT(*), 1) AS failure_rate_pct
FROM finished f
JOIN areas a USING (nct_id)
GROUP BY a.area
ORDER BY failure_rate_pct DESC;

-- @output: stop_reasons
SELECT
    reason,
    COUNT(*) AS trials,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_failed
FROM stop_reasons
GROUP BY reason
ORDER BY trials DESC;

-- @output: stop_reasons_by_sponsor
-- Share of each reason within each sponsor type (excluding trials with no reason given).
SELECT
    s.sponsor_type,
    r.reason,
    COUNT(*) AS trials,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY s.sponsor_type), 1) AS pct_within_sponsor
FROM stop_reasons r
JOIN lead_sponsor s USING (nct_id)
WHERE r.reason <> 'Not reported'
GROUP BY s.sponsor_type, r.reason
ORDER BY s.sponsor_type, trials DESC;
