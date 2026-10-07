-- Question 3: why is Alzheimer's disease so hard?
-- Alzheimer trials = trials whose normalised condition (MeSH) starts with "Alzheimer".

CREATE OR REPLACE TEMP VIEW alz AS
SELECT DISTINCT nct_id FROM browse_conditions WHERE mesh_term ILIKE 'Alzheimer%';

-- @output: alzheimer_vs_all
SELECT
    CASE WHEN a.nct_id IS NOT NULL THEN 'Alzheimer' ELSE 'All other trials' END AS grp,
    COUNT(*) AS trials,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.failed) / COUNT(*), 1) AS failure_rate_pct
FROM finished f
LEFT JOIN alz a USING (nct_id)
GROUP BY grp;

-- @output: alzheimer_vs_all_by_phase
-- Drug-development phases only, to compare like with like.
SELECT
    f.phase,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.failed AND a.nct_id IS NOT NULL) / NULLIF(COUNT(*) FILTER (WHERE a.nct_id IS NOT NULL), 0), 1) AS alzheimer_failure_pct,
    COUNT(*) FILTER (WHERE a.nct_id IS NOT NULL) AS alzheimer_trials,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.failed AND a.nct_id IS NULL) / COUNT(*) FILTER (WHERE a.nct_id IS NULL), 1) AS others_failure_pct
FROM finished f
LEFT JOIN alz a USING (nct_id)
WHERE f.phase IN ('PHASE1', 'PHASE2', 'PHASE3')
GROUP BY f.phase
ORDER BY f.phase;

-- @output: alzheimer_stop_reasons
SELECT
    r.reason,
    COUNT(*) FILTER (WHERE a.nct_id IS NOT NULL) AS alzheimer_trials,
    ROUND(100.0 * COUNT(*) FILTER (WHERE a.nct_id IS NOT NULL) / SUM(COUNT(*) FILTER (WHERE a.nct_id IS NOT NULL)) OVER (), 1) AS alzheimer_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE a.nct_id IS NULL) / SUM(COUNT(*) FILTER (WHERE a.nct_id IS NULL)) OVER (), 1) AS others_pct
FROM stop_reasons r
LEFT JOIN alz a USING (nct_id)
WHERE r.reason <> 'Not reported'
GROUP BY r.reason
ORDER BY alzheimer_trials DESC;

-- @output: alzheimer_by_year
SELECT
    year(s.start_date) AS start_year,
    COUNT(*) AS trials,
    COUNT(*) FILTER (WHERE l.sponsor_type = 'Industry') AS industry_trials
FROM studies s
JOIN alz a USING (nct_id)
JOIN lead_sponsor l USING (nct_id)
WHERE s.study_type = 'INTERVENTIONAL'
  AND year(s.start_date) BETWEEN 2000 AND 2025
GROUP BY start_year
ORDER BY start_year;

-- @output: alzheimer_interventions
-- What is being tested in Alzheimer interventional trials (a trial can test several things).
SELECT
    i.intervention_type,
    COUNT(DISTINCT i.nct_id) AS trials,
    ROUND(100.0 * COUNT(DISTINCT i.nct_id) / (SELECT COUNT(*) FROM alz JOIN studies USING (nct_id) WHERE study_type = 'INTERVENTIONAL'), 1) AS pct_of_alzheimer_trials
FROM interventions i
JOIN alz a USING (nct_id)
JOIN studies s USING (nct_id)
WHERE s.study_type = 'INTERVENTIONAL'
GROUP BY i.intervention_type
ORDER BY trials DESC;
