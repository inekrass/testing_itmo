"""
СТАРТОВЫЙ ФАЙЛ — Занятие 3. Моки.

Задача:
    Написать тесты для SettlementService, используя MagicMock
    для замены ExchangeRateProvider.

Эталон: tests/unit/test_services.py

Как запустить:
    python -m pytest student_tasks/exercise_4_mocks.py -v
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from trading_api.calendars import MOEX
from trading_api.services import ExchangeRateProvider, SettlementService


# ══════════════════════════════════════════════════════════════════
#  ФИКСТУРЫ
# ══════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_rate_provider():
    """Пустой мок провайдера курсов (spec для типобезопасности)."""
    return MagicMock(spec=ExchangeRateProvider)


@pytest.fixture
def fixed_rate_provider():
    """Мок, возвращающий курс 100.0 для любой пары/даты."""
    provider = MagicMock(spec=ExchangeRateProvider)
    provider.get_rate.return_value = 100.0
    return provider


@pytest.fixture
def service(fixed_rate_provider):
    """Сервис с MOEX и фиксированным курсом."""
    return SettlementService(fixed_rate_provider, MOEX)


# ══════════════════════════════════════════════════════════════════
#  БАЗА: return_value
# ══════════════════════════════════════════════════════════════════


class TestBasic:

    def test_basic_settlement(self, service, fixed_rate_provider):
        """
        Курс 100, объём 1000 → quote_amount 100000.
        TODO:
          1. Вызвать service.calculate_settlement на 2024-11-01
          2. Проверить applied_rate == 100.0
          3. Проверить quote_amount == 100_000.0
          4. Проверить settlement_date == 2024-11-06 (T+2 с учётом праздника)
        """
        result = service.calculate_settlement(
            trade_date=date(2024, 11, 1),
            base_amount=1000.0,
            base_currency="USD",
            quote_currency="RUB",
        )

        assert result.applied_rate == 100.0
        assert result.quote_amount == 100_000.0
        assert result.settlement_date == date(2024, 11, 6)

    def test_rate_provider_called_correctly(
        self, service, fixed_rate_provider
    ):
        """
        После вызова сервиса провайдер должен быть вызван РАЗ с нужными
        аргументами.
        TODO:
          1. Вызвать service.calculate_settlement
          2. Проверить через fixed_rate_provider.get_rate.assert_called_once_with(...)
        """
        service.calculate_settlement(
            trade_date=date(2024, 11, 1),
            base_amount=1000.0,
            base_currency="USD",
            quote_currency="RUB",
        )

        fixed_rate_provider.get_rate.assert_called_once_with(
            base="USD",
            quote="RUB",
            on_date=date(2024, 11, 1),
        )


# ══════════════════════════════════════════════════════════════════
#  side_effect как ФУНКЦИЯ — разные значения для разных входов
# ══════════════════════════════════════════════════════════════════


class TestSideEffectFunction:

    def test_different_rates_per_currency(self, mock_rate_provider):
        """
        TODO:
          1. Написать функцию rate_lookup(base, quote, on_date),
             возвращающую: USD/RUB = 97.5, EUR/RUB = 105.2.
          2. Присвоить её mock_rate_provider.get_rate.side_effect
          3. Создать SettlementService с этим провайдером
          4. Сделать два вызова и проверить разные applied_rate.
        """
        def rate_lookup(base, quote, on_date):
            rates = {
                ("USD", "RUB"): 97.5,
                ("EUR", "RUB"): 105.2,
            }
            return rates[(base, quote)]

        mock_rate_provider.get_rate.side_effect = rate_lookup
        service = SettlementService(mock_rate_provider, MOEX)

        usd_result = service.calculate_settlement(
            date(2024, 11, 1), 1000.0, "USD", "RUB"
        )
        eur_result = service.calculate_settlement(
            date(2024, 11, 1), 1000.0, "EUR", "RUB"
        )

        assert usd_result.applied_rate == 97.5
        assert eur_result.applied_rate == 105.2


# ══════════════════════════════════════════════════════════════════
#  side_effect как ИСКЛЮЧЕНИЕ — имитация сбоев
# ══════════════════════════════════════════════════════════════════


class TestSideEffectException:

    def test_lookup_error_propagates(self, mock_rate_provider):
        """
        Если провайдер выбросил LookupError — сервис должен пробросить.
        TODO:
          1. Настроить mock_rate_provider.get_rate.side_effect = LookupError(...)
          2. Создать service
          3. Проверить pytest.raises(LookupError)
        """
        mock_rate_provider.get_rate.side_effect = LookupError(
            "Курс не найден"
        )
        service = SettlementService(mock_rate_provider, MOEX)

        with pytest.raises(LookupError, match="Курс не найден"):
            service.calculate_settlement(
                date(2024, 11, 1), 1000.0, "USD", "XYZ"
            )

    def test_connection_error_propagates(self, mock_rate_provider):
        """ConnectionError тоже должен пробрасываться."""
        mock_rate_provider.get_rate.side_effect = ConnectionError(
            "Сервис курсов недоступен"
        )
        service = SettlementService(mock_rate_provider, MOEX)

        with pytest.raises(ConnectionError, match="недоступен"):
            service.calculate_settlement(
                date(2024, 11, 1), 1000.0, "USD", "RUB"
            )


# ══════════════════════════════════════════════════════════════════
#  ПРОВЕРКА НЕ-ВЫЗОВОВ: assert_not_called
# ══════════════════════════════════════════════════════════════════


class TestInputValidationDoesntCallMock:
    """
    При невалидных входных данных провайдер НЕ должен вызываться —
    это оптимизация: не тратим HTTP-запрос на заведомо ошибочные данные.
    """

    def test_zero_amount_skips_provider(self, mock_rate_provider):
        """
        TODO:
          1. Создать service с mock_rate_provider
          2. Вызвать service.calculate_settlement с amount=0 в pytest.raises
          3. Проверить mock_rate_provider.get_rate.assert_not_called()
        """
        service = SettlementService(mock_rate_provider, MOEX)

        with pytest.raises(ValueError, match="положительным"):
            service.calculate_settlement(
                date(2024, 11, 1), 0.0, "USD", "RUB"
            )

        mock_rate_provider.get_rate.assert_not_called()
