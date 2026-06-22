"""
Бизнес-домен «Пиццерия» — для демонстрации BDD-тестов.

Сценарии написаны на человеческом языке, понятны менеджерам и аналитикам.
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from decimal import Decimal
from enum import Enum


class PizzaSize(str, Enum):
    SMALL = "SMALL"        # 25 см
    MEDIUM = "MEDIUM"      # 30 см
    LARGE = "LARGE"        # 35 см


class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    COOKING = "COOKING"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Pizza:
    """Пицца из каталога."""
    name: str
    base_price: Decimal       # цена за размер MEDIUM
    is_vegetarian: bool = False


@dataclass
class OrderItem:
    """Позиция в заказе."""
    pizza: Pizza
    size: PizzaSize
    quantity: int = 1

    @property
    def line_total(self) -> Decimal:
        """Стоимость позиции с учётом размера и количества."""
        size_multiplier = {
            PizzaSize.SMALL: Decimal("0.8"),
            PizzaSize.MEDIUM: Decimal("1.0"),
            PizzaSize.LARGE: Decimal("1.3"),
        }
        return self.pizza.base_price * size_multiplier[self.size] * self.quantity


@dataclass
class Customer:
    name: str
    phone: str
    is_loyal: bool = False           # участник программы лояльности
    orders_completed: int = 0


@dataclass
class Order:
    """Заказ пиццы."""
    customer: Customer
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.DRAFT
    promo_code: str | None = None
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def subtotal(self) -> Decimal:
        """Сумма позиций без скидок."""
        return sum((item.line_total for item in self.items), Decimal("0"))

    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0


# ═════════════════════════════════════════════════════════════════
#  Сервис расчёта стоимости
# ═════════════════════════════════════════════════════════════════


class PricingService:
    """Расчёт итоговой стоимости заказа с учётом скидок и доставки."""

    DELIVERY_FEE = Decimal("200")
    FREE_DELIVERY_THRESHOLD = Decimal("1500")
    LOYAL_DISCOUNT = Decimal("0.10")
    HAPPY_HOUR_START = time(14, 0)
    HAPPY_HOUR_END = time(17, 0)
    HAPPY_HOUR_DISCOUNT = Decimal("0.15")

    PROMO_CODES = {
        "WELCOME10": Decimal("0.10"),
        "SUMMER20": Decimal("0.20"),
        "VIP30": Decimal("0.30"),
    }

    def calculate_total(self, order: Order, now: datetime | None = None) -> Decimal:
        """
        Итоговая стоимость = subtotal − все скидки + доставка (если применима).

        Скидки применяются последовательно, максимум одна (выбирается лучшая).
        """
        if order.is_empty:
            raise ValueError("Невозможно рассчитать стоимость пустого заказа")

        subtotal = order.subtotal

        # Подбираем лучшую скидку
        best_discount = Decimal("0")

        if order.customer.is_loyal:
            best_discount = max(best_discount, self.LOYAL_DISCOUNT)

        if order.promo_code and order.promo_code in self.PROMO_CODES:
            best_discount = max(best_discount, self.PROMO_CODES[order.promo_code])

        if now is None:
            now = datetime.now()
        current_time = now.time()
        if self.HAPPY_HOUR_START <= current_time < self.HAPPY_HOUR_END:
            best_discount = max(best_discount, self.HAPPY_HOUR_DISCOUNT)

        discount_amount = subtotal * best_discount
        after_discount = subtotal - discount_amount

        # Доставка
        delivery = Decimal("0") if after_discount >= self.FREE_DELIVERY_THRESHOLD else self.DELIVERY_FEE

        return after_discount + delivery

    def estimate_discount(self, order: Order, now: datetime | None = None) -> Decimal:
        """Сколько денег сэкономлено благодаря скидкам."""
        subtotal = order.subtotal
        total = self.calculate_total(order, now)
        delivery = Decimal("0") if (total - self.DELIVERY_FEE) >= 0 and (
            subtotal >= self.FREE_DELIVERY_THRESHOLD
        ) else self.DELIVERY_FEE
        return subtotal - (total - delivery)


# ═════════════════════════════════════════════════════════════════
#  Сервис управления заказами
# ═════════════════════════════════════════════════════════════════


class OrderService:
    """Управление жизненным циклом заказа."""

    def __init__(self, pricing: PricingService):
        self._pricing = pricing

    def add_item(self, order: Order, pizza: Pizza, size: PizzaSize, quantity: int = 1):
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным")
        if order.status < OrderStatus.DRAFT:
            raise ValueError(
                f"Нельзя изменить заказ в статусе {order.status.value}"
            )
        order.items.append(OrderItem(pizza, size, quantity))

    def remove_item(self, order: Order, index: int):
        if order.status != OrderStatus.DRAFT:
            raise ValueError("Нельзя изменить подтверждённый заказ")
        if index < 0 or index >= len(order.items):
            raise IndexError(f"Нет позиции с индексом {index}")
        order.items.pop(index)

    def apply_promo(self, order: Order, code: str):
        if order.status != OrderStatus.DRAFT:
            raise ValueError("Промокод можно применить только к черновику")
        if code not in PricingService.PROMO_CODES:
            raise ValueError(f"Неизвестный промокод: {code}")
        order.promo_code = code

    def confirm(self, order: Order, now: datetime | None = None) -> Decimal:
        """Подтвердить заказ. Возвращает итоговую сумму к оплате."""
        if order.is_empty:
            raise ValueError("Нельзя подтвердить пустой заказ")
        if order.status != OrderStatus.DRAFT:
            raise ValueError(f"Заказ уже в статусе {order.status.value}")

        total = self._pricing.calculate_total(order, now)
        order.status = OrderStatus.CONFIRMED
        return total

    def cancel(self, order: Order):
        if order.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
            raise ValueError(f"Нельзя отменить заказ в статусе {order.status.value}")
        order.status = OrderStatus.CANCELLED


# ═════════════════════════════════════════════════════════════════
#  Каталог пицц (для удобства в тестах)
# ═════════════════════════════════════════════════════════════════

MARGHERITA = Pizza("Маргарита", Decimal("450"), is_vegetarian=True)
PEPPERONI = Pizza("Пепперони", Decimal("550"))
QUATTRO_FORMAGGI = Pizza("Четыре сыра", Decimal("650"), is_vegetarian=True)
HAWAIIAN = Pizza("Гавайская", Decimal("600"))

CATALOG = {
    "Маргарита": MARGHERITA,
    "Пепперони": PEPPERONI,
    "Четыре сыра": QUATTRO_FORMAGGI,
    "Гавайская": HAWAIIAN,
}
