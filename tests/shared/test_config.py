"""
tests/shared/test_config.py — Unit tests for ConfigCache and ProviderResolver.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from shared.config.config_cache import ConfigCache
from shared.providers.provider_resolver import ProviderResolver


@pytest.mark.asyncio
async def test_config_cache_singleton():
    cache1 = ConfigCache.get_instance()
    cache2 = ConfigCache.get_instance()
    assert cache1 is cache2


@pytest.mark.asyncio
async def test_config_cache_get_value():
    cache = ConfigCache.get_instance()
    biz_id = str(uuid.uuid4())
    
    # Manually inject into internal dict for testing without DB
    cache._business_configs[biz_id] = {"industry": "Fintech"}
    
    val = cache.get_config_value(biz_id, "industry")
    assert val == "Fintech"
    
    val_default = cache.get_config_value(biz_id, "missing", "default_val")
    assert val_default == "default_val"


@pytest.mark.asyncio
async def test_provider_resolver_resolution(monkeypatch):
    resolver = ProviderResolver.get_instance()
    
    # Mock ConfigCache to return a specific provider override
    mock_cache = MagicMock()
    mock_cache.get_config_value.return_value = {"stt": "deepgram"}
    mock_cache.get_system_setting.return_value = None
    
    with patch("shared.config.config_cache.ConfigCache.get_instance", return_value=mock_cache):
        # We need to clear the resolver's internal instance or mock its dependencies
        # Since it's a singleton, we can just mock the methods it calls
        
        biz_id = str(uuid.uuid4())
        
        # Manually verify resolution logic
        with patch.object(resolver, "_get_business_overrides", return_value={"stt": "deepgram"}):
            name = resolver.get_provider_name("stt", biz_id)
            assert name == "deepgram"
            
        with patch.object(resolver, "_get_business_overrides", return_value={}):
            with patch.object(resolver, "_get_system_setting", return_value="sarvam"):
                name = resolver.get_provider_name("stt", biz_id)
                assert name == "sarvam"
