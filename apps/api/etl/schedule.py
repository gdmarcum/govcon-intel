import os
from datetime import date, timedelta

import psycopg
from apscheduler.schedulers.blocking import BlockingScheduler

from etl.sam_pull import enrich_entities
from etl.usaspending_pull import fetch_award_detail, search_awards

NAICS_CODES = ["541512", "541519"]
AGENCIES = ["Department of Defense", "Department of Homeland Security"]


def run_daily_pull():
    awards = search_awards(
        naics_codes=NAICS_CODES,
        agency_names=AGENCIES,
        start_date=date.today() - timedelta(days=1),
        end_date=date.today(),
    )
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            for award in awards:
                detail = fetch_award_detail(award["generated_internal_id"])
                cur.execute(
                    "INSERT INTO staging_usaspending_awards (raw_payload) VALUES (%s)",
                    (psycopg.types.json.Json(detail),),
                )
        conn.commit()


def run_sam_enrichment():
    api_key = os.environ["SAM_API_KEY"]
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT uei FROM companies WHERE uei IS NOT NULL AND cage_code IS NULL LIMIT 10"
            )
            ueis = [row[0] for row in cur.fetchall()]
        records = enrich_entities(ueis, api_key, requests_per_day_cap=10)
        with conn.cursor() as cur:
            for record in records:
                cur.execute(
                    "INSERT INTO staging_sam_entities (raw_payload) VALUES (%s)",
                    (psycopg.types.json.Json(record),),
                )
        conn.commit()


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(run_daily_pull, "cron", hour=3)
    scheduler.add_job(run_sam_enrichment, "cron", hour=4)
    scheduler.start()
