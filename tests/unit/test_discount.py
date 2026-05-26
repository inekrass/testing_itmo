"""
Тесты для модуля discount.py
Практика 1–2: Полный тестовый сценарий.

Демонстрирует:
- Группировку тестов по сценариям (Positive / Boundary / Negative / Special)
- Параметризацию с pytest.param и id
- Маркеры smoke, boundary, negative
- Паттерн Given — When — Then в docstring
"""

import pytest
from discount import calculate_discount


class TestDiscountPositive:
    """
    Группа 1: Позитивные сценарии.
    Проверяем все комбинации типа клиента × праздничный день.
    """

    @pytest.mark.smoke
    @pytest.mark.parametrize(
        "price, customer_type, is_holiday, expected",
        [
            pytest.param(1000, "regular", False, 0.0, id="TS-D01_regular_normal"),
            pytest.param(1000, "regular", True, 50.0, id="TS-D02_regular_holiday"),
            pytest.param(1000, "premium", False, 100.0, id="TS-D03_premium_normal"),
            pytest.param(1000, "premium", True, 150.0, id="TS-D04_premium_holiday"),
            pytest.param(1000, "vip", False, 200.0, id="TS-D05_vip_normal"),
            pytest.param(1000, "vip", True, 250.0, id="TS-D06_vip_holiday"),
        ],
    )
    def test_discount_for_all_customer_types(
        self, price, customer_type, is_holiday, expected
    ):
        """
        Given: клиент определённого типа и цена 1000 руб.
        When:  рассчитываем скидку
        Then:  скидка соответствует тарифу
        """
        result = calculate_discount(price, customer_type, is_holiday)
        assert result == expected


class TestDiscountBoundary:
    """
    Группа 2: Граничные значения.
    Пороги цен и ограничение максимальной скидки (500 руб.).
    """

    @pytest.mark.boundary
    def test_minimum_price(self):
        """TS-D07: Скидка от минимально допустимой цены (0.01 руб.)."""
        # Arrange
        price = 0.01
        # Act — 25% от 0.01 = 0.0025
        result = calculate_discount(price, "vip", True)
        # Assert
        assert result == pytest.approx(0.0025)

    @pytest.mark.boundary
    def test_discount_exactly_at_cap(self):
        """TS-D08: Скидка ровно 500 руб. (VIP, праздник, цена 2000)."""
        # 25% от 2000 = 500.0 — совпадает с cap
        result = calculate_discount(2000, "vip", True)
        assert result == 500.0

    @pytest.mark.boundary
    def test_discount_just_above_cap(self):
        """TS-D09: Скидка ограничена 500 руб. (25% от 2001 = 500.25 → 500)."""
        result = calculate_discount(2001, "vip", True)
        assert result == 500.0

    @pytest.mark.boundary
    def test_very_large_price(self):
        """TS-D10: При любой цене скидка не более 500 руб."""
        result = calculate_discount(100_000, "vip", True)
        assert result == 500.0

    @pytest.mark.boundary
    def test_cap_for_vip_normal_day(self):
        """Порог для VIP в обычный день: 20% от 2500 = 500."""
        result = calculate_discount(2500, "vip", False)
        assert result == 500.0

    @pytest.mark.boundary
    def test_just_below_cap_for_vip_normal(self):
        """Чуть ниже порога для VIP в обычный день: 20% от 2499 = 499.8."""
        result = calculate_discount(2499, "vip", False)
        assert result == pytest.approx(499.8)


class TestDiscountNegative:
    """
    Группа 3: Негативные сценарии.
    Невалидные входные данные.
    """

    @pytest.mark.negative
    @pytest.mark.parametrize(
        "price, customer_type, is_holiday, exc_type, exc_match",
        [
            pytest.param(
                0, "regular", False, ValueError, "положительной",
                id="TS-D11_zero_price",
            ),
            pytest.param(
                -100, "vip", True, ValueError, "положительной",
                id="TS-D12_negative_price",
            ),
            pytest.param(
                -0.01, "premium", False, ValueError, "положительной",
                id="TS-D12b_tiny_negative",
            ),
            pytest.param(
                1000, "gold", False, ValueError, "Неизвестный тип",
                id="TS-D13_unknown_type",
            ),
            pytest.param(
                1000, "", False, ValueError, "Неизвестный тип",
                id="TS-D13b_empty_type",
            ),
        ],
    )
    def test_invalid_input_raises_error(
        self, price, customer_type, is_holiday, exc_type, exc_match
    ):
        """
        Given: невалидные входные данные
        When:  вызываем calculate_discount
        Then:  выбрасывается исключение с понятным сообщением
        """
        with pytest.raises(exc_type, match=exc_match):
            calculate_discount(price, customer_type, is_holiday)


class TestDiscountSpecialCases:
    """
    Группа 4: Специальные и крайние случаи.
    """

    def test_regular_no_holiday_always_zero(self):
        """TS-D16: Обычный клиент без праздника всегда получает скидку 0."""
        assert calculate_discount(0.01, "regular", False) == 0.0
        assert calculate_discount(1000, "regular", False) == 0.0
        assert calculate_discount(100_000, "regular", False) == 0.0

    def test_discount_is_float(self):
        """Скидка всегда возвращается как float."""
        result = calculate_discount(100, "premium", False)
        assert isinstance(result, float)

    @pytest.mark.parametrize(
        "price, customer_type",
        [
            (200, "regular"),
            (200, "premium"),
            (200, "vip"),
        ],
    )
    def test_no_holiday_consistent(self, price, customer_type):
        """В обычный день скидка всегда ≤ скидки в праздник."""
        normal = calculate_discount(price, customer_type, False)
        holiday = calculate_discount(price, customer_type, True)
        assert normal <= holiday
