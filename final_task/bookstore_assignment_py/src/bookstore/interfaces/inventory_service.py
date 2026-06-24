from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class InventoryService(Protocol):
    """Управление остатками книг на складе."""

    def get_stock(self, isbn: str) -> int:
        """Текущий остаток книги на складе."""
        ...

    def reserve(self, isbn: str, quantity: int) -> str:
        """Зарезервировать количество книг и вернуть идентификатор резервации.
        Бросает InventoryError при нехватке товара."""
        ...

    def release(self, reservation_id: str) -> None:
        """Снять резервацию (например, при отмене заказа)."""
        ...
