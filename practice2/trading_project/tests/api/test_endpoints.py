"""
API-тесты через FastAPI TestClient.

Главная тема Пары 4:
- Как тестировать REST API без поднятия сервера
- Проверка статус-кодов и схемы ответа
- Мокирование зависимостей через dependency_overrides
- Параметризованная матрица: разные биржи × разные даты
"""

from datetime import datetime

import pytest


# ═════════════════════════════════════════════════════════════════
#  GET /exchanges
# ═════════════════════════════════════════════════════════════════


class TestListExchanges:
    @pytest.mark.smoke
    def test_returns_200(self, client):
        response = client.get("/exchanges")
        assert response.status_code == 200

    def test_returns_list_of_exchanges(self, client):
        response = client.get("/exchanges")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4   # MOEX, NYSE, LSE, TSE

    def test_each_exchange_has_required_fields(self, client):
        """Каждый элемент содержит обязательные поля."""
        response = client.get("/exchanges")
        for exchange in response.json():
            assert "code" in exchange
            assert "name" in exchange
            assert "timezone" in exchange
            assert "open_time" in exchange
            assert "close_time" in exchange

    def test_moex_is_in_response(self, client):
        """MOEX присутствует в списке."""
        response = client.get("/exchanges")
        codes = {e["code"] for e in response.json()}
        assert "MOEX" in codes
        assert "NYSE" in codes


# ═════════════════════════════════════════════════════════════════
#  GET /exchanges/{code}/status
# ═════════════════════════════════════════════════════════════════


class TestMarketStatus:
    """
    Здесь используем dependency_overrides для контроля над временем.
    Это ключевой паттерн для тестирования API с "сейчас".
    """

    @pytest.mark.smoke
    def test_moex_open_during_trading_hours(
        self, client_with_frozen_time, moex_trading_time
    ):
        """В 12:00 МСК MOEX открыт."""
        client = client_with_frozen_time(moex_trading_time)

        response = client.get("/exchanges/MOEX/status")
        assert response.status_code == 200

        data = response.json()
        assert data["is_open"] is True
        assert data["reason"] == "OPEN"
        assert data["exchange_code"] == "MOEX"

    def test_moex_closed_on_weekend(
        self, client_with_frozen_time, weekend_moment
    ):
        """В субботу MOEX закрыт."""
        client = client_with_frozen_time(weekend_moment)

        response = client.get("/exchanges/MOEX/status")
        data = response.json()

        assert data["is_open"] is False
        assert data["reason"] == "CLOSED_WEEKEND"

    def test_unknown_exchange_returns_404(self, client):
        """Несуществующая биржа → 404."""
        response = client.get("/exchanges/UNKNOWN/status")
        assert response.status_code == 404
        assert "Неизвестная биржа" in response.json()["detail"]

    def test_code_is_case_insensitive(self, client_with_frozen_time, moex_trading_time):
        """moex, MOEX, Moex — всё работает."""
        client = client_with_frozen_time(moex_trading_time)
        for code in ["MOEX", "moex", "Moex"]:
            response = client.get(f"/exchanges/{code}/status")
            assert response.status_code == 200


# ═════════════════════════════════════════════════════════════════
#  GET /exchanges/{code}/is-trading-day/{day}
# ═════════════════════════════════════════════════════════════════


class TestIsTradingDay:
    @pytest.mark.smoke
    @pytest.mark.parametrize(
        "day, expected",
        [
            pytest.param("2024-11-01", True, id="friday"),
            pytest.param("2024-11-02", False, id="saturday"),
            pytest.param("2024-11-04", False, id="moex_holiday"),
            pytest.param("2024-11-06", True, id="regular_wednesday"),
        ],
    )
    def test_moex_trading_days(self, client, day, expected):
        response = client.get(f"/exchanges/MOEX/is-trading-day/{day}")
        assert response.status_code == 200
        assert response.json()["is_trading_day"] is expected

    def test_flags_weekend_vs_holiday(self, client):
        """API различает выходной и праздник."""
        # 2 ноября — суббота (не праздник MOEX)
        sat = client.get("/exchanges/MOEX/is-trading-day/2024-11-02").json()
        assert sat["is_weekend"] is True
        assert sat["is_holiday"] is False

        # 4 ноября — праздник (не выходной)
        hol = client.get("/exchanges/MOEX/is-trading-day/2024-11-04").json()
        assert hol["is_weekend"] is False
        assert hol["is_holiday"] is True

    def test_invalid_date_format_rejected(self, client):
        """'not-a-date' не пройдёт валидацию Pydantic → 422."""
        response = client.get("/exchanges/MOEX/is-trading-day/not-a-date")
        assert response.status_code == 422


# ═════════════════════════════════════════════════════════════════
#  POST /trading-days/add
# ═════════════════════════════════════════════════════════════════


class TestAddTradingDaysEndpoint:
    @pytest.mark.smoke
    def test_t_plus_2_moex(self, client):
        """Классический кейс: T+2 с учётом праздника."""
        response = client.post(
            "/trading-days/add",
            json={
                "exchange": "MOEX",
                "start_date": "2024-11-01",
                "days": 2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result_date"] == "2024-11-06"

    @pytest.mark.parametrize(
        "exchange, start, days, expected",
        [
            pytest.param("MOEX", "2024-11-01", 2, "2024-11-06", id="moex_t2"),
            pytest.param("MOEX", "2024-11-01", 1, "2024-11-05", id="moex_t1"),
            pytest.param("MOEX", "2024-11-06", 0, "2024-11-06", id="t0_trading"),
            pytest.param("MOEX", "2024-11-06", -2, "2024-11-01", id="negative"),
            pytest.param("NYSE", "2024-07-03", 1, "2024-07-05", id="nyse_skip_independence"),
        ],
    )
    def test_parametrized_scenarios(
        self, client, exchange, start, days, expected
    ):
        response = client.post(
            "/trading-days/add",
            json={"exchange": exchange, "start_date": start, "days": days},
        )
        assert response.status_code == 200
        assert response.json()["result_date"] == expected

    def test_unknown_exchange_returns_404(self, client):
        response = client.post(
            "/trading-days/add",
            json={
                "exchange": "UNKNOWN",
                "start_date": "2024-11-01",
                "days": 2,
            },
        )
        assert response.status_code == 404

    def test_excessive_days_rejected_by_pydantic(self, client):
        """days > 365 — Pydantic вернёт 422."""
        response = client.post(
            "/trading-days/add",
            json={"exchange": "MOEX", "start_date": "2024-11-01", "days": 1000},
        )
        assert response.status_code == 422

    def test_missing_required_field(self, client):
        response = client.post(
            "/trading-days/add",
            json={"exchange": "MOEX", "days": 2},   # нет start_date
        )
        assert response.status_code == 422

    def test_invalid_date_format(self, client):
        response = client.post(
            "/trading-days/add",
            json={
                "exchange": "MOEX",
                "start_date": "not-a-date",
                "days": 2,
            },
        )
        assert response.status_code == 422


# ═════════════════════════════════════════════════════════════════
#  POST /trading-days/count
# ═════════════════════════════════════════════════════════════════


class TestCountTradingDaysEndpoint:
    def test_basic_count(self, client):
        """С 11 по 15 ноября 2024 (пн-пт) exclusive = 4."""
        response = client.post(
            "/trading-days/count",
            json={
                "exchange": "MOEX",
                "start_date": "2024-11-11",
                "end_date": "2024-11-15",
            },
        )
        assert response.status_code == 200
        assert response.json()["trading_days"] == 4

    def test_inclusive_flag(self, client):
        """С тем же интервалом, но inclusive — 5."""
        response = client.post(
            "/trading-days/count",
            json={
                "exchange": "MOEX",
                "start_date": "2024-11-11",
                "end_date": "2024-11-15",
                "inclusive": True,
            },
        )
        assert response.json()["trading_days"] == 5

    def test_end_before_start_rejected(self, client):
        """Валидатор Pydantic не должен пропустить end < start."""
        response = client.post(
            "/trading-days/count",
            json={
                "exchange": "MOEX",
                "start_date": "2024-11-15",
                "end_date": "2024-11-11",
            },
        )
        assert response.status_code == 422


# ═════════════════════════════════════════════════════════════════
#  POST /dates/adjust
# ═════════════════════════════════════════════════════════════════


class TestAdjustDateEndpoint:
    @pytest.mark.smoke
    @pytest.mark.parametrize(
        "target, convention, expected",
        [
            pytest.param(
                "2024-11-02", "FOLLOWING", "2024-11-05",
                id="sat_following_skips_holiday",
            ),
            pytest.param(
                "2024-11-02", "PRECEDING", "2024-11-01",
                id="sat_preceding",
            ),
            pytest.param(
                "2024-11-04", "FOLLOWING", "2024-11-05",
                id="holiday_following",
            ),
            pytest.param(
                "2024-11-01", "FOLLOWING", "2024-11-01",
                id="trading_day_unchanged",
            ),
            pytest.param(
                "2024-11-30", "MODIFIED_FOLLOWING", "2024-11-29",
                id="end_of_month_rollback",
            ),
        ],
    )
    def test_adjustment_matrix(self, client, target, convention, expected):
        response = client.post(
            "/dates/adjust",
            json={
                "exchange": "MOEX",
                "target_date": target,
                "convention": convention,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["adjusted_date"] == expected

    def test_was_adjusted_flag(self, client):
        """Если дата реально изменилась — was_adjusted=True."""
        response = client.post(
            "/dates/adjust",
            json={
                "exchange": "MOEX",
                "target_date": "2024-11-04",
                "convention": "FOLLOWING",
            },
        )
        assert response.json()["was_adjusted"] is True

    def test_was_not_adjusted_for_trading_day(self, client):
        """Рабочий день — was_adjusted=False."""
        response = client.post(
            "/dates/adjust",
            json={
                "exchange": "MOEX",
                "target_date": "2024-11-06",
                "convention": "FOLLOWING",
            },
        )
        assert response.json()["was_adjusted"] is False

    def test_invalid_convention_rejected(self, client):
        """Несуществующая конвенция → 422."""
        response = client.post(
            "/dates/adjust",
            json={
                "exchange": "MOEX",
                "target_date": "2024-11-04",
                "convention": "INVALID_RULE",
            },
        )
        assert response.status_code == 422


# ═════════════════════════════════════════════════════════════════
#  Схема OpenAPI
# ═════════════════════════════════════════════════════════════════


class TestOpenAPISchema:
    """FastAPI генерирует OpenAPI автоматически — можно тестировать."""

    def test_openapi_json_available(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "Trading Days API"

    def test_all_endpoints_are_documented(self, client):
        """Все наши пути попали в схему."""
        schema = client.get("/openapi.json").json()
        paths = schema["paths"]
        assert "/exchanges" in paths
        assert "/trading-days/add" in paths
        assert "/dates/adjust" in paths
