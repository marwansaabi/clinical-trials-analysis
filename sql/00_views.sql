-- Shared views used by every analysis.
-- "Finished" trials: interventional studies whose final outcome is known.
--   failed = TERMINATED (stopped early) or WITHDRAWN (cancelled before enrolling anyone)
--   Excluded: ongoing trials, UNKNOWN status (not updated for years) and the 123 trials with no phase recorded.
CREATE OR REPLACE TEMP VIEW finished AS
SELECT
    nct_id,
    phase,
    overall_status,
    why_stopped,
    year(start_date) AS start_year,
    overall_status IN ('TERMINATED', 'WITHDRAWN') AS failed
FROM studies
WHERE study_type = 'INTERVENTIONAL'
  AND overall_status IN ('COMPLETED', 'TERMINATED', 'WITHDRAWN')
  AND phase IS NOT NULL;

-- Lead sponsor grouped into three types (every trial has exactly one lead sponsor).
CREATE OR REPLACE TEMP VIEW lead_sponsor AS
SELECT
    nct_id,
    name AS sponsor_name,
    CASE
        WHEN agency_class = 'INDUSTRY' THEN 'Industry'
        WHEN agency_class IN ('NIH', 'FED', 'OTHER_GOV') THEN 'Government'
        ELSE 'Universities, hospitals & others'
    END AS sponsor_type
FROM sponsors
WHERE lead_or_collaborator = 'lead';

-- Free-text stop reasons (why_stopped) grouped into categories with keyword rules.
-- Order matters: the first matching rule wins. "Not due to safety" phrases are caught
-- before the safety rule so they are not counted as safety problems.
CREATE OR REPLACE TEMP VIEW stop_reasons AS
WITH r AS (
    SELECT nct_id, lower(coalesce(why_stopped, '')) AS txt
    FROM finished
    WHERE failed
)
SELECT
    nct_id,
    CASE
        WHEN txt = '' THEN 'Not reported'
        WHEN regexp_matches(txt, 'covid|pandemi|coronavirus|sars-cov') THEN 'COVID-19'
        WHEN regexp_matches(txt, 'recr|enrol|accru|participant|subjects|eligible patients|inclusion|feasib|slow|no patients') THEN 'Low recruitment / feasibility'
        WHEN regexp_matches(txt, 'fund|financ|budget|grant|money|cost') THEN 'Funding'
        WHEN regexp_matches(txt, 'safety|adverse|toxicit|side effect|tolerab')
             AND NOT regexp_matches(txt, 'no(t)? (due to |related to |because of |based on |for )?(any )?(safety|tolerab)|without safety') THEN 'Safety'
        WHEN regexp_matches(txt, 'efficacy|futil|lack of (benefit|effect|response)|interim analys|ineffective|did not meet|endpoint|not effective|cure rate|response rate') THEN 'Efficacy / futility'
        WHEN regexp_matches(txt, 'business|strateg|portfolio|commercial|sponsor|decision|development|program|priorit|administrative|no longer (relevant|needed|necessary)') THEN 'Sponsor / business decision'
        WHEN regexp_matches(txt, 'never (activated|started|opened|initiated|began)|not (been )?(initiated|started|opened|activated)|did not (start|begin|open)') THEN 'Never started'
        WHEN regexp_matches(txt, 'investigator|\bpi\b|relocat|moved|leav|left the|staff|physician|team member|logistic|supply|equipment|resources') THEN 'Investigator / logistics'
        WHEN regexp_matches(txt, 'regulat|irb|ethic|fda|approval|authorit|clinical hold|\bind\b') THEN 'Regulatory / ethics'
        ELSE 'Other'
    END AS reason
FROM r;
