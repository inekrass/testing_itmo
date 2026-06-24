"""Интерфейсы внешних зависимостей магазина."""

from bookstore.interfaces.book_repository import BookRepository
from bookstore.interfaces.clock import Clock
from bookstore.interfaces.currency_converter import CurrencyConverter
from bookstore.interfaces.inventory_service import InventoryService
from bookstore.interfaces.ml_recommendation_provider import MLRecommendationProvider
from bookstore.interfaces.notification_service import NotificationService
from bookstore.interfaces.payment_gateway import (
    PaymentGateway,
    PaymentResult,
    PaymentStatus,
)

__all__ = [
    "BookRepository",
    "Clock",
    "CurrencyConverter",
    "InventoryService",
    "MLRecommendationProvider",
    "NotificationService",
    "PaymentGateway",
    "PaymentResult",
    "PaymentStatus",
]
