"""The provider-agnostic LLM contract used by the pipeline.

Any answer generator - Claude, a local model, or the offline stub - implements
:class:`LLMClient`.  The pipeline depends only on this interface, so adding a
provider never touches pipeline code (Dependency Inversion).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import RetrievedChunk, SuggestedAnswer


class LLMClient(ABC):
    """Generates a concise, document-grounded answer to a participant question."""

    @abstractmethod
    def generate_answer(
        self, question: str, contexts: list[RetrievedChunk]
    ) -> SuggestedAnswer:
        """Answer ``question`` using only ``contexts``.

        Args:
            question: The detected question text.
            contexts: Retrieved document chunks, best match first. May be empty,
                in which case the implementation should return an answer with
                ``grounded=False``.

        Returns:
            A :class:`SuggestedAnswer`. Implementations must not raise for an
            empty ``contexts`` list.
        """
        raise NotImplementedError
