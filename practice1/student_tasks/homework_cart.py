"""
ДОМАШНЕЕ ЗАДАНИЕ — после Занятия 2.

Задача:
    Написать полный набор тестов для корзины покупок (src/cart.py).
    Требования:
        - Использовать фикстуры (минимум 3)
        - Применить параметризацию (хотя бы для промокодов)
        - Разметить тесты маркерами smoke/boundary/negative
        - Добиться покрытия ≥ 95%
        - Минимум 15 тест-кейсов

Эталон: tests/unit/test_cart.py

Как проверить:
    pytest student_tasks/homework_cart.py -v
    python3 -m pytest student_tasks/homework_cart.py --cov=cart --cov-report=term-missing

Критерии оценки:
    [ ] ≥ 15 тест-кейсов
    [ ] ≥ 3 фикстуры (пустая корзина, корзина с товарами, товары)
    [ ] Параметризация для промокодов SAVE10/SAVE20/HALF
    [ ] Маркеры smoke, boundary, negative использованы
    [ ] Покрытие ≥ 95% (branch coverage)
    [ ] Все тесты проходят
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cart import Cart, Product


# ══════════════════════════════════════════════════════════════
#  ФИКСТУРЫ (3+)
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def product_book():
    """Товар 'Книга' — 500 руб., 10 на складе."""
    return Product(name="Книга", price=500.0, stock=10)


@pytest.fixture
def product_pen():
    """Товар 'Ручка' — 50 руб., 100 на складе."""
    return Product(name="Ручка", price=50.0, stock=100)


@pytest.fixture
def product_laptop():
    """Товар 'Ноутбук' — 75000 руб., 2 на складе."""
    return Product(name="Ноутбук", price=75000.0, stock=2)


@pytest.fixture
def empty_cart():
    """Пустая корзина."""
    return Cart()


@pytest.fixture
def cart_with_items(empty_cart, product_book, product_pen):
    """Корзина с книгой ×2 и ручкой ×3."""
    empty_cart.add(product_book, 2)
    empty_cart.add(product_pen, 3)
    return empty_cart


# ══════════════════════════════════════════════════════════════
#  ТЕСТЫ
# ══════════════════════════════════════════════════════════════


class TestCartAdd:
    """Добавление товаров."""

    @pytest.mark.smoke
    def test_add_single_item(self, empty_cart, product_book):
        """Добавление одного товара."""
        empty_cart.add(product_book)

        assert empty_cart.get_item_count() == 1
        assert empty_cart.is_empty() is False

    def test_add_different_products(self, empty_cart, product_book, product_pen):
        """Добавление разных товаров."""
        empty_cart.add(product_book)
        empty_cart.add(product_pen, 3)

        assert empty_cart.get_item_count() == 4

    def test_add_increments_existing_product(self, empty_cart, product_book):
        """Повторное добавление увеличивает количество товара."""
        empty_cart.add(product_book, 2)
        empty_cart.add(product_book, 3)

        assert empty_cart.get_item_count() == 5

    @pytest.mark.boundary
    def test_add_incremental_over_stock_raises(self, empty_cart, product_laptop):
        """Сумма нескольких добавлений больше остатка на складе → ValueError."""
        empty_cart.add(product_laptop, 1)

        with pytest.raises(ValueError, match="Недостаточно товара"):
            empty_cart.add(product_laptop, 2)

    @pytest.mark.negative
    def test_add_zero_quantity_raises(self, empty_cart, product_book):
        """Нулевое количество → ValueError."""
        with pytest.raises(ValueError, match="положительным"):
            empty_cart.add(product_book, 0)

    @pytest.mark.negative
    def test_add_over_stock_raises(self, empty_cart, product_laptop):
        """Количество больше остатка на складе → ValueError."""
        with pytest.raises(ValueError, match="Недостаточно товара"):
            empty_cart.add(product_laptop, 3)


class TestCartPromo:
    """Промокоды — используйте параметризацию!"""

    @pytest.mark.parametrize(
        "code, expected_total",
        [
            pytest.param("SAVE10", 1035.0, id="save10"),
            pytest.param("SAVE20", 920.0, id="save20"),
            pytest.param("HALF", 575.0, id="half"),
        ],
    )
    def test_apply_promo_codes(self, cart_with_items, code, expected_total):
        """Промокод уменьшает стоимость корзины."""
        assert cart_with_items.apply_promo(code) == expected_total

    @pytest.mark.negative
    def test_unknown_promo_raises(self, cart_with_items):
        """Неизвестный промокод → ValueError."""
        with pytest.raises(ValueError, match="Неизвестный промокод"):
            cart_with_items.apply_promo("UNKNOWN")


class TestCartTotal:
    """Расчёт стоимости."""

    @pytest.mark.boundary
    def test_empty_cart_total_is_zero(self, empty_cart):
        """Пустая корзина → 0."""
        assert empty_cart.get_total() == 0.0

    @pytest.mark.smoke
    def test_cart_with_items_total(self, cart_with_items):
        """Книга ×2 и ручка ×3 → 1150."""
        assert cart_with_items.get_total() == 1150.0

    def test_total_after_remove(self, cart_with_items):
        """Стоимость пересчитывается после удаления товара."""
        cart_with_items.remove("Книга")

        assert cart_with_items.get_total() == 150.0


class TestCartRemove:
    """Удаление товаров."""

    def test_remove_existing_item(self, cart_with_items):
        """Удаление существующего товара."""
        cart_with_items.remove("Книга")

        assert cart_with_items.get_item_count() == 3

    @pytest.mark.boundary
    def test_remove_last_item_makes_cart_empty(self, empty_cart, product_book):
        """Удаление единственного товара делает корзину пустой."""
        empty_cart.add(product_book)
        empty_cart.remove("Книга")

        assert empty_cart.is_empty() is True

    @pytest.mark.negative
    def test_remove_unknown_item_raises(self, empty_cart):
        """Удаление несуществующего товара → KeyError."""
        with pytest.raises(KeyError, match="не найден"):
            empty_cart.remove("Листок")
