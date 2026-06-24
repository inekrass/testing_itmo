from __future__ import annotations

from typing import Protocol, runtime_checkable

from bookstore.models.customer import Customer
from bookstore.models.order import Order


@runtime_checkable
class NotificationService(Protocol):
    """Отправка уведомлений покупателю (email, SMS, push)."""

    def send_order_confirmation(self, customer: Customer, order: Order) -> None:
        """Отправить подтверждение оформленного заказа."""
        ...

    def send_shipping_notification(
        self,
        customer: Customer,
        order: Order,
        tracking_number: str,
    ) -> None:
        """Отправить уведомление об отправке заказа с трек-номером."""
        ...
