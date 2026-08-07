import os
from datetime import date, timedelta

import psycopg
from apscheduler.schedulers.blocking import BlockingScheduler

from etl.sam_pull import enrich_entities
from etl.usaspending_pull import fetch_award_detail, search_awards, search_subawards
from graph.queries import GraphClient

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

def run_subaward_pull():
    graph = GraphClient(os.environ["NEO4J_URI"], os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
    subawards = search_subawards(
        naics_codes=NAICS_CODES,
        agency_names=AGENCIES,
        start_date=date.today() - timedelta(days=1),
        end_date=date.today(),
    )
    for sub in subawards:
        prime_uei = sub.get("Prime Recipient UEI") or ""
        sub_uei = sub.get("Sub-Awardee UEI") or ""
        amount = sub.get("Sub-Award Amount") or 0
        if prime_uei and sub_uei:
            graph.upsert_subcontract(prime_uei=prime_uei, sub_uei=sub_uei, amount=amount)
    graph.close()

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(run_daily_pull, "cron", hour=3)
    scheduler.add_job(run_sam_enrichment, "cron", hour=4)
    scheduler.add_job(run_subaward_pull, "cron", hour=5)
    scheduler.start()
