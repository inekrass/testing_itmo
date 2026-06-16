"""
Тесты для модуля conventions.

Демонстрирует:
- Параметризацию для всех конвенций корректировки
- Граничные случаи T+N расчёта (переход через праздники)
- Проверку day-count конвенций
"""

from datetime import date

import pytest

from trading_api.conventions import (
    BusinessDayConvention,
    DayCountConvention,
    add_trading_days,
    adjust_date,
    count_trading_days,
    year_fraction,
)


# ═════════════════════════════════════════════════════════════════
#  adjust_date: корректировка даты
# ═════════════════════════════════════════════════════════════════


class TestAdjustDateUnadjusted:
    """UNADJUSTED никогда не меняет дату."""

    @pytest.mark.parametrize(
        "test_date",
        [
            date(2024, 11, 1),   # Пятница — рабочий
            date(2024, 11, 2),   # Суббота
            date(2024, 11, 4),   # Праздник MOEX
        ],
    )
    def test_unadjusted_returns_same_date(self, moex, test_date):
        result = adjust_date(
            test_date,
            BusinessDayConvention.UNADJUSTED,
            moex,
        )
        assert result == test_date


class TestAdjustDateFollowing:
    """FOLLOWING — переносим вперёд на следующий рабочий день."""

    def test_trading_day_not_changed(self, moex):
        """Рабочий день не меняется."""
        friday = date(2024, 11, 1)
        result = adjust_date(friday, BusinessDayConvention.FOLLOWING, moex)
        assert result == friday

    def test_saturday_moves_to_monday(self, moex):
        """Суббота 2 ноября → понедельник 4 ноября? Нет, 4 ноября — праздник!
        Значит → вторник 5 ноября."""
        saturday = date(2024, 11, 2)
        result = adjust_date(saturday, BusinessDayConvention.FOLLOWING, moex)
        assert result == date(2024, 11, 5)   # вторник

    def test_holiday_moves_forward(self, moex):
        """4 ноября (праздник MOEX) → 5 ноября (вторник)."""
        unity_day = date(2024, 11, 4)
        result = adjust_date(unity_day, BusinessDayConvention.FOLLOWING, moex)
        assert result == date(2024, 11, 5)

    def test_long_holiday_chain(self, moex):
        """3 января 2025 (праздник) → перескочит через 4-5 (выходные)
        и 6-8 (праздники) → 9 января."""
        holiday = date(2025, 1, 3)
        result = adjust_date(holiday, BusinessDayConvention.FOLLOWING, moex)
        assert result == date(2025, 1, 9)


class TestAdjustDatePreceding:
    """PRECEDING — переносим назад на предыдущий рабочий день."""

    def test_saturday_moves_to_friday(self, moex):
        saturday = date(2024, 11, 2)
        result = adjust_date(saturday, BusinessDayConvention.PRECEDING, moex)
        assert result == date(2024, 11, 1)   # пятница

    def test_holiday_moves_back(self, moex):
        """4 ноября (праздник) + назад через 2-3 (выходные) → 1 ноября (пятница)."""
        unity_day = date(2024, 11, 4)
        result = adjust_date(unity_day, BusinessDayConvention.PRECEDING, moex)
        assert result == date(2024, 11, 1)


class TestAdjustDateModifiedFollowing:
    """MODIFIED_FOLLOWING — как FOLLOWING, но не перескочить месяц."""

    def test_end_of_month_special_case(self, moex):
        """
        30 ноября 2024 — суббота. FOLLOWING дал бы 2 декабря (другой месяц)
        → MODIFIED_FOLLOWING откатит на последний рабочий день ноября.
        """
        saturday_nov_30 = date(2024, 11, 30)
        result = adjust_date(
            saturday_nov_30,
            BusinessDayConvention.MODIFIED_FOLLOWING,
            moex,
        )
        # Последний рабочий ноября — пятница 29 ноября
        assert result == date(2024, 11, 29)
        assert result.month == 11   # Остались в ноябре

    def test_mid_month_behaves_like_following(self, moex):
        """В середине месяца MODIFIED_FOLLOWING == FOLLOWING."""
        saturday = date(2024, 11, 2)
        modified = adjust_date(
            saturday, BusinessDayConvention.MODIFIED_FOLLOWING, moex
        )
        following = adjust_date(
            saturday, BusinessDayConvention.FOLLOWING, moex
        )
        assert modified == following


class TestAdjustDateModifiedPreceding:
    """MODIFIED_PRECEDING — как PRECEDING, но не перескочить месяц."""

    def test_first_of_month_special_case(self, moex):
        """
        1 ноября 2024 — пятница (рабочий) — не требует корректировки.
        Возьмём 1 мая 2024 (праздник MOEX) — предыдущий рабочий
        был бы 30 апреля, но 30 апреля — тоже праздник! 29 апреля — тоже!
        Идём вперёд на первый рабочий мая — 6 мая.
        """
        may_1 = date(2024, 5, 1)
        result = adjust_date(
            may_1, BusinessDayConvention.MODIFIED_PRECEDING, moex
        )
        # Первый рабочий в мае
        assert result.month == 5
        assert moex.is_trading_day(result)


# ═════════════════════════════════════════════════════════════════
#  add_trading_days: T+N расчёт
# ═════════════════════════════════════════════════════════════════


class TestAddTradingDaysBasic:
    """Базовые случаи T+N."""

    @pytest.mark.smoke
    def test_t_plus_0_returns_same_date(self, moex):
        """T+0 не меняет дату, даже если она выходная."""
        any_date = date(2024, 11, 2)   # суббота
        assert add_trading_days(any_date, 0, moex) == any_date

    def test_t_plus_1_from_regular_day(self, moex):
        """T+1 с обычного рабочего дня."""
        wednesday = date(2024, 11, 6)
        result = add_trading_days(wednesday, 1, moex)
        assert result == date(2024, 11, 7)   # четверг

    def test_t_plus_1_from_friday_skips_weekend(self, moex):
        """T+1 с пятницы — понедельник (через выходные)."""
        # Берём 8 ноября 2024 (пятница) — понедельник 11 ноября обычный
        friday = date(2024, 11, 8)
        result = add_trading_days(friday, 1, moex)
        assert result == date(2024, 11, 11)


class TestAddTradingDaysWithHolidays:
    """T+N с учётом праздников — главные кейсы."""

    @pytest.mark.smoke
    def test_t_plus_2_with_holiday_in_middle(self, moex, friday):
        """
        Пятница 1 ноября 2024 → T+2:
        Шаг 1: 4 ноября (праздник, пропускаем) → 5 ноября (вторник)
        Шаг 2: 6 ноября (среда)
        Итого: T+2 = 6 ноября (а не 5-го).
        """
        result = add_trading_days(friday, 2, moex)
        assert result == date(2024, 11, 6)

    def test_t_plus_5_through_weekend_and_holiday(self, moex):
        """T+5 от 1 ноября (пятница) — через выходные и праздник 4 ноября."""
        friday = date(2024, 11, 1)
        # 5, 6, 7, 8 ноября, затем 11 ноября = 5 торговых дней
        result = add_trading_days(friday, 5, moex)
        assert result == date(2024, 11, 11)

    def test_long_holiday_chain_january(self, moex):
        """Январские каникулы: с 30 декабря 2024 T+1 = 9 января 2025."""
        # 30 декабря 2024 — выходной MOEX, 31 декабря тоже.
        # 1-8 января — новогодние, 9 января — первый рабочий.
        dec_30 = date(2024, 12, 30)
        result = add_trading_days(dec_30, 1, moex)
        assert result == date(2025, 1, 9)


class TestAddTradingDaysNegative:
    """T-N — обратный расчёт (отнимаем торговые дни)."""

    def test_t_minus_1_from_monday(self, moex):
        """T-1 с понедельника 11 ноября → пятница 8 ноября."""
        monday = date(2024, 11, 11)
        result = add_trading_days(monday, -1, moex)
        assert result == date(2024, 11, 8)

    def test_t_minus_2_with_holiday(self, moex):
        """
        T-2 от 6 ноября 2024 (среда):
        Шаг 1 назад: 5 ноября (вторник)
        Шаг 2 назад: 4 ноября (праздник, пропуск) → 1 ноября (пятница)
        """
        wednesday = date(2024, 11, 6)
        result = add_trading_days(wednesday, -2, moex)
        assert result == date(2024, 11, 1)


class TestAddTradingDaysValidation:
    """Негативные сценарии и границы."""

    @pytest.mark.negative
    @pytest.mark.parametrize("invalid_n", [366, -366, 1000, -1000])
    def test_excessive_offset_raises(self, moex, invalid_n):
        with pytest.raises(ValueError, match="Слишком большое смещение"):
            add_trading_days(date(2024, 11, 1), invalid_n, moex)

    @pytest.mark.boundary
    def test_boundary_365_days(self, moex):
        """Ровно 365 торговых дней — должно отработать без исключения."""
        result = add_trading_days(date(2024, 1, 9), 365, moex)
        assert isinstance(result, date)
        assert moex.is_trading_day(result)


# ═════════════════════════════════════════════════════════════════
#  count_trading_days
# ═════════════════════════════════════════════════════════════════


class TestCountTradingDays:
    """Подсчёт торговых дней в интервале."""

    def test_same_week(self, moex):
        """Пн-пт одной недели, exclusive → 4 дня (без пятницы)."""
        monday = date(2024, 11, 11)
        friday = date(2024, 11, 15)
        result = count_trading_days(monday, friday, moex)
        assert result == 4   # Пн, Вт, Ср, Чт

    def test_inclusive_adds_end_day(self, moex):
        """inclusive=True включает end."""
        monday = date(2024, 11, 11)
        friday = date(2024, 11, 15)
        result = count_trading_days(monday, friday, moex, inclusive=True)
        assert result == 5

    def test_with_holiday(self, moex):
        """Включая 4 ноября (праздник) — он не считается."""
        start = date(2024, 11, 1)
        end = date(2024, 11, 8)
        result = count_trading_days(start, end, moex, inclusive=True)
        # 1, 5, 6, 7, 8 ноября = 5 торговых дней (2-3 выходные, 4 праздник)
        assert result == 5

    def test_end_before_start_returns_zero(self, moex):
        """Если end < start, возвращаем 0."""
        assert count_trading_days(
            date(2024, 11, 10), date(2024, 11, 1), moex
        ) == 0

    def test_same_date_exclusive_zero(self, moex):
        """Один и тот же день, exclusive → 0."""
        d = date(2024, 11, 6)
        assert count_trading_days(d, d, moex) == 0

    def test_same_date_inclusive_one_if_trading(self, moex):
        """Один торговый день, inclusive → 1."""
        d = date(2024, 11, 6)
        assert count_trading_days(d, d, moex, inclusive=True) == 1


# ═════════════════════════════════════════════════════════════════
#  year_fraction: day-count конвенции
# ═════════════════════════════════════════════════════════════════


class TestYearFraction:
    """Проверка конвенций подсчёта долей года."""

    def test_act_360_full_year(self):
        """ACT/360: 365 дней = 365/360 ≈ 1.0139."""
        result = year_fraction(
            date(2024, 1, 1),
            date(2025, 1, 1),
            DayCountConvention.ACT_360,
        )
        assert result == pytest.approx(366 / 360)   # 2024 — високосный

    def test_act_365_full_year(self):
        """ACT/365: 365 дней = 1.0 (в невисокосный год)."""
        result = year_fraction(
            date(2023, 1, 1),
            date(2024, 1, 1),
            DayCountConvention.ACT_365,
        )
        assert result == pytest.approx(1.0)

    def test_30_360_exact_month(self):
        """30/360: ровно месяц = 30/360."""
        result = year_fraction(
            date(2024, 1, 15),
            date(2024, 2, 15),
            DayCountConvention.THIRTY_360,
        )
        assert result == pytest.approx(30 / 360)

    def test_30_360_six_months(self):
        """30/360: ровно 6 месяцев = 0.5."""
        result = year_fraction(
            date(2024, 1, 1),
            date(2024, 7, 1),
            DayCountConvention.THIRTY_360,
        )
        assert result == pytest.approx(0.5)

    def test_reversed_dates_give_negative(self):
        """end < start → отрицательная доля (для ACT-конвенций)."""
        result = year_fraction(
            date(2024, 6, 1),
            date(2024, 1, 1),
            DayCountConvention.ACT_365,
        )
        assert result < 0
