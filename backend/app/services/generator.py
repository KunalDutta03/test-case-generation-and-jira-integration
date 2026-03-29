"""
GPT-4.1 test case generator using RAG-augmented prompts.
Outputs structured Gherkin scenarios as JSON.
"""
import json
import logging
import re
from openai import AzureOpenAI
from app.config import settings
from app.services.embedder import embed_single
from app.services.vector_store import retrieve_top_k

logger = logging.getLogger(__name__)

_client = None

SYSTEM_PROMPT = """You are a senior QA engineer with expertise in writing Gherkin test cases.
Your task is to generate comprehensive Gherkin scenario test cases from the provided requirements.

OUTPUT FORMAT: Return ONLY a valid JSON array. No markdown, no code blocks, just raw JSON.
Each element must have:
{
  "feature": "Short feature name",
  "scenario": "Scenario title",
  "gherkin_text": "Feature: ...\\n\\n  Scenario: ...\\n    Given ...\\n    When ...\\n    Then ...",
  "type": "positive|negative|edge_case"
}

Rules:
- Use proper Gherkin syntax: Feature, Scenario (or Scenario Outline), Given/When/Then/And/But
- Cover positive cases (happy path), negative cases (error paths), and edge cases
- Be specific and actionable - reference actual data from requirements
- Each scenario must be independent and executable
"""


def get_llm_client() -> AzureOpenAI:
    global _client
    if _client is None:
        _client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )
    return _client


def generate_test_cases(
    document_id: str,
    domain: str,
    count: int,
    document_text: str,
    extra_context: str = "",
) -> list[dict]:
    """
    Retrieve relevant context via RAG and generate Gherkin test cases.
    Returns list of {feature, scenario, gherkin_text, type}.
    """
    client = get_llm_client()

    # RAG retrieval: embed a query derived from domain + document snippet
    query = f"{domain} test cases for: {document_text[:500]}"
    try:
        query_embedding = embed_single(query)
        retrieved_chunks = retrieve_top_k(
            document_id, query_embedding, k=5,
            index_dir=settings.faiss_index_path
        )
        context = "\n\n---\n\n".join(retrieved_chunks) if retrieved_chunks else document_text[:3000]
    except Exception as e:
        logger.warning(f"RAG retrieval failed, using raw text: {e}")
        context = document_text[:3000]

    # Distribution: ~half positive, ~quarter negative, ~quarter edge
    positive_count = max(1, count // 2)
    negative_count = max(1, count // 4)
    edge_count = count - positive_count - negative_count

    user_message = f"""Domain: {domain}
Extra Context: {extra_context or 'None'}

RETRIEVED REQUIREMENTS CONTEXT:
{context}

Generate exactly {count} test scenarios:
- {positive_count} positive/happy-path scenarios
- {negative_count} negative/error scenarios  
- {edge_count} edge case scenarios

Focus on {domain} testing patterns and best practices."""

    response = client.chat.completions.create(
        model=settings.azure_openai_deployment_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content.strip()
    return _parse_gherkin_json(raw)


def _parse_gherkin_json(raw: str) -> list[dict]:
    """Parse the LLM JSON response, handling common formatting issues."""
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "scenarios" in data:
            return data["scenarios"]
        return [data] if isinstance(data, dict) else []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse GPT-4.1 JSON output: {e}\nRaw: {raw[:500]}")
        # Attempt to extract JSON array from response
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse test case JSON: {e}")
