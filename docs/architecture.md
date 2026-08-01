# Architecture

Four layers, mirroring the source product-strategy doc:

1. **Data Acquisition** (`apps/api/etl/`) - scheduled pulls from USASpending.gov (award/contract data) and SAM.gov (entity registration, certifications, solicitations) into Postgres staging tables.
2. **Intelligence Extraction** (`apps/api/resolution/`, `apps/api/extraction/`) - entity resolution (Splink) collapses name variants into canonical companies; Claude structured outputs turn free-text award descriptions into schema-validated capability tags.
3. **Contractor Intelligence Graph** (`apps/api/graph/`, Neo4j) - `Company`, `Contract`, `Agency`, `Capability`, `NAICSCode` nodes; `WON`, `SUBCONTRACTED_WITH`, `REQUIRES`, `AWARDED_BY`, `HAS_CAPABILITY` relationships.
4. **Recommendation Engine** (`apps/api/recommend/`) - deterministic, weighted scoring over graph query results; the LLM only narrates the evidence behind a score, it never generates the score itself.

## Notes

- `companies.capability_embedding` is declared as `vector(1536)` in the migration as a placeholder - resize to match whichever embedding model you pick.
- The scoring weights in `recommend/score.py` are a starting guess, not a fitted model - tune once real graph data exists to check them against.
