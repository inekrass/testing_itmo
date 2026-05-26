"""
Тесты для модуля cart.py
Практика 2: Домашнее задание — полное тестирование корзины.

Демонстрирует:
- Фикстуры product_*, empty_cart, cart_with_items из conftest.py
- Параметризацию для промокодов
- Полное покрытие всех ветвей
"""

import pytest
from cart import Cart, Product


# ══════════════════════════════════════════════════════════
#  ДОБАВЛЕНИЕ ТОВАРОВ
# ══════════════════════════════════════════════════════════


class TestCartAdd:
    """Тесты добавления товаров в корзину."""

    @pytest.mark.smoke
    def test_add_single_item(self, empty_cart, product_book):
        """
        Given: пустая корзина
        When:  добавляем 1 книгу
        Then:  корзина содержит 1 единицу товара
        """
        empty_cart.add(product_book)
        assert empty_cart.get_item_count() == 1
        assert empty_cart.is_empty() is False

    def test_add_multiple_units(self, empty_cart, product_book):
        """Добавление нескольких единиц одного товара."""
        empty_cart.add(product_book, quantity=5)
        assert empty_cart.get_item_count() == 5

    def test_add_increments_existing(self, empty_cart, product_book):
        """Повторное добавление увеличивает количество."""
        empty_cart.add(product_book, 2)
        empty_cart.add(product_book, 3)
        assert empty_cart.get_item_count() == 5

    def test_add_different_products(self, empty_cart, product_book, product_pen):
        """Добавление разных товаров."""
        empty_cart.add(product_book, 1)
        empty_cart.add(product_pen, 2)
        assert empty_cart.get_item_count() == 3

    @pytest.mark.negative
    def test_add_zero_quantity_raises(self, empty_cart, product_book):
        """Нулевое количество → ValueError."""
        with pytest.raises(ValueError, match="положительным"):
            empty_cart.add(product_book, 0)

    @pytest.mark.negative
    def test_add_negative_quantity_raises(self, empty_cart, product_book):
        """Отрицательное количество → ValueError."""
        with pytest.raises(ValueError, match="положительным"):
            empty_cart.add(product_book, -1)

    @pytest.mark.negative
    def test_add_over_stock_raises(self, empty_cart, product_laptop):
        """Количество больше остатка на складе → ValueError."""
        # У ноутбука stock=2
        with pytest.raises(ValueError, match="Недостаточно товара"):
            empty_cart.add(product_laptop, 3)

    @pytest.mark.boundary
    def test_add_exactly_stock(self, empty_cart, product_laptop):
        """Количество ровно равно остатку на складе → успех."""
        empty_cart.add(product_laptop, 2)  # stock=2
        assert empty_cart.get_item_count() == 2

    @pytest.mark.negative
    def test_add_incremental_over_stock_raises(self, empty_cart, product_laptop):
        """Сумма добавлений превышает остаток → ValueError."""
        empty_cart.add(product_laptop, 1)
        with pytest.raises(ValueError, match="Недостаточно товара"):
            empty_cart.add(product_laptop, 2)  # 1 + 2 = 3 > stock=2


# ══════════════════════════════════════════════════════════
#  УДАЛЕНИЕ ТОВАРОВ
# ══════════════════════════════════════════════════════════


class TestCartRemove:
    """Тесты удаления товаров из корзины."""

    def test_remove_existing_item(self, cart_with_items):
        """Удаление существующего товара."""
        cart_with_items.remove("Книга")
        assert cart_with_items.get_item_count() == 3  # Осталась только Ручка ×3

    def test_remove_makes_cart_empty(self, empty_cart, product_book):
        """Удаление единственного товара делает корзину пустой."""
        empty_cart.add(product_book)
        empty_cart.remove("Книга")
        assert empty_cart.is_empty() is True

    @pytest.mark.negative
    def test_remove_nonexistent_raises(self, empty_cart):
        """Удаление несуществующего товара → KeyError."""
        with pytest.raises(KeyError, match="не найден"):
            empty_cart.remove("Фантом")

    @pytest.mark.negative
    def test_remove_from_empty_cart_raises(self, empty_cart):
        """Удаление из пустой корзины → KeyError."""
        with pytest.raises(KeyError):
            empty_cart.remove("Книга")


# ══════════════════════════════════════════════════════════
#  ПОДСЧЁТ СТОИМОСТИ
# ══════════════════════════════════════════════════════════


class TestCartTotal:
    """Тесты расчёта стоимости."""

    def test_empty_cart_total_is_zero(self, empty_cart):
        """Пустая корзина → 0."""
        assert empty_cart.get_total() == 0.0

    @pytest.mark.smoke
    def test_total_with_items(self, cart_with_items):
        """
        Given: корзина с Книга ×2 (500) + Ручка ×3 (50)
        When:  запрашиваем итого
        Then:  2×500 + 3×50 = 1150
        """
        assert cart_with_items.get_total() == 1150.0

    def test_total_after_remove(self, cart_with_items):
        """Итого обновляется после удаления товара."""
        cart_with_items.remove("Книга")
        assert cart_with_items.get_total() == 150.0  # 3 × 50


# ══════════════════════════════════════════════════════════
#  ПРОМОКОДЫ
# ══════════════════════════════════════════════════════════


class TestCartPromo:
    """Тесты применения промокодов."""

    @pytest.mark.parametrize(
        "code, expected_total",
        [
            pytest.param("SAVE10", 1035.0, id="10_percent_off"),
            pytest.param("SAVE20", 920.0, id="20_percent_off"),
            pytest.param("HALF", 575.0, id="50_percent_off"),
        ],
    )
    def test_promo_codes(self, cart_with_items, code, expected_total):
        """
        Given: корзина на 1150 руб.
        When:  применяем промокод
        Then:  стоимость уменьшается на соответствующий процент
        """
        result = cart_with_items.apply_promo(code)
        assert result == expected_total

    @pytest.mark.negative
    def test_invalid_promo_raises(self, cart_with_items):
        """Неизвестный промокод → ValueError."""
        with pytest.raises(ValueError, match="Неизвестный промокод"):
            cart_with_items.apply_promo("FREEBIE")

    def test_promo_on_empty_cart(self, empty_cart):
        """Промокод на пустую корзину → 0."""
        result = empty_cart.apply_promo("HALF")
        assert result == 0.0


# ══════════════════════════════════════════════════════════
#  СОСТОЯНИЕ КОРЗИНЫ
# ══════════════════════════════════════════════════════════


class TestCartState:
    """Тесты проверки состояния корзины."""

    def test_new_cart_is_empty(self, empty_cart):
        """Новая корзина пуста."""
        assert empty_cart.is_empty() is True
        assert empty_cart.get_item_count() == 0
        assert empty_cart.get_total() == 0.0

    def test_cart_with_items_is_not_empty(self, cart_with_items):
        """Корзина с товарами не пуста."""
        assert cart_with_items.is_empty() is False
        assert cart_with_items.get_item_count() > 0
