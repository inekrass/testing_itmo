# Отчет

**Выполнил**: Некрасов Богдан  
**Группа**: Р4150

## Предметная область

Сервис для работы с заказами пиццерии:

- каталог пицц с разными размерами и ценами;
- создание заказа и управление позициями;
- расчет итоговой стоимости с учетом скидок и доставки;
- промокоды `WELCOME10`, `SUMMER20`, `VIP30`;
- скидка постоянного клиента;
- happy hours с 14:00 до 17:00;
- жизненный цикл заказа через `OrderService`.

## Быстрый старт

2. Установка зависимостей:

```bash
python -m pip install -r requirements.txt
```

3. Выполненные задания находятся в `/student_tasks`:

- `student_tasks/features/order_management.feature`
- `student_tasks/step_defs/test_order_management.py`
- `student_tasks/exercise_property_based.py`

4. Как запустить тесты:

```bash
python -m pytest student_tasks/step_defs/test_order_management.py -v
python -m pytest student_tasks/exercise_property_based.py -v
```

## Выполненные задания

### `features/order_management.feature`

Дописаны BDD-сценарии для управления заказом:

- клиент удаляет позицию из заказа;
- клиент отменяет подтвержденный заказ;
- система запрещает изменить подтвержденный заказ.

### `step_defs/test_order_management.py`

Реализованы step definitions для сценариев из `order_management.feature`:

- добавление пиццы в существующий заказ;
- создание и подтверждение заказа на заданную сумму;
- удаление позиции по индексу;
- отмена заказа;
- проверка количества оставшихся позиций;
- проверка оставшейся пиццы;
- проверка статуса заказа;
- проверка сообщения об ошибке.

### `exercise_property_based.py`

Реализованы property-based тесты через Hypothesis:

- промокод не увеличивает итоговую сумму заказа;
- итоговая сумма непустого заказа всегда положительная;
- при сумме заказа от 1500 рублей доставка становится бесплатной;
- удаление позиции уменьшает сумму заказа без скидок.

## Результаты

```bash
# test_order_management.py
================================ 3 passed in 0.12s ================================
```

```bash
# exercise_property_based.py
================================ 4 passed in 0.21s ================================
```

## Дополнительные команды

```bash
# Все тесты проекта
python -m pytest

# Только эталонные BDD-тесты
python -m pytest tests/bdd/

# Только эталонные property-based тесты
python -m pytest tests/property/

# Property-based тесты со статистикой Hypothesis
python -m pytest tests/property/ --hypothesis-show-statistics
```


