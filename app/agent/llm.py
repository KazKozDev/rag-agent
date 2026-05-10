from langchain_openai import ChatOpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from pydantic import SecretStr
from app.config import settings


# GPT-5 family rejects any temperature other than the default (1). Older
# models (gpt-4o-mini, gpt-4.1, etc.) accept 0 for deterministic output.
# Detect by model id prefix and only pass temperature when the model allows it.
_LEGACY_TEMPERATURE_PREFIXES = ("gpt-4", "gpt-3", "o1", "o3")


def _supports_zero_temperature(model: str) -> bool:
    return model.startswith(_LEGACY_TEMPERATURE_PREFIXES)


def get_chat_llm() -> ChatOpenAI:
    """Chat model. The OpenAI SDK does exponential backoff with jitter on
    429 and 5xx by itself; we just bump max_retries and set a hard timeout
    so a stuck connection doesn't hang the whole graph.

    Temperature: GPT-5 family only accepts the default (1). Older models
    (gpt-4o, gpt-4.1, ...) accept 0 for deterministic classification.
    """
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=SecretStr(settings.openai_api_key),
        temperature=0 if _supports_zero_temperature(settings.llm_model) else 1,
        max_retries=3,
        timeout=60,
    )


def get_embed_model() -> OpenAIEmbedding:
    return OpenAIEmbedding(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
        max_retries=3,
    )


def get_llama_llm() -> LlamaOpenAI:
    return LlamaOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=0 if _supports_zero_temperature(settings.llm_model) else 1,
        max_retries=3,
    )
