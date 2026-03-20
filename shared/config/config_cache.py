"""
shared/config/config_cache.py — In-memory configuration cache (Singleton).

Purpose:
    Provides fast, in-memory access to business configuration and system
    settings without hitting the database on every request.

Pattern:
    Singleton — one instance per process, shared across all sessions
    and requests.

Methods:
    ConfigCache.get_instance() → ConfigCache          (singleton accessor)
    config.get_business_config(business_id) → dict
    config.get_system_setting(key) → Any
    config.invalidate(business_id)                    (force refresh for one business)
    config.refresh_all()                              (reload everything from DB)

Refresh Strategy:
    - Loaded from the database at service startup.
    - A background asyncio task re-reads the database every 5 minutes.
    - For immediate refresh: Core exposes POST /internal/cache/refresh
      (internal network only).

No Redis:
    All caching is in-process. Each ECS task maintains its own copy.
    This is acceptable because config changes are infrequent admin
    operations and a 5-minute propagation delay is tolerable.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Optional

from shared.utils.logging import get_logger

logger = get_logger("shared.config.config_cache")

_REFRESH_INTERVAL_SECONDS = 300  # 5 minutes


class ConfigCache:
    """
    Process-level in-memory cache for business configs and system settings.

    Thread/coroutine safety:
        Reads are lock-free (dict lookups).
        Writes (refresh) acquire an asyncio.Lock to prevent concurrent DB hits.
    """

    _instance: Optional["ConfigCache"] = None

    def __init__(self) -> None:
        # {business_id (str) → {config_key → config_value}}
        self._business_configs: dict[str, dict[str, Any]] = {}
        # {setting_key → setting_value}
        self._system_settings: dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._refresh_task: Optional[asyncio.Task] = None

    # ── Singleton ─────────────────────────────────────────────────────────────

    @classmethod
    def get_instance(cls) -> "ConfigCache":
        """Return (or lazily create) the process-level singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Public API ────────────────────────────────────────────────────────────

    def get_business_config(self, business_id: str | uuid.UUID) -> dict[str, Any]:
        """
        Return the full config dict for a business.

        Args:
            business_id: UUID of the business (string or uuid.UUID).

        Returns:
            Dict of {config_key: config_value}. Empty dict if not cached.
        """
        return self._business_configs.get(str(business_id), {})

    def get_config_value(
        self,
        business_id: str | uuid.UUID,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Return a single config value for a business.

        Args:
            business_id: UUID of the business.
            key:         config_key to look up.
            default:     Fallback if key is not found.
        """
        return self._business_configs.get(str(business_id), {}).get(key, default)

    def get_system_setting(self, key: str, default: Any = None) -> Any:
        """
        Return a system-level setting value.

        Args:
            key:     Setting key.
            default: Fallback if key is not found.
        """
        return self._system_settings.get(key, default)

    async def invalidate(self, business_id: str | uuid.UUID) -> None:
        """
        Force a refresh of the configuration for a single business.

        Args:
            business_id: UUID of the business to refresh.
        """
        logger.info(f"ConfigCache: invalidating business {business_id}")
        async with self._lock:
            await self._load_business_config(str(business_id))

    async def refresh_all(self) -> None:
        """Reload all business configs and system settings from the database."""
        logger.info("ConfigCache: refreshing all configurations from DB")
        async with self._lock:
            await self._load_all()

    # ── Startup / Shutdown ────────────────────────────────────────────────────

    async def initialize(self) -> None:
        """
        Load initial data from DB and start the background refresh loop.
        Call once at service startup (inside FastAPI lifespan).
        """
        await self.refresh_all()
        self._refresh_task = asyncio.create_task(self._background_refresh())
        logger.info("ConfigCache: background refresh task started.")

    async def shutdown(self) -> None:
        """Cancel the background refresh task. Call at service shutdown."""
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        logger.info("ConfigCache: background refresh task stopped.")

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _background_refresh(self) -> None:
        """Periodically reload configs from the database."""
        while True:
            await asyncio.sleep(_REFRESH_INTERVAL_SECONDS)
            try:
                async with self._lock:
                    await self._load_all()
            except Exception as exc:
                logger.error(f"ConfigCache: background refresh failed: {exc}", exc_info=True)

    async def _load_all(self) -> None:
        """Load system settings and all business configs from Repository."""
        from core.repositories.config_repository import ConfigRepository
        repo = ConfigRepository()

        # 1. System settings
        self._system_settings = await repo.get_system_settings()
        logger.debug(f"ConfigCache: loaded {len(self._system_settings)} system settings.")

        # 2. All active businesses
        biz_rows = await repo.get_active_businesses()

        # Load per-business tenant configs
        loaded = 0
        for biz_row in biz_rows:
            biz_id = str(biz_row["id"])
            schema_name = biz_row["schema_name"]
            try:
                await self._load_business_config(biz_id, schema_name)
                loaded += 1
            except Exception as exc:
                logger.warning(
                    f"ConfigCache: failed to load config for business {biz_id}: {exc}"
                )

        logger.info(f"ConfigCache: loaded configs for {loaded}/{len(biz_rows)} businesses.")

    async def _load_business_config(
        self,
        business_id: str,
        schema_name: Optional[str] = None,
    ) -> None:
        """Load configs for a single business using Repository."""
        from core.repositories.config_repository import ConfigRepository
        repo = ConfigRepository()

        if schema_name is None:
            # Note: For internal refresh we still might need business info lookup
            # but usually this is called with schema_name during main _load_all
            from shared.db.connection import get_connection
            async with get_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT schema_name FROM public.businesses WHERE id = $1",
                    uuid.UUID(business_id),
                )
                if not row: return
                schema_name = row["schema_name"]

        self._business_configs[business_id] = await repo.get_business_config(
            uuid.UUID(business_id), schema_name
        )
        logger.debug(
            f"ConfigCache: loaded config for business {business_id} (schema={schema_name})."
        )

