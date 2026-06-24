from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from bookstore.exceptions import PricingError
from bookstore.models.book import BookCategory
from bookstore.models.cart_item import CartItem
from bookstore.models.customer import CustomerTier
from bookstore.models.order import Order


# Скидка по уровню покупателя.
TIER_DISCOUNTS: dict[CustomerTier, Decimal] = {
    CustomerTier.BRONZE: Decimal("0.00"),
    CustomerTier.SILVER: Decimal("0.05"),
    CustomerTier.GOLD: Decimal("0.10"),
}

# Доступные промокоды и их скидка.
PROMO_CODES: dict[str, Decimal] = {
    "WELCOME15": Decimal("0.15"),
    "SUMMER20": Decimal("0.20"),
    "STUDENT25": Decimal("0.25"),
}

# Промокод STUDENT25 действует только на учебники.
STUDENT_PROMO_CATEGORY = BookCategory.TEXTBOOK

# Доставка.
BASE_DELIVERY_FEE = Decimal("300")
FREE_DELIVERY_THRESHOLD = Decimal("3000")
DELIVERY_PER_100G_OVER_1KG = Decimal("1")

# НДС на книги.
VAT_RATE = Decimal("0.10")

# Ограничения заказа.
MAX_QUANTITY_PER_ITEM = 20
ORDER_LIMIT_GOLD = Decimal("500000")
ORDER_LIMIT_REGULAR = Decimal("100000")

# Период распродажи «чёрная пятница» (включительно) и её скидка.
BLACK_FRIDAY_START = (11, 24)
BLACK_FRIDAY_END = (11, 30)
BLACK_FRIDAY_DISCOUNT = Decimal("0.30")


@dataclass
class PriceBreakdown:
    """Детализация итоговой стоимости заказа по составляющим."""

    subtotal: Decimal
    discountable_subtotal: Decimal
    non_discountable_subtotal: Decimal
    discount_rate: Decimal
    discount_amount: Decimal
    subtotal_after_discount: Decimal
    delivery_fee: Decimal
    vat: Decimal
    total: Decimal


class PricingService:
    """Расчёт стоимости заказа: скидки, доставка и налог."""

    def calculate_order_total(
        self,
        order: Order,
        moment: Optional[datetime] = None,
    ) -> PriceBreakdown:
        """Посчитать полную стоимость заказа с разбивкой по составляющим."""
        self.validate_order(order)

        if moment is None:
            moment = datetime.now()

        discountable = self._discountable_subtotal(order.items)
        non_discountable = self._non_discountable_subtotal(order.items)
        subtotal = discountable + non_discountable

        discount_rate = self.best_discount_rate(order, moment)
        discount_amount = (discountable * discount_rate).quantize(Decimal("0.01"))
        subtotal_after_discount = subtotal - discount_amount

        delivery_fee = self.calculate_delivery_fee(order.items, subtotal_after_discount)
        vat = self.calculate_vat(subtotal_after_discount)
        total = subtotal_after_discount + delivery_fee + vat

        return PriceBreakdown(
            subtotal=subtotal,
            discountable_subtotal=discountable,
            non_discountable_subtotal=non_discountable,
            discount_rate=discount_rate,
            discount_amount=discount_amount,
            subtotal_after_discount=subtotal_after_discount,
            delivery_fee=delivery_fee,
            vat=vat,
            total=total,
        )

    def best_discount_rate(self, order: Order, moment: datetime) -> Decimal:
        """Выбрать наибольшую из применимых скидок: по уровню, по промокоду
        и по распродаже."""
        tier_discount = TIER_DISCOUNTS[order.customer.tier]
        promo_discount = self.applicable_promo_discount(order.promo_code, order.items)
        black_friday = (
            BLACK_FRIDAY_DISCOUNT if self.is_black_friday(moment) else Decimal("0")
        )
        return max(tier_discount, promo_discount, black_friday)

    def applicable_promo_discount(
        self,
        promo_code: Optional[str],
        items: list[CartItem],
    ) -> Decimal:
        """Скидка по промокоду. STUDENT25 действует, только если все позиции —
        учебники. Для неизвестного кода бросает PricingError."""
        if promo_code is None:
            return Decimal("0")
        if promo_code not in PROMO_CODES:
            raise PricingError(f"Неизвестный промокод: {promo_code}")

        base = PROMO_CODES[promo_code]
        if promo_code == "STUDENT25":
            all_textbooks = all(
                item.book.category == STUDENT_PROMO_CATEGORY for item in items
            )
            return base if all_textbooks else Decimal("0")
        return base

    def calculate_delivery_fee(
        self,
        items: list[CartItem],
        subtotal_after_discount: Decimal,
    ) -> Decimal:
        """Стоимость доставки. Бесплатно при наличии детских книг или при сумме
        заказа не ниже порога; иначе базовая ставка плюс надбавка за вес свыше 1 кг."""
        if self._has_children_books(items):
            return Decimal("0")
        if subtotal_after_discount >= FREE_DELIVERY_THRESHOLD:
            return Decimal("0")

        weight = sum(item.book.weight_grams * item.quantity for item in items)
        fee = BASE_DELIVERY_FEE
        if weight > 1000:
            extra_blocks = (weight - 1000) // 100
            fee += DELIVERY_PER_100G_OVER_1KG * Decimal(extra_blocks)
        return fee

    def calculate_vat(self, amount: Decimal) -> Decimal:
        """НДС на книги от переданной суммы."""
        return (amount * VAT_RATE).quantize(Decimal("0.01"))

    def validate_order(self, order: Order) -> None:
        """Проверить заказ перед расчётом: непустой, покупатель не заблокирован,
        количество в допустимых пределах, сумма в рамках лимита уровня."""
        if order.is_empty:
            raise PricingError("Заказ не может быть пустым")
        if order.customer.is_blocked:
            raise PricingError("Покупатель заблокирован")

        for item in order.items:
            if item.quantity <= 0:
                raise PricingError(
                    f"Количество должно быть положительным: {item.book.isbn}"
                )
            if item.quantity > MAX_QUANTITY_PER_ITEM:
                raise PricingError(
                    f"Превышен лимит количества ({MAX_QUANTITY_PER_ITEM}) "
                    f"для {item.book.isbn}"
                )

        limit = (
            ORDER_LIMIT_GOLD
            if order.customer.tier == CustomerTier.GOLD
            else ORDER_LIMIT_REGULAR
        )
        if order.subtotal > limit:
            raise PricingError(f"Сумма заказа {order.subtotal} превышает лимит {limit}")

    @staticmethod
    def is_black_friday(moment: datetime) -> bool:
        """Попадает ли момент в период распродажи «чёрная пятница»."""
        start = BLACK_FRIDAY_START
        end = BLACK_FRIDAY_END
        return start <= (moment.month, moment.day) <= end

    @staticmethod
    def _discountable_subtotal(items: list[CartItem]) -> Decimal:
        """Сумма позиций, к которым применимы скидки (все, кроме коллекционных)."""
        return sum(
            (item.line_total for item in items if item.book.category != BookCategory.RARE),
            Decimal("0"),
        )

    @staticmethod
    def _non_discountable_subtotal(items: list[CartItem]) -> Decimal:
        """Сумма коллекционных книг, на которые скидки не распространяются."""
        return sum(
            (item.line_total for item in items if item.book.category == BookCategory.RARE),
            Decimal("0"),
        )

    @staticmethod
    def _has_children_books(items: list[CartItem]) -> bool:
        """Есть ли в заказе хотя бы одна детская книга."""
        return any(item.book.category == BookCategory.CHILDREN for item in items)
