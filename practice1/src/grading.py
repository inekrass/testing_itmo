"""
Модуль оценивания студентов.
Практика 1: Тест-дизайн и первые тесты.
"""


def assign_grade(score: int, is_olympiad_winner: bool = False) -> str:
    """
    Определяет оценку студента по набранным баллам.

    Правила:
    - score < 0 или score > 100: ValueError
    - 90–100: "A"
    - 75–89:  "B"
    - 60–74:  "C"
    - 40–59:  "D"
    - 0–39:   "F"
    - Олимпиадники (is_olympiad_winner=True) получают +1 к оценке
      (F→D, D→C, C→B, B→A, A→A). Бонус не применяется при score < 0 или > 100.

    Args:
        score: Балл от 0 до 100 (целое число).
        is_olympiad_winner: Является ли студент победителем олимпиады.

    Returns:
        Оценка: "A", "B", "C", "D" или "F".

    Raises:
        TypeError: Если score не является целым числом.
        ValueError: Если score вне диапазона 0–100.
    """
    if not isinstance(score, int):
        raise TypeError("Балл должен быть целым числом")
    if score < 0 or score > 100:
        raise ValueError(f"Балл должен быть от 0 до 100, получено: {score}")

    grades = ["F", "D", "C", "B", "A"]

    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    if is_olympiad_winner and grade != "A":
        idx = grades.index(grade)
        grade = grades[idx + 1]

    return grade
