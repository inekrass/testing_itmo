from __future__ import annotations

from decimal import Decimal
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from bookstore.exceptions import (
    BookNotFoundError,
    InvalidOrderStateError,
    InventoryError,
    OrderError,
    PaymentDeclinedError,
    PaymentError,
    PricingError,
)
from bookstore.interfaces.book_repository import BookRepository
from bookstore.interfaces.clock import Clock
from bookstore.interfaces.inventory_service import InventoryService
from bookstore.interfaces.notification_service import NotificationService
from bookstore.interfaces.payment_gateway import PaymentGateway
from bookstore.models.address import Address
from bookstore.models.customer import Customer
from bookstore.models.order import Order
from bookstore.order_service import CheckoutResult, OrderService

app = FastAPI(title="Bookstore API")


# Провайдеры зависимостей. Конкретные реализации подключаются при сборке
# приложения. Здесь оставлены точки расширения.

def get_book_repository() -> BookRepository:
    """Репозиторий книг."""
    raise NotImplementedError("Реализация BookRepository не подключена")


def get_inventory() -> InventoryService:
    """Сервис остатков на складе."""
    raise NotImplementedError("Реализация InventoryService не подключена")


def get_payment_gateway() -> PaymentGateway:
    """Платёжный шлюз."""
    raise NotImplementedError("Реализация PaymentGateway не подключена")


def get_notifications() -> NotificationService:
    """Сервис уведомлений."""
    raise NotImplementedError("Реализация NotificationService не подключена")


def get_clock() -> Clock:
    """Источник текущего времени."""
    raise NotImplementedError("Реализация Clock не подключена")


def get_order_service(
    books: BookRepository = Depends(get_book_repository),
    inventory: InventoryService = Depends(get_inventory),
    payment: PaymentGateway = Depends(get_payment_gateway),
    notifications: NotificationService = Depends(get_notifications),
    clock: Clock = Depends(get_clock),
) -> OrderService:
    """Собрать сервис заказов из подключённых зависимостей."""
    return OrderService(
        book_repository=books,
        inventory=inventory,
        payment_gateway=payment,
        notifications=notifications,
        clock=clock,
    )


# Хранилища заказов и покупателей. В реальной системе — база данных.
_ORDERS: dict[str, Order] = {}
_CUSTOMERS: dict[str, Customer] = {}


def get_orders_storage() -> dict[str, Order]:
    """Хранилище заказов."""
    return _ORDERS


def get_customers_storage() -> dict[str, Customer]:
    """Хранилище покупателей."""
    return _CUSTOMERS


# Схемы запросов и ответов.

class CreateOrderRequest(BaseModel):
    """Тело запроса на создание заказа."""

    customer_id: str


class AddItemRequest(BaseModel):
    """Тело запроса на добавление позиции в заказ."""

    isbn: str = Field(..., min_length=10, max_length=17)
    quantity: int = Field(..., ge=1, le=100)


class ApplyPromoRequest(BaseModel):
    """Тело запроса на применение промокода."""

    code: str = Field(..., min_length=2, max_length=50)


class AddressDto(BaseModel):
    """Адрес доставки в запросе оформления заказа."""

    country: str = Field(..., min_length=2, max_length=2)
    city: str
    postal_code: str
    street: str


class CheckoutRequest(BaseModel):
    """Тело запроса на оформление заказа."""

    shipping_address: AddressDto


class OrderDto(BaseModel):
    """Представление заказа в ответах API."""

    order_id: str
    status: str
    customer_id: str
    items_count: int
    subtotal: Decimal
    promo_code: Optional[str] = None


class CheckoutResponse(BaseModel):
    """Ответ на успешное оформление заказа."""

    order_id: str
    status: str
    total: Decimal
    transaction_id: str


def _to_dto(order: Order) -> OrderDto:
    """Преобразовать доменный заказ в DTO для ответа."""
    return OrderDto(
        order_id=order.order_id,
        status=order.status.value,
        customer_id=order.customer.customer_id,
        items_count=len(order.items),
        subtotal=order.subtotal,
        promo_code=order.promo_code,
    )


@app.post("/orders", response_model=OrderDto, status_code=201)
def create_order(
    body: CreateOrderRequest,
    service: OrderService = Depends(get_order_service),
    customers: dict = Depends(get_customers_storage),
    orders: dict = Depends(get_orders_storage),
):
    """Создать новый заказ для существующего покупателя."""
    customer = customers.get(body.customer_id)
    if customer is None:
        raise HTTPException(404, detail=f"Покупатель {body.customer_id} не найден")
    try:
        order = service.create_order(customer)
    except OrderError as exc:
        raise HTTPException(403, detail=str(exc))
    orders[order.order_id] = order
    return _to_dto(order)


@app.get("/orders/{order_id}", response_model=OrderDto)
def get_order(
    order_id: str,
    orders: dict = Depends(get_orders_storage),
):
    """Вернуть заказ по идентификатору."""
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(404, detail=f"Заказ {order_id} не найден")
    return _to_dto(order)


@app.post("/orders/{order_id}/items", response_model=OrderDto)
def add_item(
    order_id: str,
    body: AddItemRequest,
    service: OrderService = Depends(get_order_service),
    orders: dict = Depends(get_orders_storage),
):
    """Добавить позицию в заказ."""
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(404, detail=f"Заказ {order_id} не найден")
    try:
        service.add_item(order, body.isbn, body.quantity)
    except BookNotFoundError as exc:
        raise HTTPException(404, detail=str(exc))
    except InvalidOrderStateError as exc:
        raise HTTPException(409, detail=str(exc))
    except OrderError as exc:
        raise HTTPException(400, detail=str(exc))
    return _to_dto(order)


@app.delete("/orders/{order_id}/items/{isbn}", response_model=OrderDto)
def remove_item(
    order_id: str,
    isbn: str,
    service: OrderService = Depends(get_order_service),
    orders: dict = Depends(get_orders_storage),
):
    """Удалить позицию из заказа."""
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(404, detail=f"Заказ {order_id} не найден")
    try:
        service.remove_item(order, isbn)
    except InvalidOrderStateError as exc:
        raise HTTPException(409, detail=str(exc))
    return _to_dto(order)


@app.post("/orders/{order_id}/promo", response_model=OrderDto)
def apply_promo(
    order_id: str,
    body: ApplyPromoRequest,
    service: OrderService = Depends(get_order_service),
    orders: dict = Depends(get_orders_storage),
):
    """Применить промокод к заказу."""
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(404, detail=f"Заказ {order_id} не найден")
    try:
        service.apply_promo_code(order, body.code)
    except InvalidOrderStateError as exc:
        raise HTTPException(409, detail=str(exc))
    return _to_dto(order)


@app.post("/orders/{order_id}/checkout", response_model=CheckoutResponse)
def checkout(
    order_id: str,
    body: CheckoutRequest,
    service: OrderService = Depends(get_order_service),
    orders: dict = Depends(get_orders_storage),
):
    """Оформить и оплатить заказ."""
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(404, detail=f"Заказ {order_id} не найден")

    address = Address(
        country=body.shipping_address.country,
        city=body.shipping_address.city,
        postal_code=body.shipping_address.postal_code,
        street=body.shipping_address.street,
    )

    try:
        result: CheckoutResult = service.checkout(order, address)
    except InvalidOrderStateError as exc:
        raise HTTPException(409, detail=str(exc))
    except PricingError as exc:
        raise HTTPException(422, detail=str(exc))
    except InventoryError as exc:
        raise HTTPException(409, detail=str(exc))
    except PaymentDeclinedError as exc:
        raise HTTPException(402, detail=str(exc))
    except PaymentError as exc:
        raise HTTPException(502, detail=str(exc))

    return CheckoutResponse(
        order_id=result.order.order_id,
        status=result.order.status.value,
        total=result.total,
        transaction_id=result.payment_transaction_id,
    )


@app.post("/orders/{order_id}/cancel", response_model=OrderDto)
def cancel(
    order_id: str,
    service: OrderService = Depends(get_order_service),
    orders: dict = Depends(get_orders_storage),
):
    """Отменить заказ (с возвратом средств, если он был оплачен)."""
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(404, detail=f"Заказ {order_id} не найден")
    try:
        service.cancel(order)
    except InvalidOrderStateError as exc:
        raise HTTPException(409, detail=str(exc))
    return _to_dto(order)
