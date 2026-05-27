"""
Тесты для модуля grading.py — параметризованная версия.
Практика 2: Параметризация и маркеры.

Демонстрирует:
- @pytest.mark.parametrize для компактных наборов тестов
- pytest.param с id для читаемого вывода
- Маркеры: smoke, boundary, negative
"""

import pytest
from grading import assign_grade


class TestAssignGradeParametrized:
    """Параметризованные тесты — компактная альтернатива отдельным методам."""

    # ── Все оценки без олимпиадного бонуса ────────────

    @pytest.mark.smoke
    @pytest.mark.parametrize(
        "score, expected_grade",
        [
            pytest.param(20, "F", id="EP_middle_F"),
            pytest.param(50, "D", id="EP_middle_D"),
            pytest.param(67, "C", id="EP_middle_C"),
            pytest.param(82, "B", id="EP_middle_B"),
            pytest.param(95, "A", id="EP_middle_A"),
        ],
    )
    def test_grade_equivalence_classes(self, score, expected_grade):
        """Середины классов эквивалентности (по одному из каждого класса)."""
        assert assign_grade(score) == expected_grade

    # ── Граничные значения ────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "score, expected_grade",
        [
            pytest.param(0, "F", id="BVA_min_valid"),
            pytest.param(39, "F", id="BVA_F_upper"),
            pytest.param(40, "D", id="BVA_D_lower"),
            pytest.param(59, "D", id="BVA_D_upper"),
            pytest.param(60, "C", id="BVA_C_lower"),
            pytest.param(74, "C", id="BVA_C_upper"),
            pytest.param(75, "B", id="BVA_B_lower"),
            pytest.param(89, "B", id="BVA_B_upper"),
            pytest.param(90, "A", id="BVA_A_lower"),
            pytest.param(100, "A", id="BVA_max_valid"),
        ],
    )
    def test_grade_boundaries(self, score, expected_grade):
        """Граничные значения на стыках классов."""
        assert assign_grade(score) == expected_grade

    # ── Олимпиадный бонус ─────────────────────────────

    @pytest.mark.parametrize(
        "score, expected_grade",
        [
            pytest.param(20, "D", id="olympiad_F_to_D"),
            pytest.param(50, "C", id="olympiad_D_to_C"),
            pytest.param(67, "B", id="olympiad_C_to_B"),
            pytest.param(82, "A", id="olympiad_B_to_A"),
            pytest.param(95, "A", id="olympiad_A_stays_A"),
            pytest.param(100, "A", id="olympiad_max_stays_A"),
        ],
    )
    def test_grade_with_olympiad_bonus(self, score, expected_grade):
        """Олимпиадный бонус: +1 к оценке (A → A без изменения)."""
        assert assign_grade(score, is_olympiad_winner=True) == expected_grade

    # ── Невалидные входные данные ─────────────────────

    @pytest.mark.negative
    @pytest.mark.parametrize(
        "invalid_score, exception_type, match_text",
        [
            pytest.param(-1, ValueError, "от 0 до 100", id="negative_score"),
            pytest.param(-100, ValueError, "от 0 до 100", id="large_negative"),
            pytest.param(101, ValueError, "от 0 до 100", id="over_100"),
            pytest.param(999, ValueError, "от 0 до 100", id="large_positive"),
            pytest.param(85.5, TypeError, "целым числом", id="float_score"),
            pytest.param("abc", TypeError, "целым числом", id="string_score"),
            pytest.param(None, TypeError, "целым числом", id="none_score"),
        ],
    )
    def test_invalid_input_raises(self, invalid_score, exception_type, match_text):
        """Невалидные данные вызывают исключения с понятным сообщением."""
        with pytest.raises(exception_type, match=match_text):
            assign_grade(invalid_score)
