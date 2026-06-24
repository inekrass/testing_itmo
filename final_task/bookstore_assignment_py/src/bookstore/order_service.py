from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from bookstore.exceptions import (
    InvalidOrderStateError,
    InventoryError,
    OrderError,
    PaymentDeclinedError,
    PaymentError,
)
from bookstore.interfaces.book_repository import BookRepository
from bookstore.interfaces.clock import Clock
from bookstore.interfaces.inventory_service import InventoryService
from bookstore.interfaces.notification_service import NotificationService
from bookstore.interfaces.payment_gateway import PaymentGateway, PaymentStatus
from bookstore.models.address import Address
from bookstore.models.cart_item import CartItem
from bookstore.models.customer import Customer
from bookstore.models.order import Order, OrderStatus
from bookstore.pricing import PricingService


@dataclass
class CheckoutResult:
    """Итог успешного оформления и оплаты заказа."""

    order: Order
    total: Decimal
    payment_transaction_id: str
    reservation_ids: list[str]


class OrderService:
    """Оформление, оплата и отмена заказов."""

    def __init__(
        self,
        book_repository: BookRepository,
        inventory: InventoryService,
        payment_gateway: PaymentGateway,
        notifications: NotificationService,
        clock: Clock,
    ):
        self._books = book_repository
        self._inventory = inventory
        self._payment = payment_gateway
        self._notifications = notifications
        self._clock = clock
        self._pricing = PricingService()

    def create_order(self, customer: Customer) -> Order:
        """Создать новый пустой заказ для покупателя."""
        if customer.is_blocked:
            raise OrderError("Покупатель заблокирован")
        return Order(order_id=str(uuid.uuid4()), customer=customer)

    def add_item(self, order: Order, isbn: str, quantity: int) -> None:
        """Добавить книгу в заказ. Если книга уже есть, увеличить её количество.
        Резервирование на складе здесь не выполняется — только при оформлении."""
        if order.status != OrderStatus.DRAFT:
            raise InvalidOrderStateError(
                f"Нельзя изменить заказ в статусе {order.status.value}"
            )
        if quantity <= 0:
            raise OrderError("Количество должно быть положительным")

        book = self._books.get_by_isbn(isbn)

        for item in order.items:
            if item.book.isbn == isbn:
                item.quantity += quantity
                return
        order.items.append(CartItem(book=book, quantity=quantity))

    def remove_item(self, order: Order, isbn: str) -> None:
        """Удалить книгу из заказа по ISBN."""
        if order.status != OrderStatus.DRAFT:
            raise InvalidOrderStateError(
                f"Нельзя изменить заказ в статусе {order.status.value}"
            )
        order.items = [item for item in order.items if item.book.isbn != isbn]

    def apply_promo_code(self, order: Order, code: str) -> None:
        """Привязать промокод к заказу. Его корректность проверяется при расчёте."""
        if order.status != OrderStatus.DRAFT:
            raise InvalidOrderStateError("Промокод можно применить только к черновику")
        order.promo_code = code

    def checkout(self, order: Order, shipping_address: Address) -> CheckoutResult:
        """Оформить и оплатить заказ.

        Шаги: проверка остатков, резервирование, расчёт стоимости, списание
        средств, перевод заказа в статус PAID и отправка подтверждения.
        Если оплата не прошла, резервирования снимаются и заказ отменяется.
        """
        if order.status != OrderStatus.DRAFT:
            raise InvalidOrderStateError(f"Заказ уже в статусе {order.status.value}")

        self._pricing.validate_order(order)
        order.shipping_address = shipping_address

        # Проверяем наличие до резервирования, чтобы быстро отказать.
        for item in order.items:
            stock = self._inventory.get_stock(item.book.isbn)
            if stock < item.quantity:
                raise InventoryError(
                    f"Недостаточно товара {item.book.isbn}: "
                    f"требуется {item.quantity}, доступно {stock}"
                )

        # Резервируем все позиции. При сбое снимаем уже сделанные резервации.
        reservations: list[str] = []
        try:
            for item in order.items:
                reservation_id = self._inventory.reserve(item.book.isbn, item.quantity)
                reservations.append(reservation_id)
        except InventoryError:
            for reservation_id in reservations:
                self._inventory.release(reservation_id)
            raise

        breakdown = self._pricing.calculate_order_total(order, self._clock.now())
        total = breakdown.total

        order.status = OrderStatus.PENDING_PAYMENT
        idempotency_key = f"order-{order.order_id}"

        try:
            result = self._payment.charge(
                customer_id=order.customer.customer_id,
                amount=total,
                currency="RUB",
                idempotency_key=idempotency_key,
            )
            if result.status != PaymentStatus.SUCCESS:
                for reservation_id in reservations:
                    self._inventory.release(reservation_id)
                order.status = OrderStatus.CANCELLED
                raise PaymentDeclinedError(
                    f"Платёж отклонён: {result.decline_reason or result.status.value}"
                )
        except PaymentError:
            for reservation_id in reservations:
                self._inventory.release(reservation_id)
            order.status = OrderStatus.CANCELLED
            raise

        order.status = OrderStatus.PAID
        order.payment_transaction_id = result.transaction_id

        # Сбой отправки уведомления не отменяет уже оплаченный заказ.
        try:
            self._notifications.send_order_confirmation(order.customer, order)
        except Exception:
            pass

        return CheckoutResult(
            order=order,
            total=total,
            payment_transaction_id=result.transaction_id or "",
            reservation_ids=reservations,
        )

    def cancel(self, order: Order) -> None:
        """Отменить заказ. Для оплаченного заказа выполняется возврат средств."""
        if order.status in (
            OrderStatus.CANCELLED,
            OrderStatus.DELIVERED,
            OrderStatus.REFUNDED,
        ):
            raise InvalidOrderStateError(
                f"Нельзя отменить заказ в статусе {order.status.value}"
            )

        if order.status == OrderStatus.PAID and order.payment_transaction_id:
            breakdown = self._pricing.calculate_order_total(order, self._clock.now())
            self._payment.refund(
                transaction_id=order.payment_transaction_id,
                amount=breakdown.total,
            )
            order.status = OrderStatus.REFUNDED
        else:
            order.status = OrderStatus.CANCELLED
