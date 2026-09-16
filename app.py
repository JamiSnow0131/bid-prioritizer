import pandas as pd
import streamlit as st

import auth
import branding
from scoring import (
    DEFAULT_WEIGHTS,
    band_stats,
    recommendation,
    score_bid,
    score_breakdown,
    win_probability,
)

st.set_page_config(page_title="Bid Prioritizer", page_icon="📋", layout="wide")

auth.require_password()

branding.render_header()

HIST_PATH = "data/historical_bids.csv"

PROJECT_TYPES = [
    "Tenant Fit-Out",
    "Warehouse",
    "Retail Buildout",
    "Light Industrial",
    "Cold Storage Facility",
    "Medical Office Buildout",
    "Multi-Family Renovation",
    "Other",
]

# Raw export column -> internal schema. Handles the source file's spacing/
# casing quirks (e.g. " Project_Value ", "Estimating_Team_Capacity").
COLUMN_MAP = {
    "Bid_ID": "bid_id",
    "Client_Name": "client_name",
    "Client_Type": "client_type",
    "Payment_History": "payment_history",
    "Project_Type": "project_type",
    "Project_Fit": "project_fit",
    "Project_Value": "project_value",
    "Timeline_Pressure": "timeline_pressure",
    "Competitor_Count": "competitor_count",
    "Estimating_Team_Capacity": "estimating_capacity_pct",
    "Crew_Needed": "crew_needed",
    "Crew_Available": "crew_available",
    "Specialist": "specialist",
    "Specialist_Type": "specialist_type",
    "Bid_Outcome": "bid_outcome",
}


@st.cache_data
def load_historical():
    try:
        df = pd.read_csv(HIST_PATH)
    except FileNotFoundError:
        return None

    df.columns = df.columns.str.strip()
    df = df.rename(columns=COLUMN_MAP)

    text_columns = [
        "client_name", "client_type", "payment_history", "project_type",
        "project_fit", "timeline_pressure", "specialist", "specialist_type",
        "bid_outcome",
    ]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].str.strip()

    if "project_value" in df.columns:
        df["project_value"] = (
            df["project_value"].str.replace(r"[\$,]", "", regex=True).astype(float)
        )

    return df


if "weights" not in st.session_state:
    st.session_state.weights = dict(DEFAULT_WEIGHTS)

historical_df = load_historical()


def next_bid_id_placeholder():
    if historical_df is None or "bid_id" not in historical_df.columns:
        return "e.g. B-101"
    numbers = historical_df["bid_id"].str.extract(r"(\d+)$")[0].dropna().astype(int)
    if numbers.empty:
        return "e.g. B-101"
    return f"e.g. B-{numbers.max() + 1}"


st.title("Bid Prioritizer")

tab_new_bid, tab_weights = st.tabs(["New Bid", "Criteria Weights"])

# ---------------------------------------------------------------- New Bid --
with tab_new_bid:
    if historical_df is None:
        st.warning(
            f"No historical data found at `{HIST_PATH}`. Score and "
            "recommendation will still work, but Probability of Win needs "
            "the historical bids CSV to be in place."
        )

    with st.form("new_bid_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            bid_id = st.text_input("Bid ID", placeholder=next_bid_id_placeholder())
            client_name = st.text_input("Client Name")
            client_type = st.selectbox("Client Type", ["Repeat", "New"])
            payment_history = st.selectbox(
                "Payment History", ["Established-Good", "Unknown", "Flagged-Slow"]
            )

        with col2:
            project_type = st.selectbox("Project Type", PROJECT_TYPES)
            project_type_other = st.text_input(
                "Specify Other Project Type", disabled=(project_type != "Other")
            )
            project_fit = st.selectbox("Project Fit", ["Core", "Stretch"])
            project_value = st.number_input("Project Value ($)", min_value=0, step=1000)
            timeline_pressure = st.selectbox("Timeline Pressure", ["Normal", "Rushed"])
            competitor_count = st.number_input("Competitor Count", min_value=0, step=1)

        with col3:
            estimating_capacity_pct = st.select_slider(
                "Estimating Team Capacity Committed (%)", options=[0, 25, 50, 75, 100]
            )
            crew_needed = st.number_input("Crew Needed", min_value=0, step=1)
            crew_available = st.number_input("Crew Available", min_value=0, step=1)
            specialist = st.selectbox("Specialist?", ["No", "Yes"])
            specialist_type = st.text_input("Specialist Type", disabled=(specialist == "No"))

        submitted = st.form_submit_button("Score This Bid")

    if submitted:
        bid = {
            "client_type": client_type,
            "payment_history": payment_history,
            "project_fit": project_fit,
            "timeline_pressure": timeline_pressure,
            "estimating_capacity_pct": estimating_capacity_pct,
            "crew_needed": crew_needed,
            "crew_available": crew_available,
        }

        score = score_bid(bid, st.session_state.weights)
        rec = recommendation(score)
        prob = (
            win_probability(score, historical_df, st.session_state.weights)
            if historical_df is not None
            else None
        )

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Score", f"{score:.1f} / 100")

        rec_color = {"Bid": "green", "Maybe": "orange", "No-bid": "red"}[rec]
        m2.markdown(f"### Recommendation\n:{rec_color}[**{rec}**]")

        if prob is not None:
            m3.metric("Probability of Win", f"{prob * 100:.0f}%")
        else:
            m3.metric("Probability of Win", "No data")

        if crew_available < crew_needed:
            st.error(
                "Crew Available is less than Crew Needed — this forces the "
                "score to 0 regardless of other criteria (hard gate, same as "
                "the original spreadsheet)."
            )

        st.subheader("Score Breakdown")
        st.dataframe(
            pd.DataFrame(score_breakdown(bid, st.session_state.weights)),
            hide_index=True,
            use_container_width=True,
        )

# ----------------------------------------------------------- Weights tab --
with tab_weights:
    st.write(
        "Adjust the weight each criterion carries in the score (weights are "
        "normalized to sum to 100, so the No-bid / Maybe / Bid bands stay "
        "meaningful). Changes here apply immediately to the New Bid tab."
    )

    w = st.session_state.weights
    c1, c2 = st.columns(2)
    with c1:
        w["client_type"] = st.number_input("Client Type", min_value=0.0, value=w["client_type"])
        w["payment_history"] = st.number_input(
            "Payment History", min_value=0.0, value=w["payment_history"]
        )
        w["project_fit"] = st.number_input("Project Fit", min_value=0.0, value=w["project_fit"])
    with c2:
        w["timeline_pressure"] = st.number_input(
            "Timeline Pressure", min_value=0.0, value=w["timeline_pressure"]
        )
        w["estimating_capacity"] = st.number_input(
            "Estimating Capacity", min_value=0.0, value=w["estimating_capacity"]
        )
        w["crew"] = st.number_input("Crew Availability", min_value=0.0, value=w["crew"])

    total = sum(w.values())
    st.write(f"**Current total: {total:.1f}** (should be 100)")

    b1, b2 = st.columns(2)
    if b1.button("Normalize to 100"):
        if total > 0:
            for k in w:
                w[k] = round(w[k] / total * 100, 3)
            st.rerun()
    if b2.button("Reset to Original Weights"):
        st.session_state.weights = dict(DEFAULT_WEIGHTS)
        st.rerun()

    if historical_df is not None:
        st.divider()
        st.subheader("How these weights sort your historical bids")

        rows = band_stats(historical_df, st.session_state.weights)
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    else:
        st.info(f"Add `{HIST_PATH}` to see how weight changes affect historical bid outcomes.")

branding.render_footer()
