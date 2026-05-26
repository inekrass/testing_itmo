"""
СТАРТОВЫЙ ФАЙЛ — Занятие 1, Упражнение 1.

Задача: дописать тесты для функции assign_grade из src/grading.py.
Эталонное решение: tests/unit/test_grading.py

Как запустить:
    pytest student_tasks/exercise_1_grading.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from grading import assign_grade


class TestAssignGradePositive:
    """Позитивные сценарии: середины классов эквивалентности."""

    def test_score_20_returns_F(self):
        """TC-01: Середина класса F (0–39)."""
        # Arrange
        score = 20
        # Act
        result = assign_grade(score)
        # Assert
        assert result == "F"

    def test_score_50_returns_D(self):
        """TC-02: Середина класса D (40–59)."""
        score = 50
        result = assign_grade(score)
        assert result == "D"

    def test_score_67_returns_C(self):
        """TC-03: Середина класса C (60–74)."""
        score = 67
        result = assign_grade(score)
        assert result == "C"

    def test_score_82_returns_B(self):
        """TC-04: Середина класса B (75–89)."""
        score = 82
        result = assign_grade(score)
        assert result == "B"

    def test_score_95_returns_A(self):
        """TC-05: Середина класса A (90–100)."""
        score = 95
        result = assign_grade(score)
        assert result == "A"


class TestAssignGradeBoundary:
    """Граничные значения на стыках классов."""

    def test_F_D_boundary_below(self):
        """TC-10: 39 — последнее значение для F."""
        assert assign_grade(39) == "F"

    def test_F_D_boundary_above(self):
        """TC-11: 40 — первое значение для D."""
        assert assign_grade(40) == "D"

    # TODO: добавьте тесты для границ D/C (59, 60), C/B (74, 75), B/A (89, 90)
    def test_D_C_boundary_below(self):
        """TC-12: 59 — последнее значение для D."""
        assert assign_grade(59) == "D"

    def test_D_C_boundary_above(self):
        """TC-13: 60 — первое значение для C."""
        assert assign_grade(60) == "C"

    def test_C_B_boundary_below(self):
        """TC-14: 74 — последнее значение для C."""
        assert assign_grade(74) == "C"

    def test_C_B_boundary_above(self):
        """TC-15: 75 — первое значение для B."""
        assert assign_grade(75) == "B"

    def test_B_A_boundary_below(self):
        """TC-16: 89 — последнее значение для B."""
        assert assign_grade(89) == "B"

    def test_B_A_boundary_above(self):
        """TC-17: 90 — первое значение для A."""
        assert assign_grade(90) == "A"


class TestAssignGradeNegative:
    """Негативные сценарии."""

    def test_negative_score_raises(self):
        """TC-08: Отрицательный балл → ValueError."""
        with pytest.raises(ValueError, match="от 0 до 100"):
            assign_grade(-1)

    def test_over_100_raises(self):
        """TC-09: Больше 100 → ValueError."""
        with pytest.raises(ValueError, match="от 0 до 100"):
            assign_grade(101)

    def test_float_raises_type_error(self):
        """TC-23: Дробное число → TypeError."""
        with pytest.raises(TypeError, match="целым числом"):
            assign_grade(85.5)


class TestAssignGradeOlympiad:
    """Олимпиадный бонус +1 к оценке."""

    def test_olympiad_F_becomes_D(self):
        """TC-18: Олимпиадник с F → D."""
        assert assign_grade(20, is_olympiad_winner=True) == "D"

    # TODO: добавьте тесты:
    #   - олимпиадник с D → C
    #   - олимпиадник с C → B
    #   - олимпиадник с B → A
    #   - олимпиадник с A → A (не повышается)
    def test_olympiad_D_becomes_C(self):
        """TC-19: Олимпиадник с D → C."""
        assert assign_grade(50, is_olympiad_winner=True) == "C"

    def test_olympiad_C_becomes_B(self):
        """TC-20: Олимпиадник с C → B."""
        assert assign_grade(67, is_olympiad_winner=True) == "B"

    def test_olympiad_B_becomes_A(self):
        """TC-21: Олимпиадник с B → A."""
        assert assign_grade(82, is_olympiad_winner=True) == "A"

    def test_olympiad_A_stays_A(self):
        """TC-22: Олимпиадник с A → A."""
        assert assign_grade(95, is_olympiad_winner=True) == "A"
