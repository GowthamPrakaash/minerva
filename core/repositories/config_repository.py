"""
core/repositories/config_repository.py — Data access for Business Configs and System Settings.
"""

import uuid
from typing import Any, Optional
from shared.db.connection import get_connection

class ConfigRepository:
    """Encapsulates SQL logic for Global and Tenant configurations."""

    async def get_system_settings(self) -> dict[str, Any]:
        """Fetch all settings from the public schema."""
        async with get_connection() as conn: # Public schema by default
            rows = await conn.fetch("SELECT key, value FROM public.system_settings")
            return {row["key"]: row["value"] for row in rows}

    async def get_business_config(self, business_id: uuid.UUID, schema_name: str) -> dict[str, Any]:
        """Fetch all config keys for a specific tenant schema."""
        async with get_connection(schema_name) as conn:
            rows = await conn.fetch("SELECT config_key, config_value FROM configs")
            return {row["config_key"]: row["config_value"] for row in rows}

    async def get_active_businesses(self) -> list[dict]:
        """Fetch basic info for all active businesses for cache warming."""
        async with get_connection() as conn:
            return await conn.fetch("SELECT id, schema_name FROM public.businesses WHERE is_active = true")
