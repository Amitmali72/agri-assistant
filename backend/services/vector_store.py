"""
Vector Store Service
FAISS-based vector store for semantic document search with metadata filtering,
document removal, and index rebuilding for document governance.
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Set


class VectorStore:
    """
    FAISS IndexFlatIP vector store with parallel metadata/texts persistence,
    metadata filtering, and incremental removal/rebuilding.
    """

    INDEX_FILENAME = "index.faiss"
    METADATA_FILENAME = "metadata.json"
    TEXTS_FILENAME = "texts.json"

    def __init__(self, store_path: Optional[str] = None, storage_path: Optional[str] = None):
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            raise ImportError("faiss-cpu is required. Install with: pip install faiss-cpu")

        self.store_path = store_path or storage_path
        self._index = None
        self._metadata: List[Dict[str, Any]] = []
        self._texts: List[str] = []
        self._dim: Optional[int] = None

        if self.store_path:
            self.init_from_disk_if_exists()

    def init_from_disk_if_exists(self):
        if not self.store_path:
            return
        index_path = os.path.join(self.store_path, self.INDEX_FILENAME)
        metadata_path = os.path.join(self.store_path, self.METADATA_FILENAME)
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            try:
                self.load(self.store_path)
            except Exception as e:
                print(f"[VectorStore] Warning: Could not load existing index: {e}. Starting fresh.")
                self._reset()

    def _reset(self):
        self._index = None
        self._metadata = []
        self._texts = []
        self._dim = None

    def _init_index(self, dim: int):
        self._dim = dim
        self._index = self.faiss.IndexFlatIP(dim)

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        return vectors / norms

    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: Optional[np.ndarray] = None):
        if not chunks:
            return
        if embeddings is not None:
            texts = [c.get("text", "") for c in chunks]
            metadatas = [c.get("metadata", {}) for c in chunks]
            return self.add_embeddings(embeddings, texts, metadatas)

        if "embedding" not in chunks[0]:
            raise ValueError("Each chunk must have an 'embedding' key or pass embeddings parameter.")

        embeddings_arr = np.array([c["embedding"] for c in chunks], dtype=np.float32)
        texts = [c.get("text", "") for c in chunks]
        metadatas = [c.get("metadata", {}) for c in chunks]
        return self.add_embeddings(embeddings_arr, texts, metadatas)

    def add_embeddings(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
    ):
        if len(embeddings) == 0:
            return

        embeddings = np.array(embeddings, dtype=np.float32)
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        embeddings = self._normalize(embeddings)

        if self._index is None:
            self._init_index(embeddings.shape[1])

        self._index.add(embeddings)
        self._metadata.extend(metadatas)
        self._texts.extend(texts)

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        allowed_filenames: Optional[Set[str]] = None,
        crop_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search top-k vectors, optionally filtering to approved filenames or crop.
        """
        if self._index is None or self._index.ntotal == 0:
            return []

        query = np.array(query_embedding, dtype=np.float32)
        if query.ndim == 1:
            query = query.reshape(1, -1)
        query = self._normalize(query)

        # Fetch wider candidate pool if filtering is active
        search_k = self._index.ntotal if (allowed_filenames is not None or crop_filter) else min(k, self._index.ntotal)
        search_k = max(search_k, 1)
        scores, indices = self._index.search(query, search_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            meta = self._metadata[idx] if idx < len(self._metadata) else {}
            fname = meta.get("filename", "")

            if allowed_filenames is not None and fname not in allowed_filenames:
                continue
            if crop_filter:
                doc_crop = (meta.get("crop") or "").lower()
                if doc_crop and crop_filter.lower() not in doc_crop:
                    continue

            results.append({
                "text": self._texts[idx] if idx < len(self._texts) else "",
                "metadata": meta,
                "score": float(score),
                "index": int(idx),
            })
            if len(results) >= k:
                break

        return results

    def remove_by_filename(self, filename: str, embedding_service=None) -> int:
        """
        Remove all chunks belonging to *filename* and rebuild the FAISS index.
        Returns number of chunks removed.
        """
        keep_indices = [
            i for i, m in enumerate(self._metadata)
            if m.get("filename") != filename
        ]
        removed = len(self._metadata) - len(keep_indices)
        if removed == 0:
            return 0

        kept_texts = [self._texts[i] for i in keep_indices]
        kept_metas = [self._metadata[i] for i in keep_indices]

        # Reconstruct vectors if no embedding service passed
        if embedding_service is None and self._index is not None and keep_indices:
            kept_vecs = np.array([self._index.reconstruct(i) for i in keep_indices], dtype=np.float32)
            self._reset()
            self.add_embeddings(kept_vecs, kept_texts, kept_metas)
        elif keep_indices and embedding_service is not None:
            kept_vecs = embedding_service.encode(kept_texts)
            self._reset()
            self.add_embeddings(kept_vecs, kept_texts, kept_metas)
        else:
            self._reset()

        if self.store_path:
            self.save()
        return removed

    def update_metadata_status(self, filename: str, approval_status: str) -> int:
        """Update approval_status in stored metadata for a given filename."""
        updated = 0
        for meta in self._metadata:
            if meta.get("filename") == filename:
                meta["approval_status"] = approval_status
                updated += 1
        if updated and self.store_path:
            self.save()
        return updated

    def save(self, path: Optional[str] = None):
        save_dir = path or self.store_path
        if not save_dir:
            raise ValueError("No save path specified.")
        os.makedirs(save_dir, exist_ok=True)

        index_path = os.path.join(save_dir, self.INDEX_FILENAME)
        metadata_path = os.path.join(save_dir, self.METADATA_FILENAME)
        texts_path = os.path.join(save_dir, self.TEXTS_FILENAME)

        if self._index is None:
            # Write empty metadata/texts and remove stale index if emptied
            if os.path.exists(index_path):
                os.remove(index_path)
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump([], f)
            with open(texts_path, "w", encoding="utf-8") as f:
                json.dump([], f)
            return

        self.faiss.write_index(self._index, index_path)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False, indent=2)
        with open(texts_path, "w", encoding="utf-8") as f:
            json.dump(self._texts, f, ensure_ascii=False, indent=2)

    def load(self, path: str):
        index_path = os.path.join(path, self.INDEX_FILENAME)
        metadata_path = os.path.join(path, self.METADATA_FILENAME)
        texts_path = os.path.join(path, self.TEXTS_FILENAME)

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Index file not found: {index_path}")

        self._index = self.faiss.read_index(index_path)
        self._dim = self._index.d

        with open(metadata_path, "r", encoding="utf-8") as f:
            self._metadata = json.load(f)

        if os.path.exists(texts_path):
            with open(texts_path, "r", encoding="utf-8") as f:
                self._texts = json.load(f)

    @property
    def total_documents(self) -> int:
        return self._index.ntotal if self._index else 0

    @property
    def all_texts(self) -> List[str]:
        return self._texts

    @property
    def all_metadata(self) -> List[Dict[str, Any]]:
        return self._metadata
