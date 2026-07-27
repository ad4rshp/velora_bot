"""
Velora SQLite Database Layer.
Handles async connection management, WAL mode, foreign keys, transactions,
and schema migrations.
"""

import aiosqlite
from typing import Any, List, Optional, Tuple, Dict
from pathlib import Path
from utils.logger import db_logger
from config import config

INITIAL_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS guild_settings (
        guild_id INTEGER PRIMARY KEY,
        prefix TEXT NOT NULL DEFAULT 'v',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY,
        coins INTEGER NOT NULL DEFAULT 1000,
        sigils INTEGER NOT NULL DEFAULT 10,
        title_id TEXT DEFAULT NULL,
        pvp_rating INTEGER NOT NULL DEFAULT 1000,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS player_stats (
        user_id INTEGER PRIMARY KEY,
        pvp_battles INTEGER NOT NULL DEFAULT 0,
        pvp_wins INTEGER NOT NULL DEFAULT 0,
        pvp_losses INTEGER NOT NULL DEFAULT 0,
        win_streak INTEGER NOT NULL DEFAULT 0,
        highest_win_streak INTEGER NOT NULL DEFAULT 0,
        coins_earned INTEGER NOT NULL DEFAULT 0,
        coins_spent INTEGER NOT NULL DEFAULT 0,
        sigils_earned INTEGER NOT NULL DEFAULT 0,
        characters_collected INTEGER NOT NULL DEFAULT 0,
        equipment_collected INTEGER NOT NULL DEFAULT 0,
        scrolls_collected INTEGER NOT NULL DEFAULT 0,
        rerolls INTEGER NOT NULL DEFAULT 0,
        trades INTEGER NOT NULL DEFAULT 0,
        market_sales INTEGER NOT NULL DEFAULT 0,
        blank_scrolls_used INTEGER NOT NULL DEFAULT 0,
        repair_kits_used INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
    );
    """
]

class DatabaseManager:
    """Thread-safe, non-blocking SQLite database manager wrapper."""

    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Establish database connection and configure Pragmas."""
        db_path_obj = Path(self.db_path)
        if db_path_obj.parent:
            db_path_obj.parent.mkdir(parents=True, exist_ok=True)

        db_logger.info(f"Connecting to database at '{self.db_path}'...")
        self._conn = await aiosqlite.connect(self.db_path)

        self._conn.row_factory = aiosqlite.Row
        
        # Configure WAL Mode, Busy Timeout & Concurrency Pragmas
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA foreign_keys=ON;")
        await self._conn.execute("PRAGMA busy_timeout=30000;")
        await self._conn.execute("PRAGMA synchronous=NORMAL;")
        await self._conn.execute("PRAGMA auto_vacuum=INCREMENTAL;")
        await self._conn.commit()
        
        db_logger.info("Database connection established. Initializing migrations...")
        await self._run_migrations()
        await self.perform_auto_cleanup()

    async def perform_auto_cleanup(self) -> None:
        """Automatic DB optimization, WAL truncation, incremental vacuum & expired market purging."""
        if not self._conn:
            return
        db_logger.info("Executing database traffic management & auto-cleanup...")
        try:
            await self._conn.execute("DELETE FROM market_listings WHERE datetime(created_at) < datetime('now', '-7 days')")
            await self._conn.commit()
            await self._conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
            await self._conn.execute("PRAGMA incremental_vacuum;")
            await self._conn.commit()
            db_logger.info("Database auto-cleanup & WAL checkpoint completed successfully.")
        except Exception as e:
            db_logger.debug(f"Database auto-cleanup info: {e}")



    async def close(self) -> None:
        """Gracefully close database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            db_logger.info("Database connection closed gracefully.")

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database connection is not initialized. Call connect() first.")
        return self._conn

    async def _run_migrations(self) -> None:
        """Executes schema and catalog SQL scripts from sql/ directory automatically on startup."""
        import os
        from pathlib import Path

        sql_dir = Path("sql")
        if sql_dir.exists():
            sql_files = sorted(sql_dir.glob("*.sql"))
            for file_path in sql_files:
                db_logger.info(f"Executing SQL catalog file '{file_path.name}'...")
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    await self.conn.executescript(content)
        await self.conn.commit()
        db_logger.info("Database schema and catalog migrations synced successfully.")


        async with self.conn.execute("SELECT version FROM schema_migrations WHERE version = 1") as cursor:
            row = await cursor.fetchone()
            if not row:
                await self.conn.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (1, "initial_core_tables")
                )
                await self.conn.commit()
                db_logger.info("Applied migration 1: initial_core_tables")

        # Migration 2: Characters & Player Inventory Tables
        async with self.conn.execute("SELECT version FROM schema_migrations WHERE version = 2") as cursor:
            row = await cursor.fetchone()
            if not row:
                db_logger.info("Applying migration 2: character_system_tables...")
                await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    character_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    class_type TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_max INTEGER NOT NULL,
                    base_rarity TEXT NOT NULL DEFAULT 'D',
                    base_hp INTEGER NOT NULL,
                    base_atk INTEGER NOT NULL,
                    base_def INTEGER NOT NULL,
                    base_spd INTEGER NOT NULL,
                    description TEXT NOT NULL
                );
                """)
                await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS player_characters (
                    instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    character_id TEXT NOT NULL,
                    level INTEGER NOT NULL DEFAULT 1,
                    xp INTEGER NOT NULL DEFAULT 0,
                    rarity TEXT NOT NULL DEFAULT 'D',
                    is_active INTEGER NOT NULL DEFAULT 0,
                    team_slot INTEGER DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (character_id) REFERENCES characters(character_id)
                );
                """)
                
                # Seed catalog starter characters
                from utils.constants import STARTER_CHARACTERS
                for char in STARTER_CHARACTERS:
                    await self.conn.execute("""
                    INSERT INTO characters (
                        character_id, name, class_type, resource_type, resource_max,
                        base_rarity, base_hp, base_atk, base_def, base_spd, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(character_id) DO NOTHING;
                    """, (
                        char["id"], char["name"], char["class_type"], char["resource_type"],
                        char["resource_max"], char["base_rarity"], char["base_hp"],
                        char["base_atk"], char["base_def"], char["base_spd"], char["description"]
                    ))

                await self.conn.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (2, "character_system_tables")
                )
                await self.conn.commit()
                db_logger.info("Applied migration 2: character_system_tables successfully.")

        # Migration 3: Equipment, Scroll System & Loadout Tables
        async with self.conn.execute("SELECT version FROM schema_migrations WHERE version = 3") as cursor:
            row = await cursor.fetchone()
            if not row:
                db_logger.info("Applying migration 3: equipment_scroll_tables...")
                await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS player_equipment (
                    equipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    slot TEXT NOT NULL,
                    rarity TEXT NOT NULL DEFAULT 'D',
                    quality INTEGER NOT NULL DEFAULT 50,
                    durability INTEGER NOT NULL DEFAULT 100,
                    max_durability INTEGER NOT NULL DEFAULT 100,
                    stat_hp INTEGER NOT NULL DEFAULT 0,
                    stat_atk INTEGER NOT NULL DEFAULT 0,
                    stat_def INTEGER NOT NULL DEFAULT 0,
                    stat_spd INTEGER NOT NULL DEFAULT 0,
                    equipped_character_id INTEGER DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (equipped_character_id) REFERENCES player_characters(instance_id) ON DELETE SET NULL
                );
                """)

                await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS scrolls (
                    scroll_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    scroll_type TEXT NOT NULL,
                    power INTEGER NOT NULL DEFAULT 0,
                    cooldown INTEGER NOT NULL DEFAULT 0,
                    status_chance INTEGER NOT NULL DEFAULT 0,
                    required_class_tags TEXT NOT NULL,
                    description TEXT NOT NULL
                );
                """)

                await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS player_scrolls (
                    instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    scroll_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (scroll_id) REFERENCES scrolls(scroll_id)
                );
                """)

                await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS character_loadouts (
                    character_instance_id INTEGER NOT NULL,
                    slot_index INTEGER NOT NULL, -- 1-4 for active, 5-6 for passive
                    scroll_instance_id INTEGER NOT NULL,
                    PRIMARY KEY (character_instance_id, slot_index),
                    FOREIGN KEY (character_instance_id) REFERENCES player_characters(instance_id) ON DELETE CASCADE,
                    FOREIGN KEY (scroll_instance_id) REFERENCES player_scrolls(instance_id) ON DELETE CASCADE
                );
                """)

                # Seed catalog scrolls
                from utils.constants import STARTER_SCROLLS
                for s in STARTER_SCROLLS:
                    await self.conn.execute("""
                    INSERT INTO scrolls (
                        scroll_id, name, scroll_type, power, cooldown, status_chance, required_class_tags, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(scroll_id) DO NOTHING;
                    """, (
                        s["id"], s["name"], s["scroll_type"], s["power"], s["cooldown"],
                        s["status_chance"], s["required_class_tags"], s["description"]
                    ))

                await self.conn.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (3, "equipment_scroll_tables")
                )
                await self.conn.commit()
                db_logger.info("Applied migration 3: equipment_scroll_tables successfully.")

        # Migration 4: Economy, Market, Quests, Titles & Admin Tables
        async with self.conn.execute("SELECT version FROM schema_migrations WHERE version = 4") as cursor:
            row = await cursor.fetchone()
            if not row:
                db_logger.info("Applying migration 4: market_economy_quests_admin_tables...")
                
                await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS player_consumables (
                    user_id INTEGER NOT NULL,
                    item_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (user_id, item_id),
                    FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
                );
                """)

                await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS market_listings (
                    listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    seller_id INTEGER NOT NULL,
                    item_name TEXT NOT NULL,
                    item_type TEXT NOT NULL, -- equipment, scroll, consumable
                    item_data_json TEXT NOT NULL,
                    price_coins INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (seller_id) REFERENCES players(user_id) ON DELETE CASCADE
                );
                """)

                await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS player_titles (
                    user_id INTEGER NOT NULL,
                    title_id TEXT NOT NULL,
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, title_id),
                    FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
                );
                """)

                await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS player_quests (
                    quest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    quest_type TEXT NOT NULL, -- daily, weekly
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    target_count INTEGER NOT NULL,
                    current_count INTEGER NOT NULL DEFAULT 0,
                    reward_coins INTEGER NOT NULL DEFAULT 0,
                    reward_sigils INTEGER NOT NULL DEFAULT 0,
                    is_claimed INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
                );
                """)

                await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS banned_users (
                    user_id INTEGER PRIMARY KEY,
                    reason TEXT NOT NULL,
                    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)

                await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS blacklisted_guilds (
                    guild_id INTEGER PRIMARY KEY,
                    reason TEXT NOT NULL,
                    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)

                await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """)

                await self.conn.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (4, "market_economy_quests_admin_tables")
                )
                await self.conn.commit()
                db_logger.info("Applied migration 4: market_economy_quests_admin_tables successfully.")



    # Generic Query Interface (Parameterized ONLY)

    async def fetchone(self, sql: str, params: Tuple[Any, ...] = ()) -> Optional[aiosqlite.Row]:
        """Fetch a single record using parameterized SQL."""
        async with self.conn.execute(sql, params) as cursor:
            return await cursor.fetchone()

    async def fetchall(self, sql: str, params: Tuple[Any, ...] = ()) -> List[aiosqlite.Row]:
        """Fetch all matching records using parameterized SQL."""
        async with self.conn.execute(sql, params) as cursor:
            return await cursor.fetchall()

    async def execute(self, sql: str, params: Tuple[Any, ...] = ()) -> int:
        """Execute DML (INSERT, UPDATE, DELETE) query within transaction."""
        async with self.conn.execute(sql, params) as cursor:
            await self.conn.commit()
            return cursor.rowcount

    async def executemany(self, sql: str, params_seq: List[Tuple[Any, ...]]) -> None:
        """Execute bulk DML operation."""
        await self.conn.executemany(sql, params_seq)
        await self.conn.commit()

    # Guild Settings Helpers

    async def get_guild_prefix(self, guild_id: int) -> str:
        """Fetch custom prefix for guild or return default."""
        row = await self.fetchone(
            "SELECT prefix FROM guild_settings WHERE guild_id = ?", (guild_id,)
        )
        return row["prefix"] if row else config.DEFAULT_PREFIX

    async def set_guild_prefix(self, guild_id: int, prefix: str) -> None:
        """Update or insert guild prefix."""
        await self.execute(
            """
            INSERT INTO guild_settings (guild_id, prefix, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id) DO UPDATE SET
                prefix = excluded.prefix,
                updated_at = CURRENT_TIMESTAMP
            """,
            (guild_id, prefix)
        )

    # Player Profile Helpers

    async def get_or_create_player(self, user_id: int) -> aiosqlite.Row:
        """Fetch player or create new profile record with initial stats."""
        player = await self.fetchone("SELECT * FROM players WHERE user_id = ?", (user_id,))
        if not player:
            await self.execute("INSERT INTO players (user_id) VALUES (?)", (user_id,))
            await self.execute("INSERT INTO player_stats (user_id) VALUES (?)", (user_id,))
            player = await self.fetchone("SELECT * FROM players WHERE user_id = ?", (user_id,))
        return player

    # Character System Helpers

    async def get_catalog_characters(self) -> List[aiosqlite.Row]:
        """Fetch all character catalog definitions."""
        return await self.fetchall("SELECT * FROM characters")


    async def get_catalog_character_by_id(self, character_id: str) -> Optional[aiosqlite.Row]:
        """Fetch character catalog details by ID."""
        return await self.fetchone("SELECT * FROM characters WHERE character_id = ?", (character_id,))

    async def has_claimed_starter(self, user_id: int) -> bool:
        """Check if a player has already claimed a starter character team."""
        row = await self.fetchone(
            "SELECT count(*) as cnt FROM player_characters WHERE user_id = ?", (user_id,)
        )
        return row["cnt"] >= 3 if row else False

    async def claim_starter_characters(self, user_id: int, character_ids: List[str]) -> List[aiosqlite.Row]:
        """Assign up to 3 starter characters to a player to form their initial 3v3 team."""
        await self.get_or_create_player(user_id)
        if await self.has_claimed_starter(user_id):
            raise ValueError("You have already claimed your 3 starter heroes!")

        claimed = []
        for idx, char_id in enumerate(character_ids[:3], start=1):
            cat_char = await self.get_catalog_character_by_id(char_id)
            if not cat_char:
                continue

            is_active = 1 if idx == 1 else 0
            await self.execute(
                """
                INSERT INTO player_characters (user_id, character_id, level, xp, rarity, is_active, team_slot)
                VALUES (?, ?, 1, 0, ?, ?, ?)
                """,
                (user_id, char_id, cat_char["base_rarity"], is_active, idx)
            )

            char_inst = await self.fetchone("SELECT last_insert_rowid() as id")
            char_instance_id = char_inst["id"]

            await self.execute(
                "UPDATE player_stats SET characters_collected = characters_collected + 1 WHERE user_id = ?",
                (user_id,)
            )

            # Auto-grant starter weapon for each hero
            class_type = cat_char["class_type"]
            weapon_catalog = await self.get_catalog_equipment(slot="Weapon", class_type=class_type)
            if weapon_catalog:
                w_item = dict(weapon_catalog[0])
                w_data = {
                    "name": w_item["name"], "slot": "Weapon", "compatible_class": w_item["compatible_class"],
                    "rarity": w_item["base_rarity"], "quality": 50, "durability": 100, "max_durability": 100,
                    "stat_hp": w_item["base_hp"], "stat_atk": w_item["base_atk"], "stat_def": w_item["base_def"], "stat_spd": w_item["base_spd"]
                }
                eq_inst = await self.add_equipment(user_id, w_data)
                await self.equip_gear(user_id, eq_inst["equipment_id"], char_instance_id)

            char_row = await self.fetchone(
                """
                SELECT pc.*, c.name, c.class_type, c.resource_type, c.resource_max,
                       c.base_hp, c.base_atk, c.base_def, c.base_spd, c.description
                FROM player_characters pc
                JOIN characters c ON pc.character_id = c.character_id
                WHERE pc.instance_id = ?
                """,
                (char_instance_id,)
            )
            claimed.append(char_row)

        return claimed

    async def claim_starter_character(self, user_id: int, character_id: str) -> aiosqlite.Row:
        """Single character fallback wrapper for claim_starter_characters."""
        claimed = await self.claim_starter_characters(user_id, [character_id])
        return claimed[0] if claimed else None


        # Get inserted character instance_id
        char_inst = await self.fetchone("SELECT last_insert_rowid() as id")
        char_instance_id = char_inst["id"]
        
        # Increment characters collected stat
        await self.execute(
            "UPDATE player_stats SET characters_collected = characters_collected + 1 WHERE user_id = ?",
            (user_id,)
        )

        # Automatically grant class-compatible starter weapon
        class_type = cat_char["class_type"]
        weapon_catalog = await self.get_catalog_equipment(slot="Weapon", class_type=class_type)
        if weapon_catalog:
            weapon_item = dict(weapon_catalog[0])
            starter_weapon_data = {
                "name": weapon_item["name"],
                "slot": "Weapon",
                "compatible_class": weapon_item["compatible_class"],
                "rarity": weapon_item["base_rarity"],
                "quality": 50,
                "durability": 100,
                "max_durability": 100,
                "stat_hp": weapon_item["base_hp"],
                "stat_atk": weapon_item["base_atk"],
                "stat_def": weapon_item["base_def"],
                "stat_spd": weapon_item["base_spd"]
            }
            eq_inst = await self.add_equipment(user_id, starter_weapon_data)
            await self.equip_gear(user_id, eq_inst["equipment_id"], char_instance_id)

        return await self.fetchone(
            """
            SELECT pc.*, c.name, c.class_type, c.resource_type, c.resource_max,
                   c.base_hp, c.base_atk, c.base_def, c.base_spd, c.description
            FROM player_characters pc
            JOIN characters c ON pc.character_id = c.character_id
            WHERE pc.user_id = ? AND pc.character_id = ?
            """,
            (user_id, character_id)
        )


    async def get_player_characters(self, user_id: int) -> List[aiosqlite.Row]:
        """Fetch all owned characters for a player with catalog joined stats."""
        return await self.fetchall(
            """
            SELECT pc.*, c.name, c.class_type, c.resource_type, c.resource_max,
                   c.base_hp, c.base_atk, c.base_def, c.base_spd, c.description
            FROM player_characters pc
            JOIN characters c ON pc.character_id = c.character_id
            WHERE pc.user_id = ?
            ORDER BY pc.is_active DESC, pc.level DESC, pc.instance_id ASC
            """,
            (user_id,)
        )

    async def get_player_character_by_instance(self, instance_id: int) -> Optional[aiosqlite.Row]:
        """Fetch a specific player character instance with catalog stats."""
        return await self.fetchone(
            """
            SELECT pc.*, c.name, c.class_type, c.resource_type, c.resource_max,
                   c.base_hp, c.base_atk, c.base_def, c.base_spd, c.description
            FROM player_characters pc
            JOIN characters c ON pc.character_id = c.character_id
            WHERE pc.instance_id = ?
            """,
            (instance_id,)
        )

    async def set_active_character(self, user_id: int, instance_id: int, slot: int = 1) -> None:
        """Set a character as active team member in slot (1, 2, or 3)."""
        await self.execute(
            "UPDATE player_characters SET is_active = 0, team_slot = NULL WHERE user_id = ? AND team_slot = ?",
            (user_id, slot)
        )
        await self.execute(
            "UPDATE player_characters SET is_active = 1, team_slot = ? WHERE instance_id = ? AND user_id = ?",
            (slot, instance_id, user_id)
        )

    # Equipment Helpers

    async def get_catalog_equipment(self, slot: str = None, class_type: str = None) -> List[aiosqlite.Row]:
        """Fetch matching items from equipment catalog."""
        sql = "SELECT * FROM equipment_catalog WHERE 1=1"
        params = []
        if slot:
            sql += " AND (slot = ?)"
            params.append(slot)
        if class_type:
            sql += " AND (compatible_class = ? OR compatible_class = 'All')"
            params.append(class_type)
        return await self.fetchall(sql, tuple(params))

    async def get_player_equipment(self, user_id: int, slot_filter: str = None) -> List[aiosqlite.Row]:

        """Fetch all equipment owned by a player, optionally filtered by slot."""
        if slot_filter:
            return await self.fetchall(
                "SELECT * FROM player_equipment WHERE user_id = ? AND slot = ? ORDER BY quality DESC, equipment_id ASC",
                (user_id, slot_filter)
            )
        return await self.fetchall(
            "SELECT * FROM player_equipment WHERE user_id = ? ORDER BY slot ASC, quality DESC",
            (user_id,)
        )

    async def get_equipment_by_id(self, equipment_id: int) -> Optional[aiosqlite.Row]:
        """Fetch equipment instance by ID."""
        return await self.fetchone("SELECT * FROM player_equipment WHERE equipment_id = ?", (equipment_id,))

    async def add_equipment(self, user_id: int, eq_data: Dict[str, Any]) -> aiosqlite.Row:
        """Add new equipment piece to player inventory."""
        await self.execute(
            """
            INSERT INTO player_equipment (
                user_id, name, slot, rarity, quality, durability, max_durability,
                stat_hp, stat_atk, stat_def, stat_spd
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, eq_data["name"], eq_data["slot"], eq_data["rarity"],
                eq_data["quality"], eq_data["durability"], eq_data["max_durability"],
                eq_data["stat_hp"], eq_data["stat_atk"], eq_data["stat_def"], eq_data["stat_spd"]
            )
        )
        await self.execute("UPDATE player_stats SET equipment_collected = equipment_collected + 1 WHERE user_id = ?", (user_id,))
        await self.update_quest_progress(user_id, "daily_collector", 1)
        await self.update_quest_progress(user_id, "weekly_collector", 1)
        return await self.fetchone(
            "SELECT * FROM player_equipment WHERE user_id = ? ORDER BY equipment_id DESC LIMIT 1",
            (user_id,)
        )

    async def update_quest_progress(self, user_id: int, quest_key_substring: str, increment: int = 1) -> None:
        """Increment progress for any active matching user quest."""
        await self.execute(
            """
            UPDATE player_quests
            SET current_count = MIN(target_count, current_count + ?)
            WHERE user_id = ? AND is_claimed = 0 AND title LIKE ?
            """,
            (increment, user_id, f"%{quest_key_substring}%")
        )


    async def equip_gear(self, user_id: int, equipment_id: int, character_instance_id: int) -> None:
        """Equip gear to a character, auto-unequipping any existing piece in that slot."""
        gear = await self.get_equipment_by_id(equipment_id)
        if not gear or gear["user_id"] != user_id:
            raise ValueError("Equipment not found in your inventory.")

        # Unequip old gear in same slot on this character
        await self.execute(
            """
            UPDATE player_equipment SET equipped_character_id = NULL
            WHERE user_id = ? AND slot = ? AND equipped_character_id = ?
            """,
            (user_id, gear["slot"], character_instance_id)
        )
        # Equip new gear
        await self.execute(
            "UPDATE player_equipment SET equipped_character_id = ? WHERE equipment_id = ?",
            (character_instance_id, equipment_id)
        )

    async def repair_equipment(self, user_id: int, equipment_id: int, cost_coins: int) -> None:
        """Restore equipment durability to max."""
        player = await self.get_or_create_player(user_id)
        if player["coins"] < cost_coins:
            raise ValueError(f"Insufficient coins! Repair costs {cost_coins} coins.")

        await self.execute("UPDATE players SET coins = coins - ? WHERE user_id = ?", (cost_coins, user_id))
        await self.execute(
            "UPDATE player_equipment SET durability = max_durability WHERE equipment_id = ?",
            (equipment_id,)
        )

    async def update_equipment_stats(self, equipment_id: int, new_stats: Dict[str, Any]) -> None:
        """Update equipment attributes after accepting a reroll."""
        await self.execute(
            """
            UPDATE player_equipment SET
                name = ?, rarity = ?, quality = ?,
                stat_hp = ?, stat_atk = ?, stat_def = ?, stat_spd = ?
            WHERE equipment_id = ?
            """,
            (
                new_stats["name"], new_stats["rarity"], new_stats["quality"],
                new_stats["stat_hp"], new_stats["stat_atk"], new_stats["stat_def"], new_stats["stat_spd"],
                equipment_id
            )
        )

    async def consume_sigils(self, user_id: int, amount: int) -> None:
        """Deduct sigils from player or raise ValueError if insufficient."""
        player = await self.get_or_create_player(user_id)
        if player["sigils"] < amount:
            raise ValueError(f"Insufficient Sigils! You have {player['sigils']} Sigils, but need {amount}.")
        await self.execute("UPDATE players SET sigils = sigils - ? WHERE user_id = ?", (amount, user_id))
        await self.execute("UPDATE player_stats SET rerolls = rerolls + 1 WHERE user_id = ?", (user_id,))

    # Consumables & Inventory Helpers

    async def get_consumable_quantity(self, user_id: int, item_id: str) -> int:
        """Get player quantity of a consumable item."""
        row = await self.fetchone(
            "SELECT quantity FROM player_consumables WHERE user_id = ? AND item_id = ?",
            (user_id, item_id)
        )
        return row["quantity"] if row else 0

    async def add_consumable(self, user_id: int, item_id: str, quantity: int = 1) -> None:
        """Add quantity of a consumable item to player inventory."""
        await self.execute(
            """
            INSERT INTO player_consumables (user_id, item_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, item_id) DO UPDATE SET
                quantity = quantity + excluded.quantity
            """,
            (user_id, item_id, quantity)
        )

    async def use_consumable(self, user_id: int, item_id: str, quantity: int = 1) -> None:
        """Deduct consumable item from player inventory."""
        curr = await self.get_consumable_quantity(user_id, item_id)
        if curr < quantity:
            raise ValueError(f"You do not own enough of that item!")
        await self.execute(
            "UPDATE player_consumables SET quantity = quantity - ? WHERE user_id = ? AND item_id = ?",
            (quantity, user_id, item_id)
        )

    # Market Helpers

    async def create_market_listing(self, seller_id: int, item_name: str, item_type: str, item_data_json: str, price_coins: int) -> int:
        """Create a marketplace listing."""
        await self.execute(
            """
            INSERT INTO market_listings (seller_id, item_name, item_type, item_data_json, price_coins)
            VALUES (?, ?, ?, ?, ?)
            """,
            (seller_id, item_name, item_type, item_data_json, price_coins)
        )
        return await self.fetchone("SELECT last_insert_rowid() as id")

    async def get_active_market_listings(self) -> List[aiosqlite.Row]:
        """Fetch all active marketplace listings."""
        return await self.fetchall("SELECT * FROM market_listings ORDER BY listing_id DESC")

    async def buy_market_listing(self, buyer_id: int, listing_id: int) -> aiosqlite.Row:
        """Process purchasing a marketplace listing within transaction."""
        listing = await self.fetchone("SELECT * FROM market_listings WHERE listing_id = ?", (listing_id,))
        if not listing:
            raise ValueError("Market listing not found or already sold.")
        
        if listing["seller_id"] == buyer_id:
            raise ValueError("You cannot buy your own market listing.")

        buyer = await self.get_or_create_player(buyer_id)
        price = listing["price_coins"]
        if buyer["coins"] < price:
            raise ValueError(f"Insufficient Coins! You need {price:,} coins.")

        # Deduct from buyer
        await self.execute("UPDATE players SET coins = coins - ? WHERE user_id = ?", (price, buyer_id))
        # Credit seller (after 5% market tax)
        payout = int(price * 0.95)
        await self.execute("UPDATE players SET coins = coins + ? WHERE user_id = ?", (payout, listing["seller_id"]))
        # Increment market sales stat
        await self.execute("UPDATE player_stats SET market_sales = market_sales + 1 WHERE user_id = ?", (listing["seller_id"],))
        # Remove listing
        await self.execute("DELETE FROM market_listings WHERE listing_id = ?", (listing_id,))

        return listing

    # Leaderboards & Quests Helpers

    async def get_leaderboard_pvp(self, limit: int = 10) -> List[aiosqlite.Row]:
        """Fetch top players by PvP rating."""
        return await self.fetchall("SELECT user_id, pvp_rating, coins FROM players ORDER BY pvp_rating DESC LIMIT ?", (limit,))

    async def get_leaderboard_coins(self, limit: int = 10) -> List[aiosqlite.Row]:
        """Fetch richest players by coin balance."""
        return await self.fetchall("SELECT user_id, coins, sigils FROM players ORDER BY coins DESC LIMIT ?", (limit,))

    async def unlock_title(self, user_id: int, title_id: str) -> None:
        """Unlock cosmetic title for player."""
        await self.execute("INSERT INTO player_titles (user_id, title_id) VALUES (?, ?) ON CONFLICT DO NOTHING", (user_id, title_id))

    async def get_unlocked_titles(self, user_id: int) -> List[aiosqlite.Row]:
        """Get unlocked titles for player."""
        return await self.fetchall("SELECT title_id FROM player_titles WHERE user_id = ?", (user_id,))

    async def set_active_title(self, user_id: int, title_id: str) -> None:
        """Set equipped title."""
        await self.execute("UPDATE players SET title_id = ? WHERE user_id = ?", (title_id, user_id))

db = DatabaseManager()




