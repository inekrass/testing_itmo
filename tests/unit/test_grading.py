"""
Тесты для модуля grading.py
Практика 1: Тест-дизайн и первые тесты.

Демонстрирует:
- Паттерн AAA (Arrange — Act — Assert)
- Позитивные, негативные и граничные тесты
- pytest.raises для проверки исключений
"""

import pytest
from grading import assign_grade


# ══════════════════════════════════════════════════════════
#  ПОЗИТИВНЫЕ СЦЕНАРИИ
#  Проверяем корректную работу при валидных входных данных.
# ══════════════════════════════════════════════════════════


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
        # Arrange
        score = 50
        # Act
        result = assign_grade(score)
        # Assert
        assert result == "D"

    def test_score_67_returns_C(self):
        """TC-03: Середина класса C (60–74)."""
        # Arrange
        score = 67
        # Act
        result = assign_grade(score)
        # Assert
        assert result == "C"

    def test_score_82_returns_B(self):
        """TC-04: Середина класса B (75–89)."""
        # Arrange
        score = 82
        # Act
        result = assign_grade(score)
        # Assert
        assert result == "B"

    def test_score_95_returns_A(self):
        """TC-05: Середина класса A (90–100)."""
        # Arrange
        score = 95
        # Act
        result = assign_grade(score)
        # Assert
        assert result == "A"


# ══════════════════════════════════════════════════════════
#  ГРАНИЧНЫЕ ЗНАЧЕНИЯ
#  Проверяем стыки между классами эквивалентности.
# ══════════════════════════════════════════════════════════


class TestAssignGradeBoundary:
    """Граничные значения: тестируем переходы между оценками."""

    def test_lower_valid_boundary_0(self):
        """TC-06: Минимальный валидный балл → F."""
        assert assign_grade(0) == "F"

    def test_upper_valid_boundary_100(self):
        """TC-07: Максимальный валидный балл → A."""
        assert assign_grade(100) == "A"

    def test_F_D_boundary_below(self):
        """TC-10: 39 — последнее значение для F."""
        assert assign_grade(39) == "F"

    def test_F_D_boundary_above(self):
        """TC-11: 40 — первое значение для D."""
        assert assign_grade(40) == "D"

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


# ══════════════════════════════════════════════════════════
#  НЕГАТИВНЫЕ СЦЕНАРИИ
#  Проверяем обработку невалидных входных данных.
# ══════════════════════════════════════════════════════════


class TestAssignGradeNegative:
    """Негативные сценарии: невалидные входные данные."""

    def test_negative_score_raises_value_error(self):
        """TC-08: Отрицательный балл → ValueError."""
        # Arrange + Act + Assert
        with pytest.raises(ValueError, match="от 0 до 100"):
            assign_grade(-1)

    def test_over_100_raises_value_error(self):
        """TC-09: Балл больше 100 → ValueError."""
        with pytest.raises(ValueError, match="от 0 до 100"):
            assign_grade(101)

    def test_large_negative_raises_value_error(self):
        """TC-25: Большое отрицательное число → ValueError."""
        with pytest.raises(ValueError):
            assign_grade(-1000)

    def test_large_positive_raises_value_error(self):
        """Очень большое число → ValueError."""
        with pytest.raises(ValueError):
            assign_grade(999)

    def test_float_raises_type_error(self):
        """TC-23: Дробное число → TypeError."""
        with pytest.raises(TypeError, match="целым числом"):
            assign_grade(85.5)

    def test_string_raises_type_error(self):
        """TC-24: Строка → TypeError."""
        with pytest.raises(TypeError, match="целым числом"):
            assign_grade("abc")

    def test_none_raises_type_error(self):
        """None → TypeError."""
        with pytest.raises(TypeError):
            assign_grade(None)

    def test_bool_treated_as_int(self):
        """
        bool — подкласс int в Python.
        True == 1 → "F", False == 0 → "F".
        Это не баг, а особенность Python. Полезно знать.
        """
        # bool является подклассом int, поэтому isinstance(True, int) == True
        assert assign_grade(True) == "F"   # True == 1
        assert assign_grade(False) == "F"  # False == 0


# ══════════════════════════════════════════════════════════
#  ОЛИМПИАДНЫЙ БОНУС
#  Проверяем повышение оценки для олимпиадников.
# ══════════════════════════════════════════════════════════


class TestAssignGradeOlympiad:
    """Тесты олимпиадного бонуса (+1 к оценке)."""

    def test_olympiad_F_becomes_D(self):
        """TC-18: Олимпиадник с F (score=20) → D."""
        # Arrange
        score = 20
        # Act
        result = assign_grade(score, is_olympiad_winner=True)
        # Assert
        assert result == "D"

    def test_olympiad_D_becomes_C(self):
        """TC-19: Олимпиадник с D (score=50) → C."""
        assert assign_grade(50, is_olympiad_winner=True) == "C"

    def test_olympiad_C_becomes_B(self):
        """TC-20: Олимпиадник с C (score=67) → B."""
        assert assign_grade(67, is_olympiad_winner=True) == "B"

    def test_olympiad_B_becomes_A(self):
        """TC-21: Олимпиадник с B (score=82) → A."""
        assert assign_grade(82, is_olympiad_winner=True) == "A"

    def test_olympiad_A_stays_A(self):
        """TC-22: Олимпиадник с A (score=95) → A (потолок)."""
        assert assign_grade(95, is_olympiad_winner=True) == "A"

    def test_olympiad_boundary_39_F_to_D(self):
        """Олимпиадник на границе F (39) → D."""
        assert assign_grade(39, is_olympiad_winner=True) == "D"

    def test_olympiad_boundary_40_D_to_C(self):
        """Олимпиадник на границе D (40) → C."""
        assert assign_grade(40, is_olympiad_winner=True) == "C"

    def test_olympiad_boundary_90_A_stays_A(self):
        """Олимпиадник на границе A (90) → A (без повышения)."""
        assert assign_grade(90, is_olympiad_winner=True) == "A"

    def test_olympiad_100_A_stays_A(self):
        """Олимпиадник с максимальным баллом → A."""
        assert assign_grade(100, is_olympiad_winner=True) == "A"
