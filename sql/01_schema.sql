-- Velora RPG Database Schema Definition

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER PRIMARY KEY,
    prefix TEXT NOT NULL DEFAULT 'v',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS players (
    user_id INTEGER PRIMARY KEY,
    coins INTEGER NOT NULL DEFAULT 1000,
    sigils INTEGER NOT NULL DEFAULT 10,
    title_id TEXT DEFAULT NULL,
    pvp_rating INTEGER NOT NULL DEFAULT 1000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE IF NOT EXISTS player_equipment (
    equipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    slot TEXT NOT NULL,
    compatible_class TEXT NOT NULL DEFAULT 'All',
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

CREATE TABLE IF NOT EXISTS player_scrolls (
    instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    scroll_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE,
    FOREIGN KEY (scroll_id) REFERENCES scrolls(scroll_id)
);

CREATE TABLE IF NOT EXISTS character_loadouts (
    character_instance_id INTEGER NOT NULL,
    slot_index INTEGER NOT NULL,
    scroll_instance_id INTEGER NOT NULL,
    PRIMARY KEY (character_instance_id, slot_index),
    FOREIGN KEY (character_instance_id) REFERENCES player_characters(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (scroll_instance_id) REFERENCES player_scrolls(instance_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS player_consumables (
    user_id INTEGER NOT NULL,
    item_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, item_id),
    FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS market_listings (
    listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    item_type TEXT NOT NULL,
    item_data_json TEXT NOT NULL,
    price_coins INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES players(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS player_titles (
    user_id INTEGER NOT NULL,
    title_id TEXT NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, title_id),
    FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS player_quests (
    quest_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    quest_type TEXT NOT NULL,
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

CREATE TABLE IF NOT EXISTS equipment_catalog (
    item_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slot TEXT NOT NULL,
    compatible_class TEXT NOT NULL,
    base_rarity TEXT NOT NULL DEFAULT 'D',
    base_hp INTEGER NOT NULL DEFAULT 0,
    base_atk INTEGER NOT NULL DEFAULT 0,
    base_def INTEGER NOT NULL DEFAULT 0,
    base_spd INTEGER NOT NULL DEFAULT 0,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS banned_users (
    user_id INTEGER PRIMARY KEY,
    reason TEXT NOT NULL,
    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blacklisted_guilds (
    guild_id INTEGER PRIMARY KEY,
    reason TEXT NOT NULL,
    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bot_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

