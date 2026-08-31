# Wall Whisperers Bid Prioritizer

A Streamlit port of `Wall Whisperers Bid Prioritizer.xlsx`. Enter a new bid's
details, adjust criteria weights to see how prioritization shifts, and get a
Go / Maybe / No-bid recommendation plus a probability of winning based on
historical bid outcomes.

## Project layout

- `app.py` — Streamlit UI (New Bid form + Criteria Weights tab)
- `scoring.py` — scoring engine, a direct port of the Data_and_Scoring /
  CriteriaOptions / Lookups formulas from the original workbook
- `data/historical_bids.csv` — historical bids used to compute win
  probability per score band (columns: bid_id, client_name, client_type,
  payment_history, project_type, project_fit, project_value,
  timeline_pressure, competitor_count, estimating_capacity_pct, crew_needed,
  crew_available, specialist, specialist_type, bid_outcome)

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

Push to GitHub, then deploy on [share.streamlit.io](https://share.streamlit.io)
pointing at `app.py` on the main branch.
