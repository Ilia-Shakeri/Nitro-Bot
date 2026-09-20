# "tether" stays as an alias for older clients and is normalized to USDT.
PAYMENT_METHOD_ALIASES = {"tether": "usdt"}
MANUAL_CRYPTO_METHODS = frozenset({"usdt", "btc", "bnb", "usdt_bnb"})
ALLOWED_PAYMENT_METHODS = frozenset(
    {"card", "telegram_stars", *MANUAL_CRYPTO_METHODS, *PAYMENT_METHOD_ALIASES}
)


def normalize_payment_method(value: str) -> str:
    return PAYMENT_METHOD_ALIASES.get(value, value)


def receipt_is_required(value: str) -> bool:
    return normalize_payment_method(value) in {"card", *MANUAL_CRYPTO_METHODS}
