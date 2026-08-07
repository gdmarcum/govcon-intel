from datetime import date

WEIGHTS = {
    "capability_match": 0.4,
    "agency_experience": 0.3,
    "recency": 0.15,
    "teaming_history": 0.15,
}

RECENCY_HALF_LIFE_DAYS = 730


def _normalize(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return min(value / max_value, 1.0)


def _recency_score(most_recent_win, today: date) -> float:
    if most_recent_win is None:
        return 0.0
    days_ago = (today - most_recent_win.to_native()).days
    return 0.5 ** (days_ago / RECENCY_HALF_LIFE_DAYS)


def score_candidates(candidates: list[dict], today: date | None = None) -> list[dict]:
    today = today or date.today()
    max_capability = max((c["capability_match"] for c in candidates), default=0)
    max_agency = max((c["agency_contracts"] for c in candidates), default=0)
    max_teaming = max((c["teaming_count"] for c in candidates), default=0)
    scored = []
    for c in candidates:
        total = (
            WEIGHTS["capability_match"] * _normalize(c["capability_match"], max_capability)
            + WEIGHTS["agency_experience"] * _normalize(c["agency_contracts"], max_agency)
            + WEIGHTS["recency"] * _recency_score(c["most_recent_win"], today)
            + WEIGHTS["teaming_history"] * _normalize(c["teaming_count"], max_teaming)
        )
        scored.append({**c, "score": round(total, 4)})
    return sorted(scored, key=lambda c: c["score"], reverse=True)