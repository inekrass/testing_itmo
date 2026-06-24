from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import pytest

from bookstore.interfaces.payment_gateway import PaymentResult, PaymentStatus
from bookstore.models.address import Address
from bookstore.models.book import Book, BookCategory
from bookstore.models.cart_item import CartItem
from bookstore.models.customer import Customer, CustomerTier
from bookstore.models.order import Order


def make_book(
    isbn: str = "9780000000001",
    price: str = "1000",
    category: BookCategory = BookCategory.FICTION,
    weight_grams: int = 500,
) -> Book:
    return Book(
        isbn=isbn,
        title=f"Book {isbn}",
        author="Author",
        category=category,
        base_price=Decimal(price),
        weight_grams=weight_grams,
        publication_year=2025,
    )


def make_customer(
    customer_id: str = "customer-1",
    tier: CustomerTier = CustomerTier.BRONZE,
    is_blocked: bool = False,
) -> Customer:
    return Customer(
        customer_id=customer_id,
        name="Test Customer",
        email="customer@example.test",
        tier=tier,
        is_blocked=is_blocked,
    )


def make_order(
    *items: CartItem,
    tier: CustomerTier = CustomerTier.BRONZE,
    promo_code: str | None = None,
    is_blocked: bool = False,
) -> Order:
    return Order(
        order_id="order-1",
        customer=make_customer(tier=tier, is_blocked=is_blocked),
        items=list(items),
        promo_code=promo_code,
    )


def make_item(
    isbn: str = "9780000000001",
    price: str = "1000",
    quantity: int = 1,
    category: BookCategory = BookCategory.FICTION,
    weight_grams: int = 500,
) -> CartItem:
    return CartItem(
        book=make_book(
            isbn=isbn,
            price=price,
            category=category,
            weight_grams=weight_grams,
        ),
        quantity=quantity,
    )


@pytest.fixture
def address() -> Address:
    return Address(country="RU", city="Moscow", postal_code="101000", street="Main 1")


class FixedClock:
    def __init__(self, moment: datetime):
        self._moment = moment

    def now(self) -> datetime:
        return self._moment


@dataclass
class FakeBookRepository:
    books: dict[str, Book]

    def get_by_isbn(self, isbn: str) -> Book:
        from bookstore.exceptions import BookNotFoundError

        try:
            return self.books[isbn]
        except KeyError as exc:
            raise BookNotFoundError(f"Book {isbn} not found") from exc

    def search(self, query: str, limit: int = 20) -> list[Book]:
        return list(self.books.values())[:limit]


class RecordingInventory:
    def __init__(
        self,
        stock: dict[str, int],
        fail_on_reserve_isbn: str | None = None,
    ):
        self.stock = stock
        self.fail_on_reserve_isbn = fail_on_reserve_isbn
        self.reserved: list[tuple[str, int, str]] = []
        self.released: list[str] = []

    def get_stock(self, isbn: str) -> int:
        return self.stock.get(isbn, 0)

    def reserve(self, isbn: str, quantity: int) -> str:
        from bookstore.exceptions import InventoryError

        if isbn == self.fail_on_reserve_isbn:
            raise InventoryError(f"Cannot reserve {isbn}")
        reservation_id = f"reservation-{isbn}"
        self.reserved.append((isbn, quantity, reservation_id))
        return reservation_id

    def release(self, reservation_id: str) -> None:
        self.released.append(reservation_id)


class RecordingPaymentGateway:
    def __init__(
        self,
        result: PaymentResult | None = None,
        error: Exception | None = None,
    ):
        self.result = result or PaymentResult(
            status=PaymentStatus.SUCCESS,
            transaction_id="TX-1",
        )
        self.error = error
        self.charges: list[dict[str, object]] = []
        self.refunds: list[dict[str, object]] = []

    def charge(
        self,
        customer_id: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> PaymentResult:
        self.charges.append(
            {
                "customer_id": customer_id,
                "amount": amount,
                "currency": currency,
                "idempotency_key": idempotency_key,
            }
        )
        if self.error is not None:
            raise self.error
        return self.result

    def refund(self, transaction_id: str, amount: Decimal) -> PaymentResult:
        self.refunds.append({"transaction_id": transaction_id, "amount": amount})
        return PaymentResult(status=PaymentStatus.SUCCESS, transaction_id=transaction_id)


class RecordingNotifications:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.confirmations: list[Order] = []

    def send_order_confirmation(self, customer: Customer, order: Order) -> None:
        self.confirmations.append(order)
        if self.error is not None:
            raise self.error

    def send_shipping_notification(
        self,
        customer: Customer,
        order: Order,
        tracking_number: str,
    ) -> None:
        return None
