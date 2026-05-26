"""
Модуль расчёта скидок.
Практика 1: Тест-дизайн и первые тесты.
"""


def calculate_discount(price: float, customer_type: str, is_holiday: bool) -> float:
    """
    Рассчитывает скидку на товар.

    Правила:
    - "regular": 0% скидка (5% в праздники)
    - "premium": 10% скидка (15% в праздники)
    - "vip": 20% скидка (25% в праздники)
    - Цена должна быть > 0
    - Максимальная скидка не может превышать 500 руб.

    Args:
        price: Цена товара (положительное число).
        customer_type: Тип клиента ("regular", "premium", "vip").
        is_holiday: Праздничный день или нет.

    Returns:
        Размер скидки в рублях.

    Raises:
        ValueError: Если цена <= 0 или неизвестный тип клиента.
    """
    if price <= 0:
        raise ValueError("Цена должна быть положительной")

    discounts = {
        "regular": (0, 5),
        "premium": (10, 15),
        "vip": (20, 25),
    }

    if customer_type not in discounts:
        raise ValueError(f"Неизвестный тип клиента: {customer_type}")

    normal, holiday = discounts[customer_type]
    rate = holiday if is_holiday else normal
    discount = price * rate / 100
    return min(discount, 500)
