"""Thin wrapper around a local sentence-transformers embedding model.

The model is loaded lazily and cached for the lifetime of the process so the
(relatively expensive) load happens once, on first use, rather than at import
time.  All vectors are L2-normalized which lets the vector store use a plain dot
product as cosine similarity.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from app.config import settings


@lru_cache(maxsize=2)
def _load_model(name: str):
    """Load and cache a ``SentenceTransformer`` by name.

    Imported inside the function so that merely importing this module (e.g. during
    test collection) does not pull in torch.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(name)


class Embedder:
    """Encodes text into normalized float32 vectors.

    Args:
        model_name: Sentence-transformers model id. Defaults to ``settings.embed_model``.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embed_model

    @property
    def dimension(self) -> int:
        """Embedding vector length for the configured model."""
        return int(_load_model(self.model_name).get_sentence_embedding_dimension())

    def encode(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of strings.

        Args:
            texts: Strings to embed.

        Returns:
            A ``(len(texts), dimension)`` float32 array of unit-norm rows.
            An empty input yields a ``(0, dimension)`` array.
        """
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        vectors = _load_model(self.model_name).encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return np.asarray(vectors, dtype=np.float32)

    def encode_one(self, text: str) -> np.ndarray:
        """Embed a single string into a 1-D ``(dimension,)`` float32 vector."""
        return self.encode([text])[0]
