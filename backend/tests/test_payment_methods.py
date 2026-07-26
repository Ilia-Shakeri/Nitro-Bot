from payment_methods import ALLOWED_PAYMENT_METHODS


def test_only_card_and_usdt_topup_methods_are_accepted():
    assert "card" in ALLOWED_PAYMENT_METHODS
    assert "usdt" in ALLOWED_PAYMENT_METHODS
    assert "tether" in ALLOWED_PAYMENT_METHODS
    assert "btc" not in ALLOWED_PAYMENT_METHODS
