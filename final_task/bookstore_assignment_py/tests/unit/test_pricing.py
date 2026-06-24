from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from bookstore.exceptions import PricingError
from bookstore.models.book import BookCategory
from bookstore.models.customer import CustomerTier
from bookstore.pricing import PricingService

from tests.conftest import make_item, make_order


REGULAR_DAY = datetime(2025, 10, 1, 12, 0, 0)


def test_silver_order_matches_requirements_example() -> None:
    order = make_order(
        make_item(price="1500", quantity=2, weight_grams=600),
        tier=CustomerTier.SILVER,
    )

    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.subtotal == Decimal("3000")
    assert result.discount_rate == Decimal("0.05")
    assert result.discount_amount == Decimal("150.00")
    assert result.subtotal_after_discount == Decimal("2850.00")
    assert result.delivery_fee == Decimal("302")
    assert result.vat == Decimal("285.00")
    assert result.total == Decimal("3437.00")


def test_gold_order_gets_free_delivery_when_discounted_subtotal_reaches_threshold() -> None:
    order = make_order(make_item(price="5000"), tier=CustomerTier.GOLD)

    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.discount_rate == Decimal("0.10")
    assert result.discount_amount == Decimal("500.00")
    assert result.subtotal_after_discount == Decimal("4500.00")
    assert result.delivery_fee == Decimal("0")
    assert result.vat == Decimal("450.00")
    assert result.total == Decimal("4950.00")


def test_welcome_promo_beats_bronze_discount() -> None:
    order = make_order(make_item(price="2000"), promo_code="WELCOME15")

    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.discount_rate == Decimal("0.15")
    assert result.discount_amount == Decimal("300.00")
    assert result.subtotal_after_discount == Decimal("1700.00")


def test_student_promo_applies_only_when_all_items_are_textbooks() -> None:
    service = PricingService()
    textbook_order = make_order(
        make_item(category=BookCategory.TEXTBOOK),
        make_item(isbn="9780000000002", category=BookCategory.TEXTBOOK),
        promo_code="STUDENT25",
    )
    mixed_order = make_order(
        make_item(category=BookCategory.TEXTBOOK),
        make_item(isbn="9780000000002", category=BookCategory.FICTION),
        promo_code="STUDENT25",
    )

    assert service.calculate_order_total(textbook_order, REGULAR_DAY).discount_rate == Decimal("0.25")
    assert service.calculate_order_total(mixed_order, REGULAR_DAY).discount_rate == Decimal("0")


def test_black_friday_discount_beats_tier_and_promo() -> None:
    order = make_order(
        make_item(price="1000"),
        tier=CustomerTier.GOLD,
        promo_code="SUMMER20",
    )

    result = PricingService().calculate_order_total(order, datetime(2025, 11, 24))

    assert result.discount_rate == Decimal("0.30")
    assert result.discount_amount == Decimal("300.00")


def test_black_friday_period_is_inclusive() -> None:
    service = PricingService()

    assert service.is_black_friday(datetime(2025, 11, 24))
    assert service.is_black_friday(datetime(2025, 11, 30, 23, 59, 59))
    assert not service.is_black_friday(datetime(2025, 11, 23, 23, 59, 59))
    assert not service.is_black_friday(datetime(2025, 12, 1))


def test_rare_books_are_not_discounted() -> None:
    order = make_order(
        make_item(price="1000", category=BookCategory.FICTION),
        make_item(isbn="9780000000002", price="1000", category=BookCategory.RARE),
        promo_code="SUMMER20",
    )

    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.discountable_subtotal == Decimal("1000")
    assert result.non_discountable_subtotal == Decimal("1000")
    assert result.discount_amount == Decimal("200.00")
    assert result.subtotal_after_discount == Decimal("1800.00")


def test_children_book_makes_delivery_free() -> None:
    order = make_order(make_item(category=BookCategory.CHILDREN, weight_grams=5000))

    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.delivery_fee == Decimal("0")


def test_delivery_uses_only_full_100g_blocks_over_one_kg() -> None:
    order = make_order(make_item(price="100", weight_grams=1299))

    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.delivery_fee == Decimal("302")


@pytest.mark.parametrize("weight_grams", [999, 1000])
def test_delivery_has_no_weight_surcharge_up_to_one_kg(weight_grams: int) -> None:
    order = make_order(make_item(price="100", weight_grams=weight_grams))

    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.delivery_fee == Decimal("300")


def test_delivery_is_free_when_subtotal_after_discount_is_exactly_threshold() -> None:
    order = make_order(make_item(price="3000"))

    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.subtotal_after_discount == Decimal("3000.00")
    assert result.delivery_fee == Decimal("0")


@pytest.mark.parametrize("promo_code", ["UNKNOWN", "welcome15", ""])
def test_unknown_promo_code_is_pricing_error(promo_code: str) -> None:
    order = make_order(make_item(), promo_code=promo_code)

    with pytest.raises(PricingError, match="Неизвестный промокод"):
        PricingService().calculate_order_total(order, REGULAR_DAY)


def test_empty_order_is_invalid() -> None:
    with pytest.raises(PricingError, match="Заказ не может быть пустым"):
        PricingService().calculate_order_total(make_order(), REGULAR_DAY)


def test_blocked_customer_order_is_invalid() -> None:
    order = make_order(make_item(), is_blocked=True)

    with pytest.raises(PricingError, match="Покупатель заблокирован"):
        PricingService().calculate_order_total(order, REGULAR_DAY)


@pytest.mark.parametrize("quantity", [0, -1])
def test_quantity_must_be_positive(quantity: int) -> None:
    order = make_order(make_item(quantity=quantity))

    with pytest.raises(PricingError, match="Количество должно быть положительным"):
        PricingService().calculate_order_total(order, REGULAR_DAY)


def test_quantity_cannot_exceed_20_per_book() -> None:
    order = make_order(make_item(quantity=21))

    with pytest.raises(PricingError, match="Превышен лимит количества"):
        PricingService().calculate_order_total(order, REGULAR_DAY)


def test_quantity_of_20_per_book_is_valid() -> None:
    order = make_order(make_item(price="100", quantity=20))

    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.subtotal == Decimal("2000")


def test_regular_customer_order_limit_is_100000() -> None:
    order = make_order(make_item(price="100001"), tier=CustomerTier.SILVER)

    with pytest.raises(PricingError, match="превышает лимит 100000"):
        PricingService().calculate_order_total(order, REGULAR_DAY)


def test_gold_customer_order_limit_is_500000() -> None:
    order = make_order(make_item(price="500001"), tier=CustomerTier.GOLD)

    with pytest.raises(PricingError, match="превышает лимит 500000"):
        PricingService().calculate_order_total(order, REGULAR_DAY)


@pytest.mark.parametrize(
    ("tier", "price"),
    [(CustomerTier.BRONZE, "100000"), (CustomerTier.SILVER, "100000"), (CustomerTier.GOLD, "500000")],
)
def test_order_limit_boundary_is_valid(tier: CustomerTier, price: str) -> None:
    order = make_order(make_item(price=price), tier=tier)

    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.subtotal == Decimal(price)


def test_student_promo_check_works_for_non_interned_code() -> None:
    promo_code = "".join(["STUDENT", "25"])
    order = make_order(make_item(category=BookCategory.TEXTBOOK), promo_code=promo_code)

    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.discount_rate == Decimal("0.25")
