"""
Tests for Vector Store and Hybrid Retriever.
"""

import os
import pytest
import numpy as np
from backend.services.embeddings import EmbeddingService
from backend.services.vector_store import VectorStore
from backend.services.retriever import Retriever


@pytest.fixture(scope="module")
def shared_retriever():
    emb = EmbeddingService()
    vs = VectorStore("vector_store")
    return Retriever(emb, vs)


def test_vector_store_loaded(shared_retriever):
    assert shared_retriever.vector_store.total_documents > 0


def test_semantic_search(shared_retriever):
    results = shared_retriever.semantic_search("Wheat irrigation stages", k=2)
    assert len(results) > 0
    assert results[0]["score"] > 0.0
    assert "text" in results[0]
    assert "metadata" in results[0]


def test_bm25_keyword_search(shared_retriever):
    results = shared_retriever.keyword_search("NPK Nitrogen Phosphorus", k=2)
    assert len(results) > 0
    assert results[0]["score"] > 0.0


def test_hybrid_search(shared_retriever):
    results = shared_retriever.hybrid_search("PM-KISAN Samman Nidhi 6000", k=2)
    assert len(results) > 0
    assert "score" in results[0]
    assert "search_type" in results[0]
