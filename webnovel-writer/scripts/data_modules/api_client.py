#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'Data Modules API clients (v5.4, retaining the v5.0 OpenAI-compatible interface). Supports openai: OpenAI-compatible /v1/embeddings and /v1/rerank endpoints for OpenAI, Jina, Cohere, vLLM, Ollama, etc.; and modal: custom interfaces for self-hosted Modal services. Configuration example in config.py: embed_api_type = "openai"; embed_base_url = "https://api.openai.com/v1"; embed_model = "text-embedding-3-small"; embed_api_key = "<your-embed-api-key>". Reranking: rerank_api_type = "openai" (also for Jina/Cohere); rerank_base_url = "https://api.jina.ai/v1"; rerank_model = "jina-reranker-v2-base-multilingual"; rerank_api_key = "<your-rerank-api-key>".'

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .config import get_config


@dataclass
class APIStats:
    'API call statistics.'
    total_calls: int = 0
    total_time: float = 0.0
    errors: int = 0


class EmbeddingAPIClient:
    'General embedding API client supporting OpenAI-compatible /v1/embeddings and custom Modal interfaces.'

    def __init__(self, config=None):
        self.config = config or get_config()
        self.sem = asyncio.Semaphore(self.config.embed_concurrency)
        self.stats = APIStats()
        self._warmed_up = False
        self._session: Optional[aiohttp.ClientSession] = None
        self.last_error_status: Optional[int] = None
        self.last_error_message: str = ""

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=200, limit_per_host=100)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def _build_headers(self) -> Dict[str, str]:
        'Build request headers.'
        headers = {"Content-Type": "application/json"}
        if self.config.embed_api_key:
            headers["Authorization"] = f"Bearer {self.config.embed_api_key}"
        return headers

    def _build_url(self) -> str:
        'Build the request URL.'
        base_url = self.config.embed_base_url.rstrip("/")
        if self.config.embed_api_type == "openai":
            # OpenAI-compatible: /v1/embeddings
            if not base_url.endswith("/embeddings"):
                if base_url.endswith("/v1"):
                    return f"{base_url}/embeddings"
                return f"{base_url}/v1/embeddings"
            return base_url
        else:
            # Custom Modal interface: use the configured URL directly.
            return base_url

    def _build_payload(self, texts: List[str]) -> Dict[str, Any]:
        'Build the request body.'
        if self.config.embed_api_type == "openai":
            return {
                "input": texts,
                "model": self.config.embed_model,
                "encoding_format": "float"
            }
        else:
            # Modal format
            return {
                "input": texts,
                "model": self.config.embed_model
            }

    def _parse_response(self, data: Dict[str, Any]) -> Optional[List[List[float]]]:
        'Parse the response.'
        if self.config.embed_api_type == "openai":
            # OpenAI format: {"data": [{"embedding": [...], "index": 0}, ...]}
            if "data" in data:
                # Sort by index to preserve ordering.
                sorted_data = sorted(data["data"], key=lambda x: x.get("index", 0))
                return [item["embedding"] for item in sorted_data]
            return None
        else:
            # Modal format: {"data": [{"embedding": [...]}, ...]}
            if "data" in data:
                return [item["embedding"] for item in data["data"]]
            return None

    async def embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        'Call the embedding service with retries.'
        if not texts:
            return []

        # Some embedding endpoints, such as Gemini, reject empty strings; use one space to preserve index alignment.
        texts = [t if t else " " for t in texts]

        timeout = self.config.cold_start_timeout if not self._warmed_up else self.config.normal_timeout
        max_retries = getattr(self.config, 'api_max_retries', 3)
        base_delay = getattr(self.config, 'api_retry_delay', 1.0)

        async with self.sem:
            start = time.time()
            session = await self._get_session()

            for attempt in range(max_retries):
                try:
                    url = self._build_url()
                    headers = self._build_headers()
                    payload = self._build_payload(texts)

                    async with session.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            data = json.loads(text)
                            embeddings = self._parse_response(data)

                            if embeddings:
                                self.stats.total_calls += 1
                                self.stats.total_time += time.time() - start
                                self._warmed_up = True
                                self.last_error_status = None
                                self.last_error_message = ""
                                return embeddings

                        # Retryable status codes: 429 (rate limited), 500, 502, 503, 504
                        if resp.status in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)  # Exponential backoff
                            print(f"[WARN] Embed {resp.status}, retrying in {delay:.1f}s ({attempt + 1}/{max_retries})")
                            await asyncio.sleep(delay)
                            continue

                        self.stats.errors += 1
                        err_text = await resp.text()
                        self.last_error_status = int(resp.status)
                        self.last_error_message = str(err_text[:200])
                        print(f"[ERR] Embed {resp.status}: {err_text[:200]}")
                        return None

                except asyncio.TimeoutError:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"[WARN] Embed timeout, retrying in {delay:.1f}s ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    self.stats.errors += 1
                    self.last_error_status = None
                    self.last_error_message = f"Timeout after {max_retries} attempts"
                    print(f"[ERR] Embed: Timeout after {max_retries} attempts")
                    return None

                except Exception as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"[WARN] Embed error: {e}, retrying in {delay:.1f}s ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    self.stats.errors += 1
                    self.last_error_status = None
                    self.last_error_message = str(e)
                    print(f"[ERR] Embed: {e}")
                    return None

            return None

    async def embed_batch(
        self, texts: List[str], *, skip_failures: bool = True
    ) -> List[Optional[List[float]]]:
        'Embed texts in batches. Args: texts is the list of strings to embed; skip_failures=True returns None for failed texts, while False returns an empty list if any request fails. Returns a list matching the length of texts, with vectors for successes and None for failures.'
        if not texts:
            return []

        all_embeddings: List[Optional[List[float]]] = []
        batch_size = self.config.embed_batch_size

        batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
        tasks = [self.embed(batch) for batch in batches]
        results = await asyncio.gather(*tasks)

        for batch_idx, result in enumerate(results):
            actual_batch_size = len(batches[batch_idx])
            if result and len(result) == actual_batch_size:
                all_embeddings.extend(result)
            else:
                if not skip_failures:
                    print(f"[WARN] Embed batch {batch_idx} failed, aborting all")
                    return []
                print(f"[WARN] Embed batch {batch_idx} failed, marking {actual_batch_size} items as None")
                all_embeddings.extend([None] * actual_batch_size)

        return all_embeddings[:len(texts)]

    async def warmup(self):
        'Warm up the service.'
        await self.embed(["test"])
        self._warmed_up = True


class RerankAPIClient:
    'General reranking API client supporting OpenAI-compatible Jina/Cohere formats and custom Modal interfaces.'

    def __init__(self, config=None):
        self.config = config or get_config()
        self.sem = asyncio.Semaphore(self.config.rerank_concurrency)
        self.stats = APIStats()
        self._warmed_up = False
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=200, limit_per_host=100)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def _build_headers(self) -> Dict[str, str]:
        'Build request headers.'
        headers = {"Content-Type": "application/json"}
        if self.config.rerank_api_key:
            headers["Authorization"] = f"Bearer {self.config.rerank_api_key}"
        return headers

    def _is_dashscope_url(self, base_url: Optional[str] = None) -> bool:
        'Check whether the reranking configuration points to DashScope.'
        url = base_url if base_url is not None else self.config.rerank_base_url
        return "dashscope" in str(url or "").lower()

    def _is_dashscope_native_rerank_model(self) -> bool:
        'The native DashScope reranking interface uses an input/parameters request structure.'
        model = str(self.config.rerank_model or "").lower()
        return model in {"qwen3-vl-rerank", "gte-rerank-v2"}

    def _is_dashscope_native_rerank(self) -> bool:
        return (
            self.config.rerank_api_type == "openai"
            and self._is_dashscope_url()
            and self._is_dashscope_native_rerank_model()
        )

    def _dashscope_endpoint_root(self, base_url: str) -> str:
        'Strip known reranking paths from the configured DashScope base URL.'
        base_url_lower = base_url.lower()
        known_suffixes = [
            "/api/v1/services/rerank/text-rerank/text-rerank",
            "/api/v1/services/rerank/text-rerank",
            "/api/v1/services/rerank",
            "/api/v1/services",
            "/compatible-api/v1/reranks",
            "/compatible-api/v1/rerank",
            "/compatible-api/v1",
            "/compatible-api",
            "/v1/reranks",
            "/v1/rerank",
            "/api/v1",
            "/api",
            "/v1",
        ]
        for suffix in known_suffixes:
            if base_url_lower.endswith(suffix):
                return base_url[:-len(suffix)]
        return base_url

    def _build_dashscope_url(self, base_url: str) -> str:
        root_url = self._dashscope_endpoint_root(base_url)
        if self._is_dashscope_native_rerank_model():
            return f"{root_url}/api/v1/services/rerank/text-rerank/text-rerank"
        return f"{root_url}/compatible-api/v1/reranks"

    def _build_url(self) -> str:
        'Build the request URL.'
        base_url = self.config.rerank_base_url.rstrip("/")
        if self.config.rerank_api_type == "openai":
            if self._is_dashscope_url(base_url):
                return self._build_dashscope_url(base_url)
            # Jina/Cohere-compatible: /v1/rerank
            if not base_url.endswith("/rerank"):
                if base_url.endswith("/v1"):
                    return f"{base_url}/rerank"
                return f"{base_url}/v1/rerank"
            return base_url
        else:
            # Custom Modal interface
            return base_url

    def _build_payload(self, query: str, documents: List[str], top_n: Optional[int]) -> Dict[str, Any]:
        'Build the request body.'
        if self.config.rerank_api_type == "openai":
            if self._is_dashscope_native_rerank():
                parameters: Dict[str, Any] = {"return_documents": True}
                if top_n:
                    parameters["top_n"] = top_n

                if str(self.config.rerank_model or "").lower() == "qwen3-vl-rerank":
                    native_query: Any = {"text": query}
                    native_documents = [
                        document if isinstance(document, dict) else {"text": document}
                        for document in documents
                    ]
                else:
                    native_query = query
                    native_documents = documents

                return {
                    "model": self.config.rerank_model,
                    "input": {
                        "query": native_query,
                        "documents": native_documents,
                    },
                    "parameters": parameters,
                }

            # Jina/Cohere format
            payload: Dict[str, Any] = {
                "query": query,
                "documents": documents,
                "model": self.config.rerank_model
            }
            if top_n:
                payload["top_n"] = top_n
            return payload
        else:
            # Modal format
            payload = {"query": query, "documents": documents}
            if top_n:
                payload["top_n"] = top_n
            return payload

    def _parse_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        'Parse the response.'
        if self.config.rerank_api_type == "openai":
            if self._is_dashscope_native_rerank():
                # Native DashScope format: {"output": {"results": [...]}}
                return data.get("output", {}).get("results", [])
            # Jina/Cohere format: {"results": [{"index": 0, "relevance_score": 0.9}, ...]}
            return data.get("results", [])
        else:
            # Modal format: {"results": [...]}
            return data.get("results", [])

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None
    ) -> Optional[List[Dict[str, Any]]]:
        'Call the reranking service with retries.'
        if not documents:
            return []

        timeout = self.config.cold_start_timeout if not self._warmed_up else self.config.normal_timeout
        max_retries = getattr(self.config, 'api_max_retries', 3)
        base_delay = getattr(self.config, 'api_retry_delay', 1.0)

        async with self.sem:
            start = time.time()
            session = await self._get_session()

            for attempt in range(max_retries):
                try:
                    url = self._build_url()
                    headers = self._build_headers()
                    payload = self._build_payload(query, documents, top_n)

                    async with session.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()

                            self.stats.total_calls += 1
                            self.stats.total_time += time.time() - start
                            self._warmed_up = True

                            return self._parse_response(data)

                        # Retryable status codes
                        if resp.status in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            print(f"[WARN] Rerank {resp.status}, retrying in {delay:.1f}s ({attempt + 1}/{max_retries})")
                            await asyncio.sleep(delay)
                            continue

                        self.stats.errors += 1
                        err_text = await resp.text()
                        print(f"[ERR] Rerank {resp.status}: {err_text[:200]}")
                        return None

                except asyncio.TimeoutError:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"[WARN] Rerank timeout, retrying in {delay:.1f}s ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    self.stats.errors += 1
                    print(f"[ERR] Rerank: Timeout after {max_retries} attempts")
                    return None

                except Exception as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"[WARN] Rerank error: {e}, retrying in {delay:.1f}s ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    self.stats.errors += 1
                    print(f"[ERR] Rerank: {e}")
                    return None

            return None

    async def warmup(self):
        'Warm up the service.'
        await self.rerank("test", ["doc1", "doc2"])
        self._warmed_up = True


class ModalAPIClient:
    'Unified API client retaining the legacy interface. Combines embedding and reranking clients while preserving backward compatibility.'

    def __init__(self, config=None):
        self.config = config or get_config()
        self._embed_client = EmbeddingAPIClient(self.config)
        self._rerank_client = RerankAPIClient(self.config)

        # Semaphore retained for compatibility with older code.
        self.sem_embed = self._embed_client.sem
        self.sem_rerank = self._rerank_client.sem

        self._warmed_up = {"embed": False, "rerank": False}
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def stats(self) -> Dict[str, APIStats]:
        return {
            "embed": self._embed_client.stats,
            "rerank": self._rerank_client.stats
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        # Reuse the embedding client's session.
        return await self._embed_client._get_session()

    async def close(self):
        await self._embed_client.close()
        await self._rerank_client.close()

    # ==================== Warmup ====================

    async def warmup(self):
        'Warm up embedding and reranking services.'
        print("[WARMUP] Warming up Embed + Rerank...")
        start = time.time()

        tasks = [self._warmup_embed(), self._warmup_rerank()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for name, result in zip(["Embed", "Rerank"], results):
            if isinstance(result, Exception):
                print(f"  [FAIL] {name}: {result}")
            else:
                print(f"  [OK] {name} ready")

        print(f"[WARMUP] Done in {time.time() - start:.1f}s")

    async def _warmup_embed(self):
        await self._embed_client.warmup()
        self._warmed_up["embed"] = True

    async def _warmup_rerank(self):
        await self._rerank_client.warmup()
        self._warmed_up["rerank"] = True

    # ==================== Embedding API ====================

    async def embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        'Call the embedding service.'
        return await self._embed_client.embed(texts)

    async def embed_batch(
        self, texts: List[str], *, skip_failures: bool = True
    ) -> List[Optional[List[float]]]:
        'Embed in batches.'
        return await self._embed_client.embed_batch(texts, skip_failures=skip_failures)

    # ==================== Rerank API ====================

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None
    ) -> Optional[List[Dict[str, Any]]]:
        'Call the reranking service.'
        return await self._rerank_client.rerank(query, documents, top_n)

    # ==================== Statistics ====================

    def print_stats(self):
        print("\n[API STATS]")
        for name, stats in self.stats.items():
            if stats.total_calls > 0:
                avg_time = stats.total_time / stats.total_calls
                print(f"  {name.upper()}: {stats.total_calls} calls, "
                      f"{stats.total_time:.1f}s total, "
                      f"{avg_time:.2f}s avg, "
                      f"{stats.errors} errors")


# Global client
_client: Optional[ModalAPIClient] = None


def get_client(config=None) -> ModalAPIClient:
    global _client
    if _client is None or config is not None:
        _client = ModalAPIClient(config)
    return _client
