"""
Фикстуры для unit-тестов.
"""

from datetime import date, datetime, time, timezone
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest

from trading_api.calendars import MOEX, NYSE, LSE, TSE, ExchangeCalendar
from trading_api.services import ExchangeRateProvider


# ═════════════════════════════════════════════════════════════════
#  Календари
# ═════════════════════════════════════════════════════════════════


@pytest.fixture
def moex() -> ExchangeCalendar:
    return MOEX


@pytest.fixture
def nyse() -> ExchangeCalendar:
    return NYSE


@pytest.fixture
def lse() -> ExchangeCalendar:
    return LSE


@pytest.fixture
def tse() -> ExchangeCalendar:
    return TSE


@pytest.fixture
def test_calendar() -> ExchangeCalendar:
    """
    Минимальный календарь для изолированных тестов.

    Праздник: 25 декабря 2024.
    Таймзона: UTC (чтобы не путаться).
    Часы работы: 9:00-18:00.
    """
    return ExchangeCalendar(
        code="TEST",
        name="Test Exchange",
        timezone=ZoneInfo("UTC"),
        open_time=time(9, 0),
        close_time=time(18, 0),
        holidays=frozenset({date(2024, 12, 25)}),
    )


# ═════════════════════════════════════════════════════════════════
#  Типичные даты для тестов
# ═════════════════════════════════════════════════════════════════


@pytest.fixture
def friday():
    """Обычная пятница, 1 ноября 2024. Следом — праздник 4 ноября (MOEX)."""
    return date(2024, 11, 1)


@pytest.fixture
def monday_after_long_weekend():
    """Понедельник 4 ноября 2024 — праздник в MOEX."""
    return date(2024, 11, 4)


@pytest.fixture
def regular_weekday():
    """Обычный рабочий день: среда, 6 ноября 2024."""
    return date(2024, 11, 6)


# ═════════════════════════════════════════════════════════════════
#  Моки провайдера курсов
# ═════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_rate_provider():
    """
    Пустой мок провайдера курсов. Поведение настраивается в конкретных тестах.
    """
    provider = MagicMock(spec=ExchangeRateProvider)
    return provider


@pytest.fixture
def fixed_rate_provider():
    """Мок, возвращающий курс 100.0 для любой пары/даты."""
    provider = MagicMock(spec=ExchangeRateProvider)
    provider.get_rate.return_value = 100.0
    return provider


# ═════════════════════════════════════════════════════════════════
#  Timezone-aware моменты времени
# ═════════════════════════════════════════════════════════════════


@pytest.fixture
def moment_moex_trading_hours():
    """1 ноября 2024, 12:00 МСК — MOEX открыт."""
    return datetime(2024, 11, 1, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))


@pytest.fixture
def moment_moex_before_open():
    """1 ноября 2024, 09:00 МСК — до открытия (открытие в 10:00)."""
    return datetime(2024, 11, 1, 9, 0, tzinfo=ZoneInfo("Europe/Moscow"))


@pytest.fixture
def moment_moex_after_close():
    """1 ноября 2024, 19:30 МСК — после закрытия (закрытие в 18:50)."""
    return datetime(2024, 11, 1, 19, 30, tzinfo=ZoneInfo("Europe/Moscow"))


@pytest.fixture
def moment_weekend():
    """Суббота 2 ноября 2024, 12:00 UTC."""
    return datetime(2024, 11, 2, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def moment_moex_holiday():
    """4 ноября 2024, 12:00 МСК — праздник на MOEX."""
    return datetime(2024, 11, 4, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))
