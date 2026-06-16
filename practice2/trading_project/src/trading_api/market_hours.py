"""
Проверка статуса торгов: открыта ли биржа в заданный момент.

Учитывает:
- Часы работы биржи (open_time .. close_time в её локальной таймзоне)
- Торговые дни (не выходной и не праздник)
- Таймзоны: запрос может прийти в любой tz, ответ даётся в tz биржи
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from trading_api.calendars import ExchangeCalendar


@dataclass(frozen=True)
class MarketStatus:
    """Статус биржи в заданный момент."""

    is_open: bool
    exchange_code: str
    exchange_time: datetime      # Локальное время биржи
    reason: str                  # "OPEN" / "CLOSED_WEEKEND" / "CLOSED_HOLIDAY" /
                                 # "CLOSED_BEFORE_OPEN" / "CLOSED_AFTER_CLOSE"


def get_market_status(
    moment: datetime,
    calendar: ExchangeCalendar,
) -> MarketStatus:
    """
    Определить, открыта ли биржа в заданный момент.

    Алгоритм:
    1. Конвертировать moment в локальное время биржи.
    2. Проверить, что это торговый день (не выходной, не праздник).
    3. Проверить, что текущее время в окне [open_time, close_time).

    Args:
        moment: момент времени с таймзоной (timezone-aware).
        calendar: биржевой календарь.

    Returns:
        MarketStatus с полным описанием.

    Raises:
        ValueError: если moment без таймзоны (naive datetime).
    """
    if moment.tzinfo is None:
        raise ValueError(
            "moment должен быть timezone-aware (с указанной таймзоной). "
            "Naive datetime недопустим для биржевых расчётов."
        )

    # Конвертация в локальное время биржи
    exchange_time = moment.astimezone(calendar.timezone)
    exchange_date = exchange_time.date()
    exchange_clock = exchange_time.time()

    # Проверка календаря
    if calendar.is_weekend(exchange_date):
        return MarketStatus(
            is_open=False,
            exchange_code=calendar.code,
            exchange_time=exchange_time,
            reason="CLOSED_WEEKEND",
        )

    if calendar.is_holiday(exchange_date):
        return MarketStatus(
            is_open=False,
            exchange_code=calendar.code,
            exchange_time=exchange_time,
            reason="CLOSED_HOLIDAY",
        )

    # Проверка часов работы
    if exchange_clock < calendar.open_time:
        return MarketStatus(
            is_open=False,
            exchange_code=calendar.code,
            exchange_time=exchange_time,
            reason="CLOSED_BEFORE_OPEN",
        )

    if exchange_clock >= calendar.close_time:
        return MarketStatus(
            is_open=False,
            exchange_code=calendar.code,
            exchange_time=exchange_time,
            reason="CLOSED_AFTER_CLOSE",
        )

    return MarketStatus(
        is_open=True,
        exchange_code=calendar.code,
        exchange_time=exchange_time,
        reason="OPEN",
    )


def now_utc() -> datetime:
    """
    Возвращает текущий момент в UTC.

    Вынесено в отдельную функцию, чтобы её можно было замокать в тестах.
    Это — один из главных приёмов для тестируемости кода с временем.
    """
    return datetime.now(timezone.utc)


def convert_to_exchange_time(
    moment: datetime,
    calendar: ExchangeCalendar,
) -> datetime:
    """
    Конвертировать момент в локальное время биржи.

    Raises:
        ValueError: если moment без таймзоны.
    """
    if moment.tzinfo is None:
        raise ValueError("moment должен быть timezone-aware")
    return moment.astimezone(calendar.timezone)


def convert_to_utc(moment: datetime) -> datetime:
    """
    Конвертировать момент в UTC.

    Raises:
        ValueError: если moment без таймзоны.
    """
    if moment.tzinfo is None:
        raise ValueError("moment должен быть timezone-aware")
    return moment.astimezone(timezone.utc)
