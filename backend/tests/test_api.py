import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_get_user():
    # Very basic smoke test, normally would mock DB
    pass

def test_imports():
    import main
    assert main.app is not None
