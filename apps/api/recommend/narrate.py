from pydantic import BaseModel

from extraction.extract import client

NARRATION_MODEL = "claude-sonnet-5"
NARRATION_TOP_N = 5


class CandidateNarration(BaseModel):
    uei: str
    evidence: str


class NarrationResponse(BaseModel):
    narrations: list[CandidateNarration]


def narrate_candidates(capabilities: list[str], agency: str, candidates: list[dict]) -> dict[str, str]:
    top = candidates[:NARRATION_TOP_N]
    if not top:
        return {}
    candidate_lines = "\n".join(
        f"- uei={c['uei']} name={c['name']} capability_match={c['capability_match']} "
        f"agency_contracts={c['agency_contracts']} teaming_count={c['teaming_count']}"
        for c in top
    )
    prompt = (
        f"Opportunity requires: {', '.join(capabilities)}, for {agency}.\n\n"
        f"Candidates:\n{candidate_lines}\n\n"
        "Write exactly one evidence sentence per candidate uei listed above. "
        "Base each sentence only on the numbers given here - do not invent contracts, "
        "agencies, or capabilities not listed."
    )
    response = client.messages.parse(
        model=NARRATION_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        output_format=NarrationResponse,
    )
    return {n.uei: n.evidence for n in response.parsed_output.narrations}