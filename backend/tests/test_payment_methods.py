from payment_methods import ALLOWED_PAYMENT_METHODS, receipt_is_required


def test_all_supported_topup_methods_and_legacy_alias_are_accepted():
    assert {
        "card",
        "usdt",
        "tether",
        "btc",
        "bnb",
        "usdt_bnb",
        "telegram_stars",
    } <= ALLOWED_PAYMENT_METHODS


def test_receipt_is_required_only_for_card():
    assert receipt_is_required("card")
    for method in ("usdt", "tether", "btc", "bnb", "usdt_bnb", "telegram_stars"):
        assert not receipt_is_required(method)
