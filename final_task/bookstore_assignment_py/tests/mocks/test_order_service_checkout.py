from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from bookstore.exceptions import (
    InvalidOrderStateError,
    InventoryError,
    PaymentDeclinedError,
    PaymentError,
)
from bookstore.interfaces.payment_gateway import PaymentResult, PaymentStatus
from bookstore.models.order import OrderStatus
from bookstore.order_service import OrderService

from tests.conftest import (
    FakeBookRepository,
    FixedClock,
    RecordingInventory,
    RecordingNotifications,
    RecordingPaymentGateway,
    make_item,
    make_order,
)


def make_service(
    inventory: RecordingInventory,
    payment: RecordingPaymentGateway | None = None,
    notifications: RecordingNotifications | None = None,
) -> OrderService:
    return OrderService(
        book_repository=FakeBookRepository({}),
        inventory=inventory,
        payment_gateway=payment or RecordingPaymentGateway(),
        notifications=notifications or RecordingNotifications(),
        clock=FixedClock(datetime(2025, 10, 1)),
    )


def test_checkout_reserves_items_charges_customer_marks_paid_and_sends_confirmation(address) -> None:
    first = make_item(isbn="9780000000001", price="1000", quantity=2)
    second = make_item(isbn="9780000000002", price="500", quantity=1)
    order = make_order(first, second)
    inventory = RecordingInventory({first.book.isbn: 2, second.book.isbn: 1})
    payment = RecordingPaymentGateway()
    notifications = RecordingNotifications()
    service = make_service(inventory, payment, notifications)

    result = service.checkout(order, address)

    assert result.order is order
    assert order.status == OrderStatus.PAID
    assert order.shipping_address == address
    assert order.payment_transaction_id == "TX-1"
    assert result.payment_transaction_id == "TX-1"
    assert result.reservation_ids == [
        "reservation-9780000000001",
        "reservation-9780000000002",
    ]
    assert inventory.reserved == [
        (first.book.isbn, 2, "reservation-9780000000001"),
        (second.book.isbn, 1, "reservation-9780000000002"),
    ]
    assert inventory.released == []
    assert payment.charges == [
            {
                "customer_id": order.customer.customer_id,
                "amount": Decimal("3055.00"),
                "currency": "RUB",
                "idempotency_key": f"order-{order.order_id}",
            }
    ]
    assert notifications.confirmations == [order]


def test_checkout_fails_before_reservation_when_stock_is_insufficient(address) -> None:
    item = make_item(quantity=3)
    order = make_order(item)
    inventory = RecordingInventory({item.book.isbn: 2})
    payment = RecordingPaymentGateway()

    with pytest.raises(InventoryError, match="Недостаточно товара"):
        make_service(inventory, payment).checkout(order, address)

    assert order.status == OrderStatus.DRAFT
    assert inventory.reserved == []
    assert inventory.released == []
    assert payment.charges == []


def test_checkout_releases_previous_reservations_when_later_reservation_fails(address) -> None:
    first = make_item(isbn="9780000000001")
    second = make_item(isbn="9780000000002")
    order = make_order(first, second)
    inventory = RecordingInventory(
        {first.book.isbn: 1, second.book.isbn: 1},
        fail_on_reserve_isbn=second.book.isbn,
    )
    payment = RecordingPaymentGateway()

    with pytest.raises(InventoryError, match="Cannot reserve"):
        make_service(inventory, payment).checkout(order, address)

    assert order.status == OrderStatus.DRAFT
    assert inventory.reserved == [(first.book.isbn, 1, "reservation-9780000000001")]
    assert inventory.released == ["reservation-9780000000001"]
    assert payment.charges == []


def test_checkout_releases_reservations_and_cancels_order_when_payment_is_declined(address) -> None:
    item = make_item()
    order = make_order(item)
    inventory = RecordingInventory({item.book.isbn: 1})
    payment = RecordingPaymentGateway(
        PaymentResult(
            status=PaymentStatus.DECLINED,
            decline_reason="card rejected",
        )
    )

    with pytest.raises(PaymentDeclinedError, match="card rejected"):
        make_service(inventory, payment).checkout(order, address)

    assert order.status == OrderStatus.CANCELLED
    assert inventory.released
    assert payment.charges[0]["amount"] == Decimal("1400.00")


def test_checkout_releases_reservations_and_cancels_order_when_gateway_raises_error(address) -> None:
    item = make_item()
    order = make_order(item)
    inventory = RecordingInventory({item.book.isbn: 1})
    payment = RecordingPaymentGateway(error=PaymentError("gateway unavailable"))

    with pytest.raises(PaymentError, match="gateway unavailable"):
        make_service(inventory, payment).checkout(order, address)

    assert order.status == OrderStatus.CANCELLED
    assert inventory.released == ["reservation-9780000000001"]


def test_notification_failure_does_not_cancel_paid_order(address) -> None:
    item = make_item()
    order = make_order(item)
    inventory = RecordingInventory({item.book.isbn: 1})
    notifications = RecordingNotifications(error=RuntimeError("smtp unavailable"))

    result = make_service(inventory, notifications=notifications).checkout(order, address)

    assert result.order.status == OrderStatus.PAID
    assert order.payment_transaction_id == "TX-1"
    assert notifications.confirmations == [order]


def test_checkout_rejects_non_draft_order(address) -> None:
    item = make_item()
    order = make_order(item)
    order.status = OrderStatus.PAID
    inventory = RecordingInventory({item.book.isbn: 1})
    payment = RecordingPaymentGateway()

    with pytest.raises(InvalidOrderStateError, match="Заказ уже"):
        make_service(inventory, payment).checkout(order, address)

    assert inventory.reserved == []
    assert payment.charges == []
