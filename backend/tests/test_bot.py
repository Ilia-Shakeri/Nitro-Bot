import pytest
from bot import dp, cmd_start, TRANSLATIONS

def test_bot_imports():
    assert dp is not None
    assert "en" in TRANSLATIONS
    assert "fa" in TRANSLATIONS
