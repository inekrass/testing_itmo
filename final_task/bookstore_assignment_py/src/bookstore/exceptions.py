"""Исключения предметной области магазина."""


class PricingError(ValueError):
    """Нарушение правил расчёта стоимости заказа."""


class OrderError(Exception):
    """Базовая ошибка при работе с заказом."""


class InvalidOrderStateError(OrderError):
    """Операция недопустима в текущем статусе заказа."""


class BookNotFoundError(LookupError):
    """Книга с указанным ISBN отсутствует в каталоге."""


class InventoryError(Exception):
    """Ошибка склада: нехватка товара или сбой сервиса остатков."""


class PaymentError(Exception):
    """Базовая ошибка платёжного шлюза."""


class PaymentDeclinedError(PaymentError):
    """Платёж отклонён (карта, лимиты, антифрод)."""


class CurrencyError(Exception):
    """Курс валюты недоступен или валюта не поддерживается."""
