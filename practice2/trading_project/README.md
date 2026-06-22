# Отчет

**Выполнил**: Некрасов Богдан  
**Группа**: Р4150

## Предметная область

REST API для работы с биржевыми датами:

- календари 4 бирж: MOEX, NYSE, LSE, TSE;
- расчет T+N с учетом выходных и праздников;
- конвенции корректировки дат;
- статус биржи с учетом таймзон;
- `SettlementService` для расчета инструкций по сделкам.

## Быстрый старт

1. Установка зависимостей:

```bash
python -m pip install -r requirements.txt
```

2. Выполненные задания находятся в `/student_tasks`:

- `student_tasks/exercise_4_mocks.py`
- `student_tasks/exercise_5_api.py`

3. Как запустить тесты:

```bash
python -m pytest student_tasks/exercise_4_mocks.py -v
python -m pytest student_tasks/exercise_5_api.py -v
```

## Выполненные задания

### `exercise_4_mocks.py`

Реализованы тесты для `SettlementService` с использованием `MagicMock`:

- проверка базового расчета settlement;
- проверка вызова провайдера через `assert_called_once_with`;
- использование `side_effect` как функции для разных валютных пар;
- проверка проброса `LookupError`;
- проверка проброса `ConnectionError`;
- проверка, что при невалидном объеме провайдер не вызывается.

### `exercise_5_api.py`

Реализованы API-тесты через FastAPI `TestClient`:

- проверка `GET /exchanges`;
- проверка наличия биржи `MOEX`;
- проверка статуса MOEX с подменой времени через `dependency_overrides`;
- проверка `404` для неизвестной биржи;
- параметризованные тесты `POST /trading-days/add`;
- проверка Pydantic-валидации со статусом `422`.

## Результаты

```bash
# exercise_4_mocks.py
========================================= 6 passed in 0.03s =========================================
```

```bash
# exercise_5_api.py
======================================== 10 passed in 0.31s =========================================
```