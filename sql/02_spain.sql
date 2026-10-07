-- Question 2: how important is Spain in clinical research?
-- Counts interventional trials (any status) with at least one site in each country.

-- @output: europe_ranking
WITH trials AS (
    SELECT DISTINCT c.nct_id, c.name AS country
    FROM countries c
    JOIN studies s USING (nct_id)
    WHERE NOT c.removed
      AND s.study_type = 'INTERVENTIONAL'
      AND c.name IN ('Spain', 'France', 'Germany', 'Italy', 'United Kingdom', 'Netherlands', 'Belgium',
                     'Poland', 'Denmark', 'Sweden', 'Switzerland', 'Austria', 'Portugal', 'Norway',
                     'Czechia', 'Greece', 'Ireland', 'Finland', 'Hungary')
)
SELECT
    t.country,
    COUNT(*) AS trials,
    COUNT(*) FILTER (WHERE l.sponsor_type = 'Industry') AS industry_trials,
    ROUND(100.0 * COUNT(*) FILTER (WHERE l.sponsor_type = 'Industry') / COUNT(*), 1) AS industry_pct
FROM trials t
JOIN lead_sponsor l USING (nct_id)
GROUP BY t.country
ORDER BY trials DESC;

-- @output: spain_by_year
SELECT
    year(s.start_date) AS start_year,
    COUNT(DISTINCT s.nct_id) AS trials,
    ROUND(100.0 * COUNT(DISTINCT s.nct_id) FILTER (WHERE l.sponsor_type = 'Industry') / COUNT(DISTINCT s.nct_id), 1) AS industry_pct
FROM studies s
JOIN countries c USING (nct_id)
JOIN lead_sponsor l USING (nct_id)
WHERE c.name = 'Spain' AND NOT c.removed
  AND s.study_type = 'INTERVENTIONAL'
  AND year(s.start_date) BETWEEN 2005 AND 2025
GROUP BY start_year
ORDER BY start_year;

-- @output: spain_top_cities
SELECT
    f.city,
    COUNT(DISTINCT f.nct_id) AS trials
FROM facilities f
JOIN studies s USING (nct_id)
WHERE f.country = 'Spain' AND s.study_type = 'INTERVENTIONAL'
GROUP BY f.city
ORDER BY trials DESC
LIMIT 15;

-- @output: galicia_hospitals
-- Hospital names are written in many different ways (e.g. "Complejo Hospitalario Universitario
-- A Coruña", "Complexo Hospitalario...", "Hosp Univ A Coruna", "Hospital Juan Canalejo"...).
-- They are grouped into the 7 university hospital complexes of Galicia with keyword rules.
-- Sites named generically by the sponsor ("Research Site", "Novartis Investigative Site")
-- cannot be assigned and are left out.
WITH galicia AS (
    SELECT DISTINCT
        f.nct_id,
        lower(strip_accents(coalesce(f.name, ''))) AS n,
        lower(strip_accents(coalesce(f.city, ''))) AS c
    FROM facilities f
    JOIN studies s USING (nct_id)
    WHERE f.country = 'Spain' AND s.study_type = 'INTERVENTIONAL'
      AND regexp_matches(lower(strip_accents(coalesce(f.city, ''))), 'coru|santiago|vigo|lugo|ourense|orense|pontevedra|ferrol')
)
SELECT hospital, COUNT(DISTINCT nct_id) AS trials
FROM (
    SELECT nct_id,
        CASE
            WHEN regexp_matches(n, 'canalejo|chuac|(complejo|complexo|hospital|hosp)\.? ?(hospitalario )?(univ|universitario)?\.? ?(de )?(a |la )?coru') OR regexp_matches(n, 'oncologico de galicia') AND c LIKE '%coru%'
                THEN 'CHUAC'
            WHEN regexp_matches(n, 'chus|santiago|clinico universitario de santiago|conxo')
                THEN 'CHU Santiago de Compostela'
            WHEN regexp_matches(n, 'vigo|cunqueiro|meixoeiro|xeral|chuvi')
                THEN 'CHU Vigo'
            WHEN regexp_matches(n, 'lucus augusti|hula|lugo')
                THEN 'HU Lucus Augusti (Lugo)'
            WHEN regexp_matches(n, 'ourense|orense|chuo|cristal')
                THEN 'CHU Ourense'
            WHEN regexp_matches(n, 'pontevedra|montecelo|chop')
                THEN 'CHU Pontevedra'
            WHEN regexp_matches(n, 'ferrol|arquitecto marcide|naval')
                THEN 'CHU Ferrol'
            ELSE NULL
        END AS hospital
    FROM galicia
) x
WHERE hospital IS NOT NULL
GROUP BY hospital
ORDER BY trials DESC;
