"""
Внешние сервисы и торговый сервис, их использующий.

Материал для Пары 3 (моки). Есть:
- ExchangeRateProvider — внешний провайдер курсов валют (абстрактный класс)
- SettlementService — использует провайдер и календари. Чтобы его
  протестировать не ходя в сеть, нужны моки.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from trading_api.calendars import ExchangeCalendar
from trading_api.conventions import add_trading_days


# ═════════════════════════════════════════════════════════════════
#  Внешние зависимости
# ═════════════════════════════════════════════════════════════════


class ExchangeRateProvider(ABC):
    """
    Абстрактный провайдер курсов валют.

    Реальная реализация ходит в HTTP API (например, ЦБ РФ).
    В тестах заменяется моком.
    """

    @abstractmethod
    def get_rate(self, base: str, quote: str, on_date: date) -> float:
        """
        Получить курс base/quote на указанную дату.

        Пример: get_rate("USD", "RUB", date(2024, 11, 1)) → 97.5

        Raises:
            LookupError: если курс недоступен.
            ConnectionError: если сервис недоступен.
        """
        ...


class HolidayCalendarProvider(ABC):
    """
    Провайдер календаря праздников.

    В продакшне может ходить в API биржи за обновлениями,
    в тестах используется мок или захардкоженный календарь.
    """

    @abstractmethod
    def get_holidays(self, exchange_code: str, year: int) -> set[date]:
        """Получить множество праздников биржи за указанный год."""
        ...


# ═════════════════════════════════════════════════════════════════
#  Модель торговой операции
# ═════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class SettlementInstruction:
    """Инструкция по расчёту — что и когда должно быть поставлено."""

    trade_date: date
    settlement_date: date
    base_amount: float
    quote_amount: float
    base_currency: str
    quote_currency: str
    exchange_code: str
    applied_rate: float


# ═════════════════════════════════════════════════════════════════
#  SettlementService — сервис расчётов
# ═════════════════════════════════════════════════════════════════


class SettlementService:
    """
    Сервис расчётов по биржевым сделкам.

    Зависит от:
    - ExchangeRateProvider (внешний HTTP)
    - ExchangeCalendar (данные о праздниках)

    При тестировании оба зависимости заменяются моками.
    """

    def __init__(
        self,
        rate_provider: ExchangeRateProvider,
        calendar: ExchangeCalendar,
        settlement_days: int = 2,
    ):
        self._rate_provider = rate_provider
        self._calendar = calendar
        self._settlement_days = settlement_days

    def calculate_settlement(
        self,
        trade_date: date,
        base_amount: float,
        base_currency: str,
        quote_currency: str,
    ) -> SettlementInstruction:
        """
        Рассчитать инструкцию по расчёту:
        - Дата расчёта = trade_date + T+N (N настраивается, по умолчанию 2)
        - Курс берётся на trade_date
        - Объём в quote-валюте = base_amount * rate

        Raises:
            ValueError: при невалидных входных данных.
            LookupError: если курс недоступен (пробрасывается из провайдера).
            ConnectionError: если провайдер недоступен.
        """
        if base_amount <= 0:
            raise ValueError(
                f"Объём должен быть положительным, получено: {base_amount}"
            )

        if base_currency == quote_currency:
            raise ValueError(
                f"Валюты должны различаться: {base_currency}/{quote_currency}"
            )

        # Курс берётся на дату сделки
        rate = self._rate_provider.get_rate(
            base=base_currency,
            quote=quote_currency,
            on_date=trade_date,
        )

        if rate <= 0:
            raise ValueError(f"Получен некорректный курс: {rate}")

        # T+N расчёт
        settlement_date = add_trading_days(
            start=trade_date,
            n=self._settlement_days,
            calendar=self._calendar,
        )

        quote_amount = base_amount * rate

        return SettlementInstruction(
            trade_date=trade_date,
            settlement_date=settlement_date,
            base_amount=base_amount,
            quote_amount=quote_amount,
            base_currency=base_currency,
            quote_currency=quote_currency,
            exchange_code=self._calendar.code,
            applied_rate=rate,
        )

    def estimate_settlement_window(
        self,
        trade_date: date,
    ) -> tuple[date, date]:
        """
        Получить диапазон возможных дат расчёта:
        (самая ранняя возможная = T+1, стандартная = T+N).

        Пример для MOEX: T+1 и T+2.
        """
        earliest = add_trading_days(trade_date, 1, self._calendar)
        standard = add_trading_days(
            trade_date, self._settlement_days, self._calendar
        )
        return earliest, standard
