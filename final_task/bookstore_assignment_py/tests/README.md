# Тесты

```
tests/
├── unit/
│   └── test_pricing.py                  модульные тесты PricingService
├── mocks/
│   └── test_order_service_checkout.py   тесты checkout с подменой зависимостей
├── api/
│   └── test_api.py                      тесты HTTP API
├── property/
│   └── test_pricing_properties.py       property-based тесты PricingService
├── conftest.py                          общие фикстуры и фейки
├── mutation_report.md                   отчёт по cosmic-ray
└── bug_report.md                        найденные расхождения с ТЗ
```
