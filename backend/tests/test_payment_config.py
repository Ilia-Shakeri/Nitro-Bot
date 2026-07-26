import pytest
from fastapi import HTTPException

from payment_config import load_payment_settings, normalized_card_number
from routers.pricing import payment_config_payload


@pytest.fixture(autouse=True)
def payment_environment(monkeypatch):
    monkeypatch.setenv("PAYMENT_CARD_NUMBER", "1111222233334444")
    monkeypatch.setenv("PAYMENT_CARD_HOLDER", "Test Holder")
    monkeypatch.setenv("PAYMENT_USDT_TRC20_ADDRESS", "TTestWallet")


def test_persian_payment_config_has_card_and_usdt():
    config = payment_config_payload("fa")
    assert config["card"] == {
        "number": "1111222233334444",
        "holder": "Test Holder",
    }
    assert config["usdt"]["address"] == "TTestWallet"


@pytest.mark.parametrize("language", ["en", "ar", "ru", "en-US"])
def test_non_persian_payment_config_has_usdt_only(language):
    config = payment_config_payload(language)
    assert config["card"] is None
    assert config["usdt"]["address"] == "TTestWallet"


def test_non_persian_payment_config_requires_usdt(monkeypatch):
    monkeypatch.delenv("PAYMENT_USDT_TRC20_ADDRESS")
    with pytest.raises(HTTPException) as exc:
        payment_config_payload("en")
    assert exc.value.status_code == 503
    assert exc.value.detail == "payment_config_unavailable"


def test_payment_settings_load_project_env_file(monkeypatch, tmp_path):
    for key in (
        "PAYMENT_CARD_NUMBER",
        "PAYMENT_CARD_HOLDER",
        "PAYMENT_USDT_TRC20_ADDRESS",
    ):
        monkeypatch.delenv(key)
    (tmp_path / ".env").write_text(
        "\n".join(
            (
                "PAYMENT_CARD_NUMBER=1111 2222 3333 4444",
                "PAYMENT_CARD_HOLDER=Test Holder",
                "PAYMENT_USDT_TRC20_ADDRESS=TTestWallet",
            )
        ),
        encoding="utf-8",
    )
    settings = load_payment_settings(tmp_path / ".env")

    assert normalized_card_number(settings.payment_card_number) == "1111222233334444"
    assert settings.payment_card_holder == "Test Holder"
    assert settings.payment_usdt_trc20_address == "TTestWallet"
