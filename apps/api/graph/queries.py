from neo4j import GraphDatabase


class GraphClient:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def upsert_company(self, uei: str, name: str, naics_codes: list[str]):
        self.driver.execute_query(
            """
            MERGE (c:Company {uei: $uei})
            SET c.name = $name, c.naics_codes = $naics_codes
            """,
            uei=uei,
            name=name,
            naics_codes=naics_codes,
        )

    def upsert_contract(
        self,
        award_id: str,
        company_uei: str,
        agency: str,
        naics_code: str,
        amount: float,
        date_signed: str,
        capabilities: list[str],
    ):
        self.driver.execute_query(
            """
            MERGE (contract:Contract {award_id: $award_id})
            SET contract.amount = $amount, contract.date_signed = date($date_signed)
            MERGE (company:Company {uei: $company_uei})
            MERGE (agency:Agency {name: $agency})
            MERGE (naics:NAICSCode {code: $naics_code})
            MERGE (company)-[:WON]->(contract)
            MERGE (contract)-[:AWARDED_BY]->(agency)
            MERGE (contract)-[:REQUIRES]->(naics)
            WITH company, contract
            UNWIND $capabilities AS capability_name
            MERGE (cap:Capability {name: capability_name})
            MERGE (company)-[:HAS_CAPABILITY]->(cap)
            MERGE (contract)-[:REQUIRES]->(cap)
            """,
            award_id=award_id,
            company_uei=company_uei,
            agency=agency,
            naics_code=naics_code,
            amount=amount,
            date_signed=date_signed,
            capabilities=capabilities,
        )

    def upsert_subcontract(self, prime_uei: str, sub_uei: str, amount: float):
        self.driver.execute_query(
            """
            MERGE (prime:Company {uei: $prime_uei})
            MERGE (sub:Company {uei: $sub_uei})
            MERGE (prime)-[r:SUBCONTRACTED_WITH]-(sub)
            ON CREATE SET r.total_amount = $amount, r.contract_count = 1
            ON MATCH SET r.total_amount = r.total_amount + $amount, r.contract_count = r.contract_count + 1
            """,
            prime_uei=prime_uei,
            sub_uei=sub_uei,
            amount=amount,
        )

    def recommend_partners(self, capabilities: list[str], agency: str, exclude_uei: str, limit: int = 10) -> list[dict]:
        records, _, _ = self.driver.execute_query(
            """
            MATCH (candidate:Company)-[:HAS_CAPABILITY]->(cap:Capability)
            WHERE cap.name IN $capabilities AND candidate.uei <> $exclude_uei
            WITH candidate, count(DISTINCT cap) AS capability_match
            CALL {
                WITH candidate
                OPTIONAL MATCH (candidate)-[:WON]->(:Contract)-[:AWARDED_BY]->(:Agency {name: $agency})
                RETURN count(*) AS agency_contracts
            }
            CALL {
                WITH candidate
                OPTIONAL MATCH (candidate)-[:WON]->(c:Contract)
                RETURN max(c.date_signed) AS most_recent_win
            }
            CALL {
                WITH candidate
                OPTIONAL MATCH (candidate)-[r:SUBCONTRACTED_WITH]-(:Company {uei: $exclude_uei})
                RETURN coalesce(r.contract_count, 0) AS teaming_count
            }
            RETURN candidate.uei AS uei, candidate.name AS name,
                capability_match, agency_contracts, most_recent_win, teaming_count
            ORDER BY capability_match DESC, agency_contracts DESC
            LIMIT $limit
            """,
            capabilities=capabilities,
            agency=agency,
            exclude_uei=exclude_uei,
            limit=limit,
        )
        return [r.data() for r in records]
