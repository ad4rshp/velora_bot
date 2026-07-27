"""
Server Setup & Guild Settings Manager for Velora RPG.
Manages per-guild settings (custom prefix, dedicated channels, role permissions, disabled commands).
"""

import aiosqlite
from typing import Dict, Any, Optional
from utils.logger import db_logger
from utils.db import db

DEFAULT_GUILD_SETTINGS = {
    "prefix": "v",
    "battle_channel_id": 0,
    "welcome_channel_id": 0,
    "disabled_commands": "",
    "auto_clean_market": 1
}

class SettingsManager:
    """Manages cached and database-persisted per-guild settings."""

    def __init__(self):
        self._cache: Dict[int, Dict[str, Any]] = {}

    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """Fetch settings for a guild (with in-memory caching)."""
        if guild_id in self._cache:
            return self._cache[guild_id]

        row = await db.fetchone("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
        if not row:
            # Insert default row
            await db.execute(
                """
                INSERT INTO guild_settings (guild_id, prefix, created_at, updated_at)
                VALUES (?, 'v', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT DO NOTHING
                """,
                (guild_id,)
            )
            settings = dict(DEFAULT_GUILD_SETTINGS)
        else:
            settings = dict(row)

        self._cache[guild_id] = settings
        return settings

    async def update_setting(self, guild_id: int, key: str, value: Any) -> None:
        """Update a specific setting for a guild."""
        valid_keys = ["prefix", "battle_channel_id", "welcome_channel_id", "disabled_commands", "auto_clean_market"]
        if key not in valid_keys:
            raise ValueError(f"Invalid setting key '{key}'. Must be one of: {', '.join(valid_keys)}")

        await db.execute(
            f"UPDATE guild_settings SET {key} = ?, updated_at = CURRENT_TIMESTAMP WHERE guild_id = ?",
            (value, guild_id)
        )
        if guild_id in self._cache:
            self._cache[guild_id][key] = value

    async def get_prefix(self, guild_id: Optional[int]) -> str:
        """Fetch custom prefix for a guild."""
        if not guild_id:
            return "v"
        settings = await self.get_guild_settings(guild_id)
        return settings.get("prefix", "v")

settings_manager = SettingsManager()
