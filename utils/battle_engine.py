"""
3v3 Turn-Based Battle Engine for Velora RPG.
Handles combatant stats, turn state, terrain effects, 3v3 switching rules,
damage calculation, and win condition evaluation.
"""

import random
from typing import List, Dict, Any, Optional

class Combatant:
    """Represents a hero combatant on the battlefield or bench with status condition tracking."""

    def __init__(self, instance_id: int, name: str, class_type: str, stats: Dict[str, int], resource_type: str, resource_max: int):
        self.instance_id = instance_id
        self.name = name
        self.class_type = class_type
        self.max_hp = stats["hp"]
        self.current_hp = stats["hp"]
        self.atk = stats["atk"]
        self.defense = stats["def"]
        self.spd = stats["spd"]
        self.resource_type = resource_type
        self.max_resource = resource_max
        self.current_resource = resource_max
        self.is_ko = False
        self.status_effects: Dict[str, int] = {}  # e.g., {"Burn": 2, "Stun": 1, "Poison": 3, "Shield": 2}

    def apply_status(self, effect: str, turns: int = 2) -> None:
        """Apply a status condition to combatant."""
        self.status_effects[effect] = turns

    def tick_status_effects(self) -> List[str]:
        """Process turn-start status ticks (Burn damage, Poison, etc.). Returns log entries."""
        logs = []
        expired = []
        for effect, turns in list(self.status_effects.items()):
            if effect == "Burn":
                dmg = max(3, int(self.max_hp * 0.08))
                self.take_damage(dmg)
                logs.append(f"🔥 **{self.name}** suffers {dmg} Burn damage!")
            elif effect == "Poison":
                dmg = max(4, int(self.max_hp * 0.10))
                self.take_damage(dmg)
                logs.append(f"🧪 **{self.name}** takes {dmg} Poison damage!")
            
            self.status_effects[effect] -= 1
            if self.status_effects[effect] <= 0:
                expired.append(effect)

        for e in expired:
            del self.status_effects[e]
            logs.append(f"✨ **{self.name}** recovered from {e}!")
        return logs

    def take_damage(self, amount: int) -> int:
        """Apply damage and check KO status, accounting for Shield."""
        if "Shield" in self.status_effects:
            amount = max(1, int(amount * 0.6))  # 40% damage reduction
        actual_damage = max(1, amount)
        self.current_hp = max(0, self.current_hp - actual_damage)
        if self.current_hp == 0:
            self.is_ko = True
        return actual_damage

    def consume_resource(self, amount: int) -> bool:
        """Deduct resource if available, return True if successful."""
        if self.current_resource >= amount:
            self.current_resource -= amount
            return True
        return False

    def regenerate_resource(self, amount: int = 5) -> None:
        """Regenerate resource up to max at turn end."""
        self.current_resource = min(self.max_resource, self.current_resource + amount)

    def hp_bar(self) -> str:
        """Generate clean HP status string with active status indicators."""
        status_icons = ""
        if "Burn" in self.status_effects: status_icons += " 🔥"
        if "Stun" in self.status_effects: status_icons += " ⚡"
        if "Poison" in self.status_effects: status_icons += " 🧪"
        if "Shield" in self.status_effects: status_icons += " 🛡️"
        return f"❤️ **{self.current_hp}/{self.max_hp}** HP{status_icons}"

    def resource_bar(self) -> str:
        """Generate clean Resource status string."""
        return f"⚡ **{self.current_resource}/{self.max_resource}** {self.resource_type}"





class BattleSide:
    """Represents a player's 3v3 team side."""

    def __init__(self, user_id: int, display_name: str, team: List[Combatant]):
        self.user_id = user_id
        self.display_name = display_name
        self.team = team  # Up to 3 combatants
        self.active_index = 0

    @property
    def active_hero(self) -> Combatant:
        return self.team[self.active_index]

    @property
    def bench_heroes(self) -> List[Combatant]:
        return [c for idx, c in enumerate(self.team) if idx != self.active_index]

    def has_alive_heroes(self) -> bool:
        return any(not c.is_ko for c in self.team)

    def auto_switch_next_alive(self) -> Optional[int]:
        """Find next available alive combatant after KO."""
        for idx, c in enumerate(self.team):
            if not c.is_ko:
                self.active_index = idx
                return idx
        return None

class BattleEngine:
    """Turn-based 3v3 match engine."""

    def __init__(self, side_a: BattleSide, side_b: BattleSide):
        self.side_a = side_a
        self.side_b = side_b
        
        # Turn state
        self.current_side = side_a if side_a.active_hero.spd >= side_b.active_hero.spd else side_b
        self.opponent_side = side_b if self.current_side == side_a else side_a
        
        self.round_number = 1
        self.active_terrain = "Normal"
        self.battle_logs: List[str] = ["⚔️ The battle has begun!"]
        self.is_finished = False
        self.winner_side: Optional[BattleSide] = None

    def log(self, text: str) -> None:
        """Append log entry."""
        self.battle_logs.append(text)

    def switch_active(self, side: BattleSide, new_index: int, consumes_turn: bool = True) -> bool:
        """Switch active hero with a bench hero."""
        if new_index < 0 or new_index >= len(side.team):
            return False
        
        target = side.team[new_index]
        if target.is_ko or new_index == side.active_index:
            return False

        old_name = side.active_hero.name
        side.active_index = new_index
        self.log(f"🔄 **{side.display_name}** switched to **{target.name}**!")

        if consumes_turn and not self.is_finished:
            self._end_turn()
        return True

    def execute_heal(self, healer_side: BattleSide, skill_name: str = "Healing Light", power: int = 40, resource_cost: int = 25) -> Dict[str, Any]:
        """Execute healing turn restoring health to active combatant or lowest HP ally."""
        healer = healer_side.active_hero

        status_logs = healer.tick_status_effects()
        for log_msg in status_logs:
            self.log(log_msg)

        if "Stun" in healer.status_effects:
            self.log(f"⚡ **{healer.name}** is Stunned and cannot move!")
            healer.regenerate_resource(5)
            self._end_turn()
            return {"finished": self.is_finished, "winner": self.winner_side, "stunned": True}

        resource_success = healer.consume_resource(resource_cost)
        if not resource_success:
            self.log(f"⚠️ **{healer.name}** does not have enough resource to cast **{skill_name}**!")
            healer.regenerate_resource(10)
            self._end_turn()
            return {"finished": self.is_finished, "winner": self.winner_side, "no_resource": True}

        # Calculate healing amount: power + healer.atk * 0.5
        heal_amt = max(15, int(power + healer.atk * 0.5))
        
        # Target lowest HP living hero on the side
        target_hero = min([c for c in healer_side.team if not c.is_ko], key=lambda c: c.current_hp / max(1, c.max_hp))
        old_hp = target_hero.current_hp
        target_hero.current_hp = min(target_hero.max_hp, target_hero.current_hp + heal_amt)
        healed_diff = target_hero.current_hp - old_hp

        self.log(f"💚 **{healer.name}**: **{skill_name}** → **{target_hero.name}** (+{healed_diff} HP restored)")

        healer.regenerate_resource(5)
        self._end_turn()
        return {"finished": self.is_finished, "winner": self.winner_side, "healed": True}

    def execute_attack(self, attacker_side: BattleSide, defender_side: BattleSide, attack_name: str = "Basic Attack", power: int = 30, resource_cost: int = 15) -> Dict[str, Any]:

        """Execute attack turn with resource consumption, miss checks, and defense mitigation."""
        attacker = attacker_side.active_hero
        defender = defender_side.active_hero

        # Process active status ticks on turn start
        status_logs = attacker.tick_status_effects()
        for log_msg in status_logs:
            self.log(log_msg)

        # Check Stun skip
        if "Stun" in attacker.status_effects:
            self.log(f"⚡ **{attacker.name}** is Stunned and cannot move!")
            attacker.regenerate_resource(5)
            self._end_turn()
            return {"finished": self.is_finished, "winner": self.winner_side, "stunned": True}

        # Resource check & exhaustion
        resource_success = attacker.consume_resource(resource_cost)
        exhausted = not resource_success

        # Base Accuracy & Miss Check
        base_accuracy = 95.0
        if attacker.class_type in ("Archer", "Assassin"):
            base_accuracy = 85.0 if exhausted else 95.0
        elif attacker.class_type in ("Mage", "Necromancer"):
            base_accuracy = 80.0 if exhausted else 92.0
        elif exhausted:
            base_accuracy = 75.0

        # Speed difference modifier
        speed_diff = (attacker.spd - defender.spd) * 0.5
        final_accuracy = max(50.0, min(98.0, base_accuracy + speed_diff))

        # Roll hit check
        roll = random.uniform(0.0, 100.0)
        if roll > final_accuracy:
            self.log(f"💨 **{attacker.name}** missed **{defender.name}**!")
            attacker.regenerate_resource(10)
            self._end_turn()
            return {"finished": self.is_finished, "winner": self.winner_side, "missed": True}

        # Terrain multipliers
        terrain_mult = 1.2 if self.active_terrain == "Firestorm" and attacker.class_type == "Mage" else 1.0

        # Damage Mitigation Formula (Punchy 12-16 turn 3v3 pace)
        power_mult = (power / 15.0) if not exhausted else (power / 15.0 * 0.6)
        def_mitigation = 100.0 / (100.0 + (defender.defense * 0.5))
        raw_damage = max(1.0, attacker.atk * power_mult * def_mitigation * terrain_mult)

        variance = random.uniform(0.92, 1.08)
        final_damage = max(1, int(raw_damage * variance))

        dealt = defender.take_damage(final_damage)
        self.log(f"⚔️ **{attacker.name}**: **{attack_name}** → **{defender.name}** ({dealt} dmg)")

        # Status Application Triggers based on move/class type
        if "Fire" in attack_name or attacker.class_type in ("Mage", "Elementalist"):
            if random.random() < 0.25:
                defender.apply_status("Burn", 2)
                self.log(f"🔥 **{defender.name}** was Burned!")
        elif "Shield" in attack_name or "Wall" in attack_name or attacker.class_type in ("Guardian", "Paladin"):
            attacker.apply_status("Shield", 2)
            self.log(f"🛡️ **{attacker.name}** raised a Defense Shield!")
        elif "Stun" in attack_name or "Shadow" in attack_name:
            if random.random() < 0.20:
                defender.apply_status("Stun", 1)
                self.log(f"⚡ **{defender.name}** was Stunned!")

        # Regenerate small resource each turn
        attacker.regenerate_resource(5)

        # Check KO
        if defender.is_ko:
            self.log(f"💀 **{defender.name}** KO'd!")
            next_idx = defender_side.auto_switch_next_alive()
            if next_idx is not None:
                new_hero = defender_side.active_hero
                self.log(f"📢 **{defender_side.display_name}** sent out **{new_hero.name}**!")
            else:
                self.is_finished = True
                self.winner_side = attacker_side
                self.log(f"🏆 **{attacker_side.display_name}** wins!")
                return {"finished": True, "winner": attacker_side}

        self._end_turn()
        return {"finished": self.is_finished, "winner": self.winner_side, "missed": False}




    def _end_turn(self) -> None:
        """Swap active turn sides and increment round counter."""
        self.current_side, self.opponent_side = self.opponent_side, self.current_side
        self.round_number += 1
