"""
Реализация шагов для discounts.feature.
Демонстрирует Scenario Outline (структуру сценария с таблицей примеров).
"""

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from pizza_service.domain import (
    CATALOG,
    Customer,
    Order,
    OrderItem,
    OrderService,
    PizzaSize,
    PricingService,
)

scenarios("../features/discounts.feature")


@pytest.fixture
def context() -> dict:
    return {}


@pytest.fixture
def pricing() -> PricingService:
    return PricingService()


@pytest.fixture
def order_service(pricing) -> OrderService:
    return OrderService(pricing)


# ═══════════════════════════════════════════════════════════════
#  Шаги для Scenario Outline
# ═══════════════════════════════════════════════════════════════


@given(parsers.parse(
    'Клиент с признаком "{loyalty}" оформил заказ на {amount:d} руб.'
))
def customer_with_loyalty(context, loyalty, amount):
    is_loyal = (loyalty.lower() == "да")
    customer = Customer(name="Тестовый клиент", phone="+7", is_loyal=is_loyal)
    order = Order(customer=customer)

    # Подгоняем сумму через искусственную пиццу
    # (создаём пиццу с нужной базовой ценой)
    from pizza_service.domain import Pizza
    custom_pizza = Pizza("Test Pizza", Decimal(amount))
    order.items.append(OrderItem(custom_pizza, PizzaSize.MEDIUM, 1))

    context["order"] = order
    context["subtotal"] = Decimal(amount)


@given(parsers.parse('Применил промокод "{code}"'))
def with_promo_code(context, code):
    if code.lower() != "нет":
        context["order"].promo_code = code


@given(parsers.parse('Заказ оформлен в "{hh:d}:{mm:d}"'))
def order_placed_at(context, hh, mm):
    context["moment"] = datetime(2025, 5, 14, hh, mm)


@when("Рассчитывается итоговая сумма")
def calculate_total(context, pricing):
    total = pricing.calculate_total(context["order"], now=context["moment"])
    context["total"] = total


@then(parsers.parse("Применённая скидка составляет {percent:d}%"))
def assert_discount_applied(context, percent):
    subtotal = context["subtotal"]
    expected_discount = subtotal * Decimal(percent) / Decimal(100)
    after_discount = subtotal - expected_discount

    # Доставка применима только если after_discount < 1500
    if after_discount >= Decimal("1500"):
        expected_total = after_discount
    else:
        expected_total = after_discount + Decimal("200")

    assert context["total"] == expected_total, (
        f"Ожидали total={expected_total} (скидка {percent}%), "
        f"получили {context['total']}"
    )


# ═══════════════════════════════════════════════════════════════
#  Шаги для обычного сценария
# ═══════════════════════════════════════════════════════════════


@given(parsers.parse('Клиент "{name}" создаёт новый заказ'))
def customer_creates_new_order(context, name):
    customer = Customer(name=name, phone="+7-000-000-0000")
    context["order"] = Order(customer=customer)


@given(parsers.parse(
    'Клиент добавил в заказ пиццу "{pizza_name}" размера "{size}"'
))
def customer_added_pizza_discounts(context, order_service, pizza_name, size):
    pizza = CATALOG[pizza_name]
    order_service.add_item(context["order"], pizza, PizzaSize(size), 1)


@when(parsers.parse('Клиент пытается применить промокод "{code}"'))
def customer_tries_promo(context, order_service, code):
    context["exception"] = None
    try:
        order_service.apply_promo(context["order"], code)
    except Exception as e:
        context["exception"] = e


@then(parsers.parse('Система отклоняет операцию с сообщением "{msg}"'))
def assert_rejected_discounts(context, msg):
    assert context["exception"] is not None
    assert msg in str(context["exception"])
