"""
Модуль корзины покупок.
Практика 2: Домашнее задание — полное тестирование.
"""

from dataclasses import dataclass


@dataclass
class Product:
    """Товар в каталоге."""

    name: str
    price: float
    stock: int


class Cart:
    """Корзина покупок."""

    def __init__(self):
        self._items: dict[str, tuple[Product, int]] = {}

    def add(self, product: Product, quantity: int = 1):
        """
        Добавляет товар в корзину.

        Args:
            product: Товар для добавления.
            quantity: Количество (по умолчанию 1).

        Raises:
            ValueError: Если quantity <= 0 или превышает остаток на складе.
        """
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным")
        if quantity > product.stock:
            raise ValueError(
                f"Недостаточно товара на складе: {product.stock} шт."
            )

        if product.name in self._items:
            existing_product, existing_qty = self._items[product.name]
            new_qty = existing_qty + quantity
            if new_qty > product.stock:
                raise ValueError(
                    f"Недостаточно товара на складе: {product.stock} шт."
                )
            self._items[product.name] = (existing_product, new_qty)
        else:
            self._items[product.name] = (product, quantity)

    def remove(self, product_name: str):
        """
        Удаляет товар из корзины.

        Raises:
            KeyError: Если товар не найден в корзине.
        """
        if product_name not in self._items:
            raise KeyError(f"Товар '{product_name}' не найден в корзине")
        del self._items[product_name]

    def get_total(self) -> float:
        """Возвращает общую стоимость товаров в корзине."""
        return sum(p.price * q for p, q in self._items.values())

    def get_item_count(self) -> int:
        """Возвращает общее количество единиц товара в корзине."""
        return sum(q for _, q in self._items.values())

    def apply_promo(self, code: str) -> float:
        """
        Применяет промокод и возвращает итоговую стоимость.

        Доступные промокоды:
        - SAVE10: скидка 10%
        - SAVE20: скидка 20%
        - HALF: скидка 50%

        Raises:
            ValueError: Если промокод неизвестен.
        """
        promos = {"SAVE10": 0.10, "SAVE20": 0.20, "HALF": 0.50}
        if code not in promos:
            raise ValueError(f"Неизвестный промокод: {code}")
        total = self.get_total()
        discount = total * promos[code]
        return total - discount

    def is_empty(self) -> bool:
        """Проверяет, пуста ли корзина."""
        return len(self._items) == 0
