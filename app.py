"""Streamlit dashboard for the clinical trials analysis (ClinicalTrials.gov / AACT).

Reads the small CSV summaries in outputs/ produced by scripts/02_run_analysis.py,
so it can be deployed without the 560 MB database.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

OUT = Path(__file__).parent / "outputs"

st.set_page_config(page_title="Why Clinical Trials Fail", page_icon="🧪", layout="wide")

ACCENT = "#2a78d6"     # highlighted series
SECOND = "#eb6834"     # comparison series
MUTED = "#c9c8c1"      # everything else
INK = "#52514e"

PHASE_LABELS = {"EARLY_PHASE1": "Early phase 1", "PHASE1": "Phase 1", "PHASE1/PHASE2": "Phase 1/2",
                "PHASE2": "Phase 2", "PHASE2/PHASE3": "Phase 2/3", "PHASE3": "Phase 3",
                "PHASE4": "Phase 4", "NA": "No phase (devices, procedures...)"}


@st.cache_data
def load(name):
    # keep_default_na=False: "NA" is a real phase value ("not applicable"), not a missing one
    return pd.read_csv(OUT / f"{name}.csv", keep_default_na=False, na_values=[""])


def style(fig, height=380, xtitle=None, ytitle=None):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white",
                      paper_bgcolor="white", font=dict(color=INK, size=13), showlegend=False,
                      xaxis_title=xtitle, yaxis_title=ytitle, hoverlabel=dict(bgcolor="white"))
    fig.update_xaxes(gridcolor="#eeeeec", zeroline=False)
    fig.update_yaxes(gridcolor="#eeeeec", zeroline=False)
    return fig


def hbar(df, y, x, highlight, xtitle, hover_extra=None, fmt="{:.1f}%"):
    df = df.sort_values(x)
    colors = [ACCENT if v in highlight else MUTED for v in df[y]]
    fig = go.Figure(go.Bar(x=df[x], y=df[y], orientation="h", marker_color=colors,
                           text=[fmt.format(v) for v in df[x]], textposition="outside",
                           customdata=df[hover_extra] if hover_extra else None,
                           hovertemplate="%{y}<br>" + xtitle + ": %{x}" +
                                         ("<br>Trials: %{customdata:,}" if hover_extra else "") + "<extra></extra>"))
    fig.update_xaxes(range=[0, df[x].max() * 1.18])
    return style(fig, height=max(260, 34 * len(df)), xtitle=xtitle)


def table(df):
    with st.expander("See the data"):
        st.dataframe(df, hide_index=True, width="stretch")


phase = load("failure_by_phase")
reasons = load("stop_reasons")
europe = load("europe_ranking")

st.title("Why do clinical trials fail?")
st.caption("SQL analysis of 600,000+ studies registered on ClinicalTrials.gov (AACT database). "
           "Failed = stopped early (terminated) or cancelled before enrolling anyone (withdrawn).")

total = int(phase["trials"].sum())
failed = int(phase["failed"].sum())
given = reasons[reasons["reason"] != "Not reported"]
recruit_pct = 100 * given.loc[given["reason"] == "Low recruitment / feasibility", "trials"].sum() / given["trials"].sum()
spain_rank = int(europe.reset_index().query('country == "Spain"').index[0]) + 1
spain_trials = int(europe.loc[europe["country"] == "Spain", "trials"].iloc[0])
c1, c2, c3, c4 = st.columns(4)
c1.metric("Finished interventional trials", f"{total:,}")
c1.caption("with a known final outcome")
c2.metric("Failed", f"{100 * failed / total:.1f}%")
c2.caption(f"{failed:,} trials stopped early or cancelled")
c3.metric("Failed for lack of patients", f"{recruit_pct:.0f}%")
c3.caption("of failed trials that give a reason")
c4.metric("Spain in Europe", f"#{spain_rank}")
c4.caption(f"{spain_trials:,} interventional trials")

tab1, tab2, tab3, tab4 = st.tabs(["1 · Why trials fail", "2 · Spain", "3 · Alzheimer's", "About the data"])

# ---------------------------------------------------------------- 1. Why trials fail
with tab1:
    st.subheader("Most trials don't fail because the treatment doesn't work")
    st.write("Among failed trials that give a reason, the main one is not finding enough patients. "
             "Safety and lack of efficacy together explain fewer than 1 in 10.")
    r = given.copy()
    r["pct"] = 100 * r["trials"] / r["trials"].sum()
    st.plotly_chart(hbar(r, "reason", "pct", {"Low recruitment / feasibility"}, "% of failed trials with a reason",
                         hover_extra="trials"), width="stretch")
    table(reasons)

    st.subheader("Industry and academia fail for different reasons")
    st.write("Companies mostly stop trials for business decisions; universities and hospitals run out of patients or money.")
    rs = load("stop_reasons_by_sponsor")
    top = ["Sponsor / business decision", "Low recruitment / feasibility", "Funding", "Efficacy / futility", "Safety"]
    rs = rs[rs["reason"].isin(top) & rs["sponsor_type"].isin(["Industry", "Universities, hospitals & others"])]
    fig = px.bar(rs, x="pct_within_sponsor", y="reason", color="sponsor_type", orientation="h", barmode="group",
                 category_orders={"reason": top},
                 color_discrete_map={"Industry": ACCENT, "Universities, hospitals & others": SECOND},
                 labels={"pct_within_sponsor": "% of that sponsor's failed trials", "reason": "",
                         "sponsor_type": "Lead sponsor"})
    fig = style(fig, height=380, xtitle="% of that sponsor's failed trials")
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.08, x=0, title=None))
    st.plotly_chart(fig, width="stretch")
    table(load("stop_reasons_by_sponsor"))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Phase 2 is the riskiest step")
        p = phase.copy()
        p["phase"] = p["phase"].map(PHASE_LABELS)
        st.plotly_chart(hbar(p, "phase", "failure_rate_pct", {"Phase 2", "Phase 1/2"}, "Failure rate",
                             hover_extra="trials"), width="stretch")
        table(phase)
    with col2:
        st.subheader("Cancer trials fail the most")
        a = load("failure_by_area")
        st.plotly_chart(hbar(a, "area", "failure_rate_pct", {"Neoplasms"}, "Failure rate", hover_extra="trials"),
                        width="stretch")
        table(a)

# ---------------------------------------------------------------- 2. Spain
with tab2:
    st.subheader("Spain is the 4th country in Europe for clinical trials")
    e = europe.copy()
    st.plotly_chart(hbar(e, "country", "trials", {"Spain"}, "Interventional trials with a site in the country",
                         fmt="{:,.0f}"), width="stretch")
    table(europe)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Trials in Spain have quadrupled since 2005")
        y = load("spain_by_year")
        fig = go.Figure(go.Scatter(x=y["start_year"], y=y["trials"], mode="lines+markers",
                                   line=dict(color=ACCENT, width=2), marker=dict(size=8),
                                   hovertemplate="%{x}: %{y:,} trials<extra></extra>"))
        fig.update_yaxes(rangemode="tozero")
        st.plotly_chart(style(fig, xtitle="Start year", ytitle="Trials started"), width="stretch")
    with col2:
        st.subheader("…and half are now led by non-industry sponsors")
        fig = go.Figure(go.Scatter(x=y["start_year"], y=y["industry_pct"], mode="lines+markers",
                                   line=dict(color=ACCENT, width=2), marker=dict(size=8),
                                   hovertemplate="%{x}: %{y:.1f}% industry-led<extra></extra>"))
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(style(fig, xtitle="Start year", ytitle="% led by industry"), width="stretch")
    table(y)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("A Coruña and Santiago are in Spain's top 10")
        cities = load("spain_top_cities")
        st.plotly_chart(hbar(cities, "city", "trials", {"A Coruña", "Santiago de Compostela"}, "Trials",
                             fmt="{:,.0f}"), width="stretch")
        table(cities)
    with col2:
        st.subheader("Galicia: trials by university hospital complex")
        g = load("galicia_hospitals")
        st.plotly_chart(hbar(g, "hospital", "trials", {"CHU Santiago de Compostela", "CHUAC"}, "Trials",
                             fmt="{:,.0f}"), width="stretch")
        st.caption("Hospital names appear in dozens of spellings in the registry; they were grouped with keyword rules. "
                   "Sites named generically by sponsors (\"Research Site\") cannot be assigned, so these are lower bounds.")
        table(g)

# ---------------------------------------------------------------- 3. Alzheimer's
with tab3:
    vs = load("alzheimer_vs_all_by_phase")
    st.subheader("Alzheimer's trials fail late, when it costs the most")
    st.write("In phases 1 and 2 Alzheimer's trials fail at a similar rate to the rest. "
             "In phase 3, the most expensive stage, they fail almost twice as often.")
    m = vs.melt(id_vars="phase", value_vars=["alzheimer_failure_pct", "others_failure_pct"],
                var_name="group", value_name="failure_rate")
    m["group"] = m["group"].map({"alzheimer_failure_pct": "Alzheimer's", "others_failure_pct": "All other trials"})
    m["phase"] = m["phase"].map(PHASE_LABELS)
    fig = px.bar(m, x="phase", y="failure_rate", color="group", barmode="group", text="failure_rate",
                 color_discrete_map={"Alzheimer's": ACCENT, "All other trials": MUTED},
                 labels={"failure_rate": "Failure rate (%)", "phase": "", "group": ""})
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig = style(fig, height=380, ytitle="Failure rate (%)")
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.1, x=0, title=None))
    st.plotly_chart(fig, width="stretch")
    table(vs)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("When they stop, it's 2× more often for lack of efficacy")
        ar = load("alzheimer_stop_reasons")
        ar = ar[ar["reason"].isin(["Low recruitment / feasibility", "Efficacy / futility", "Safety", "Funding",
                                   "Sponsor / business decision"])]
        m2 = ar.melt(id_vars="reason", value_vars=["alzheimer_pct", "others_pct"], var_name="group", value_name="pct")
        m2["group"] = m2["group"].map({"alzheimer_pct": "Alzheimer's", "others_pct": "All other trials"})
        fig = px.bar(m2, x="pct", y="reason", color="group", orientation="h", barmode="group",
                     color_discrete_map={"Alzheimer's": ACCENT, "All other trials": MUTED},
                     labels={"pct": "% of failed trials with a reason", "reason": "", "group": ""})
        fig = style(fig, height=380, xtitle="% of failed trials with a reason")
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.1, x=0, title=None))
        st.plotly_chart(fig, width="stretch")
        table(load("alzheimer_stop_reasons"))
    with col2:
        st.subheader("Research keeps growing, but industry's share has halved")
        ay = load("alzheimer_by_year")
        ay["Industry-led"] = ay["industry_trials"]
        ay["Others"] = ay["trials"] - ay["industry_trials"]
        fig = go.Figure()
        fig.add_bar(x=ay["start_year"], y=ay["Industry-led"], name="Industry-led", marker_color=ACCENT,
                    hovertemplate="%{x}: %{y} industry-led<extra></extra>")
        fig.add_bar(x=ay["start_year"], y=ay["Others"], name="Universities, hospitals & others", marker_color=MUTED,
                    hovertemplate="%{x}: %{y} others<extra></extra>")
        fig = style(fig, height=380, xtitle="Start year", ytitle="Alzheimer's trials started")
        fig.update_layout(barmode="stack", bargap=0.15, showlegend=True,
                          legend=dict(orientation="h", y=1.1, x=0, title=None))
        st.plotly_chart(fig, width="stretch")
        table(load("alzheimer_by_year"))

# ---------------------------------------------------------------- About
with tab4:
    st.markdown("""
**Source.** [AACT](https://aact.ctti-clinicaltrials.org), the relational copy of ClinicalTrials.gov
maintained by the Clinical Trials Transformation Initiative. Queried with SQL (DuckDB); all queries are in the
`sql/` folder of the repository.

**Definitions and decisions**
- *Failed* = `TERMINATED` (stopped early) or `WITHDRAWN` (cancelled before enrolling). Compared only with
  `COMPLETED` trials; ongoing trials and those with status `UNKNOWN` are excluded because their outcome is not known.
- Only interventional trials. The 123 finished trials with no phase recorded are excluded.
- Stop reasons are free text, grouped into categories with keyword rules. 17% of the reasons given don't
  match any rule ("Other") and 11% of failed trials give no reason at all.
- Disease areas come from MeSH terms; a trial can belong to several areas.

**Limitations**
- ClinicalTrials.gov is a US registry: European trials are covered, but not completely.
- Failure rates for older trials (before ~2007) look lower, partly because reporting rules were weaker then.
- Hospital names are inconsistent across the registry, so hospital counts are approximate.
""")
