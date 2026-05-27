#Отчет

**Выполнил**: Некрасов Богдан
**Группа**: Р4150

## Быстрый старт

1. Установка зависимостей:

`pip install -r requirements-test.txt`

2. Выполненные задания в `/student_tasks`

3. Как запустить тесты:

```bash
pytest student_tasks/exercise_1_grading.py -v
pytest student_tasks/exercise_2_shipping.py -v
pytest student_tasks/exercise_3_library.py -v
pytest student_tasks/exercise_3_library.py -m smoke -v # Запуск смоук тестов в exercise_3_library.py
pytest student_tasks/homework_cart.py -v
python3 -m pytest student_tasks/homework_cart.py --cov=cart --cov-report=term-missing # покрытие в homework_cart.py
```



## Результаты:

```bash
#exercise_1_grading.py
========================= 21 passed in 0.03s ==========================
```

```bash
#exercise_2_shipping.py
===================== 3 failed, 3 passed in 0.10s =====================
```

```bash
#exercise_3_library.py
========================= 11 passed in 0.04s ==========================

#Smoke
=================== 2 passed, 9 deselected in 0.02s ===================
```

```bash
#homework_cart.py
========================= 16 passed in 0.05s ==========================

#Покрытие
Required test coverage of 85.0% reached. Total coverage: 100.00%
========================= 16 passed in 0.06s ==========================
```