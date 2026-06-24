from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from bookstore.models.book import Book


@dataclass
class CartItem:
    """Позиция в заказе: книга и её количество."""

    book: Book
    quantity: int

    @property
    def line_total(self) -> Decimal:
        """Стоимость позиции по базовой цене, без учёта скидок."""
        return self.book.base_price * self.quantity
