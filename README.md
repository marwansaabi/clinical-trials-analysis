# Why Do Clinical Trials Fail?

SQL analysis of 600,000+ studies registered on ClinicalTrials.gov, using the
[AACT database](https://aact.ctti-clinicaltrials.org) (a relational copy of the registry with 40+ tables).

Three questions:
1. **Why do clinical trials fail?**
2. **How important is Spain in clinical research?** (with a look at Galicia, where I study)
3. **Why is Alzheimer's disease so hard?** (it connects with my [Alzheimer's drug classifier](https://github.com/marwansaabi/ml-alzheimer-classifier))

Tools: SQL (DuckDB), Python, Streamlit + Plotly for the dashboard.

## Key findings

### 1. Most trials don't fail because the treatment doesn't work
Out of 302,904 finished interventional trials, **43,749 (14.4%) failed**, meaning they were stopped early or cancelled before enrolling anyone.

- **Not finding enough patients is the #1 reason (38%)** among the failed trials that say why.
  Safety (2.9%) and lack of efficacy (4.8%) together explain fewer than 1 in 10.
- **Industry and academia fail for different reasons.** Companies mostly stop trials for
  business or strategic decisions (34% of their failures); universities and hospitals run out of
  patients (44%) or money (12%).
- **Phase 2 is the riskiest step** (22.6% failure, 26.8% in combined phase 1/2 trials). It is the first
  time a treatment is tested for efficacy in patients. Phase 3 trials fail less (15.1%) because they
  have already passed that filter.
- **Cancer trials fail the most** (25.0%), against 10.7% for nutritional and metabolic diseases.

### 2. Spain is the 4th country in Europe for clinical trials
- **21,100 interventional trials** have at least one site in Spain, after France (29,310),
  the UK (22,663) and Germany (22,400).
- The number of trials started each year in Spain **has quadrupled since 2005** (319 → 1,325 in 2025).
- **Non-industry research has grown the most:** industry led 72% of Spanish trials in 2005, and about
  50% today.
- **A Coruña and Santiago de Compostela are in Spain's top 10 cities** (8th and 9th, with ~1,580 trials each),
  above Zaragoza or Córdoba. CHUS (Santiago, 889 trials) and CHUAC (A Coruña, 754) lead in Galicia.

### 3. Alzheimer's trials fail late, when it costs the most
- In phases 1 and 2, Alzheimer's trials fail at a similar rate to other trials. **In phase 3 they fail almost
  twice as often: 27.7% vs 15.0%.** Phase 3 is the largest and most expensive stage, so these failures are the costliest.
- When they stop, it is **more than twice as often for lack of efficacy** (11.0% vs 4.7% of failures with a reason).
- Research keeps growing (≈200 new trials a year), but **industry's share has more than halved**:
  from 63% of new Alzheimer's trials in 2007–2009 to 27% in 2019–2025.

## Dashboard
The interactive dashboard (`app.py`) shows every chart with its data table.

```bash
streamlit run app.py
```

## Method and decisions
- **Definition of failure:** `TERMINATED` (stopped early) or `WITHDRAWN` (cancelled before enrolling), compared
  only with `COMPLETED` trials. Ongoing trials and trials with status `UNKNOWN` (not updated for years) are
  excluded, because their outcome is not known yet.
- Only **interventional** trials (the ones testing a treatment). The **123 finished trials with no phase recorded
  are excluded**. "No phase" (`NA`, not applicable) is kept as its own group: it covers devices, procedures and
  behavioural interventions.
- **Stop reasons** are free text written by each sponsor. I grouped them into 10 categories with keyword rules
  (`sql/00_views.sql`). The rules check, for example, that "not due to safety reasons" is not counted as a safety
  problem. 17% of the reasons don't match any rule ("Other") and 11% of failed trials give no reason at all.
- **Disease areas** come from MeSH terms (the standard medical vocabulary). A trial can belong to several areas.
- **Hospital names in Galicia** appear in many spellings ("Complejo Hospitalario Universitario A Coruña",
  "Complexo Hospitalario…", "Hosp Univ A Coruna", "Hospital Juan Canalejo"…). I grouped them into the 7 university
  hospital complexes with keyword rules. Sites named generically by sponsors ("Research Site") cannot be assigned,
  so these counts are lower bounds.

## Limitations
- ClinicalTrials.gov is a US registry. European trials are well covered but not completely.
- Trials started before ~2007 show lower failure rates, partly because reporting rules were weaker then.
- Failure rates by year stop at 2018: many recent trials are still running, so the ones already finished are
  biased towards those that stopped early.
- Keyword classification of free text is approximate; the categories should be read as orders of magnitude.

## Project structure
```
sql/00_views.sql         shared definitions (finished trials, sponsor type, stop-reason categories)
sql/01_failure.sql       question 1
sql/02_spain.sql         question 2
sql/03_alzheimer.sql     question 3
scripts/01_extract_aact.py   copies the needed AACT tables into a local DuckDB file
scripts/02_run_analysis.py   runs every query and saves the results in outputs/
outputs/                 query results (CSV) used by the dashboard
app.py                   Streamlit dashboard
```

## How to reproduce
1. Create a free account at https://aact.ctti-clinicaltrials.org and request database access.
2. Copy `.env.example` to `.env` and add your AACT database username and password.
3. `pip install -r requirements.txt`
4. `python scripts/01_extract_aact.py` → downloads the tables into `data/aact.duckdb` (~560 MB, not in the repo)
5. `python scripts/02_run_analysis.py` → regenerates `outputs/`
6. `streamlit run app.py`

Data snapshot: October 2026.
