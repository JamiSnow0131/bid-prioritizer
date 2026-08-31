"""Bid scoring engine.

This is a direct port of the formulas in Wall Whisperers Bid Prioritizer.xlsx:
  - Data_and_Scoring: raw bid inputs (columns A-N) and outcomes (column O)
  - CriteriaOptions: per-criterion weights (row 1) and the weighted score formula
  - Lookups: the multiplier tables each criterion's value is translated through

Weights sum to 100 by convention, which keeps the score on a 0-100 scale and
keeps the No-bid / Maybe / Bid band thresholds (25 / 50 / 75) meaningful.
"""

import pandas as pd

DEFAULT_WEIGHTS = {
    "client_type": 21.25,
    "payment_history": 21.25,
    "project_fit": 21.25,
    "timeline_pressure": 21.25,
    "estimating_capacity": 5.0,
    "crew": 10.0,
}

# --- Lookups tab, ported as dicts -------------------------------------------

CLIENT_TYPE_MULT = {"Repeat": 1.0, "New": 0.5}
PAYMENT_HISTORY_MULT = {"Established-Good": 1.0, "Unknown": 0.5, "Flagged-Slow": 0.2}
PROJECT_FIT_MULT = {"Core": 1.0, "Stretch": 0.5}
TIMELINE_MULT = {"Normal": 1.0, "Rushed": 0.5}

# Estimating Team Capacity: % of the estimating team's time already committed
# elsewhere. Higher = less available = lower multiplier.
CAPACITY_MULT = {0: 1.0, 25: 0.8, 50: 0.6, 75: 0.4, 100: 0.2}

# Crew Available minus Crew Needed. Negative surplus (a shortfall) is a hard
# gate: it zeroes this sub-score, which in turn zeroes the whole bid score.
CREW_SURPLUS_MULT = {0: 0.2, 1: 0.4, 2: 0.6, 3: 0.8, 4: 1.0}

# (low, high, index) - bands used both for the recommendation label and for
# bucketing historical bids when computing win probability. Two distinct
# bands (2 and 3) both display as "Maybe" but are tracked separately, exactly
# like CriteriaOptions columns S:AB in the original workbook.
SCORE_BANDS = [
    (0, 25, 1, "No-bid"),
    (26, 50, 2, "Maybe"),
    (51, 75, 3, "Maybe"),
    (76, 100, 4, "Bid"),
]


def _capacity_multiplier(pct):
    if pct in CAPACITY_MULT:
        return CAPACITY_MULT[pct]
    nearest = min(CAPACITY_MULT, key=lambda k: abs(k - pct))
    return CAPACITY_MULT[nearest]


def _crew_multiplier(surplus):
    if surplus < 0:
        return 0.0
    return CREW_SURPLUS_MULT.get(min(surplus, 4), 1.0)


def band_for_score(score):
    """Returns (low, high, index, label) for the band a score falls into."""
    for low, high, index, label in SCORE_BANDS:
        if low <= score <= high:
            return (low, high, index, label)
    return SCORE_BANDS[0]


def score_bid(bid: dict, weights: dict = DEFAULT_WEIGHTS) -> float:
    """Replicates CriteriaOptions columns B-P for a single bid.

    `bid` keys: client_type, payment_history, project_fit, timeline_pressure,
    estimating_capacity_pct, crew_needed, crew_available.
    """
    client_mult = CLIENT_TYPE_MULT.get(bid["client_type"], 0.0)
    payment_mult = PAYMENT_HISTORY_MULT.get(bid["payment_history"], 0.0)
    fit_mult = PROJECT_FIT_MULT.get(bid["project_fit"], 0.0)
    timeline_mult = TIMELINE_MULT.get(bid["timeline_pressure"], 0.0)
    capacity_mult = _capacity_multiplier(bid["estimating_capacity_pct"])

    crew_surplus = bid["crew_available"] - bid["crew_needed"]
    crew_mult = _crew_multiplier(crew_surplus)

    capacity_points = capacity_mult * weights["estimating_capacity"]
    crew_points = crew_mult * weights["crew"]

    # Hard gate, mirrors CriteriaOptions!P: =IF(OR(J=0,O=0),0,...)
    if capacity_points == 0 or crew_points == 0:
        return 0.0

    score = (
        client_mult * weights["client_type"]
        + payment_mult * weights["payment_history"]
        + fit_mult * weights["project_fit"]
        + timeline_mult * weights["timeline_pressure"]
        + capacity_points
        + crew_points
    )
    return round(score, 3)


def recommendation(score: float) -> str:
    return band_for_score(score)[3]


# Denominator for the win-rate calc. Matches CriteriaOptions!Y: Won / (No-Bid
# + Won + Lost) for that band -- a declined bid still counts against the odds
# for that score band, it just isn't a win.
COUNTED_OUTCOMES = {"Won", "Lost", "No-Bid"}


def _band_win_rate(historical_df: pd.DataFrame, hist_scores: pd.Series, low: float, high: float):
    in_band = hist_scores.between(low, high)
    counted = historical_df.loc[in_band, "bid_outcome"]
    counted = counted[counted.isin(COUNTED_OUTCOMES)]
    if len(counted) == 0:
        return None
    return (counted == "Won").mean()


def win_probability(score: float, historical_df: pd.DataFrame, weights: dict):
    """Recompute every historical bid's score under `weights`, bucket it into
    the same band as `score`, and return the empirical Won rate for that
    band (None if no counted historical bids fall in it).
    """
    low, high, _index, _label = band_for_score(score)
    hist_scores = historical_df.apply(lambda r: score_bid(r.to_dict(), weights), axis=1)
    return _band_win_rate(historical_df, hist_scores, low, high)


def band_stats(historical_df: pd.DataFrame, weights: dict) -> list[dict]:
    """Per-band bid counts and win rates for the current weights, used by the
    Criteria Weights tab to show how reweighting reshuffles the historical
    bids."""
    hist_scores = historical_df.apply(lambda r: score_bid(r.to_dict(), weights), axis=1)
    rows = []
    for low, high, _index, label in SCORE_BANDS:
        in_band = hist_scores.between(low, high)
        win_rate = _band_win_rate(historical_df, hist_scores, low, high)
        rows.append(
            {
                "Band": f"{low}-{high} ({label})",
                "Historical Bids": int(in_band.sum()),
                "Win Rate": f"{win_rate * 100:.0f}%" if win_rate is not None else "no data",
            }
        )
    return rows


def score_breakdown(bid: dict, weights: dict = DEFAULT_WEIGHTS) -> list[dict]:
    """Per-criterion rows for a transparency table, mirroring CriteriaOptions
    columns B-O for one bid."""
    client_mult = CLIENT_TYPE_MULT.get(bid["client_type"], 0.0)
    payment_mult = PAYMENT_HISTORY_MULT.get(bid["payment_history"], 0.0)
    fit_mult = PROJECT_FIT_MULT.get(bid["project_fit"], 0.0)
    timeline_mult = TIMELINE_MULT.get(bid["timeline_pressure"], 0.0)
    capacity_mult = _capacity_multiplier(bid["estimating_capacity_pct"])
    crew_surplus = bid["crew_available"] - bid["crew_needed"]
    crew_mult = _crew_multiplier(crew_surplus)

    rows = [
        ("Client Type", bid["client_type"], client_mult, weights["client_type"]),
        ("Payment History", bid["payment_history"], payment_mult, weights["payment_history"]),
        ("Project Fit", bid["project_fit"], fit_mult, weights["project_fit"]),
        ("Timeline Pressure", bid["timeline_pressure"], timeline_mult, weights["timeline_pressure"]),
        ("Estimating Capacity", f"{bid['estimating_capacity_pct']}%", capacity_mult, weights["estimating_capacity"]),
        ("Crew Surplus", crew_surplus, crew_mult, weights["crew"]),
    ]
    return [
        {
            "Criterion": name,
            "Value": value,
            "Multiplier": mult,
            "Weight": weight,
            "Points": round(mult * weight, 3),
        }
        for name, value, mult, weight in rows
    ]
