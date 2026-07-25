from pricing import PRICING, has_sufficient_credits, release_cost


def test_nitro_price_uses_integer_cents():
    assert PRICING.nitro_usd_price_cents == 80
    assert isinstance(PRICING.nitro_usd_price_cents, int)
    assert [quantity * PRICING.nitro_usd_price_cents for quantity in (1, 3, 10)] == [
        80,
        240,
        800,
    ]


def test_discounted_release_and_copyright_prices():
    assert PRICING.original_release_price == 20
    assert PRICING.discounted_release_price == 8
    assert PRICING.copyright_price == 2
    assert release_cost(False, False) == 8
    assert release_cost(False, True) == 10


def test_new_profile_does_not_change_release_cost():
    assert release_cost(False, False) == PRICING.discounted_release_price


def test_edit_copyright_adds_two_nitro():
    assert release_cost(True, False) == PRICING.edit_release_price
    assert release_cost(True, True) == PRICING.edit_release_price + 2


def test_insufficient_credit_check():
    assert has_sufficient_credits(8, 8)
    assert not has_sufficient_credits(7, 8)
