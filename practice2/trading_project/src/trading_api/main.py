"""
REST API для работы с биржевыми расчётами.

Эндпоинты:
    GET  /exchanges                              — список бирж
    GET  /exchanges/{code}/status                — открыта ли биржа сейчас
    GET  /exchanges/{code}/is-trading-day/{day}  — торговый ли день
    POST /trading-days/add                       — T+N расчёт
    POST /trading-days/count                     — подсчёт торговых дней
    POST /dates/adjust                           — корректировка даты
    POST /settlements/calculate                  — расчёт инструкции

Материал для Пары 4 (API-тесты через TestClient).
"""

from datetime import date, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, status
from pydantic import BaseModel, Field, field_validator

from trading_api.calendars import EXCHANGES, ExchangeCalendar, get_calendar
from trading_api.conventions import (
    BusinessDayConvention,
    add_trading_days,
    adjust_date,
    count_trading_days,
)
from trading_api.market_hours import get_market_status, now_utc

app = FastAPI(
    title="Trading Days API",
    description="Расчёт торговых дней, корректировка дат, статус бирж",
    version="1.0.0",
)


# ═════════════════════════════════════════════════════════════════
#  Pydantic-схемы
# ═════════════════════════════════════════════════════════════════


class ExchangeInfo(BaseModel):
    code: str
    name: str
    timezone: str
    open_time: str
    close_time: str


class MarketStatusResponse(BaseModel):
    exchange_code: str
    is_open: bool
    reason: str
    exchange_time: datetime
    queried_at: datetime


class AddTradingDaysRequest(BaseModel):
    exchange: str = Field(..., examples=["MOEX"])
    start_date: date = Field(..., examples=["2024-11-01"])
    days: int = Field(..., ge=-365, le=365, examples=[2])


class AddTradingDaysResponse(BaseModel):
    start_date: date
    days: int
    result_date: date
    exchange: str


class CountTradingDaysRequest(BaseModel):
    exchange: str
    start_date: date
    end_date: date
    inclusive: bool = False

    @field_validator("end_date")
    @classmethod
    def end_not_before_start(cls, v: date, info):
        start = info.data.get("start_date")
        if start is not None and v < start:
            raise ValueError(
                "end_date не может быть раньше start_date"
            )
        return v


class CountTradingDaysResponse(BaseModel):
    start_date: date
    end_date: date
    inclusive: bool
    trading_days: int
    exchange: str


class AdjustDateRequest(BaseModel):
    exchange: str
    target_date: date
    convention: BusinessDayConvention


class AdjustDateResponse(BaseModel):
    target_date: date
    convention: BusinessDayConvention
    adjusted_date: date
    was_adjusted: bool
    exchange: str


# ═════════════════════════════════════════════════════════════════
#  Зависимости (для последующего мокирования в тестах)
# ═════════════════════════════════════════════════════════════════


def get_current_time() -> datetime:
    """
    Dependency для получения текущего времени.

    Вынесена, чтобы в тестах подменить через app.dependency_overrides
    и не зависеть от "настоящего сейчас".
    """
    return now_utc()


def resolve_calendar(
    code: Annotated[str, Path(description="Код биржи: MOEX, NYSE, LSE, TSE")],
) -> ExchangeCalendar:
    """Dependency — получить календарь по коду (с HTTP 404 при ошибке)."""
    try:
        return get_calendar(code)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ═════════════════════════════════════════════════════════════════
#  Эндпоинты
# ═════════════════════════════════════════════════════════════════


@app.get("/exchanges", response_model=list[ExchangeInfo])
def list_exchanges():
    """Список всех поддерживаемых бирж."""
    return [
        ExchangeInfo(
            code=cal.code,
            name=cal.name,
            timezone=str(cal.timezone),
            open_time=cal.open_time.strftime("%H:%M"),
            close_time=cal.close_time.strftime("%H:%M"),
        )
        for cal in EXCHANGES.values()
    ]


@app.get(
    "/exchanges/{code}/status",
    response_model=MarketStatusResponse,
)
def get_exchange_status(
    calendar: Annotated[ExchangeCalendar, Depends(resolve_calendar)],
    current_time: Annotated[datetime, Depends(get_current_time)],
):
    """
    Текущий статус биржи: открыта ли, почему закрыта.

    Время определяется через dependency get_current_time —
    в тестах оно подменяется.
    """
    result = get_market_status(current_time, calendar)
    return MarketStatusResponse(
        exchange_code=result.exchange_code,
        is_open=result.is_open,
        reason=result.reason,
        exchange_time=result.exchange_time,
        queried_at=current_time,
    )


@app.get("/exchanges/{code}/is-trading-day/{day}")
def check_trading_day(
    calendar: Annotated[ExchangeCalendar, Depends(resolve_calendar)],
    day: date,
):
    """Проверить, торговый ли день на заданной бирже."""
    return {
        "exchange": calendar.code,
        "date": day,
        "is_trading_day": calendar.is_trading_day(day),
        "is_weekend": calendar.is_weekend(day),
        "is_holiday": calendar.is_holiday(day),
    }


@app.post(
    "/trading-days/add",
    response_model=AddTradingDaysResponse,
)
def api_add_trading_days(request: AddTradingDaysRequest):
    """Прибавить N торговых дней к дате с учётом календаря биржи."""
    try:
        calendar = get_calendar(request.exchange)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    result = add_trading_days(
        start=request.start_date,
        n=request.days,
        calendar=calendar,
    )
    return AddTradingDaysResponse(
        start_date=request.start_date,
        days=request.days,
        result_date=result,
        exchange=calendar.code,
    )


@app.post(
    "/trading-days/count",
    response_model=CountTradingDaysResponse,
)
def api_count_trading_days(request: CountTradingDaysRequest):
    """Посчитать число торговых дней в интервале."""
    try:
        calendar = get_calendar(request.exchange)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    result = count_trading_days(
        start=request.start_date,
        end=request.end_date,
        calendar=calendar,
        inclusive=request.inclusive,
    )
    return CountTradingDaysResponse(
        start_date=request.start_date,
        end_date=request.end_date,
        inclusive=request.inclusive,
        trading_days=result,
        exchange=calendar.code,
    )


@app.post(
    "/dates/adjust",
    response_model=AdjustDateResponse,
)
def api_adjust_date(request: AdjustDateRequest):
    """Скорректировать дату по конвенции (FOLLOWING, MODIFIED_FOLLOWING и т.д.)."""
    try:
        calendar = get_calendar(request.exchange)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    adjusted = adjust_date(
        day=request.target_date,
        convention=request.convention,
        calendar=calendar,
    )
    return AdjustDateResponse(
        target_date=request.target_date,
        convention=request.convention,
        adjusted_date=adjusted,
        was_adjusted=adjusted != request.target_date,
        exchange=calendar.code,
    )
