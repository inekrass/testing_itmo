from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Address:
    """Адрес доставки заказа."""

    country: str
    city: str
    postal_code: str
    street: str
