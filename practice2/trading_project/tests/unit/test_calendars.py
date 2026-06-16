"""
Тесты для модуля calendars.

Демонстрирует:
- Параметризацию для проверки конкретных дат
- Разделение тестов по группам: выходные, праздники, торговые дни
- Проверку разных бирж через параметризацию календарями
"""

from datetime import date

import pytest

from trading_api.calendars import (
    EXCHANGES,
    LSE,
    MOEX,
    NYSE,
    TSE,
    get_calendar,
)


class TestCalendarBasics:
    """Базовые свойства календаря."""

    @pytest.mark.parametrize("calendar_name", ["MOEX", "NYSE", "LSE", "TSE"])
    def test_exchange_has_valid_metadata(self, calendar_name):
        """У каждой биржи заполнены основные поля."""
        cal = EXCHANGES[calendar_name]
        assert cal.code == calendar_name
        assert cal.name  # не пустая строка
        assert cal.timezone is not None
        assert cal.open_time < cal.close_time

    def test_holidays_are_frozenset(self):
        """Праздники — frozenset для неизменяемости и быстрого поиска."""
        assert isinstance(MOEX.holidays, frozenset)


class TestIsWeekend:
    """Определение выходных дней."""

    @pytest.mark.parametrize(
        "test_date, expected",
        [
            pytest.param(date(2024, 11, 1), False, id="friday"),
            pytest.param(date(2024, 11, 2), True, id="saturday"),
            pytest.param(date(2024, 11, 3), True, id="sunday"),
            pytest.param(date(2024, 11, 4), False, id="monday"),
        ],
    )
    def test_weekend_detection(self, moex, test_date, expected):
        assert moex.is_weekend(test_date) is expected


class TestIsHoliday:
    """Определение праздничных дней (MOEX)."""

    @pytest.mark.smoke
    @pytest.mark.parametrize(
        "holiday_date",
        [
            pytest.param(date(2024, 1, 1), id="new_year"),
            pytest.param(date(2024, 5, 9), id="victory_day"),
            pytest.param(date(2024, 11, 4), id="unity_day"),
            pytest.param(date(2025, 1, 7), id="orthodox_christmas_2025"),
            pytest.param(date(2025, 5, 9), id="victory_day_2025"),
        ],
    )
    def test_moex_holidays(self, moex, holiday_date):
        assert moex.is_holiday(holiday_date) is True

    @pytest.mark.parametrize(
        "regular_date",
        [
            pytest.param(date(2024, 11, 6), id="wednesday_regular"),
            pytest.param(date(2025, 3, 3), id="monday_regular"),
            pytest.param(date(2024, 7, 15), id="summer_regular"),
        ],
    )
    def test_regular_days_are_not_holidays(self, moex, regular_date):
        assert moex.is_holiday(regular_date) is False

    def test_weekend_is_not_holiday(self, moex):
        """Выходной и праздник — разные категории нерабочих дней."""
        saturday = date(2024, 11, 2)
        assert moex.is_weekend(saturday) is True
        assert moex.is_holiday(saturday) is False


class TestIsTradingDay:
    """Определение торговых дней — комбинация выходных и праздников."""

    @pytest.mark.smoke
    @pytest.mark.parametrize(
        "test_date, is_trading",
        [
            pytest.param(date(2024, 11, 1), True, id="friday_regular"),
            pytest.param(date(2024, 11, 2), False, id="saturday"),
            pytest.param(date(2024, 11, 3), False, id="sunday"),
            pytest.param(date(2024, 11, 4), False, id="holiday_monday"),
            pytest.param(date(2024, 11, 5), True, id="tuesday_after_holiday"),
            pytest.param(date(2024, 11, 6), True, id="wednesday_regular"),
        ],
    )
    def test_trading_day_detection(self, moex, test_date, is_trading):
        """Комплексный тест: выходные + праздник на MOEX."""
        assert moex.is_trading_day(test_date) is is_trading


class TestDifferentExchanges:
    """Сравнение календарей разных бирж — одна и та же дата ведёт себя по-разному."""

    def test_4_july_is_holiday_on_nyse_not_moex(self):
        """4 июля (Independence Day) — праздник на NYSE, обычный день на MOEX."""
        independence_day = date(2024, 7, 4)
        assert NYSE.is_holiday(independence_day) is True
        assert MOEX.is_holiday(independence_day) is False
        assert MOEX.is_trading_day(independence_day) is True

    def test_9_may_is_holiday_on_moex_not_nyse(self):
        """9 мая — праздник в России, обычный день в США."""
        victory_day = date(2024, 5, 9)
        assert MOEX.is_holiday(victory_day) is True
        assert NYSE.is_holiday(victory_day) is False

    def test_thanksgiving_is_us_only(self):
        """Thanksgiving — только в США."""
        thanksgiving = date(2024, 11, 28)
        assert NYSE.is_holiday(thanksgiving) is True
        assert MOEX.is_holiday(thanksgiving) is False
        assert LSE.is_holiday(thanksgiving) is False


class TestGetCalendar:
    """Получение календаря через get_calendar."""

    @pytest.mark.parametrize("code", ["MOEX", "NYSE", "LSE", "TSE"])
    def test_known_exchanges(self, code):
        cal = get_calendar(code)
        assert cal.code == code

    def test_case_insensitive(self):
        """Код биржи не зависит от регистра."""
        assert get_calendar("moex").code == "MOEX"
        assert get_calendar("Nyse").code == "NYSE"
        assert get_calendar("NYSE").code == "NYSE"

    @pytest.mark.negative
    def test_unknown_exchange_raises(self):
        """Неизвестная биржа → KeyError с перечислением доступных."""
        with pytest.raises(KeyError, match="MOEX, NYSE, LSE, TSE"):
            get_calendar("UNKNOWN")

    @pytest.mark.negative
    def test_empty_string_raises(self):
        with pytest.raises(KeyError):
            get_calendar("")
