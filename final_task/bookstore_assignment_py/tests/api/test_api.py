from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from bookstore import api
from bookstore.exceptions import PaymentError
from bookstore.interfaces.payment_gateway import PaymentResult, PaymentStatus
from bookstore.models.order import OrderStatus
from bookstore.order_service import OrderService

from tests.conftest import (
    FakeBookRepository,
    FixedClock,
    RecordingInventory,
    RecordingNotifications,
    RecordingPaymentGateway,
    make_book,
    make_customer,
    make_item,
    make_order,
)


def build_service(
    books: FakeBookRepository | None = None,
    inventory: RecordingInventory | None = None,
    payment: RecordingPaymentGateway | None = None,
) -> OrderService:
    return OrderService(
        book_repository=books or FakeBookRepository({}),
        inventory=inventory or RecordingInventory({}),
        payment_gateway=payment or RecordingPaymentGateway(),
        notifications=RecordingNotifications(),
        clock=FixedClock(datetime(2025, 10, 1)),
    )


@pytest.fixture
def api_context():
    orders = {}
    customers = {}
    service = build_service()

    def install(*, order_service: OrderService | None = None):
        api.app.dependency_overrides[api.get_order_service] = lambda: order_service or service
        api.app.dependency_overrides[api.get_orders_storage] = lambda: orders
        api.app.dependency_overrides[api.get_customers_storage] = lambda: customers
        return TestClient(api.app)

    yield orders, customers, install
    api.app.dependency_overrides.clear()


def test_create_order_returns_201_and_order_schema(api_context) -> None:
    orders, customers, install = api_context
    customers["customer-1"] = make_customer()
    client = install()

    response = client.post("/orders", json={"customer_id": "customer-1"})

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {
        "order_id",
        "status",
        "customer_id",
        "items_count",
        "subtotal",
        "promo_code",
    }
    assert body["status"] == "DRAFT"
    assert body["customer_id"] == "customer-1"
    assert body["items_count"] == 0
    assert body["subtotal"] == "0"
    assert body["order_id"] in orders


def test_create_order_for_blocked_customer_returns_403(api_context) -> None:
    _, customers, install = api_context
    customers["customer-1"] = make_customer(is_blocked=True)
    client = install()

    response = client.post("/orders", json={"customer_id": "customer-1"})

    assert response.status_code == 403
    assert "Покупатель заблокирован" in response.json()["detail"]


def test_get_missing_order_returns_404(api_context) -> None:
    client = api_context[2]()

    response = client.get("/orders/missing")

    assert response.status_code == 404
    assert "Заказ missing не найден" in response.json()["detail"]


def test_invalid_create_order_body_returns_422(api_context) -> None:
    client = api_context[2]()

    response = client.post("/orders", json={})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "customer_id"]


def test_add_item_returns_404_when_book_is_missing(api_context) -> None:
    orders, _, install = api_context
    orders["order-1"] = make_order()
    client = install(order_service=build_service(books=FakeBookRepository({})))

    response = client.post(
        "/orders/order-1/items",
        json={"isbn": "9780000000001", "quantity": 1},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_add_item_to_paid_order_returns_409(api_context) -> None:
    book = make_book()
    orders, _, install = api_context
    order = make_order()
    order.status = OrderStatus.PAID
    orders["order-1"] = order
    service = build_service(books=FakeBookRepository({book.isbn: book}))
    client = install(order_service=service)

    response = client.post(
        "/orders/order-1/items",
        json={"isbn": book.isbn, "quantity": 1},
    )

    assert response.status_code == 409
    assert "Нельзя изменить заказ" in response.json()["detail"]


def test_invalid_add_item_body_returns_422(api_context) -> None:
    orders, _, install = api_context
    orders["order-1"] = make_order()
    client = install()

    response = client.post(
        "/orders/order-1/items",
        json={"isbn": "short", "quantity": 0},
    )

    assert response.status_code == 422
    fields = {tuple(error["loc"]) for error in response.json()["detail"]}
    assert ("body", "isbn") in fields
    assert ("body", "quantity") in fields


def test_checkout_empty_order_returns_422(api_context) -> None:
    orders, _, install = api_context
    orders["order-1"] = make_order()
    client = install()

    response = client.post(
        "/orders/order-1/checkout",
        json={
            "shipping_address": {
                "country": "RU",
                "city": "Moscow",
                "postal_code": "101000",
                "street": "Main 1",
            }
        },
    )

    assert response.status_code == 422
    assert "Заказ не может быть пустым" in response.json()["detail"]


def test_checkout_insufficient_stock_returns_409(api_context) -> None:
    item = make_item(quantity=2)
    orders, _, install = api_context
    orders["order-1"] = make_order(item)
    service = build_service(inventory=RecordingInventory({item.book.isbn: 1}))
    client = install(order_service=service)

    response = client.post(
        "/orders/order-1/checkout",
        json={
            "shipping_address": {
                "country": "RU",
                "city": "Moscow",
                "postal_code": "101000",
                "street": "Main 1",
            }
        },
    )

    assert response.status_code == 409
    assert "Недостаточно товара" in response.json()["detail"]


def test_checkout_declined_payment_returns_402(api_context) -> None:
    item = make_item()
    orders, _, install = api_context
    orders["order-1"] = make_order(item)
    service = build_service(
        inventory=RecordingInventory({item.book.isbn: 1}),
        payment=RecordingPaymentGateway(
            PaymentResult(
                status=PaymentStatus.DECLINED,
                decline_reason="declined",
            )
        ),
    )
    client = install(order_service=service)

    response = client.post(
        "/orders/order-1/checkout",
        json={
            "shipping_address": {
                "country": "RU",
                "city": "Moscow",
                "postal_code": "101000",
                "street": "Main 1",
            }
        },
    )

    assert response.status_code == 402
    assert "declined" in response.json()["detail"]


def test_checkout_gateway_error_returns_502(api_context) -> None:
    item = make_item()
    orders, _, install = api_context
    orders["order-1"] = make_order(item)
    service = build_service(
        inventory=RecordingInventory({item.book.isbn: 1}),
        payment=RecordingPaymentGateway(error=PaymentError("gateway down")),
    )
    client = install(order_service=service)

    response = client.post(
        "/orders/order-1/checkout",
        json={
            "shipping_address": {
                "country": "RU",
                "city": "Moscow",
                "postal_code": "101000",
                "street": "Main 1",
            }
        },
    )

    assert response.status_code == 502
    assert "gateway down" in response.json()["detail"]


def test_successful_checkout_response_matches_schema(api_context) -> None:
    item = make_item()
    orders, _, install = api_context
    orders["order-1"] = make_order(item)
    service = build_service(inventory=RecordingInventory({item.book.isbn: 1}))
    client = install(order_service=service)

    response = client.post(
        "/orders/order-1/checkout",
        json={
            "shipping_address": {
                "country": "RU",
                "city": "Moscow",
                "postal_code": "101000",
                "street": "Main 1",
            }
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "order_id": "order-1",
        "status": "PAID",
        "total": "1400.00",
        "transaction_id": "TX-1",
    }
