from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st

from bookstore.models.book import BookCategory
from bookstore.models.customer import CustomerTier
from bookstore.pricing import PricingService

from tests.conftest import make_item, make_order


REGULAR_DAY = datetime(2025, 10, 1)


def item_strategy(
    *,
    categories: list[BookCategory] | None = None,
    max_price: int = 1000,
):
    category_strategy = st.sampled_from(categories or list(BookCategory))
    return st.builds(
        make_item,
        isbn=st.from_regex(r"978[0-9]{10}", fullmatch=True),
        price=st.integers(min_value=1, max_value=max_price).map(str),
        quantity=st.integers(min_value=1, max_value=20),
        category=category_strategy,
        weight_grams=st.integers(min_value=1, max_value=5000),
    )


@st.composite
def valid_order_strategy(draw, *, promo_code: str | None = None):
    items = draw(st.lists(item_strategy(max_price=1000), min_size=1, max_size=5))
    tier = draw(st.sampled_from(list(CustomerTier)))
    return make_order(*items, tier=tier, promo_code=promo_code)


@given(valid_order_strategy())
@settings(max_examples=100)
def test_total_is_sum_of_discounted_subtotal_delivery_and_vat(order) -> None:
    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.total == result.subtotal_after_discount + result.delivery_fee + result.vat


@given(valid_order_strategy())
@settings(max_examples=100)
def test_discount_never_exceeds_discountable_subtotal(order) -> None:
    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert Decimal("0") <= result.discount_amount <= result.discountable_subtotal
    assert result.subtotal_after_discount == result.subtotal - result.discount_amount


@given(
    st.lists(
        item_strategy(categories=[BookCategory.RARE], max_price=1000),
        min_size=1,
        max_size=5,
    )
)
@settings(max_examples=50)
def test_rare_books_are_never_discounted(items) -> None:
    order = make_order(*items, tier=CustomerTier.GOLD, promo_code="SUMMER20")

    result = PricingService().calculate_order_total(order, datetime(2025, 11, 25))

    assert result.discountable_subtotal == Decimal("0")
    assert result.non_discountable_subtotal == result.subtotal
    assert result.discount_amount == Decimal("0.00")
    assert result.subtotal_after_discount == result.subtotal


@given(
    st.lists(
        item_strategy(categories=[BookCategory.CHILDREN], max_price=1000),
        min_size=1,
        max_size=5,
    )
)
@settings(max_examples=50)
def test_any_children_book_makes_delivery_free(items) -> None:
    order = make_order(*items)

    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.delivery_fee == Decimal("0")


@given(st.sampled_from(list(CustomerTier)), st.sampled_from(["WELCOME15", "SUMMER20"]))
def test_promo_discount_is_at_least_customer_tier_discount(tier, promo_code) -> None:
    order = make_order(make_item(), tier=tier, promo_code=promo_code)

    result = PricingService().calculate_order_total(order, REGULAR_DAY)

    assert result.discount_rate >= PricingService().best_discount_rate(
        make_order(make_item(), tier=tier),
        REGULAR_DAY,
    )
