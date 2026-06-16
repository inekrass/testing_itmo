"""
Фикстуры для API-тестов.
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from trading_api.main import app, get_current_time


@pytest.fixture
def client():
    """TestClient для вызова API без поднятия сервера."""
    return TestClient(app)


@pytest.fixture
def client_with_frozen_time():
    """
    TestClient с фиксированным временем через dependency_overrides.

    Возвращает фабрику: передаём нужный момент, получаем TestClient,
    в котором любой запрос видит это время вместо now().
    """
    def _make_client(frozen_moment: datetime) -> TestClient:
        app.dependency_overrides[get_current_time] = lambda: frozen_moment
        return TestClient(app)

    yield _make_client

    # Обязательный cleanup — иначе подмена "протечёт" в следующий тест
    app.dependency_overrides.clear()


@pytest.fixture
def moex_trading_time():
    """12:00 МСК пятница 1 ноября 2024 — MOEX открыт."""
    from zoneinfo import ZoneInfo
    return datetime(2024, 11, 1, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))


@pytest.fixture
def weekend_moment():
    """Суббота 2 ноября 2024, 12:00 UTC."""
    return datetime(2024, 11, 2, 12, 0, tzinfo=timezone.utc)
