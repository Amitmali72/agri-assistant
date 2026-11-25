"""
Retriever Service (Module 7)
Hybrid retrieval combining:
- Semantic vector search (FAISS IndexFlatIP)
- Lexical keyword search (Okapi BM25)
- Reciprocal Rank Fusion (RRF) for robust rank-level merging
- Approved-document filtering & crop/region relevance boosting
"""

import re
import numpy as np
from typing import List, Dict, Any, Optional, Set


class Retriever:
    """
    Hybrid retriever combining dense semantic search, BM25 keyword search,
    Reciprocal Rank Fusion (RRF), metadata filtering, and lightweight reranking.
    """

    def __init__(self, embedding_service, vector_store):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self._bm25 = None
        self._bm25_texts: List[str] = []
        self._bm25_metadata: List[Dict[str, Any]] = []
        self._build_bm25_index()

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.split(r'[\s\u200b\u200c\u200d\u200e\u200f,.!?;:()\[\]{}"\'।]+', text.lower())
        return [t for t in tokens if t]

    def _build_bm25_index(self):
        texts = self.vector_store.all_texts
        metadata = self.vector_store.all_metadata

        if not texts:
            self._bm25 = None
            self._bm25_texts = []
            self._bm25_metadata = []
            return

        from rank_bm25 import BM25Okapi
        tokenized_corpus = [self._tokenize(t) for t in texts]
        self._bm25 = BM25Okapi(tokenized_corpus)
        self._bm25_texts = list(texts)
        self._bm25_metadata = list(metadata)

    def rebuild_bm25_index(self):
        self._build_bm25_index()

    def refresh(self):
        self._build_bm25_index()

    def _is_allowed(
        self,
        meta: Dict[str, Any],
        allowed_filenames: Optional[Set[str]] = None,
        approved_only: bool = True,
    ) -> bool:
        if approved_only:
            status = meta.get("approval_status", "approved")
            if status != "approved":
                return False
        if allowed_filenames is not None:
            if meta.get("filename", "") not in allowed_filenames:
                return False
        return True

    def semantic_search(
        self,
        query: str,
        k: int = 5,
        allowed_filenames: Optional[Set[str]] = None,
        approved_only: bool = True,
    ) -> List[Dict[str, Any]]:
        query_embedding = self.embedding_service.encode_single(query)
        raw_results = self.vector_store.search(query_embedding, k=max(k * 3, 15))

        results = []
        for r in raw_results:
            meta = r.get("metadata", {})
            if not self._is_allowed(meta, allowed_filenames, approved_only):
                continue
            results.append({
                "text": r["text"],
                "metadata": meta,
                "score": float(r["score"]),
                "search_type": "semantic",
            })
            if len(results) >= k:
                break
        return results

    def keyword_search(
        self,
        query: str,
        k: int = 5,
        allowed_filenames: Optional[Set[str]] = None,
        approved_only: bool = True,
    ) -> List[Dict[str, Any]]:
        if self._bm25 is None or not self._bm25_texts:
            return []

        tokenized_query = self._tokenize(query)
        if not tokenized_query:
            return []

        scores = self._bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1]

        results = []
        for idx in top_indices:
            if scores[idx] <= 0:
                break
            meta = self._bm25_metadata[idx]
            if not self._is_allowed(meta, allowed_filenames, approved_only):
                continue
            results.append({
                "text": self._bm25_texts[idx],
                "metadata": meta,
                "score": float(scores[idx]),
                "search_type": "keyword",
            })
            if len(results) >= k:
                break

        return results

    def hybrid_search(
        self,
        query: str,
        k: int = 5,
        semantic_weight: float = 0.7,
        crop: Optional[str] = None,
        region: Optional[str] = None,
        allowed_filenames: Optional[Set[str]] = None,
        approved_only: bool = True,
        use_rrf: bool = True,
        rrf_k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining semantic FAISS + BM25 via Reciprocal Rank Fusion (RRF),
        followed by crop/region relevance reranking.
        """
        fetch_k = max(k * 3, 12)
        semantic_results = self.semantic_search(
            query, k=fetch_k, allowed_filenames=allowed_filenames, approved_only=approved_only
        )
        keyword_results = self.keyword_search(
            query, k=fetch_k, allowed_filenames=allowed_filenames, approved_only=approved_only
        )

        combined: Dict[str, Dict[str, Any]] = {}

        # Semantic contribution (preserve raw cosine similarity for confidence gate)
        for rank, r in enumerate(semantic_results, start=1):
            key = f"{r['metadata'].get('filename', '')}_{r['metadata'].get('chunk_id', '')}_{r['text'][:80]}"
            rrf_score = (1.0 / (rrf_k + rank)) if use_rrf else 0.0
            combined[key] = {
                "text": r["text"],
                "metadata": r["metadata"],
                "raw_semantic_score": float(r["score"]),
                "rrf_score": rrf_score * semantic_weight * 20.0,
                "search_type": "semantic",
            }

        # Keyword BM25 contribution
        kw_weight = 1.0 - semantic_weight
        for rank, r in enumerate(keyword_results, start=1):
            key = f"{r['metadata'].get('filename', '')}_{r['metadata'].get('chunk_id', '')}_{r['text'][:80]}"
            rrf_kw = (1.0 / (rrf_k + rank)) * kw_weight * 20.0
            if key in combined:
                combined[key]["rrf_score"] += rrf_kw
                combined[key]["search_type"] = "hybrid_rrf"
            else:
                combined[key] = {
                    "text": r["text"],
                    "metadata": r["metadata"],
                    "raw_semantic_score": 0.25,
                    "rrf_score": rrf_kw,
                    "search_type": "keyword",
                }

        # Reranking: blend raw semantic similarity + RRF + crop/region contextual boost
        final_results = []
        crop_lower = crop.lower() if crop else ""
        region_lower = region.lower() if region else ""

        for item in combined.values():
            meta = item["metadata"]
            text_lower = item["text"].lower()
            meta_crop = (meta.get("crop") or "").lower()
            meta_region = (meta.get("region") or "").lower()

            boost = 0.0
            if crop_lower and (crop_lower in text_lower or crop_lower in meta_crop):
                boost += 0.12
            if region_lower and (region_lower in text_lower or region_lower in meta_region):
                boost += 0.06

            # Keep score aligned with semantic cosine scale [0..1] for ConfidenceGate
            blended_score = min(
                1.0,
                round(0.75 * item["raw_semantic_score"] + 0.25 * min(item["rrf_score"], 1.0) + boost, 4),
            )
            final_results.append({
                "text": item["text"],
                "metadata": meta,
                "score": blended_score,
                "raw_semantic_score": round(item["raw_semantic_score"], 4),
                "search_type": item["search_type"],
            })

        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results[:k]
