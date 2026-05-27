"""
Тесты для модуля shipping.py
Практика 1: Задание «Найди баг».

В модуле shipping.py содержится НАМЕРЕННЫЙ ДЕФЕКТ.
Часть тестов в этом файле УПАДЁТ — это ожидаемое поведение.
Задача студента: найти баг, описать его и предложить исправление.

Демонстрирует:
- Как тесты обнаруживают дефекты
- pytest.approx для сравнения float
- xfail для известных дефектов
"""

import pytest
from shipping import calculate_shipping


# ══════════════════════════════════════════════════════════
#  ВНУТРЕННЯЯ ДОСТАВКА (domestic)
# ══════════════════════════════════════════════════════════


class TestDomesticShipping:
    """Тесты внутренней доставки."""

    @pytest.mark.smoke
    def test_lightweight_under_1kg(self):
        """Посылка до 1 кг: фиксированная стоимость 200 руб."""
        # Arrange
        weight = 0.5
        # Act
        cost = calculate_shipping(weight, "domestic")
        # Assert
        assert cost == 200

    def test_exactly_1kg(self):
        """Граница: ровно 1 кг → 200 руб. (ещё в первой категории)."""
        assert calculate_shipping(1.0, "domestic") == 200

    def test_medium_5kg(self):
        """5 кг: 200 + 50 × (5 - 1) = 400 руб."""
        cost = calculate_shipping(5.0, "domestic")
        assert cost == 400

    def test_medium_10kg(self):
        """Граница: 10 кг: 200 + 50 × 9 = 650 руб."""
        cost = calculate_shipping(10.0, "domestic")
        assert cost == 650

    def test_heavy_15kg(self):
        """15 кг: 200 + 450 + 30 × 5 = 800 руб."""
        cost = calculate_shipping(15.0, "domestic")
        assert cost == 800

    def test_heavy_30kg(self):
        """Граница: максимальный вес 30 кг: 200 + 450 + 30 × 20 = 1250 руб."""
        cost = calculate_shipping(30.0, "domestic")
        assert cost == 1250

    def test_over_30kg_raises(self):
        """Больше 30 кг: ValueError."""
        with pytest.raises(ValueError, match="30 кг"):
            calculate_shipping(30.1, "domestic")

    def test_express_doubles_cost(self):
        """Экспресс удваивает стоимость."""
        normal = calculate_shipping(5.0, "domestic", is_express=False)
        express = calculate_shipping(5.0, "domestic", is_express=True)
        assert express == normal * 2


# ══════════════════════════════════════════════════════════
#  МЕЖДУНАРОДНАЯ ДОСТАВКА (international)
#
#  ЗДЕСЬ ТЕСТЫ ОБНАРУЖИВАЮТ БАГ:
#  По спецификации тариф = 150 руб./кг сверх 1 кг,
#  но в коде стоит 100 руб./кг.
# ══════════════════════════════════════════════════════════


class TestInternationalShipping:
    """Тесты международной доставки. Часть тестов обнаружит дефект."""

    @pytest.mark.smoke
    def test_lightweight_under_1kg(self):
        """Посылка до 1 кг: фиксированная стоимость 500 руб."""
        cost = calculate_shipping(0.5, "international")
        assert cost == 500

    def test_exactly_1kg(self):
        """Граница: ровно 1 кг → 500 руб."""
        assert calculate_shipping(1.0, "international") == 500

    @pytest.mark.xfail(reason="БАГ: в коде тариф 100 руб./кг вместо 150 руб./кг")
    def test_medium_5kg(self):
        """
        5 кг: по спецификации 500 + 150 × 4 = 1100 руб.
        Этот тест УПАДЁТ из-за бага (функция вернёт 900).
        """
        cost = calculate_shipping(5.0, "international")
        assert cost == 1100  # Ожидаем 1100, получим 900

    @pytest.mark.xfail(reason="БАГ: в коде тариф 100 руб./кг вместо 150 руб./кг")
    def test_medium_10kg(self):
        """10 кг: по спецификации 500 + 150 × 9 = 1850 руб."""
        cost = calculate_shipping(10.0, "international")
        assert cost == 1850  # Ожидаем 1850, получим 1400

    @pytest.mark.xfail(reason="БАГ: в коде тариф 100 руб./кг вместо 150 руб./кг")
    def test_max_20kg(self):
        """20 кг: по спецификации 500 + 150 × 19 = 3350 руб."""
        cost = calculate_shipping(20.0, "international")
        assert cost == 3350  # Ожидаем 3350, получим 2400

    def test_over_20kg_raises(self):
        """Больше 20 кг: ValueError."""
        with pytest.raises(ValueError, match="20 кг"):
            calculate_shipping(20.1, "international")

    @pytest.mark.xfail(reason="БАГ: в коде тариф 100 руб./кг вместо 150 руб./кг")
    def test_express_international(self):
        """Экспресс международная 5 кг: (500 + 150×4) × 2 = 2200 руб."""
        cost = calculate_shipping(5.0, "international", is_express=True)
        assert cost == 2200  # Ожидаем 2200, получим 1800


# ══════════════════════════════════════════════════════════
#  ОБЩИЕ ПРОВЕРКИ
# ══════════════════════════════════════════════════════════


class TestShippingGeneral:
    """Общие проверки: валидация, неизвестные направления."""

    @pytest.mark.negative
    def test_zero_weight_raises(self):
        """Нулевой вес → ValueError."""
        with pytest.raises(ValueError, match="положительным"):
            calculate_shipping(0, "domestic")

    @pytest.mark.negative
    def test_negative_weight_raises(self):
        """Отрицательный вес → ValueError."""
        with pytest.raises(ValueError, match="положительным"):
            calculate_shipping(-5, "domestic")

    @pytest.mark.negative
    def test_unknown_destination_raises(self):
        """Неизвестное направление → ValueError."""
        with pytest.raises(ValueError, match="Неизвестное направление"):
            calculate_shipping(1.0, "mars")

    def test_very_small_weight(self):
        """Граничное: минимально возможный вес."""
        cost = calculate_shipping(0.001, "domestic")
        assert cost == 200

    @pytest.mark.boundary
    def test_domestic_boundary_1kg_plus_epsilon(self):
        """Чуть больше 1 кг → переход во вторую категорию."""
        cost = calculate_shipping(1.01, "domestic")
        expected = 200 + 50 * (1.01 - 1)  # 200.5
        assert cost == pytest.approx(expected)

    @pytest.mark.boundary
    def test_domestic_boundary_10kg_plus_epsilon(self):
        """Чуть больше 10 кг → переход в третью категорию."""
        cost = calculate_shipping(10.01, "domestic")
        expected = 200 + 450 + 30 * (10.01 - 10)  # 650.3
        assert cost == pytest.approx(expected)
