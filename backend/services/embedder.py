"""Embedding service — Azure OpenAI via Azure AI Foundry."""
import os

_client = None

EMBEDDING_DIMS = 1536


def _get_client():
    global _client
    if _client is None:
        try:
            from openai import AzureOpenAI
        except ImportError:
            raise RuntimeError("openai package not installed — run: pip install openai")

        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

        if not endpoint:
            raise RuntimeError("AZURE_OPENAI_ENDPOINT env var is not set")
        if not api_key:
            raise RuntimeError("AZURE_OPENAI_API_KEY env var is not set")

        _client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using the configured Azure deployment."""
    client = _get_client()
    deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
    response = client.embeddings.create(model=deployment, input=texts)
    return [item.embedding for item in response.data]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
