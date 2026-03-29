"""
Azure OpenAI Embedder using text-embedding-3-large.
"""
import logging
from openai import AzureOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

_client = None


def get_embedding_client() -> AzureOpenAI:
    global _client
    if _client is None:
        _client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_embedding_endpoint,
            api_version=settings.azure_openai_api_version,
        )
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a batch of texts using Azure OpenAI.
    Returns list of embedding vectors.
    """
    if not texts:
        return []

    client = get_embedding_client()
    # Batch in groups of 16 to avoid rate limits
    all_embeddings = []
    batch_size = 16
    for i in range(0, len(texts), batch_size):
        batch = texts[i: i + batch_size]
        response = client.embeddings.create(
            input=batch,
            model=settings.azure_openai_embedding_deployment,
        )
        for item in response.data:
            all_embeddings.append(item.embedding)
    return all_embeddings


def embed_single(text: str) -> list[float]:
    return embed_texts([text])[0]
