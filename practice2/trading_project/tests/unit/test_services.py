"""
Тесты для SettlementService с использованием моков.

Главная тема Пары 3.

Сервис зависит от:
1. ExchangeRateProvider — внешний HTTP-сервис
2. ExchangeCalendar — данные о праздниках

При тестировании обе зависимости заменяются моками.
Демонстрируются все ключевые техники:
- MagicMock(spec=...) для типобезопасных моков
- side_effect для имитации исключений
- side_effect как функция для сложного поведения
- side_effect как список для последовательности ответов
- Проверка вызовов: assert_called_once_with, call_args
"""

from datetime import date
from unittest.mock import MagicMock, call

import pytest

from trading_api.services import (
    ExchangeRateProvider,
    SettlementService,
)


class TestCalculateSettlementHappyPath:
    """Базовые позитивные сценарии."""

    @pytest.mark.smoke
    def test_basic_settlement(self, moex, mock_rate_provider):
        """
        Given: мок провайдер, возвращающий курс 100.0
        When:  запрашиваем расчёт 1000 USD/RUB на 1 ноября 2024
        Then:  quote_amount = 1000 * 100 = 100000
               settlement_date = T+2 с учётом праздника 4 ноября = 6 ноября
        """
        # Arrange — настраиваем мок
        mock_rate_provider.get_rate.return_value = 100.0
        service = SettlementService(mock_rate_provider, moex)

        # Act
        result = service.calculate_settlement(
            trade_date=date(2024, 11, 1),
            base_amount=1000.0,
            base_currency="USD",
            quote_currency="RUB",
        )

        # Assert — бизнес-результат
        assert result.applied_rate == 100.0
        assert result.quote_amount == 100_000.0
        assert result.settlement_date == date(2024, 11, 6)

        # Assert — проверяем, что мок был вызван правильно
        mock_rate_provider.get_rate.assert_called_once_with(
            base="USD",
            quote="RUB",
            on_date=date(2024, 11, 1),
        )

    def test_settlement_respects_calendar(self, moex, fixed_rate_provider):
        """T+2 от пятницы 1 ноября через праздник 4 ноября → 6 ноября."""
        service = SettlementService(fixed_rate_provider, moex)

        result = service.calculate_settlement(
            trade_date=date(2024, 11, 1),
            base_amount=100.0,
            base_currency="USD",
            quote_currency="RUB",
        )

        # 1 нояб (пт) + 2 рабочих дня (через 4 ноя - праздник) = 6 ноя
        assert result.settlement_date == date(2024, 11, 6)

    def test_custom_settlement_days(self, moex, fixed_rate_provider):
        """Сервис с T+1 вместо T+2."""
        service = SettlementService(
            fixed_rate_provider, moex, settlement_days=1
        )

        result = service.calculate_settlement(
            trade_date=date(2024, 11, 1),
            base_amount=100.0,
            base_currency="USD",
            quote_currency="RUB",
        )

        # T+1 от пятницы через выходные и праздник → 5 ноября (вторник)
        assert result.settlement_date == date(2024, 11, 5)


class TestSideEffectAsFunction:
    """
    side_effect = функция позволяет возвращать разные значения
    в зависимости от аргументов вызова.
    """

    def test_different_rates_for_different_currencies(self, moex):
        """Мок возвращает разный курс в зависимости от пары валют."""
        # Arrange — side_effect как функция
        def rate_lookup(base, quote, on_date):
            rates = {
                ("USD", "RUB"): 97.5,
                ("EUR", "RUB"): 105.2,
                ("GBP", "RUB"): 123.0,
            }
            return rates[(base, quote)]

        provider = MagicMock(spec=ExchangeRateProvider)
        provider.get_rate.side_effect = rate_lookup

        service = SettlementService(provider, moex)

        # Act — три расчёта с разными валютами
        usd_result = service.calculate_settlement(
            date(2024, 11, 1), 1000, "USD", "RUB"
        )
        eur_result = service.calculate_settlement(
            date(2024, 11, 1), 1000, "EUR", "RUB"
        )
        gbp_result = service.calculate_settlement(
            date(2024, 11, 1), 1000, "GBP", "RUB"
        )

        # Assert
        assert usd_result.applied_rate == 97.5
        assert usd_result.quote_amount == 97_500.0
        assert eur_result.applied_rate == 105.2
        assert gbp_result.applied_rate == 123.0

        # Проверяем, что провайдер был вызван 3 раза
        assert provider.get_rate.call_count == 3

    def test_rate_depends_on_date(self, moex):
        """Курс меняется по датам — имитация исторических данных."""
        historical_rates = {
            date(2024, 11, 1): 97.5,
            date(2024, 11, 5): 98.0,
            date(2024, 11, 6): 98.3,
        }

        provider = MagicMock(spec=ExchangeRateProvider)
        provider.get_rate.side_effect = (
            lambda base, quote, on_date: historical_rates[on_date]
        )

        service = SettlementService(provider, moex)

        result_nov1 = service.calculate_settlement(
            date(2024, 11, 1), 100, "USD", "RUB"
        )
        result_nov5 = service.calculate_settlement(
            date(2024, 11, 5), 100, "USD", "RUB"
        )

        assert result_nov1.applied_rate == 97.5
        assert result_nov5.applied_rate == 98.0


class TestSideEffectAsException:
    """
    side_effect = исключение (или список с исключением) позволяет
    имитировать сбои внешних сервисов.
    """

    @pytest.mark.negative
    def test_rate_not_found_propagates(self, moex):
        """Если провайдер выбросил LookupError — сервис пробрасывает его."""
        provider = MagicMock(spec=ExchangeRateProvider)
        provider.get_rate.side_effect = LookupError(
            "Курс USD/XYZ на 2024-11-01 не найден"
        )
        service = SettlementService(provider, moex)

        with pytest.raises(LookupError, match="не найден"):
            service.calculate_settlement(
                date(2024, 11, 1), 1000, "USD", "XYZ"
            )

    @pytest.mark.negative
    def test_connection_error_propagates(self, moex):
        """ConnectionError от HTTP — проброс без обёртки."""
        provider = MagicMock(spec=ExchangeRateProvider)
        provider.get_rate.side_effect = ConnectionError(
            "Сервис курсов недоступен"
        )
        service = SettlementService(provider, moex)

        with pytest.raises(ConnectionError, match="недоступен"):
            service.calculate_settlement(
                date(2024, 11, 1), 1000, "USD", "RUB"
            )


class TestSideEffectAsSequence:
    """
    side_effect = список — имитация серии ответов.
    Полезно для retry-сценариев.
    """

    def test_sequence_of_responses(self, moex):
        """Провайдер возвращает разные значения при каждом вызове."""
        provider = MagicMock(spec=ExchangeRateProvider)
        provider.get_rate.side_effect = [95.0, 100.0, 105.0]

        service = SettlementService(provider, moex)

        r1 = service.calculate_settlement(
            date(2024, 11, 1), 100, "USD", "RUB"
        )
        r2 = service.calculate_settlement(
            date(2024, 11, 5), 100, "USD", "RUB"
        )
        r3 = service.calculate_settlement(
            date(2024, 11, 6), 100, "USD", "RUB"
        )

        assert r1.applied_rate == 95.0
        assert r2.applied_rate == 100.0
        assert r3.applied_rate == 105.0


class TestInputValidation:
    """Валидация входных данных — моки не должны вызываться при ошибках."""

    @pytest.mark.negative
    def test_zero_amount_rejected(self, moex, mock_rate_provider):
        service = SettlementService(mock_rate_provider, moex)
        with pytest.raises(ValueError, match="положительным"):
            service.calculate_settlement(
                date(2024, 11, 1), 0.0, "USD", "RUB"
            )
        # Важно: провайдер НЕ должен был вызываться
        mock_rate_provider.get_rate.assert_not_called()

    @pytest.mark.negative
    def test_negative_amount_rejected(self, moex, mock_rate_provider):
        service = SettlementService(mock_rate_provider, moex)
        with pytest.raises(ValueError, match="положительным"):
            service.calculate_settlement(
                date(2024, 11, 1), -100.0, "USD", "RUB"
            )
        mock_rate_provider.get_rate.assert_not_called()

    @pytest.mark.negative
    def test_same_currency_rejected(self, moex, mock_rate_provider):
        service = SettlementService(mock_rate_provider, moex)
        with pytest.raises(ValueError, match="различаться"):
            service.calculate_settlement(
                date(2024, 11, 1), 100.0, "USD", "USD"
            )
        mock_rate_provider.get_rate.assert_not_called()

    @pytest.mark.negative
    def test_zero_rate_rejected(self, moex):
        """Если провайдер вернул 0 — сервис отказывает."""
        provider = MagicMock(spec=ExchangeRateProvider)
        provider.get_rate.return_value = 0.0
        service = SettlementService(provider, moex)

        with pytest.raises(ValueError, match="некорректный курс"):
            service.calculate_settlement(
                date(2024, 11, 1), 100.0, "USD", "RUB"
            )

    @pytest.mark.negative
    def test_negative_rate_rejected(self, moex):
        provider = MagicMock(spec=ExchangeRateProvider)
        provider.get_rate.return_value = -50.0
        service = SettlementService(provider, moex)

        with pytest.raises(ValueError, match="некорректный курс"):
            service.calculate_settlement(
                date(2024, 11, 1), 100.0, "USD", "RUB"
            )


class TestMockCallInspection:
    """
    Ключевая фишка моков — можно проверять ФАКТ вызовов.
    Не только "что вернул", но и "что ему передали".
    """

    def test_inspect_call_args_explicit(self, moex, fixed_rate_provider):
        """Проверяем конкретные аргументы последнего вызова."""
        service = SettlementService(fixed_rate_provider, moex)

        service.calculate_settlement(
            date(2024, 11, 1), 1000, "USD", "RUB"
        )

        # Вариант 1: assert_called_once_with (точное совпадение)
        fixed_rate_provider.get_rate.assert_called_once_with(
            base="USD",
            quote="RUB",
            on_date=date(2024, 11, 1),
        )

        # Вариант 2: call_args — получить аргументы
        call_args = fixed_rate_provider.get_rate.call_args
        assert call_args.kwargs["base"] == "USD"
        assert call_args.kwargs["on_date"] == date(2024, 11, 1)

    def test_multiple_calls_order(self, moex):
        """Проверяем порядок и содержание нескольких вызовов."""
        provider = MagicMock(spec=ExchangeRateProvider)
        provider.get_rate.side_effect = [100.0, 200.0, 300.0]
        service = SettlementService(provider, moex)

        # Три разных сделки
        service.calculate_settlement(date(2024, 11, 1), 10, "USD", "RUB")
        service.calculate_settlement(date(2024, 11, 1), 20, "EUR", "RUB")
        service.calculate_settlement(date(2024, 11, 1), 30, "GBP", "RUB")

        # Проверяем весь список вызовов
        expected_calls = [
            call(base="USD", quote="RUB", on_date=date(2024, 11, 1)),
            call(base="EUR", quote="RUB", on_date=date(2024, 11, 1)),
            call(base="GBP", quote="RUB", on_date=date(2024, 11, 1)),
        ]
        provider.get_rate.assert_has_calls(expected_calls)
        assert provider.get_rate.call_count == 3


class TestEstimateSettlementWindow:
    """
    estimate_settlement_window не обращается к провайдеру — только к календарю.
    Проверяем это через .assert_not_called.
    """

    def test_window_does_not_call_rate_provider(
        self, moex, mock_rate_provider
    ):
        """Не нужен внешний сервис — только календарь."""
        service = SettlementService(mock_rate_provider, moex)

        earliest, standard = service.estimate_settlement_window(
            date(2024, 11, 1)
        )

        # Проверяем, что провайдер курсов не был потрёпан
        mock_rate_provider.get_rate.assert_not_called()

        # Бизнес-проверка
        assert earliest == date(2024, 11, 5)   # T+1 через праздник = 5 ноября
        assert standard == date(2024, 11, 6)   # T+2 = 6 ноября
