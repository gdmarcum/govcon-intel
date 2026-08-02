from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from pydantic import BaseModel

from extraction.extract import EXTRACTION_MODEL, client as anthropic_client
from graph.queries import GraphClient
from recommend.score import score_candidates

graph_client = GraphClient(
    uri=os.environ["NEO4J_URI"],
    user=os.environ["NEO4J_USER"],
    password=os.environ["NEO4J_PASSWORD"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    graph_client.close()


app = FastAPI(title="GovCon Intelligence API", lifespan=lifespan)


class OpportunityRequirements(BaseModel):
    capabilities: list[str]
    agency: str


class RecommendRequest(BaseModel):
    opportunity: str
    exclude_uei: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/recommend")
def recommend(request: RecommendRequest):
    parsed = anthropic_client.messages.parse(
        model=EXTRACTION_MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": request.opportunity}],
        output_format=OpportunityRequirements,
    )
    requirements = parsed.parsed_output
    candidates = graph_client.recommend_partners(
        capabilities=requirements.capabilities,
        agency=requirements.agency,
        exclude_uei=request.exclude_uei,
    )
    ranked = score_candidates(candidates)
    return {"requirements": requirements.model_dump(), "recommendations": ranked}
