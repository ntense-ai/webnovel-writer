# RAG and Configuration

## RAG Retrieval Pipeline

During writing, the system automatically retrieves relevant content from previous chapters to help maintain consistency.

```text
Query → QueryRouter(auto) → vector / bm25 / hybrid / graph_hybrid
                       └→ RRF fusion + Rerank → Top-K
```

- The default mode is `auto`: vector retrieval is preferred, with automatic fallback to BM25 on failure.
- The `graph_hybrid` mode adds entity-graph associations.

### Default Models

| Component | Default model |
|------|----------|
| Embedding | `Qwen/Qwen3-Embedding-8B` (hosted by ModelScope) |
| Reranker | `jina-reranker-v3` (hosted by Jina AI) |

## Environment Variable Loading Order

Configuration is loaded in the following priority order (earlier entries take precedence):

1. **Process environment variables** (highest priority)
2. `.env` in the **book project root**
3. **User-wide global configuration**: `~/.claude/webnovel-writer/.env`

## Minimal `.env` Configuration

Project initialization automatically generates `.env.example`. Copy it to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required settings:

```bash
EMBED_BASE_URL=https://api-inference.modelscope.cn/v1
EMBED_MODEL=Qwen/Qwen3-Embedding-8B
EMBED_API_KEY=your_embed_api_key

RERANK_BASE_URL=https://api.jina.ai/v1
RERANK_MODEL=jina-reranker-v3
RERANK_API_KEY=your_rerank_api_key
```

## Notes

- If no Embedding Key is configured, semantic retrieval automatically falls back to BM25 (the system remains usable, but retrieval is less effective than vector retrieval).
- Configure `${PROJECT_ROOT}/.env` separately for each book to avoid mixing settings across projects.
- The Embedding and Rerank models can be replaced with any OpenAI-format-compatible API.
