from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class CurrencyConverter(Protocol):
    """Конвертация сумм между валютами по актуальному курсу."""

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        on_date: Optional[date] = None,
    ) -> Decimal:
        """Перевести сумму из одной валюты в другую.
        Без указания даты используется текущий курс. Бросает CurrencyError,
        если курс недоступен."""
        ...
