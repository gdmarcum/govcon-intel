import pandas as pd
import psycopg
import splink.comparison_library as cl
from splink import DuckDBAPI, Linker, SettingsCreator, block_on

SETTINGS = SettingsCreator(
    link_type="dedupe_only",
    blocking_rules_to_generate_predictions=[
        block_on("naics_code"),
        block_on("substr(canonical_name, 1, 4)"),
    ],
    comparisons=[
        cl.NameComparison("canonical_name"),
        cl.ExactMatch("naics_code").configure(term_frequency_adjustments=True),
        cl.ExactMatch("state").configure(term_frequency_adjustments=True),
        cl.LevenshteinAtThresholds("uei", 2),
    ],
)


def load_unresolved_companies(database_url: str) -> pd.DataFrame:
    query = """
        SELECT
            id,
            raw_payload->>'recipient_name' AS canonical_name,
            raw_payload->>'naics_code' AS naics_code,
            raw_payload->>'recipient_state' AS state,
            raw_payload->>'recipient_uei' AS uei
        FROM staging_usaspending_awards
        WHERE processed = false
    """
    with psycopg.connect(database_url) as conn:
        return pd.read_sql(query, conn)


def resolve_companies(raw_companies_df: pd.DataFrame) -> pd.DataFrame:
    db_api = DuckDBAPI()
    linker = Linker(raw_companies_df, SETTINGS, db_api=db_api)
    linker.training.estimate_probability_two_random_records_match(["l.uei = r.uei"], recall=0.9)
    linker.training.estimate_u_using_random_sampling(max_pairs=1e6)
    linker.training.estimate_parameters_using_expectation_maximisation(block_on("naics_code"))
    predictions = linker.inference.predict(threshold_match_probability=0.85)
    clusters = linker.clustering.cluster_pairwise_predictions_at_threshold(
        predictions, threshold_match_probability=0.85
    )
    return clusters.as_pandas_dataframe()


def write_resolved_companies(clusters_df: pd.DataFrame, database_url: str):
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for cluster_id, group in clusters_df.groupby("cluster_id"):
                canonical_name = group["canonical_name"].mode().iloc[0]
                cur.execute(
                    "INSERT INTO companies (canonical_name) VALUES (%s) RETURNING id",
                    (canonical_name,),
                )
                company_id = cur.fetchone()[0]
                for _, row in group.iterrows():
                    cur.execute(
                        "INSERT INTO company_aliases (company_id, alias_name, source) VALUES (%s, %s, %s)",
                        (company_id, row["canonical_name"], "usaspending"),
                    )
        conn.commit()
