from __future__ import annotations

from dataclasses import dataclass

from bookstore.exceptions import BookNotFoundError
from bookstore.interfaces.book_repository import BookRepository
from bookstore.interfaces.ml_recommendation_provider import MLRecommendationProvider
from bookstore.models.book import Book, BookCategory
from bookstore.models.customer import Customer


@dataclass
class Recommendation:
    """Рекомендованная книга с оценкой релевантности и пояснением."""

    book: Book
    score: float
    reason: str


class RecommendationService:
    """Подбор рекомендаций книг для покупателя."""

    def __init__(
        self,
        books: BookRepository,
        ml_provider: MLRecommendationProvider,
    ):
        self._books = books
        self._ml = ml_provider

    def recommend_for(self, customer: Customer, limit: int = 5) -> list[Recommendation]:
        """Подобрать до `limit` рекомендаций. Заблокированным покупателям и при
        неположительном лимите возвращается пустой список. Если ML-сервис
        недоступен, используется простой подбор по популярным книгам."""
        if customer.is_blocked:
            return []
        if limit <= 0:
            return []

        try:
            isbns = self._ml.recommend_isbns(customer.customer_id, limit * 2)
        except RuntimeError:
            return self._fallback_recommendations(limit)

        candidates: list[tuple[Book, float]] = []
        for index, isbn in enumerate(isbns):
            try:
                book = self._books.get_by_isbn(isbn)
            except BookNotFoundError:
                continue
            score = max(0.0, 1.0 - index * 0.1)
            candidates.append((book, score))

        candidates.sort(key=lambda pair: pair[1], reverse=True)
        return [
            Recommendation(
                book=book,
                score=score,
                reason="Рекомендовано на основе вашей истории",
            )
            for book, score in candidates[:limit]
        ]

    def _fallback_recommendations(self, limit: int) -> list[Recommendation]:
        """Запасной подбор популярных книг художественной литературы."""
        candidates = self._books.search(query="", limit=limit * 3)
        result: list[Recommendation] = []
        for book in candidates:
            if book.category == BookCategory.FICTION and len(result) < limit:
                result.append(
                    Recommendation(
                        book=book,
                        score=0.5,
                        reason="Популярное в этой категории",
                    )
                )
        return result
