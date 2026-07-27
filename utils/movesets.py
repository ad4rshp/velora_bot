"""
Class Movesets & Level Unlocks for Velora RPG.
Concise, punchy 1-2 word move names to keep Discord Embeds sleek and readable.
"""

CLASS_MOVESETS = {
    "Knight": {
        "basic": ("Slash", "Standard blade strike", 30, 10, "⚔️", 1),
        "skill": ("Shield Bash", "Blunt shield blow", 45, 25, "🛡️", 5),
        "ultimate": ("Holy Slash", "Sacred energy slice", 75, 45, "🔥", 10)
    },
    "Mage": {
        "basic": ("Arcane Bolt", "Concentrated magic bolt", 30, 10, "🔮", 1),
        "skill": ("Lightning", "Surge of electric plasma", 45, 25, "⚡", 5),
        "ultimate": ("Fireball", "Explosive fire orb", 75, 50, "🔥", 10)
    },
    "Archer": {
        "basic": ("Quick Arrow", "Swift precision arrow", 30, 10, "🏹", 1),
        "skill": ("Piercing Shot", "Armor-piercing shaft", 45, 25, "🎯", 5),
        "ultimate": ("Arrow Volley", "Barrage of holy arrows", 75, 45, "💥", 10)
    },
    "Assassin": {
        "basic": ("Dagger Jab", "Swift dagger strike", 30, 10, "🗡️", 1),
        "skill": ("Venom Strike", "Fatal blade slash", 45, 25, "🐍", 5),
        "ultimate": ("Assassinate", "Lethal strike from shadows", 80, 50, "💀", 10)
    },
    "Guardian": {
        "basic": ("Smash", "Heavy mace blow", 30, 10, "🔨", 1),
        "skill": ("Iron Bastion", "Defensive shield impact", 40, 25, "🛡️", 5),
        "ultimate": ("Bulwark Shield", "Unbreakable barrier slam", 65, 45, "🏰", 10)
    },
    "Necromancer": {
        "basic": ("Shadow Bolt", "Dark spirit magic", 30, 10, "💀", 1),
        "skill": ("Life Siphon", "Drains target vitality", 45, 25, "🩸", 5),
        "ultimate": ("Soul Drain", "Devours target soul energy", 70, 50, "🔮", 10)
    },
    "Valkyrie": {
        "basic": ("Spear Thrust", "Piercing spear strike", 30, 10, "🔱", 1),
        "skill": ("Holy Cleave", "Sweeping spear arc", 45, 25, "✨", 5),
        "ultimate": ("Gungnir Thrust", "Celestial spear impale", 75, 45, "⚡", 10)
    },
    "Paladin": {
        "basic": ("Hammer Strike", "Blessed hammer strike", 30, 10, "🔨", 1),
        "skill": ("Sacred Smite", "Holy radiant smite", 45, 25, "✝️", 5),
        "ultimate": ("Radiant Shield", "Radiant aura blast", 65, 45, "🛡️", 10)
    },
    "Elementalist": {
        "basic": ("Primal Flame", "Blasts primal flame", 30, 10, "🔥", 1),
        "skill": ("Tempest", "Whirling lightning surge", 45, 25, "🌩️", 5),
        "ultimate": ("Firestorm", "Apocalyptic inferno", 80, 50, "☄️", 10)
    }
}

CLASS_PASSIVES = {
    "Knight": {"name": "Honor Shield", "desc": "Gains a 🛡️ Shield when HP drops below 30%."},
    "Mage": {"name": "Arcane Mastery", "desc": "Deals 20% extra damage in Firestorm / Mana fields."},
    "Archer": {"name": "Eagle Eye", "desc": "Crit attacks ignore 30% of target Defense."},
    "Assassin": {"name": "Shadow Step", "desc": "25% chance to dodge incoming attacks."},
    "Guardian": {"name": "Unyielding Bastion", "desc": "Takes 25% reduced damage from physical attacks."},
    "Necromancer": {"name": "Vampiric Touch", "desc": "Restores HP equal to 20% of damage dealt."},
    "Valkyrie": {"name": "Divine Light", "desc": "Immune to Stun and Burn status effects."},
    "Paladin": {"name": "Aegis Blessing", "desc": "Regenerates 5% HP at turn start."},
    "Elementalist": {"name": "Primal Surge", "desc": "Attacks have a 30% chance to apply Burn or Stun."}
}

DEFAULT_MOVESET = {
    "basic": ("Strike", "Standard attack", 30, 10, "⚔️", 1),
    "skill": ("Power Strike", "Tactical strike", 45, 25, "💥", 5),
    "ultimate": ("Ultimate", "Devastating move", 75, 45, "🔥", 10)
}

RARITY_POWER_MULT = {
    "D": 1.00,
    "C": 1.05,
    "B": 1.10,
    "A": 1.18,
    "S": 1.25,
    "SS": 1.35
}


def get_class_moveset(class_type: str) -> dict:
    """Retrieve thematic moveset for class."""
    return CLASS_MOVESETS.get(class_type, DEFAULT_MOVESET)

def get_scaled_moveset(class_type: str, rarity: str = "D") -> dict:
    """Retrieve moveset with move power scaled according to hero rarity tier."""
    base = get_class_moveset(class_type)
    mult = RARITY_POWER_MULT.get(rarity.upper(), 1.0)
    
    scaled = {}
    for slot in ("basic", "skill", "ultimate"):
        name, desc, pwr, cost, emoji, lvl = base[slot]
        scaled_pwr = int(pwr * mult)
        scaled[slot] = (name, desc, scaled_pwr, cost, emoji, lvl)
    return scaled

def get_class_passive(class_type: str) -> dict:
    """Retrieve unique passive ability for class."""
    return CLASS_PASSIVES.get(class_type, {"name": "Battle Hardened", "desc": "Standard combat training."})
