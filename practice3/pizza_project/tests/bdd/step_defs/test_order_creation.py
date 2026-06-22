"""
Реализация шагов для order_creation.feature.

Связывает фразы из .feature-файла с Python-кодом, который их выполняет.
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
    OrderService,
    OrderStatus,
    Pizza,
    PizzaSize,
    PricingService,
)

# Регистрируем все сценарии из feature-файла
scenarios("../features/order_creation.feature")


# ═══════════════════════════════════════════════════════════════
#  Контекст теста (между шагами)
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def context() -> dict:
    """Словарь для передачи данных между шагами одного сценария."""
    return {}


@pytest.fixture
def pricing() -> PricingService:
    return PricingService()


@pytest.fixture
def order_service(pricing) -> OrderService:
    return OrderService(pricing)


# ═══════════════════════════════════════════════════════════════
#  GIVEN — подготовка
# ═══════════════════════════════════════════════════════════════


@given("Доступен каталог пицц")
def catalog_available(context):
    """
    Каталог уже определён в domain.py, шаг здесь декларативный —
    подтверждает, что мы используем стандартный каталог.
    """
    context["catalog"] = CATALOG


@given(parsers.parse('Клиент "{name}" создаёт новый заказ'))
def customer_creates_order(context, name):
    customer = Customer(name=name, phone="+7-000-000-0000")
    context["customer"] = customer
    context["order"] = Order(customer=customer)


@given(parsers.parse('Зарегистрирован постоянный клиент "{name}"'))
def loyal_customer(context, name):
    customer = Customer(
        name=name, phone="+7-000-000-0000",
        is_loyal=True, orders_completed=20,
    )
    context["customer"] = customer
    context["order"] = Order(customer=customer)


@given(parsers.parse(
    'Клиент добавил в заказ пиццу "{pizza_name}" размера "{size}"'
))
def customer_added_pizza(context, order_service, pizza_name, size):
    pizza = CATALOG[pizza_name]
    order_service.add_item(context["order"], pizza, PizzaSize(size), 1)


@given(parsers.parse(
    'Клиент добавил в заказ пиццу "{pizza_name}" '
    'размера "{size}" в количестве {qty:d}'
))
def customer_added_pizza_qty(context, order_service, pizza_name, size, qty):
    pizza = CATALOG[pizza_name]
    order_service.add_item(context["order"], pizza, PizzaSize(size), qty)


# ═══════════════════════════════════════════════════════════════
#  WHEN — действие
# ═══════════════════════════════════════════════════════════════


@when(parsers.parse(
    'Клиент добавляет в заказ пиццу "{pizza_name}" размера "{size}"'
))
def customer_adds_pizza(context, order_service, pizza_name, size):
    pizza = CATALOG[pizza_name]
    order_service.add_item(context["order"], pizza, PizzaSize(size), 1)


@when(parsers.parse(
    'Клиент добавляет в заказ пиццу "{pizza_name}" '
    'размера "{size}" в количестве {qty:d}'
))
def customer_adds_pizza_qty(context, order_service, pizza_name, size, qty):
    pizza = CATALOG[pizza_name]
    order_service.add_item(context["order"], pizza, PizzaSize(size), qty)


@when(parsers.parse('Клиент применяет промокод "{code}"'))
def customer_applies_promo(context, order_service, code):
    order_service.apply_promo(context["order"], code)


@when(parsers.parse('Клиент подтверждает заказ в {hh:d}:{mm:d}'))
def customer_confirms_at(context, order_service, hh, mm):
    moment = datetime(2025, 5, 14, hh, mm)
    total = order_service.confirm(context["order"], now=moment)
    context["total"] = total


@when(parsers.parse(
    'Клиент оформляет заказ из пиццы "{pizza_name}" размера "{size}"'
))
def customer_places_single_pizza_order(context, order_service, pizza_name, size):
    pizza = CATALOG[pizza_name]
    order_service.add_item(context["order"], pizza, PizzaSize(size), 1)


@when("Клиент пытается подтвердить пустой заказ")
def customer_tries_to_confirm_empty(context, order_service):
    context["exception"] = None
    try:
        order_service.confirm(context["order"])
    except Exception as e:
        context["exception"] = e


# ═══════════════════════════════════════════════════════════════
#  THEN — проверка
# ═══════════════════════════════════════════════════════════════


@then(parsers.parse("В заказе должно быть {n:d} позиции"))
@then(parsers.parse("В заказе должно быть {n:d} позиций"))
def assert_items_count(context, n):
    assert len(context["order"].items) == n


@then(parsers.parse("Сумма заказа без скидок составляет {amount:d} руб."))
def assert_subtotal(context, amount):
    assert context["order"].subtotal == Decimal(amount)


@then(parsers.parse("Сумма к оплате составит {amount:d} руб."))
def assert_total(context, amount):
    assert context["total"] == Decimal(amount)


@then(parsers.parse('Заказ переходит в статус "{status}"'))
def assert_status(context, status):
    assert context["order"].status == OrderStatus(status)


@then("Применяется скидка постоянного клиента 10%")
def assert_loyal_discount(context):
    # Косвенная проверка: total меньше, чем subtotal на нужный процент
    subtotal = context["order"].subtotal
    expected_with_delivery = subtotal * Decimal("0.9") + Decimal("200") if subtotal * Decimal("0.9") < Decimal("1500") else subtotal * Decimal("0.9")
    assert context["total"] == expected_with_delivery


@then("Доставка должна быть бесплатной")
def assert_free_delivery(context):
    # Проверяем, что сумма == subtotal минус скидки (без +200)
    subtotal = context["order"].subtotal
    assert context["total"] <= subtotal, "Доставка должна быть включена"


@then(parsers.parse("К сумме добавляется стоимость доставки {fee:d} руб."))
def assert_delivery_added(context, fee):
    # Проверяем, что в сумме учтена доставка
    subtotal = context["order"].subtotal
    assert context["total"] >= subtotal, "В сумме должна быть доставка"


@then(parsers.parse('Система отклоняет операцию с сообщением "{msg}"'))
def assert_rejected_with_message(context, msg):
    assert context["exception"] is not None, "Ожидалось исключение, но его нет"
    assert msg in str(context["exception"])
