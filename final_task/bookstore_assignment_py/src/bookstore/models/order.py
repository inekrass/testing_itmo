from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from bookstore.models.address import Address
from bookstore.models.cart_item import CartItem
from bookstore.models.customer import Customer


class OrderStatus(str, Enum):
    """Текущее состояние заказа в его жизненном цикле."""

    DRAFT = "DRAFT"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


@dataclass
class Order:
    """Заказ покупателя со списком позиций и текущим статусом."""

    order_id: str
    customer: Customer
    items: list[CartItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.DRAFT
    promo_code: Optional[str] = None
    shipping_address: Optional[Address] = None
    created_at: datetime = field(default_factory=datetime.now)
    payment_transaction_id: Optional[str] = None

    @property
    def subtotal(self) -> Decimal:
        """Сумма всех позиций по базовым ценам, без скидок и доставки."""
        return sum((item.line_total for item in self.items), Decimal("0"))

    @property
    def total_weight_grams(self) -> int:
        """Суммарный вес всех книг заказа в граммах."""
        return sum(item.book.weight_grams * item.quantity for item in self.items)

    @property
    def is_empty(self) -> bool:
        """True, если в заказе нет ни одной позиции."""
        return len(self.items) == 0
