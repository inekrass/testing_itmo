from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class MLRecommendationProvider(Protocol):
    """Внешний сервис рекомендаций, возвращающий ISBN подходящих книг."""

    def recommend_isbns(self, customer_id: str, limit: int) -> list[str]:
        """Вернуть список ISBN рекомендованных книг.
        Бросает RuntimeError, если сервис недоступен."""
        ...
