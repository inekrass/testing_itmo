from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CustomerTier(str, Enum):
    """Уровень покупателя. Определяет размер скидки и лимит на сумму заказа."""

    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"


@dataclass
class Customer:
    """Покупатель магазина."""

    customer_id: str
    name: str
    email: str
    tier: CustomerTier = CustomerTier.BRONZE
    orders_last_year: int = 0
    country: str = "RU"
    is_blocked: bool = False
