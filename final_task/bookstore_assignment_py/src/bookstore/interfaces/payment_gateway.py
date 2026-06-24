from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional, Protocol, runtime_checkable


class PaymentStatus(str, Enum):
    """Результат обращения к платёжному шлюзу."""

    SUCCESS = "SUCCESS"
    DECLINED = "DECLINED"
    GATEWAY_ERROR = "GATEWAY_ERROR"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"


@dataclass
class PaymentResult:
    """Ответ платёжного шлюза на операцию списания или возврата."""

    status: PaymentStatus
    transaction_id: Optional[str] = None
    decline_reason: Optional[str] = None


@runtime_checkable
class PaymentGateway(Protocol):
    """Внешний платёжный провайдер."""

    def charge(
        self,
        customer_id: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> PaymentResult:
        """Списать средства. Повторный вызов с тем же ключом не дублирует платёж."""
        ...

    def refund(self, transaction_id: str, amount: Decimal) -> PaymentResult:
        """Вернуть средства по ранее проведённой операции."""
        ...
