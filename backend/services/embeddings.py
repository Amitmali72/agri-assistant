"""
Embedding Service
Uses sentence-transformers with a multilingual model to encode text into dense vectors.
Supports Hindi, Marathi, English and other languages natively.
"""

import numpy as np
from typing import List, Optional


class EmbeddingService:
    """
    Lazy-loading embedding service using sentence-transformers.
    Model: paraphrase-multilingual-MiniLM-L12-v2 (supports 50+ languages including
    Hindi and Marathi via Devanagari script).
    """

    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or self.MODEL_NAME
        self._model = None  # Lazy-loaded on first use

    def _load_model(self):
        """Load the sentence-transformer model (called once, cached)."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def encode(self, texts: List[str], batch_size: int = 32, normalize: bool = True) -> np.ndarray:
        """
        Encode a list of texts into embedding vectors.

        Args:
            texts: List of strings to encode
            batch_size: Batch size for encoding
            normalize: If True, L2-normalize embeddings (required for cosine similarity via dot product)

        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])

        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
        )
        return embeddings

    def encode_single(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Encode a single string into an embedding vector.

        Args:
            text: String to encode
            normalize: If True, L2-normalize embedding

        Returns:
            numpy array of shape (embedding_dim,)
        """
        embeddings = self.encode([text], normalize=normalize)
        return embeddings[0]

    @property
    def embedding_dim(self) -> int:
        """Return the dimensionality of the embedding vectors."""
        model = self._load_model()
        return model.get_sentence_embedding_dimension()


# Module-level singleton for convenience
_default_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the default embedding service singleton."""
    global _default_service
    if _default_service is None:
        _default_service = EmbeddingService()
    return _default_service


if __name__ == "__main__":
    svc = EmbeddingService()
    # Test with English, Hindi and Marathi
    test_texts = [
        "How to grow rice?",
        "चावल कैसे उगाएं?",   # Hindi
        "भात कसा पिकवायचा?",   # Marathi
    ]
    embeddings = svc.encode(test_texts)
    print(f"Embedding shape: {embeddings.shape}")
    print(f"Embedding dim: {svc.embedding_dim}")
    single = svc.encode_single("test")
    print(f"Single embedding shape: {single.shape}")
