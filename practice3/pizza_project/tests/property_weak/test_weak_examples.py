"""
ДЕМО-ТЕСТЫ для практики мутационного тестирования (Пара 6, блок 1:00-1:20).

Эти тесты НАМЕРЕННО неполные — содержат типичные пробелы реальных проектов:
- Только базовый happy path
- Не проверяют граничные значения
- Не проверяют разные категории клиентов
- Используют единственный example, а не диапазон

Цель упражнения:
    1. Запустить cosmic-ray на этих тестах:
         cosmic-ray init cosmic-ray-weak.toml weak.sqlite
         cosmic-ray exec cosmic-ray-weak.toml weak.sqlite
         cr-report weak.sqlite

    2. Получить отчёт (ожидается ~40-60% выживших мутантов)

    3. Открыть HTML-отчёт, выбрать одного выжившего мутанта

    4. Понять, почему наш тест не ловит эту мутацию

    5. Добавить тест, который её убьёт

    6. Перезапустить cosmic-ray, проверить, что survival rate уменьшился
"""

from datetime import datetime
from decimal import Decimal

import pytest

from pizza_service.domain import (
    CATALOG,
    Customer,
    Order,
    OrderItem,
    OrderService,
    OrderStatus,
    PizzaSize,
    PricingService,
)


@pytest.fixture
def pricing():
    return PricingService()


@pytest.fixture
def order_service(pricing):
    return OrderService(pricing)


# ═══════════════════════════════════════════════════════════════════
#  СЛАБЫЕ ТЕСТЫ — намеренно с пробелами
# ═══════════════════════════════════════════════════════════════════


class TestPricingWeak:
    """
    Намеренно неполный набор тестов.
    Большинство мутантов в PricingService выживут.
    """

    def test_basic_order_total(self, pricing):
        """Простой тест на конкретное число.
        НЕ проверяет: разные размеры, разные пиццы, разное время, разное количество.
        """
        customer = Customer(name="X", phone="+7", is_loyal=False)
        order = Order(customer=customer)
        order.items.append(
            OrderItem(CATALOG["Маргарита"], PizzaSize.MEDIUM, 1)
        )
        total = pricing.calculate_total(order, now=datetime(2025, 5, 14, 12, 0))
        # 450 + 200 доставка = 650
        assert total == Decimal("650")

    def test_loyal_customer_pays_less(self, pricing):
        """Loyal клиент платит меньше — но только в одной точке.
        НЕ проверяет: точный процент скидки, разные размеры заказа, разные пиццы.
        """
        customer = Customer(name="X", phone="+7", is_loyal=True)
        order = Order(customer=customer)
        order.items.append(
            OrderItem(CATALOG["Маргарита"], PizzaSize.MEDIUM, 1)
        )
        total = pricing.calculate_total(order, now=datetime(2025, 5, 14, 12, 0))
        # 450 - 10% = 405 + 200 = 605
        assert total == Decimal("605")

    # ❌ НЕ ПОКРЫТО:
    #   - Размеры SMALL и LARGE (только MEDIUM)
    #   - Промокоды (никакие не проверяются)
    #   - Happy hours (вообще ни одного теста на 14:00-17:00)
    #   - Граничные случаи бесплатной доставки
    #   - Конкурирующие скидки (loyal + promo, какая выиграет)
    #   - Большое количество пицц
    #   - Множитель LARGE (1.3) — нигде явно не проверен


class TestOrderServiceWeak:
    """Слабые тесты для OrderService."""

    def test_add_one_item(self, order_service):
        """Добавляет одну позицию."""
        customer = Customer(name="X", phone="+7")
        order = Order(customer=customer)
        order_service.add_item(order, CATALOG["Маргарита"], PizzaSize.MEDIUM)
        assert len(order.items) == 1

    # ❌ НЕ ПОКРЫТО:
    #   - Что добавилась именно эта пицца, а не другая
    #   - Что quantity сохраняется правильно
    #   - Что нельзя добавлять в подтверждённый заказ
    #   - Удаление позиций
    #   - Применение промокодов (валидных и невалидных)
    #   - Подтверждение и отмена заказа
