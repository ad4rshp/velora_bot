"""
Centralized Configuration Manager for Velora RPG.
Loads settings from environment variables and default constants.
"""

import os
from dataclasses import dataclass
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    """Velora Bot Configuration Data Class."""
    TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    DEFAULT_PREFIX: str = os.getenv("DEFAULT_PREFIX", "v")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "database/velora.db")

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Embed Theme Colors (Hex values)
    COLOR_PRIMARY: int = 0x6C5CE7     # Sleek modern purple
    COLOR_SUCCESS: int = 0x00B894     # Soft emerald green
    COLOR_ERROR: int = 0xFF7675       # Soft coral red
    COLOR_WARNING: int = 0xFDCB6E     # Warm amber yellow
    COLOR_INFO: int = 0x0984E3        # Deep sky blue
    COLOR_BATTLE: int = 0xD63031      # Dark crimson red
    
    # Gameplay Limits & Defaults
    LEVEL_CAP: int = 100
    MAX_TEAM_SIZE: int = 3
    EQUIPMENT_SLOTS: List[str] = (
        "Weapon", "Helmet", "Armor", "Boots", 
        "Ring", "Necklace", "Artifact", "Pet"
    )
    
    # Rarity Hierarchy
    RARITY_ORDER: List[str] = ("D", "C", "B", "A", "S", "SS")
    
    # Default Cooldowns (in seconds)
    COMMAND_COOLDOWN: float = 2.0
    BATTLE_COOLDOWN: float = 10.0
    MARKET_COOLDOWN: float = 5.0
    
    # Owner User IDs (populated from environment if set, comma separated)
    OWNER_IDS: List[int] = tuple(
        int(x.strip()) for x in os.getenv("OWNER_IDS", "").split(",") if x.strip().isdigit()
    )

    @property
    def is_production(self) -> bool:
        """Check if environment is production."""
        return self.ENVIRONMENT.lower() in ("production", "prod")

    @property
    def is_development(self) -> bool:
        """Check if environment is development."""
        return not self.is_production

    def validate(self) -> List[str]:
        """Validate configuration settings and return missing variable warnings."""
        warnings = []
        if not self.TOKEN:
            warnings.append("DISCORD_TOKEN environment variable is not set!")
        if not self.OWNER_IDS:
            warnings.append("OWNER_IDS environment variable is empty. No bot owners registered!")
        return warnings

config = Config()

