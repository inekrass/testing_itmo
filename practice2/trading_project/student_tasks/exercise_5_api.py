"""
СТАРТОВЫЙ ФАЙЛ — Занятие 4. API-тесты.

Задача:
    Написать тесты для FastAPI-приложения через TestClient.
    Проверить status codes, тело ответа, валидацию Pydantic,
    и использовать dependency_overrides для подмены времени.

Эталон: tests/api/test_endpoints.py

Как запустить:
    python -m pytest student_tasks/exercise_5_api.py -v
"""

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from trading_api.main import app, get_current_time


# ══════════════════════════════════════════════════════════════════
#  ФИКСТУРЫ
# ══════════════════════════════════════════════════════════════════


@pytest.fixture
def client():
    """Обычный TestClient."""
    return TestClient(app)


@pytest.fixture
def client_with_frozen_time():
    """
    Фабрика TestClient с подменённым временем через dependency_overrides.
    Используется так:
        client = client_with_frozen_time(нужный_момент)
    """
    def _make_client(frozen: datetime) -> TestClient:
        app.dependency_overrides[get_current_time] = lambda: frozen
        return TestClient(app)

    yield _make_client
    app.dependency_overrides.clear()   # cleanup


# ══════════════════════════════════════════════════════════════════
#  GET /exchanges — список бирж
# ══════════════════════════════════════════════════════════════════


class TestListExchanges:

    def test_returns_200(self, client):
        """
        TODO: GET /exchanges, проверить статус 200.
        """
        response = client.get("/exchanges")

        assert response.status_code == 200

    def test_contains_moex(self, client):
        """
        TODO: Проверить, что в ответе есть биржа с code == "MOEX".
        """
        response = client.get("/exchanges")
        codes = {exchange["code"] for exchange in response.json()}

        assert "MOEX" in codes


# ══════════════════════════════════════════════════════════════════
#  GET /exchanges/{code}/status — статус с подменой времени
# ══════════════════════════════════════════════════════════════════


class TestStatusEndpoint:

    def test_moex_open_during_trading(self, client_with_frozen_time):
        """
        Подменить время на 12:00 МСК пятницы 1 ноября 2024.
        TODO:
          1. moment = datetime(2024, 11, 1, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))
          2. client = client_with_frozen_time(moment)
          3. GET /exchanges/MOEX/status → is_open=True, reason="OPEN"
        """
        moment = datetime(
            2024, 11, 1, 12, 0, tzinfo=ZoneInfo("Europe/Moscow")
        )
        client = client_with_frozen_time(moment)

        response = client.get("/exchanges/MOEX/status")
        data = response.json()

        assert response.status_code == 200
        assert data["is_open"] is True
        assert data["reason"] == "OPEN"

    def test_unknown_exchange_returns_404(self, client):
        """TODO: GET /exchanges/UNKNOWN/status → 404."""
        response = client.get("/exchanges/UNKNOWN/status")

        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════
#  POST /trading-days/add — параметризованная матрица
# ══════════════════════════════════════════════════════════════════


class TestAddTradingDays:

    @pytest.mark.parametrize(
        "exchange, start, days, expected",
        [
            pytest.param("MOEX", "2024-11-01", 2, "2024-11-06", id="moex_t2"),
            pytest.param("MOEX", "2024-11-01", 1, "2024-11-05", id="moex_t1"),
            pytest.param("MOEX", "2024-11-06", 0, "2024-11-06", id="moex_t0"),
            pytest.param("MOEX", "2024-11-06", -2, "2024-11-01", id="moex_minus_2"),
        ],
    )
    def test_scenarios(self, client, exchange, start, days, expected):
        """
        TODO:
          1. POST /trading-days/add с JSON {"exchange": ..., "start_date": ..., "days": ...}
          2. Проверить response.json()["result_date"] == expected
        """
        response = client.post(
            "/trading-days/add",
            json={
                "exchange": exchange,
                "start_date": start,
                "days": days,
            },
        )

        assert response.status_code == 200
        assert response.json()["result_date"] == expected

    def test_invalid_days_rejected(self, client):
        """
        Pydantic должен отклонить days > 365 с статусом 422.
        TODO:
        """
        response = client.post(
            "/trading-days/add",
            json={
                "exchange": "MOEX",
                "start_date": "2024-11-01",
                "days": 1000,
            },
        )

        assert response.status_code == 422

    def test_missing_field_422(self, client):
        """
        Если не передать start_date — Pydantic вернёт 422.
        TODO:
        """
        response = client.post(
            "/trading-days/add",
            json={
                "exchange": "MOEX",
                "days": 2,
            },
        )

        assert response.status_code == 422
