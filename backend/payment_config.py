from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIRECTORY = Path(__file__).resolve().parent
_PROJECT_ENV_FILE = _BACKEND_DIRECTORY.parent / ".env"
_BACKEND_ENV_FILE = _BACKEND_DIRECTORY / ".env"


class PaymentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_PROJECT_ENV_FILE, _BACKEND_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        str_strip_whitespace=True,
    )

    payment_card_number: str = Field(default="", repr=False)
    payment_card_holder: str = Field(default="", repr=False)
    payment_usdt_trc20_address: str = Field(default="", repr=False)
    payment_btc_address: str = Field(default="", repr=False)
    payment_bnb_bep20_address: str = Field(default="", repr=False)
    payment_usdt_bep20_address: str = Field(default="", repr=False)
    telegram_stars_per_nitro: int = Field(default=0, ge=0)
    crypto_quote_url: str = Field(
        default="https://api.coingecko.com/api/v3/simple/price",
        repr=False,
    )


def load_payment_settings(env_file: Path | str | None = None) -> PaymentSettings:
    if env_file is None:
        return PaymentSettings()
    return PaymentSettings(_env_file=env_file)


def normalized_card_number(value: str) -> str:
    return "".join(character for character in value if not character.isspace() and character != "-")
