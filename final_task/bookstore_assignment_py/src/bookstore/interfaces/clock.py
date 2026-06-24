from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Источник текущего времени. Вынесён в зависимость, чтобы время можно было
    подменять при расчёте сезонных правил (например, акций по датам)."""

    def now(self) -> datetime:
        """Текущий момент времени."""
        ...
