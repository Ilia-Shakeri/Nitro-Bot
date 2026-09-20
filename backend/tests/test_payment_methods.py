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


def test_receipt_is_required_for_manual_payment_claims():
    for method in ("card", "usdt", "tether", "btc", "bnb", "usdt_bnb"):
        assert receipt_is_required(method)
    assert not receipt_is_required("telegram_stars")
