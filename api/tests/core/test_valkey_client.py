from app.core.valkey.client import check_valkey_health


async def test_valkey_responde_ping():
    assert await check_valkey_health() is True
