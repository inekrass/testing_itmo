"""
Property-based тесты с Hypothesis — Пара 6.

Демонстрирует:
- Генерацию случайных входных данных
- Проверку СВОЙСТВ (инвариантов), а не конкретных примеров
- Автоматическое shrinking — поиск минимального контрпримера
- Stateful testing — генерация последовательностей действий
"""

from datetime import datetime
from decimal import Decimal

import pytest
from hypothesis import assume, given, settings, strategies as st
from hypothesis.strategies import composite

from pizza_service.domain import (
    CATALOG,
    Customer,
    Order,
    OrderItem,
    OrderService,
    OrderStatus,
    Pizza,
    PizzaSize,
    PricingService,
)


# ═══════════════════════════════════════════════════════════════
#  Стратегии — генераторы случайных данных
# ═══════════════════════════════════════════════════════════════


# Базовые стратегии: построение данных предметной области
pizza_names = st.sampled_from(list(CATALOG.keys()))
pizza_sizes = st.sampled_from(list(PizzaSize))
quantities = st.integers(min_value=1, max_value=10)
amounts = st.decimals(min_value=Decimal("100"), max_value=Decimal("10000"), places=2)


@composite
def order_items(draw):
    """Стратегия для одной позиции заказа."""
    name = draw(pizza_names)
    size = draw(pizza_sizes)
    qty = draw(quantities)
    return OrderItem(CATALOG[name], size, qty)


@composite
def orders(draw, is_loyal=None, with_promo=None):
    """Стратегия для целого заказа."""
    loyal = draw(st.booleans()) if is_loyal is None else is_loyal
    customer = Customer(name="Test", phone="+7", is_loyal=loyal)
    order = Order(customer=customer)

    items = draw(st.lists(order_items(), min_size=1, max_size=5))
    for item in items:
        order.items.append(item)

    if with_promo is True:
        order.promo_code = draw(st.sampled_from(list(PricingService.PROMO_CODES.keys())))
    elif with_promo is None and draw(st.booleans()):
        order.promo_code = draw(st.sampled_from(list(PricingService.PROMO_CODES.keys())))

    return order


# ═══════════════════════════════════════════════════════════════
#  Свойства (инварианты)
# ═══════════════════════════════════════════════════════════════


class TestPricingProperties:
    """
    Property-based: вместо примеров проверяем свойства, которые
    должны быть истинны ДЛЯ ЛЮБЫХ валидных входов.
    """

    @given(order=orders())
    def test_total_is_never_negative(self, order):
        """СВОЙСТВО: итоговая сумма заказа не может быть отрицательной."""
        pricing = PricingService()
        total = pricing.calculate_total(
            order, now=datetime(2025, 5, 14, 12, 0)
        )
        assert total >= Decimal("0"), f"Total {total} оказалось отрицательным!"

    @given(order=orders())
    def test_total_not_greater_than_subtotal_plus_delivery(self, order):
        """
        СВОЙСТВО: итог не превышает subtotal + макс. доставка.
        Скидки могут только уменьшить сумму.
        """
        pricing = PricingService()
        total = pricing.calculate_total(
            order, now=datetime(2025, 5, 14, 12, 0)
        )
        max_possible = order.subtotal + PricingService.DELIVERY_FEE
        assert total <= max_possible

    @given(order=orders(is_loyal=False, with_promo=False))
    def test_no_discount_no_promo_means_no_savings(self, order):
        """
        СВОЙСТВО: если клиент не loyal, без промокода, не в happy hour —
        скидки не применяются. Только базовая стоимость + доставка.
        """
        pricing = PricingService()
        # 12:00 — не happy hour
        total = pricing.calculate_total(
            order, now=datetime(2025, 5, 14, 12, 0)
        )

        expected_delivery = (
            Decimal("0") if order.subtotal >= PricingService.FREE_DELIVERY_THRESHOLD
            else PricingService.DELIVERY_FEE
        )
        assert total == order.subtotal + expected_delivery

    @given(order=orders(is_loyal=True, with_promo=False))
    def test_loyal_customer_pays_no_more_than_regular_for_large_orders(self, order):
        """
        СВОЙСТВО: для крупных заказов (subtotal >= 1700) loyal платит ≤ обычного.

        ⚠️ ВНИМАНИЕ! Это поучительный пример.
        Изначально хотелось проверить: "loyal клиент платит не больше обычного".
        Но property-based может найти контрпример:
            subtotal=1560 (выше порога 1500 → доставка 0)
            loyal: 1560*0.9 = 1404 (упало ниже 1500!) → +200 доставка = 1604
            regular: 1560 + 0 = 1560

        Это РЕАЛЬНАЯ особенность бизнес-логики: скидка может «опустить»
        заказ ниже порога бесплатной доставки, и loyal клиент заплатит
        больше. Поэтому свойство формулируется СТРОЖЕ — для заказов с
        запасом от порога.
        """
        assume(order.subtotal >= Decimal("1700"))   # запас от порога

        pricing = PricingService()

        loyal_total = pricing.calculate_total(
            order, now=datetime(2025, 5, 14, 12, 0)
        )

        # Сравним с тем же заказом, но НЕ loyal
        regular_order = Order(
            customer=Customer(name="X", phone="+7", is_loyal=False),
            items=order.items.copy(),
        )
        regular_total = pricing.calculate_total(
            regular_order, now=datetime(2025, 5, 14, 12, 0)
        )

        assert loyal_total <= regular_total


class TestOrderServiceProperties:
    """Свойства сервиса заказов."""

    @given(items=st.lists(order_items(), min_size=1, max_size=10))
    def test_add_remove_preserves_count(self, items):
        """
        СВОЙСТВО: добавление и удаление одного и того же товара
        не меняет состав заказа.
        """
        order_service = OrderService(PricingService())
        customer = Customer(name="X", phone="+7")
        order = Order(customer=customer)

        # Добавляем
        for item in items:
            order_service.add_item(order, item.pizza, item.size, item.quantity)

        count_before_extra = len(order.items)

        # Добавляем лишнюю позицию и сразу удаляем
        extra_pizza = CATALOG["Маргарита"]
        order_service.add_item(order, extra_pizza, PizzaSize.MEDIUM, 1)
        order_service.remove_item(order, len(order.items) - 1)

        assert len(order.items) == count_before_extra

    @given(qty=st.integers(max_value=0))
    def test_non_positive_quantity_rejected(self, qty):
        """СВОЙСТВО: любое количество <= 0 отклоняется."""
        order_service = OrderService(PricingService())
        order = Order(customer=Customer(name="X", phone="+7"))

        with pytest.raises(ValueError):
            order_service.add_item(order, CATALOG["Маргарита"], PizzaSize.MEDIUM, qty)


# ═══════════════════════════════════════════════════════════════
#  Знаменитый пример: assume() — отсечение неинтересных случаев
# ═══════════════════════════════════════════════════════════════


class TestWithAssumptions:
    """Использование assume() для фильтрации генерируемых данных."""

    @given(order=orders(is_loyal=False, with_promo=False))
    def test_free_delivery_when_above_threshold(self, order):
        """
        СВОЙСТВО: доставка бесплатна, если subtotal >= 1500.
        Отфильтровываем случаи, когда сумма меньше — они не интересны для теста.
        """
        assume(order.subtotal >= PricingService.FREE_DELIVERY_THRESHOLD)

        pricing = PricingService()
        total = pricing.calculate_total(
            order, now=datetime(2025, 5, 14, 12, 0)
        )

        # Не loyal, не промокод, не happy hour → скидок нет
        # subtotal >= 1500 → доставка бесплатна
        assert total == order.subtotal
