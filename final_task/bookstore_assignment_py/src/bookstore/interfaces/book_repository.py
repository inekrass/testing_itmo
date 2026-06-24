from __future__ import annotations

from typing import Protocol, runtime_checkable

from bookstore.models.book import Book


@runtime_checkable
class BookRepository(Protocol):
    """Источник данных о книгах (база каталога)."""

    def get_by_isbn(self, isbn: str) -> Book:
        """Вернуть книгу по ISBN. Бросает BookNotFoundError, если книги нет."""
        ...

    def search(self, query: str, limit: int = 20) -> list[Book]:
        """Найти книги по подстроке в названии или авторе."""
        ...
