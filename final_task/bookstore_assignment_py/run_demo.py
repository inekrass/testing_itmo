"""
Демонстрационный запуск приложения с простыми реализациями зависимостей
в памяти. Позволяет открыть /docs и пройти весь сценарий заказа, не подключая
реальные склад, платёжный шлюз и сервис уведомлений.

Запуск из каталога проекта:
    uvicorn run_demo:app --reload

Затем откройте http://127.0.0.1:8000/docs

Этот файл — вспомогательный. Код в src/bookstore он не меняет.
"""
from __future__ import annotations

import itertools
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Добавляем src в путь, чтобы пакет bookstore импортировался при запуске из корня.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from fastapi.responses import RedirectResponse

from bookstore.api import (
    app,
    get_book_repository,
    get_clock,
    get_customers_storage,
    get_inventory,
    get_notifications,
    get_orders_storage,
    get_payment_gateway,
)
from bookstore.exceptions import BookNotFoundError, InventoryError
from bookstore.interfaces import PaymentResult, PaymentStatus
from bookstore.models import Book, BookCategory, Customer, CustomerTier, Order


# --- Каталог книг в памяти (по одной книге каждой категории) ---
CATALOG: dict[str, Book] = {
    "978-5-0010-0001-1": Book(
        "978-5-0010-0001-1", "Чистый код", "Роберт Мартин",
        BookCategory.NON_FICTION, Decimal("1500"), 600, 2019,
    ),
    "978-5-0010-0002-2": Book(
        "978-5-0010-0002-2", "Высшая математика", "А. Иванов",
        BookCategory.TEXTBOOK, Decimal("900"), 800, 2021,
    ),
    "978-5-0010-0003-3": Book(
        "978-5-0010-0003-3", "Сказки на ночь", "М. Петрова",
        BookCategory.CHILDREN, Decimal("500"), 300, 2020,
    ),
    "978-5-0010-0004-4": Book(
        "978-5-0010-0004-4", "Первое издание", "Редкий Автор",
        BookCategory.RARE, Decimal("12000"), 1200, 1965,
    ),
    "978-5-0010-0005-5": Book(
        "978-5-0010-0005-5", "Война и мир", "Л. Толстой",
        BookCategory.FICTION, Decimal("800"), 1400, 2018,
    ),
}


class InMemoryBookRepository:
    """Каталог книг в памяти."""

    def get_by_isbn(self, isbn: str) -> Book:
        try:
            return CATALOG[isbn]
        except KeyError:
            raise BookNotFoundError(f"Книга {isbn} не найдена")

    def search(self, query: str, limit: int = 20) -> list[Book]:
        q = query.lower()
        found = [
            b for b in CATALOG.values()
            if q in b.title.lower() or q in b.author.lower()
        ]
        return found[:limit]


class InMemoryInventory:
    """Склад в памяти. У каждой книги по 100 экземпляров."""

    def __init__(self) -> None:
        self._stock = {isbn: 100 for isbn in CATALOG}
        self._reservations: dict[str, tuple[str, int]] = {}
        self._counter = itertools.count(1)

    def get_stock(self, isbn: str) -> int:
        return self._stock.get(isbn, 0)

    def reserve(self, isbn: str, quantity: int) -> str:
        if self._stock.get(isbn, 0) < quantity:
            raise InventoryError(f"Недостаточно товара {isbn}")
        self._stock[isbn] -= quantity
        reservation_id = f"RES-{next(self._counter)}"
        self._reservations[reservation_id] = (isbn, quantity)
        return reservation_id

    def release(self, reservation_id: str) -> None:
        item = self._reservations.pop(reservation_id, None)
        if item is not None:
            isbn, quantity = item
            self._stock[isbn] += quantity


class FakePaymentGateway:
    """Платёжный шлюз, который всегда подтверждает оплату."""

    def __init__(self) -> None:
        self._counter = itertools.count(1)

    def charge(self, customer_id, amount, currency, idempotency_key) -> PaymentResult:
        return PaymentResult(
            status=PaymentStatus.SUCCESS,
            transaction_id=f"TX-{next(self._counter)}",
        )

    def refund(self, transaction_id, amount) -> PaymentResult:
        return PaymentResult(
            status=PaymentStatus.SUCCESS,
            transaction_id=f"RF-{next(self._counter)}",
        )


class ConsoleNotifications:
    """Уведомления, которые печатаются в консоль."""

    def send_order_confirmation(self, customer: Customer, order: Order) -> None:
        print(f"[notify] Заказ {order.order_id} подтверждён для {customer.email}")

    def send_shipping_notification(self, customer, order, tracking_number) -> None:
        print(f"[notify] Заказ {order.order_id} отправлен, трек {tracking_number}")


class SystemClock:
    """Системные часы."""

    def now(self) -> datetime:
        return datetime.now()


# --- Хранилища и начальные данные (живут на всё время работы сервера) ---
orders_db: dict[str, Order] = {}
customers_db: dict[str, Customer] = {
    "demo": Customer(
        customer_id="demo",
        name="Демо Покупатель",
        email="demo@example.com",
        tier=CustomerTier.SILVER,
    ),
}

_books = InMemoryBookRepository()
_inventory = InMemoryInventory()
_payment = FakePaymentGateway()
_notifications = ConsoleNotifications()
_clock = SystemClock()

# Подключаем реализации зависимостей.
app.dependency_overrides[get_book_repository] = lambda: _books
app.dependency_overrides[get_inventory] = lambda: _inventory
app.dependency_overrides[get_payment_gateway] = lambda: _payment
app.dependency_overrides[get_notifications] = lambda: _notifications
app.dependency_overrides[get_clock] = lambda: _clock
app.dependency_overrides[get_customers_storage] = lambda: customers_db
app.dependency_overrides[get_orders_storage] = lambda: orders_db


@app.get("/", include_in_schema=False)
def root():
    """Перенаправление с корня на документацию."""
    return RedirectResponse(url="/docs")


print("Демо-режим. Покупатель: demo. Примеры ISBN: " + ", ".join(CATALOG))
