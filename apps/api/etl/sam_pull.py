import time

import httpx

SAM_BASE = "https://api.sam.gov"


def fetch_entity(uei: str, api_key: str) -> dict:
    with httpx.Client(base_url=SAM_BASE, timeout=30.0) as client:
        response = client.get(
            "/entity-information/v3/entities",
            params={
                "api_key": api_key,
                "ueiSAM": uei,
                "includeSections": "entityRegistration,coreData,assertions",
            },
        )
        response.raise_for_status()
        return response.json()


def enrich_entities(ueis: list[str], api_key: str, requests_per_day_cap: int = 10) -> list[dict]:
    records = []
    for uei in ueis[:requests_per_day_cap]:
        records.append(fetch_entity(uei, api_key))
        time.sleep(1.0)
    return records


def search_opportunities(naics_code: str, posted_from: str, posted_to: str, api_key: str) -> dict:
    with httpx.Client(base_url=SAM_BASE, timeout=30.0) as client:
        response = client.get(
            "/opportunities/v2/search",
            params={
                "api_key": api_key,
                "postedFrom": posted_from,
                "postedTo": posted_to,
                "ncode": naics_code,
                "ptype": "o,k",
                "limit": 100,
                "offset": 0,
            },
        )
        response.raise_for_status()
        return response.json()
