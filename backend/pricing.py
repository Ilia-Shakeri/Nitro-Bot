from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Pricing:
    nitro_usd_price_cents: int = 80
    original_release_price: int = 20
    discounted_release_price: int = 8
    copyright_price: int = 2
    edit_release_price: int = 2
    minimum_topup_nitro: int = 3


PRICING = Pricing()


def release_cost(is_edit: bool, copyright_requested: bool) -> int:
    base = PRICING.edit_release_price if is_edit else PRICING.discounted_release_price
    return base + (PRICING.copyright_price if copyright_requested else 0)


def pricing_payload() -> dict[str, int]:
    return asdict(PRICING)


def has_sufficient_credits(balance: int, cost: int) -> bool:
    return balance >= cost
