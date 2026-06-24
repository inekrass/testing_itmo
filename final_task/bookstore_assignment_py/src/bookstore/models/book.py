from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class BookCategory(str, Enum):
    """Категория книги. От неё зависят правила скидок и доставки."""

    FICTION = "FICTION"
    NON_FICTION = "NON_FICTION"
    TEXTBOOK = "TEXTBOOK"
    CHILDREN = "CHILDREN"
    RARE = "RARE"


@dataclass(frozen=True)
class Book:
    """Книга в каталоге магазина. Неизменяемый объект."""

    isbn: str
    title: str
    author: str
    category: BookCategory
    base_price: Decimal
    weight_grams: int
    publication_year: int
