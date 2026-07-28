"""
Game Constants, Character Class Identities, and Formula Calculations for Velora RPG.
"""

from typing import Dict, Any, List

# Rarity Multiplier Scaling
RARITY_MULTIPLIERS: Dict[str, float] = {
    "D": 1.0,
    "C": 1.25,
    "B": 1.55,
    "A": 1.95,
    "S": 2.45,
    "SS": 3.10
}

# XP Required for level N formula: level * 100 + (level ** 1.5) * 20
def get_xp_for_level(level: int) -> int:
    """Calculate total XP required to reach next level."""
    if level >= 100:
        return 0
    return int(level * 100 + (level ** 1.5) * 20)

# Starter Character Definitions
STARTER_CHARACTERS: List[Dict[str, Any]] = [
    {
        "id": "knight_01",
        "name": "Knight",
        "class_type": "Knight",
        "resource_type": "Stamina",
        "resource_max": 100,
        "base_rarity": "D",
        "base_hp": 120,
        "base_atk": 18,
        "base_def": 15,
        "base_spd": 10,
        "description": "A frontline warrior who relies on Stamina to unleash powerful Weapon Arts and shield allies."
    },
    {
        "id": "mage_01",
        "name": "Mage",
        "class_type": "Mage",
        "resource_type": "Mana",
        "resource_max": 120,
        "base_rarity": "D",
        "base_hp": 85,
        "base_atk": 25,
        "base_def": 8,
        "base_spd": 12,
        "description": "A master of arcane elementals who channels Mana to cast high-damage Spells from afar."
    },
    {
        "id": "archer_01",
        "name": "Archer",
        "class_type": "Archer",
        "resource_type": "Focus",
        "resource_max": 100,

        "base_rarity": "D",
        "base_hp": 95,
        "base_atk": 22,
        "base_def": 10,
        "base_spd": 16,
        "description": "A agile marksman managing Stamina and Arrow supply to deliver multi-hit ranged volleys."
    },
    {
        "id": "assassin_01",
        "name": "Assassin",
        "class_type": "Assassin",
        "resource_type": "Energy",
        "resource_max": 100,
        "base_rarity": "D",
        "base_hp": 80,
        "base_atk": 26,
        "base_def": 7,
        "base_spd": 20,
        "description": "A lethal shadow striker utilizing rapidly regenerating Energy to land devastating critical blows."
    },
    {
        "id": "guardian_01",
        "name": "Guardian",
        "class_type": "Guardian",
        "resource_type": "Stamina",
        "resource_max": 120,
        "base_rarity": "D",
        "base_hp": 150,
        "base_atk": 14,
        "base_def": 22,
        "base_spd": 8,
        "description": "An impenetrable wall absorbing massive damage and protecting the party with high HP and Defense."
    },
    {
        "id": "necromancer_01",
        "name": "Necromancer",
        "class_type": "Necromancer",
        "resource_type": "Mana",
        "resource_max": 100,
        "base_rarity": "D",
        "base_hp": 90,
        "base_atk": 21,
        "base_def": 11,
        "base_spd": 11,
        "description": "A dark warlock wielding Mana to drain opponent vitality and siphon life back to themselves."
    }
]

def calculate_stats(
    base_hp: int, base_atk: int, base_def: int, base_spd: int,
    level: int, rarity: str
) -> Dict[str, int]:
    """
    Calculate effective stats based on base stats, level (1-100), and rarity tier (D-SS).
    Formula: stat = (base_stat + (level - 1) * growth) * rarity_mult
    """
    rarity_mult = RARITY_MULTIPLIERS.get(rarity, 1.0)
    level_scale = (level - 1) * 0.12  # Stat gains per level
    
    hp = int((base_hp + base_hp * level_scale) * rarity_mult)
    atk = int((base_atk + base_atk * level_scale) * rarity_mult)
    defense = int((base_def + base_def * level_scale) * rarity_mult)
    spd = int((base_spd + base_spd * (level_scale * 0.5)) * rarity_mult)
    
    return {
        "hp": hp,
        "atk": atk,
        "def": defense,
        "spd": spd
    }

    
# Starter Scroll Catalog Definitions
STARTER_SCROLLS: List[Dict[str, Any]] = [
    {
        "id": "scroll_slash",
        "name": "Heavy Slash",
        "scroll_type": "Attack",
        "power": 35,
        "cooldown": 1,
        "status_chance": 0,
        "required_class_tags": "Knight,Guardian",
        "description": "A heavy physical strike utilizing weapon momentum."
    },
    {
        "id": "scroll_fireball",
        "name": "Fireball",
        "scroll_type": "Attack",
        "power": 45,
        "cooldown": 2,
        "status_chance": 20,
        "required_class_tags": "Mage,Necromancer",
        "description": "Hurls a fiery orb inflicting high damage with a chance to Burn."
    },
    {
        "id": "scroll_quickshot",
        "name": "Rapid Fire",
        "scroll_type": "Multi-hit",
        "power": 20,
        "cooldown": 2,
        "status_chance": 10,
        "required_class_tags": "Archer",
        "description": "Fires 3 rapid arrows in quick succession."
    },
    {
        "id": "scroll_shadowstrike",
        "name": "Shadow Strike",
        "scroll_type": "Priority",
        "power": 40,
        "cooldown": 3,
        "status_chance": 30,
        "required_class_tags": "Assassin",
        "description": "Strikes instantly before enemy turn with high Critical chance."
    },
    {
        "id": "scroll_ironwall",
        "name": "Iron Bastion",
        "scroll_type": "Support",
        "power": 0,
        "cooldown": 3,
        "status_chance": 100,
        "required_class_tags": "Knight,Guardian",
        "description": "Bolsters party Defense by 30% for 2 turns."
    },
    {
        "id": "scroll_lifedrain",
        "name": "Vampiric Drain",
        "scroll_type": "Status",
        "power": 30,
        "cooldown": 2,
        "status_chance": 100,
        "required_class_tags": "Necromancer",
        "description": "Deals damage and restores HP equal to 50% of damage dealt."
    },
    {
        "id": "scroll_passive_thickhide",
        "name": "Thick Hide",
        "scroll_type": "Passive",
        "power": 0,
        "cooldown": 0,
        "status_chance": 0,
        "required_class_tags": "Knight,Guardian",
        "description": "Permanently increases HP by 15%."
    },
    {
        "id": "scroll_passive_focus",
        "name": "Arcane Focus",
        "scroll_type": "Passive",
        "power": 0,
        "cooldown": 0,
        "status_chance": 0,
        "required_class_tags": "Mage,Necromancer",
        "description": "Permanently increases Magic Attack by 15%."
    }
]

import random

EQUIPMENT_NAMES_CATALOG: Dict[str, Dict[str, List[str]]] = {
    "Weapon": {
        "D": ["Iron Longsword", "Apprentice Wand", "Hunting Bow", "Shadow Daggers", "Iron Warhammer", "Bone Reaper Scythe", "Radiant Spear", "Blessed Warhammer", "Primal Elemental Staff"],
        "C": ["Steel Broadsword", "Rune Wand", "Recurve Bow", "Assassin Blade", "Battle Axe", "Soul Scythe", "Guarded Spear", "Paladin Mace", "Arcane Staff"],
        "B": ["Paladin Greatsword", "Starlight Crystal Staff", "Windrunner Composite Bow", "Nightstalker Katana", "Bulwark Tower Shield", "Grimoire of Souls", "Lance of the Valkyrie", "Sacred Bastion Shield", "Tempest Crystal Orb"],
        "A": ["Mythic Claymore", "Archon Spellstaff", "Falcon Featherbow", "Venom Shadowblade", "Titan Shield", "Reaper Harvester", "Celestial Spear", "Holy Crusader Mace", "Storm Orb"],
        "S": ["Excalibur Holy Sword", "Archmage Staff of Eternity", "Artemis Celestial Longbow", "Eclipse Death Blades", "Aegis of the Immortal", "Death God Reaper Scythe", "Gungnir Divine Spear", "Mjolnir Holy Bulwark", "Aetherial Primordial Staff"],
        "SS": ["Divine Executioner Excalibur", "Omnipotent Archmage Staff", "Godseye Artemis Longbow", "Infinite Eclipse Daggers", "Aegis of Supreme Gods", "Eternal Soul Reaper Scythe", "Absolute Gungnir Spear", "Sacred Mjolnir of Archangels", "Genesis Aetherial Staff"]
    },
    "Armor": {
        "D": ["Iron Armor", "Leather Vest", "Cloth Robe", "Steel Plate Armor"],
        "C": ["Reinforced Steel Armor", "Chainmail Vest", "Silk Arcane Robe"],
        "B": ["Knight Paladin Armor", "Shadow Leather Armor", "Archmage Robe"],
        "A": ["Mythic Mithril Armor", "Nightstalker Armor", "Empress Celestial Robe"],
        "S": ["Dragon Scale Mail", "Aegis Guardian Armor", "Divine Archangel Robe"],
        "SS": ["Godly Dragon Lord Plate", "Infinite Void Armor", "Genesis Supreme Robes"]
    },
    "Helmet": {
        "D": ["Iron Helm", "Leather Cap", "Cloth Hood"],
        "C": ["Reinforced Steel Helm", "Hunter Mask", "Arcane Hood"],
        "B": ["Knight Crusader Crown", "Shadow Mask", "Wizard Crown"],
        "A": ["Mythic Mithril Crown", "Nightstalker Hood", "Empress Arcane Crown"],
        "S": ["Crown of Kings", "Dragon Scale Helm", "Divine Halo Crown"],
        "SS": ["Godly Crown of All Kings", "Infinite Void Helmet", "Genesis Celestial Crown"]
    },
    "Boots": {
        "D": ["Windrider Boots", "Leather Greaves", "Cloth Shoes"],
        "C": ["Reinforced Steel Boots", "Shadow Boots", "Arcane Shoes"],
        "B": ["Knight Paladin Sabatons", "Nightstalker Treads", "Wizard Striders"],
        "A": ["Mythic Mithril Boots", "Swift Treads", "Empress Striders"],
        "S": ["Hermes Winged Sandals", "Dragon Scale Sabatons", "Divine Swift Shoes"],
        "SS": ["Godly Hermes Winged Boots", "Infinite Void Sabatons", "Genesis Celestial Striders"]
    }
}

def generate_random_equipment(slot: str, name: str = None) -> Dict[str, Any]:
    """Generate randomized equipment with rarity, quality, stats, and durability."""
    rarities = ["D", "C", "B", "A", "S", "SS"]
    weights = [50, 25, 15, 7, 2.5, 0.5]
    rarity = random.choices(rarities, weights=weights)[0]
    quality = random.randint(1, 100)
    
    q_mult = 0.5 + (quality / 100) * 0.75  # Quality scaling 0.5x to 1.25x
    r_mult = RARITY_MULTIPLIERS.get(rarity, 1.0)
    
    base_val = int(10 * r_mult * q_mult)
    
    # Slot stat focus
    hp = base_val * 5 if slot in ("Helmet", "Armor", "Pet") else base_val * 2
    atk = base_val * 3 if slot in ("Weapon", "Artifact", "Ring") else base_val
    defense = base_val * 3 if slot in ("Armor", "Helmet", "Boots") else base_val
    spd = base_val * 2 if slot in ("Boots", "Necklace") else base_val // 2
    
    if not name:
        slot_cat = EQUIPMENT_NAMES_CATALOG.get(slot, EQUIPMENT_NAMES_CATALOG["Armor"])
        names_list = slot_cat.get(rarity, slot_cat["D"])
        name = random.choice(names_list)

    return {
        "name": name,
        "slot": slot,
        "rarity": rarity,
        "quality": quality,
        "durability": 100,
        "max_durability": 100,
        "stat_hp": hp,
        "stat_atk": atk,
        "stat_def": defense,
        "stat_spd": spd
    }


def roll_new_equipment_stats(current_slot: str) -> Dict[str, Any]:
    """Reroll equipment stats simultaneously (OwO style)."""
    return generate_random_equipment(current_slot)

