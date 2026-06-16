"""
Тесты для модуля market_hours.

Главная тема — работа с таймзонами:
- Запрос в UTC → открыт ли MOEX?
- Запрос в времени Нью-Йорка → открыт ли LSE?
- Граничные моменты: ровно на открытии, ровно на закрытии
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from trading_api.market_hours import (
    convert_to_exchange_time,
    convert_to_utc,
    get_market_status,
)


class TestMarketStatusBasic:
    """Базовые сценарии статуса биржи."""

    @pytest.mark.smoke
    def test_moex_open_during_trading_hours(
        self, moex, moment_moex_trading_hours
    ):
        """12:00 МСК в пятницу — MOEX открыт."""
        result = get_market_status(moment_moex_trading_hours, moex)
        assert result.is_open is True
        assert result.reason == "OPEN"
        assert result.exchange_code == "MOEX"

    def test_moex_closed_before_open(self, moex, moment_moex_before_open):
        """09:00 МСК — до открытия (открытие в 10:00)."""
        result = get_market_status(moment_moex_before_open, moex)
        assert result.is_open is False
        assert result.reason == "CLOSED_BEFORE_OPEN"

    def test_moex_closed_after_close(self, moex, moment_moex_after_close):
        """19:30 МСК — после закрытия (закрытие в 18:50)."""
        result = get_market_status(moment_moex_after_close, moex)
        assert result.is_open is False
        assert result.reason == "CLOSED_AFTER_CLOSE"

    def test_moex_closed_on_weekend(self, moex, moment_weekend):
        """Суббота — выходной."""
        result = get_market_status(moment_weekend, moex)
        assert result.is_open is False
        assert result.reason == "CLOSED_WEEKEND"

    def test_moex_closed_on_holiday(self, moex, moment_moex_holiday):
        """4 ноября — праздник."""
        result = get_market_status(moment_moex_holiday, moex)
        assert result.is_open is False
        assert result.reason == "CLOSED_HOLIDAY"


class TestBoundaryTimes:
    """Граничные моменты: ровно на открытии/закрытии."""

    @pytest.mark.boundary
    def test_exactly_at_open_is_open(self, moex):
        """Ровно 10:00:00 МСК — биржа открыта (включительно)."""
        moment = datetime(2024, 11, 1, 10, 0, 0, tzinfo=ZoneInfo("Europe/Moscow"))
        result = get_market_status(moment, moex)
        assert result.is_open is True

    @pytest.mark.boundary
    def test_one_second_before_open(self, moex):
        """9:59:59 — ещё закрыто."""
        moment = datetime(2024, 11, 1, 9, 59, 59, tzinfo=ZoneInfo("Europe/Moscow"))
        result = get_market_status(moment, moex)
        assert result.is_open is False
        assert result.reason == "CLOSED_BEFORE_OPEN"

    @pytest.mark.boundary
    def test_exactly_at_close_is_closed(self, moex):
        """Ровно 18:50:00 МСК — уже закрыто (close_time exclusive)."""
        moment = datetime(2024, 11, 1, 18, 50, 0, tzinfo=ZoneInfo("Europe/Moscow"))
        result = get_market_status(moment, moex)
        assert result.is_open is False
        assert result.reason == "CLOSED_AFTER_CLOSE"

    @pytest.mark.boundary
    def test_one_second_before_close(self, moex):
        """18:49:59 — ещё открыто."""
        moment = datetime(2024, 11, 1, 18, 49, 59, tzinfo=ZoneInfo("Europe/Moscow"))
        result = get_market_status(moment, moex)
        assert result.is_open is True


class TestTimezoneConversion:
    """
    Главное для магистров: запрос приходит в UTC,
    MOEX открыт по своему московскому времени.
    """

    def test_moex_open_at_9_utc(self, moex):
        """
        09:00 UTC в пятницу = 12:00 МСК → MOEX открыт.
        """
        moment_utc = datetime(2024, 11, 1, 9, 0, tzinfo=timezone.utc)
        result = get_market_status(moment_utc, moex)
        assert result.is_open is True
        # Проверим, что exchange_time сконвертировано правильно
        assert result.exchange_time.hour == 12
        assert result.exchange_time.tzinfo == ZoneInfo("Europe/Moscow")

    def test_ny_midday_is_moex_evening(self, moex):
        """
        Полдень в Нью-Йорке (12:00 EST) = 20:00 МСК → MOEX уже закрыт.
        """
        moment_ny = datetime(
            2024, 11, 1, 12, 0, tzinfo=ZoneInfo("America/New_York")
        )
        result = get_market_status(moment_ny, moex)
        assert result.is_open is False
        assert result.reason == "CLOSED_AFTER_CLOSE"

    def test_nyse_open_at_15_utc(self, nyse):
        """
        15:00 UTC в пятницу = 10:00 EST → NYSE открыт (откр. в 9:30).
        Берём дату без праздников на NYSE.
        """
        moment_utc = datetime(2024, 11, 1, 15, 0, tzinfo=timezone.utc)
        result = get_market_status(moment_utc, nyse)
        assert result.is_open is True

    def test_tse_open_in_tokyo_morning_utc_night(self, tse):
        """
        Токио торгуется 9:00-15:00 JST.
        3:00 UTC = 12:00 JST (четверг) → TSE открыт.
        Берём дату, которая не праздник в TSE.
        """
        moment_utc = datetime(2025, 6, 12, 3, 0, tzinfo=timezone.utc)
        result = get_market_status(moment_utc, tse)
        assert result.is_open is True
        assert result.exchange_time.hour == 12

    def test_date_differs_between_timezones(self, tse):
        """
        Внимание на дате!
        22:00 UTC пятницы = 7:00 JST субботы → выходной в Токио.
        Пример: 22:00 UTC 13 июня 2025 = 07:00 JST 14 июня 2025 (сб).
        """
        moment_utc = datetime(2025, 6, 13, 22, 0, tzinfo=timezone.utc)
        result = get_market_status(moment_utc, tse)
        assert result.is_open is False
        # Важно: exchange_time показывает дату по токийскому календарю
        assert result.exchange_time.date().weekday() == 5   # суббота
        assert result.reason == "CLOSED_WEEKEND"


class TestNaiveDatetimeRejected:
    """
    Критически важно для биржи: naive datetime недопустимы.
    Они неоднозначны — неясно, в какой таймзоне считать.
    """

    @pytest.mark.negative
    def test_naive_datetime_raises(self, moex):
        naive = datetime(2024, 11, 1, 12, 0)   # без tzinfo
        with pytest.raises(ValueError, match="timezone-aware"):
            get_market_status(naive, moex)

    @pytest.mark.negative
    def test_convert_to_exchange_rejects_naive(self, moex):
        with pytest.raises(ValueError, match="timezone-aware"):
            convert_to_exchange_time(datetime(2024, 11, 1, 12, 0), moex)

    @pytest.mark.negative
    def test_convert_to_utc_rejects_naive(self):
        with pytest.raises(ValueError, match="timezone-aware"):
            convert_to_utc(datetime(2024, 11, 1, 12, 0))


class TestDSTHandling:
    """
    Переход на летнее/зимнее время.
    Это — классическая ловушка для биржевых систем.
    """

    def test_nyse_dst_transition_march(self, nyse):
        """
        В США DST начинается 10 марта 2024.
        10 марта — воскресенье, биржа закрыта.
        Проверим, что 11 марта (понедельник) в 10:00 EDT — открыто.
        """
        # 10:00 EDT 11 марта 2024 = 14:00 UTC
        moment_utc = datetime(2024, 3, 11, 14, 0, tzinfo=timezone.utc)
        result = get_market_status(moment_utc, nyse)
        assert result.is_open is True
        # Ещё важно: локальное время — 10:00
        assert result.exchange_time.hour == 10

    def test_tse_no_dst(self, tse):
        """
        Токио не использует DST. В любое время года:
        9:00 JST = 00:00 UTC ± ничего.
        """
        # 9 июня 2025 (обычный рабочий день)
        moment_utc = datetime(2025, 6, 9, 0, 0, tzinfo=timezone.utc)
        result = get_market_status(moment_utc, tse)
        # 9:00 JST — момент открытия (equality → open)
        assert result.is_open is True
        assert result.exchange_time.hour == 9
