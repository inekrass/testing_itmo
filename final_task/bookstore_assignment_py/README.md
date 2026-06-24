## Отчет

**Выполнил**: Некрасов Богдан
**Группа**: Р4150

Результаты работы:

- тесты: [`tests/`](tests/)
- модульные тесты расчёта стоимости: [`tests/unit/test_pricing.py`](tests/unit/test_pricing.py)
- тесты `OrderService.checkout` с подменой зависимостей: [`tests/mocks/test_order_service_checkout.py`](tests/mocks/test_order_service_checkout.py)
- HTTP API тесты: [`tests/api/test_api.py`](tests/api/test_api.py)
- property-based тесты: [`tests/property/test_pricing_properties.py`](tests/property/test_pricing_properties.py)
- отчёт по мутационному тестированию: [`tests/mutation_report.md`](tests/mutation_report.md)
- баг-репорт по расхождениям с ТЗ: [`tests/bug_report.md`](tests/bug_report.md)

Запуск всех тестов:

```bash
python3 -m pytest -q
```

## Установка

```bash
pip install -r requirements.txt
```

## Запуск API

```bash
uvicorn bookstore.api:app --reload --app-dir src
```

Документация OpenAPI будет доступна на `http://localhost:8000/docs`.

Конкретные реализации внешних зависимостей (склад, платёжный шлюз, уведомления) подключаются при сборке приложения через механизм зависимостей FastAPI.
