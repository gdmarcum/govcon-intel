import time
from datetime import date

import httpx

USASPENDING_BASE = "https://api.usaspending.gov"

SEARCH_FIELDS = [
    "Award ID",
    "Recipient Name",
    "Recipient UEI",
    "Awarding Agency",
    "Award Amount",
    "Start Date",
    "generated_internal_id",
]


def search_awards(
    naics_codes: list[str],
    agency_names: list[str],
    start_date: date,
    end_date: date,
    award_type_codes: tuple[str, ...] = ("A", "B", "C", "D"),
) -> list[dict]:
    results = []
    page = 1
    with httpx.Client(base_url=USASPENDING_BASE, timeout=30.0) as client:
        while True:
            body = {
                "filters": {
                    "time_period": [
                        {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
                    ],
                    "naics_codes": naics_codes,
                    "agencies": [
                        {"type": "awarding", "tier": "toptier", "name": name}
                        for name in agency_names
                    ],
                    "award_type_codes": list(award_type_codes),
                },
                "fields": SEARCH_FIELDS,
                "page": page,
                "limit": 100,
                "sort": "Award Amount",
                "order": "desc",
            }
            response = client.post("/api/v2/search/spending_by_award/", json=body)
            response.raise_for_status()
            payload = response.json()
            results.extend(payload["results"])
            if not payload.get("page_metadata", {}).get("hasNext", False):
                break
            page += 1
            time.sleep(0.3)
    return results


def fetch_award_detail(generated_internal_id: str) -> dict:
    with httpx.Client(base_url=USASPENDING_BASE, timeout=30.0) as client:
        response = client.get(f"/api/v2/awards/{generated_internal_id}/")
        response.raise_for_status()
        return response.json()
