import time

from anthropic import Anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from pydantic import BaseModel

EXTRACTION_MODEL = "claude-haiku-4-5-20251001"

client = Anthropic()


class ContractExtraction(BaseModel):
    capabilities: list[str]
    technology_area: str
    contract_type: str


def extract_capabilities(description: str) -> ContractExtraction:
    response = client.messages.parse(
        model=EXTRACTION_MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": description}],
        output_format=ContractExtraction,
    )
    return response.parsed_output


def submit_extraction_batch(contracts: list[dict]) -> str:
    requests = [
        Request(
            custom_id=contract["id"],
            params=MessageCreateParamsNonStreaming(
                model=EXTRACTION_MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": contract["description"]}],
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": ContractExtraction.model_json_schema(),
                    }
                },
            ),
        )
        for contract in contracts
    ]
    batch = client.messages.batches.create(requests=requests)
    return batch.id


def collect_extraction_batch(batch_id: str, poll_seconds: int = 30) -> dict[str, ContractExtraction]:
    while client.messages.batches.retrieve(batch_id).processing_status != "ended":
        time.sleep(poll_seconds)
    results = {}
    for entry in client.messages.batches.results(batch_id):
        if entry.result.type == "succeeded":
            text = entry.result.message.content[0].text
            results[entry.custom_id] = ContractExtraction.model_validate_json(text)
    return results
