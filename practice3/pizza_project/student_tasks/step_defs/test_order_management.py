"""
СТАРТОВЫЙ ФАЙЛ — Пара 5, упражнение по BDD.

Задача:
    Дописать step definitions для сценариев из
    student_tasks/features/order_management.feature

Эталон: tests/bdd/step_defs/test_order_creation.py

Как запустить:
    python -m pytest student_tasks/step_defs/test_order_management.py -v
"""

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from pizza_service.domain import (
    CATALOG,
    Customer,
    Order,
    OrderService,
    OrderStatus,
    Pizza,
    PizzaSize,
    PricingService,
)

scenarios(str(Path(__file__).resolve().parents[1] / "features" / "order_management.feature"))


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
#  Готовый шаг — пример для подражания
# ═══════════════════════════════════════════════════════════════


@given(parsers.parse(
    'Клиент создал заказ с пиццей "{pizza_name}" размера "{size}"'
))
def customer_created_order_with(context, order_service, pizza_name, size):
    customer = Customer(name="Тест", phone="+7")
    order = Order(customer=customer)
    pizza = CATALOG[pizza_name]
    order_service.add_item(order, pizza, PizzaSize(size), 1)
    context["order"] = order


@given(parsers.parse(
    'Клиент добавил пиццу "{pizza_name}" размера "{size}"'
))
def customer_added_pizza(context, order_service, pizza_name, size):
    pizza = CATALOG[pizza_name]
    order_service.add_item(context["order"], pizza, PizzaSize(size), 1)


@given(parsers.parse(
    "Клиент оформил и подтвердил заказ на сумму {amount:d} руб."
))
def customer_confirmed_order_for_amount(context, order_service, amount):
    customer = Customer(name="Тест", phone="+7")
    order = Order(customer=customer)
    pizza = Pizza("Тестовая пицца", Decimal(amount))
    order_service.add_item(order, pizza, PizzaSize.MEDIUM, 1)
    order_service.confirm(order, now=datetime(2026, 6, 22, 12, 0))
    context["order"] = order


@when(parsers.parse("Клиент удаляет позицию с индексом {index:d}"))
def customer_removes_item(context, order_service, index):
    order_service.remove_item(context["order"], index)


@when("Клиент отменяет заказ")
def customer_cancels_order(context, order_service):
    order_service.cancel(context["order"])


@when(parsers.parse(
    'Клиент пытается добавить пиццу "{pizza_name}" размера "{size}"'
))
def customer_tries_to_add_pizza(context, order_service, pizza_name, size):
    context["exception"] = None
    try:
        pizza = CATALOG[pizza_name]
        order_service.add_item(context["order"], pizza, PizzaSize(size), 1)
    except Exception as e:
        context["exception"] = e


@then(parsers.parse("В заказе остаётся {n:d} позиция"))
@then(parsers.parse("В заказе остаётся {n:d} позиции"))
def assert_items_count(context, n):
    assert len(context["order"].items) == n


@then(parsers.parse('Оставшаяся позиция — "{name}"'))
def assert_remaining_item(context, name):
    assert context["order"].items[0].pizza.name == name


@then(parsers.parse('Заказ переходит в статус "{status}"'))
def assert_status(context, status):
    assert context["order"].status == OrderStatus(status)


@then(parsers.parse('Система отклоняет операцию с сообщением "{msg}"'))
def assert_rejected_with_message(context, msg):
    assert context["exception"] is not None, "Ожидалось исключение, но его нет"
    assert msg in str(context["exception"])
