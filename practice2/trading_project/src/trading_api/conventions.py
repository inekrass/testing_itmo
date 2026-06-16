"""
Биржевые конвенции: правила корректировки дат и подсчёта дней.

Корректировка (Business Day Conventions):
    Что делать, если дата попадает на нерабочий день:
    - FOLLOWING: перенести на следующий рабочий день
    - MODIFIED_FOLLOWING: перенести вперёд, но если перескочил месяц — назад
    - PRECEDING: перенести на предыдущий рабочий день
    - MODIFIED_PRECEDING: перенести назад, но если перескочил месяц — вперёд
    - UNADJUSTED: не корректировать (вернуть как есть)

Конвенции подсчёта дней (Day Count Conventions) — для расчёта
процентов и NPV. Упрощённый набор для обучения:
    - ACT/360: фактические дни, база 360
    - ACT/365: фактические дни, база 365
    - 30/360: каждый месяц = 30 дней, год = 360 дней
"""

from datetime import date, timedelta
from enum import Enum

from trading_api.calendars import ExchangeCalendar


class BusinessDayConvention(str, Enum):
    """Правила корректировки нерабочих дат."""

    FOLLOWING = "FOLLOWING"
    MODIFIED_FOLLOWING = "MODIFIED_FOLLOWING"
    PRECEDING = "PRECEDING"
    MODIFIED_PRECEDING = "MODIFIED_PRECEDING"
    UNADJUSTED = "UNADJUSTED"


class DayCountConvention(str, Enum):
    """Конвенции подсчёта дней."""

    ACT_360 = "ACT/360"
    ACT_365 = "ACT/365"
    THIRTY_360 = "30/360"


# ═════════════════════════════════════════════════════════════════
#  Корректировка даты по конвенции
# ═════════════════════════════════════════════════════════════════


def adjust_date(
    day: date,
    convention: BusinessDayConvention,
    calendar: ExchangeCalendar,
) -> date:
    """
    Скорректировать дату согласно конвенции.

    Если day уже рабочий — возвращается без изменений.
    Иначе применяется правило convention.

    Args:
        day: исходная дата.
        convention: правило корректировки.
        calendar: биржевой календарь.

    Returns:
        Скорректированная дата (гарантированно рабочий день, кроме UNADJUSTED).
    """
    if convention == BusinessDayConvention.UNADJUSTED:
        return day

    if calendar.is_trading_day(day):
        return day

    if convention == BusinessDayConvention.FOLLOWING:
        return _next_trading_day(day, calendar)

    if convention == BusinessDayConvention.MODIFIED_FOLLOWING:
        next_day = _next_trading_day(day, calendar)
        # Если перескочили на следующий месяц — идём назад
        if next_day.month != day.month:
            return _previous_trading_day(day, calendar)
        return next_day

    if convention == BusinessDayConvention.PRECEDING:
        return _previous_trading_day(day, calendar)

    if convention == BusinessDayConvention.MODIFIED_PRECEDING:
        prev_day = _previous_trading_day(day, calendar)
        # Если перескочили на предыдущий месяц — идём вперёд
        if prev_day.month != day.month:
            return _next_trading_day(day, calendar)
        return prev_day

    # Для подстраховки (на случай расширения Enum)
    raise ValueError(f"Неизвестная конвенция: {convention}")


def _next_trading_day(day: date, calendar: ExchangeCalendar) -> date:
    """Следующий рабочий день после day (не включая сам day)."""
    current = day + timedelta(days=1)
    # Защита от бесконечного цикла — максимум 30 дней
    for _ in range(30):
        if calendar.is_trading_day(current):
            return current
        current += timedelta(days=1)
    raise RuntimeError(
        f"Не найден рабочий день в течение 30 дней после {day}"
    )


def _previous_trading_day(day: date, calendar: ExchangeCalendar) -> date:
    """Предыдущий рабочий день до day (не включая сам day)."""
    current = day - timedelta(days=1)
    for _ in range(30):
        if calendar.is_trading_day(current):
            return current
        current -= timedelta(days=1)
    raise RuntimeError(
        f"Не найден рабочий день в течение 30 дней до {day}"
    )


# ═════════════════════════════════════════════════════════════════
#  T+N расчёт — ключевая функция для биржевых расчётов
# ═════════════════════════════════════════════════════════════════


def add_trading_days(
    start: date,
    n: int,
    calendar: ExchangeCalendar,
) -> date:
    """
    Прибавить N торговых дней к дате.

    Пример: T+2 для 1 ноября 2024 (пятница) на MOEX = 5 ноября (вторник,
    потому что 4 ноября — праздник).

    Args:
        start: стартовая дата (T). Не обязана быть рабочим днём.
        n: количество торговых дней для прибавления. Может быть 0 или
           отрицательным.
        calendar: биржевой календарь.

    Returns:
        Дата, отстоящая на n торговых дней от start.

    Raises:
        ValueError: если |n| > 365.
    """
    if abs(n) > 365:
        raise ValueError(
            f"Слишком большое смещение: {n}. Допустимый диапазон: "
            f"-365..365 торговых дней."
        )

    if n == 0:
        # T+0: возвращаем ту же дату (может быть выходным)
        return start

    step = 1 if n > 0 else -1
    remaining = abs(n)
    current = start

    while remaining > 0:
        current += timedelta(days=step)
        if calendar.is_trading_day(current):
            remaining -= 1

    return current


# ═════════════════════════════════════════════════════════════════
#  Подсчёт торговых дней в интервале
# ═════════════════════════════════════════════════════════════════


def count_trading_days(
    start: date,
    end: date,
    calendar: ExchangeCalendar,
    inclusive: bool = False,
) -> int:
    """
    Посчитать количество торговых дней в интервале [start, end).

    Args:
        start: начало интервала.
        end: конец интервала.
        calendar: биржевой календарь.
        inclusive: включать ли end в подсчёт.

    Returns:
        Число торговых дней.
        Если end < start → 0.
    """
    if end < start:
        return 0

    count = 0
    current = start
    boundary = end + timedelta(days=1) if inclusive else end

    while current < boundary:
        if calendar.is_trading_day(current):
            count += 1
        current += timedelta(days=1)

    return count


# ═════════════════════════════════════════════════════════════════
#  Day Count Conventions — доля года между датами
# ═════════════════════════════════════════════════════════════════


def year_fraction(
    start: date,
    end: date,
    convention: DayCountConvention,
) -> float:
    """
    Вычислить долю года между датами по day-count конвенции.

    Используется в финансовых расчётах (проценты, NPV, накопленный доход).

    Args:
        start: начальная дата.
        end: конечная дата.
        convention: способ подсчёта.

    Returns:
        Доля года (float). Может быть отрицательной, если end < start.

    Raises:
        ValueError: если неизвестная конвенция.
    """
    if convention == DayCountConvention.ACT_360:
        return (end - start).days / 360.0

    if convention == DayCountConvention.ACT_365:
        return (end - start).days / 365.0

    if convention == DayCountConvention.THIRTY_360:
        # 30/360 US (Bond Basis)
        d1 = min(start.day, 30)
        d2 = min(end.day, 30) if d1 == 30 else end.day
        days = (
            360 * (end.year - start.year)
            + 30 * (end.month - start.month)
            + (d2 - d1)
        )
        return days / 360.0

    raise ValueError(f"Неизвестная конвенция: {convention}")
