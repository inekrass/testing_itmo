"""
Модуль расчёта стоимости доставки.
Практика 1: Задание «Найди баг».

ВНИМАНИЕ: В этом модуле содержится намеренный дефект.
"""


def calculate_shipping(
    weight_kg: float, destination: str, is_express: bool = False
) -> float:
    """
    Рассчитывает стоимость доставки.

    Тарифы:
    - Внутри страны ("domestic"):
        - до 1 кг: 200 руб.
        - 1–10 кг: 200 + 50 руб. за каждый кг сверх 1
        - 10–30 кг: 200 + 450 + 30 руб. за каждый кг сверх 10
        - > 30 кг: отказ (ValueError)
    - Международная ("international"):
        - до 1 кг: 500 руб.
        - 1–20 кг: 500 + 150 руб. за каждый кг сверх 1
        - > 20 кг: отказ (ValueError)
    - Экспресс: ×2 от итоговой стоимости
    - Вес ≤ 0: ValueError

    Args:
        weight_kg: Вес посылки в килограммах.
        destination: Направление ("domestic" или "international").
        is_express: Экспресс-доставка (×2 от стоимости).

    Returns:
        Стоимость доставки в рублях.

    Raises:
        ValueError: Если вес <= 0, превышен лимит или неизвестное направление.
    """
    if weight_kg <= 0:
        raise ValueError("Вес должен быть положительным")

    if destination == "domestic":
        if weight_kg > 30:
            raise ValueError("Максимальный вес для внутренней доставки: 30 кг")
        if weight_kg <= 1:
            cost = 200
        elif weight_kg <= 10:
            cost = 200 + 50 * (weight_kg - 1)
        else:
            cost = 200 + 450 + 30 * (weight_kg - 10)

    elif destination == "international":
        if weight_kg > 20:
            raise ValueError("Максимальный вес для международной доставки: 20 кг")
        if weight_kg <= 1:
            cost = 500
        elif weight_kg <= 20:
            # БАГ: по спецификации должно быть 150, а не 100
            cost = 500 + 100 * (weight_kg - 1)
    else:
        raise ValueError(f"Неизвестное направление: {destination}")

    if is_express:
        cost *= 2

    return cost
