from etl.usaspending_pull import fetch_award_detail, search_awards, search_subawards

def build_subcontracts():
    client = GraphClient(os.environ["NEO4J_URI"], os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
    subawards = search_subawards(
        naics_codes=NAICS_CODES,
        agency_names=AGENCIES,
        start_date=date.today() - timedelta(days=730),
        end_date=date.today(),
    )
    if subawards:
        print("sample subaward keys, confirm before trusting the .get() calls below:")
        print(sorted(subawards[0].keys()))
    written = 0
    for sub in subawards[:SAMPLE_SIZE]:
        prime_uei = sub.get("Prime Recipient UEI") or ""
        sub_uei = sub.get("Sub-Awardee UEI") or ""
        amount = sub.get("Sub-Award Amount") or 0
        if prime_uei and sub_uei:
            client.upsert_subcontract(prime_uei=prime_uei, sub_uei=sub_uei, amount=amount)
            written += 1
    client.close()
    print(f"wrote {written} subcontract relationships")


if __name__ == "__main__":
    staged = stage_awards()
    resolve()
    build_graph(staged)
    build_subcontracts()