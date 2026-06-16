"""
Биржевые календари разных стран.

Содержат:
- Захардкоженный список праздников на 2024-2026 годы
- Информацию о таймзоне биржи
- Стандартные часы работы (для информации)
"""

from dataclasses import dataclass, field
from datetime import date, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class ExchangeCalendar:
    """Описание биржевого календаря."""

    code: str
    name: str
    timezone: ZoneInfo
    open_time: time
    close_time: time
    holidays: frozenset[date] = field(default_factory=frozenset)

    def is_holiday(self, day: date) -> bool:
        """Является ли день биржевым праздником (без учёта выходных)."""
        return day in self.holidays

    def is_weekend(self, day: date) -> bool:
        """Суббота или воскресенье (стандартное правило для большинства бирж)."""
        return day.weekday() >= 5

    def is_trading_day(self, day: date) -> bool:
        """День торгов: не выходной и не праздник."""
        return not self.is_weekend(day) and not self.is_holiday(day)


# ═════════════════════════════════════════════════════════════════
#  MOEX — Московская биржа (UTC+3)
# ═════════════════════════════════════════════════════════════════

MOEX = ExchangeCalendar(
    code="MOEX",
    name="Московская биржа",
    timezone=ZoneInfo("Europe/Moscow"),
    open_time=time(10, 0),
    close_time=time(18, 50),
    holidays=frozenset({
        # 2024
        date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3),
        date(2024, 1, 4), date(2024, 1, 5), date(2024, 1, 8),
        date(2024, 2, 23),
        date(2024, 3, 8),
        date(2024, 4, 29), date(2024, 4, 30), date(2024, 5, 1),
        date(2024, 5, 9), date(2024, 5, 10),
        date(2024, 6, 12),
        date(2024, 11, 4),
        date(2024, 12, 30), date(2024, 12, 31),
        # 2025
        date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3),
        date(2025, 1, 6), date(2025, 1, 7), date(2025, 1, 8),
        date(2025, 2, 24),
        date(2025, 3, 10),
        date(2025, 5, 1), date(2025, 5, 2), date(2025, 5, 8), date(2025, 5, 9),
        date(2025, 6, 12), date(2025, 6, 13),
        date(2025, 11, 3), date(2025, 11, 4),
        date(2025, 12, 31),
        # 2026
        date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 5),
        date(2026, 1, 6), date(2026, 1, 7), date(2026, 1, 8),
        date(2026, 2, 23),
        date(2026, 3, 9),
        date(2026, 5, 1), date(2026, 5, 4), date(2026, 5, 11),
        date(2026, 6, 12),
        date(2026, 11, 4),
    }),
)


# ═════════════════════════════════════════════════════════════════
#  NYSE — New York Stock Exchange (UTC-5/-4 с DST)
# ═════════════════════════════════════════════════════════════════

NYSE = ExchangeCalendar(
    code="NYSE",
    name="New York Stock Exchange",
    timezone=ZoneInfo("America/New_York"),
    open_time=time(9, 30),
    close_time=time(16, 0),
    holidays=frozenset({
        # 2024
        date(2024, 1, 1),
        date(2024, 1, 15),   # MLK Day
        date(2024, 2, 19),   # Presidents Day
        date(2024, 3, 29),   # Good Friday
        date(2024, 5, 27),   # Memorial Day
        date(2024, 6, 19),   # Juneteenth
        date(2024, 7, 4),    # Independence Day
        date(2024, 9, 2),    # Labor Day
        date(2024, 11, 28),  # Thanksgiving
        date(2024, 12, 25),
        # 2025
        date(2025, 1, 1),
        date(2025, 1, 9),    # State funeral (Jimmy Carter)
        date(2025, 1, 20),   # MLK Day
        date(2025, 2, 17),   # Presidents Day
        date(2025, 4, 18),   # Good Friday
        date(2025, 5, 26),   # Memorial Day
        date(2025, 6, 19),   # Juneteenth
        date(2025, 7, 4),    # Independence Day
        date(2025, 9, 1),    # Labor Day
        date(2025, 11, 27),  # Thanksgiving
        date(2025, 12, 25),
        # 2026
        date(2026, 1, 1),
        date(2026, 1, 19),   # MLK Day
        date(2026, 2, 16),   # Presidents Day
        date(2026, 4, 3),    # Good Friday
        date(2026, 5, 25),   # Memorial Day
        date(2026, 6, 19),   # Juneteenth
        date(2026, 7, 3),    # Independence Day (observed, т.к. 4 — суббота)
        date(2026, 9, 7),    # Labor Day
        date(2026, 11, 26),  # Thanksgiving
        date(2026, 12, 25),
    }),
)


# ═════════════════════════════════════════════════════════════════
#  LSE — London Stock Exchange (UTC+0/+1 с DST)
# ═════════════════════════════════════════════════════════════════

LSE = ExchangeCalendar(
    code="LSE",
    name="London Stock Exchange",
    timezone=ZoneInfo("Europe/London"),
    open_time=time(8, 0),
    close_time=time(16, 30),
    holidays=frozenset({
        # 2024
        date(2024, 1, 1),
        date(2024, 3, 29),   # Good Friday
        date(2024, 4, 1),    # Easter Monday
        date(2024, 5, 6),    # Early May Bank Holiday
        date(2024, 5, 27),   # Spring Bank Holiday
        date(2024, 8, 26),   # Summer Bank Holiday
        date(2024, 12, 25),
        date(2024, 12, 26),  # Boxing Day
        # 2025
        date(2025, 1, 1),
        date(2025, 4, 18),   # Good Friday
        date(2025, 4, 21),   # Easter Monday
        date(2025, 5, 5),    # Early May Bank Holiday
        date(2025, 5, 26),   # Spring Bank Holiday
        date(2025, 8, 25),   # Summer Bank Holiday
        date(2025, 12, 25),
        date(2025, 12, 26),
        # 2026
        date(2026, 1, 1),
        date(2026, 4, 3),    # Good Friday
        date(2026, 4, 6),    # Easter Monday
        date(2026, 5, 4),    # Early May Bank Holiday
        date(2026, 5, 25),   # Spring Bank Holiday
        date(2026, 8, 31),   # Summer Bank Holiday
        date(2026, 12, 25),
        date(2026, 12, 28),  # Boxing Day (observed)
    }),
)


# ═════════════════════════════════════════════════════════════════
#  TSE — Tokyo Stock Exchange (UTC+9, без DST)
# ═════════════════════════════════════════════════════════════════

TSE = ExchangeCalendar(
    code="TSE",
    name="Tokyo Stock Exchange",
    timezone=ZoneInfo("Asia/Tokyo"),
    open_time=time(9, 0),
    close_time=time(15, 0),
    holidays=frozenset({
        # 2025 (сокращённый набор для демонстрации)
        date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3),
        date(2025, 1, 13),
        date(2025, 2, 11),
        date(2025, 2, 24),
        date(2025, 3, 20),
        date(2025, 4, 29),
        date(2025, 5, 5), date(2025, 5, 6),
        date(2025, 7, 21),
        date(2025, 8, 11),
        date(2025, 9, 15), date(2025, 9, 23),
        date(2025, 10, 13),
        date(2025, 11, 3), date(2025, 11, 24),
        date(2025, 12, 31),
    }),
)


# ═════════════════════════════════════════════════════════════════
#  Реестр всех календарей
# ═════════════════════════════════════════════════════════════════

EXCHANGES: dict[str, ExchangeCalendar] = {
    "MOEX": MOEX,
    "NYSE": NYSE,
    "LSE": LSE,
    "TSE": TSE,
}


def get_calendar(code: str) -> ExchangeCalendar:
    """
    Получить календарь по коду биржи.

    Raises:
        KeyError: если биржа неизвестна.
    """
    code_upper = code.upper()
    if code_upper not in EXCHANGES:
        available = ", ".join(EXCHANGES.keys())
        raise KeyError(
            f"Неизвестная биржа: '{code}'. Доступны: {available}"
        )
    return EXCHANGES[code_upper]
