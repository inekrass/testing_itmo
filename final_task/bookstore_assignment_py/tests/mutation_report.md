# Отчёт по мутационному тестированию

## Объект проверки

- Модуль: `src/bookstore/pricing.py`
- Инструмент: `cosmic-ray 8.4.6`
- Конфиг: `cosmic-ray.toml`
- Команда тестов для мутантов: `python3 -m pytest tests/unit/test_pricing.py -q`

Property-based тесты запускаются отдельно в общем наборе `pytest`; в cosmic-ray
использован быстрый unit-слой, чтобы прогон завершался за разумное время.

## Результат

- Всего мутантов: 238
- Убито тестами: 221
- Выжило: 17
- Полнота выполнения: 238/238, 100%
- Доля выживших: 7.14%

## Команды

```bash
python3 -m pytest -q
cosmic-ray init cosmic-ray.toml mutation-session.sqlite --force
cosmic-ray exec cosmic-ray.toml mutation-session.sqlite
cr-report mutation-session.sqlite
```
