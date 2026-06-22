"""
СТАРТОВЫЙ ФАЙЛ — Пара 6, упражнение по property-based testing.

Задача:
    Написать property-based тесты для домена пиццерии,
    проверяющие инварианты предметной области.

Эталон: tests/property/test_pricing_properties.py

Как запустить:
    python -m pytest student_tasks/exercise_property_based.py -v

    # С увеличенным числом примеров:
    python -m pytest student_tasks/exercise_property_based.py --hypothesis-show-statistics
"""

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import assume, given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pizza_service.domain import (
    CATALOG,
    Customer,
    Order,
    OrderItem,
    OrderService,
    PizzaSize,
    PricingService,
)


# ══════════════════════════════════════════════════════════════════
#  Стратегии (генераторы случайных значений)
# ══════════════════════════════════════════════════════════════════


pizza_names = st.sampled_from(list(CATALOG.keys()))
pizza_sizes = st.sampled_from(list(PizzaSize))
quantities = st.integers(min_value=1, max_value=10)


# ══════════════════════════════════════════════════════════════════
#  СВОЙСТВО 1. Промокод не увеличивает сумму
# ══════════════════════════════════════════════════════════════════


@given(
    pizza_name=pizza_names,
    size=pizza_sizes,
)
def test_promo_never_increases_total(pizza_name, size):
    """
    СВОЙСТВО: применение промокода не делает заказ дороже.

    TODO:
      1. Создать клиента и заказ с одной пиццей
      2. Рассчитать total без промокода (запомнить)
      3. Применить промокод "WELCOME10"
      4. Рассчитать total с промокодом
      5. Проверить, что total с промокодом <= total без
    """
    pricing = PricingService()
    customer = Customer(name="Тест", phone="+7")
    order = Order(customer=customer)
    order.items.append(OrderItem(CATALOG[pizza_name], size, 1))

    moment = datetime(2026, 6, 22, 12, 0)
    total_without_promo = pricing.calculate_total(order, now=moment)

    order.promo_code = "WELCOME10"
    total_with_promo = pricing.calculate_total(order, now=moment)

    assert total_with_promo <= total_without_promo


# ══════════════════════════════════════════════════════════════════
#  СВОЙСТВО 2. Положительная стоимость
# ══════════════════════════════════════════════════════════════════


@given(
    items_count=st.integers(min_value=1, max_value=5),
)
def test_total_is_always_positive(items_count):
    """
    СВОЙСТВО: для непустого заказа итоговая сумма всегда > 0.

    TODO:
      1. Создать заказ с items_count позициями
      2. Рассчитать total
      3. Проверить total > 0
    """
    pricing = PricingService()
    customer = Customer(name="Тест", phone="+7")
    order = Order(customer=customer)

    for _ in range(items_count):
        order.items.append(OrderItem(CATALOG["Маргарита"], PizzaSize.MEDIUM, 1))

    total = pricing.calculate_total(
        order, now=datetime(2026, 6, 22, 12, 0)
    )

    assert total > Decimal("0")


# ══════════════════════════════════════════════════════════════════
#  СВОЙСТВО 3. Бесплатная доставка как точная граница
# ══════════════════════════════════════════════════════════════════


@given(qty=st.integers(min_value=1, max_value=20))
def test_free_delivery_kicks_in_at_threshold(qty):
    """
    СВОЙСТВО: при subtotal >= 1500 доставка обнуляется.
    Используйте assume() для отсечения случаев < 1500.

    TODO:
      1. Создать заказ с qty пицц "Маргарита" размера LARGE
         (одна стоит 585, qty=3 даст 1755 — выше порога)
      2. assume(order.subtotal >= 1500)
      3. Проверить, что total == subtotal (без доставки)
    """
    pricing = PricingService()
    customer = Customer(name="Тест", phone="+7")
    order = Order(customer=customer)
    order.items.append(OrderItem(CATALOG["Маргарита"], PizzaSize.LARGE, qty))

    assume(order.subtotal >= PricingService.FREE_DELIVERY_THRESHOLD)

    total = pricing.calculate_total(
        order, now=datetime(2026, 6, 22, 12, 0)
    )

    assert total == order.subtotal


# ══════════════════════════════════════════════════════════════════
#  СВОЙСТВО 4. Удаление позиции уменьшает сумму
# ══════════════════════════════════════════════════════════════════


@given(
    pizza_name1=pizza_names,
    pizza_name2=pizza_names,
    size1=pizza_sizes,
    size2=pizza_sizes,
)
def test_remove_item_decreases_total(pizza_name1, pizza_name2, size1, size2):
    """
    СВОЙСТВО: удаление позиции из заказа уменьшает subtotal.

    TODO:
      1. Создать заказ с двумя позициями
      2. Запомнить subtotal_before
      3. Удалить первую позицию
      4. Проверить subtotal < subtotal_before
    """
    order_service = OrderService(PricingService())
    customer = Customer(name="Тест", phone="+7")
    order = Order(customer=customer)

    order_service.add_item(order, CATALOG[pizza_name1], size1, 1)
    order_service.add_item(order, CATALOG[pizza_name2], size2, 1)

    subtotal_before = order.subtotal
    order_service.remove_item(order, 0)

    assert order.subtotal < subtotal_before
