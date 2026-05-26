"""
СТАРТОВЫЙ ФАЙЛ — Занятие 1, Challenge «Найди баг».

Задача:
    В модуле src/shipping.py есть НАМЕРЕННЫЙ дефект.
    Напишите тесты согласно спецификации — один из них упадёт.
    Опишите найденный баг в комментарии в конце файла.

Спецификация (краткая):
    Международная доставка:
        - до 1 кг: 500 руб.
        - 1–20 кг: 500 + 150 руб. за каждый кг сверх 1
        - > 20 кг: ValueError

Как запустить:
    pytest student_tasks/exercise_2_shipping.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shipping import calculate_shipping


class TestInternationalShipping:
    """Международная доставка — здесь должен быть обнаружен баг."""

    def test_light_package_under_1kg(self):
        """Посылка 0.5 кг → 500 руб."""
        assert calculate_shipping(0.5, "international") == 500

    def test_exactly_1kg(self):
        """1 кг → 500 руб. (ещё фиксированный тариф)."""
        assert calculate_shipping(1.0, "international") == 500

    def test_5kg_package(self):
        """
        Посылка 5 кг по спецификации:
            500 + 150 × (5 - 1) = 500 + 600 = 1100 руб.
        """
        assert calculate_shipping(5.0, "international") == 1100

    def test_10kg_package(self):
        """
        Посылка 10 кг:
            500 + 150 × 9 = 1850 руб.
        """
        assert calculate_shipping(10.0, "international") == 1850

    def test_max_20kg(self):
        """
        Граница — посылка 20 кг:
            500 + 150 × 19 = 3350 руб.
        """
        assert calculate_shipping(20.0, "international") == 3350

    def test_over_20kg_raises(self):
        """Больше 20 кг → ValueError."""
        with pytest.raises(ValueError, match="20 кг"):
            calculate_shipping(20.1, "international")


# ════════════════════════════════════════════════════════════════
# ОПИСАНИЕ БАГА (заполнить после обнаружения)
# ════════════════════════════════════════════════════════════════
#
# Файл и строка: src/shipping.py, строка 58
# Ожидаемое поведение: для международной доставки весом больше 1 кг
#     стоимость считается как 500 + 150 * (weight_kg - 1).
# Фактическое поведение: в формуле используется 100 руб. за каждый кг
#     сверх 1 кг, поэтому стоимость получается ниже спецификации.
# Шаги воспроизведения: вызвать calculate_shipping(5.0, "international").
#     Ожидается 1100, фактически функция возвращает 900.
# Предлагаемое исправление: заменить 100 на 150 в формуле расчета
#     международной доставки.
#
# ════════════════════════════════════════════════════════════════
