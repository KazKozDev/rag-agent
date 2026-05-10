# RAG Agent v2 — Customization Guide

## Changing the LLM

Edit `.env`:

```
LLM_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1
```

For local LLMs via Ollama:

```
LLM_MODEL=llama3
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
EMBEDDING_MODEL=nomic-embed-text
```

## Pricing Tiers

| Tier    | Price  | Features                                     |
|---------|--------|----------------------------------------------|
| Basic   | $1,500 | Vector search, 1 source, Streamlit           |
| Standard| $3,500 | Hybrid retrieval, citation, feedback, clarification |
| Enterprise | $6,000 | All features + auto-report + maintenance     |

## Customizing Chunking

Edit `app/ingestion/chunker.py` to change `chunk_size` and `chunk_overlap`.

## Customizing the FAQ

Edit `app/agent/faq_agent.py` to add or modify FAQ entries in the `FAQ_ANSWERS` dictionary.

## Customizing Citation Format

Edit `app/retrieval/citation.py` to change the citation format string.

## Adding Custom Agents

1. Create a new node function in `app/agent/`
2. Add it to `build_supervisor()` in `app/agent/supervisor.py`
3. Add routing logic in `route_after_clarification()`
