"""
Character Detail & Management View for Velora.
Displays detailed character attributes, level/XP progress, and actions (e.g. Set Active).
"""

import discord
from aiosqlite import Row
from views.base_view import VeloraView
from utils.embeds import Embeds
from utils.db import db
from utils.constants import calculate_stats, get_xp_for_level

class CharacterDetailView(VeloraView):
    """Interactive view for inspecting and managing a single character instance."""

    def __init__(self, author_id: int, char_row: Row):
        super().__init__(author_id=author_id, timeout=120.0)
        self.char_data = dict(char_row)
        
        self.btn_set_active = discord.ui.Button(
            label="Set Active Hero",
            style=discord.ButtonStyle.primary if not self.char_data.get("is_active") else discord.ButtonStyle.success,
            emoji="⚔️",
            disabled=bool(self.char_data.get("is_active")),
            row=0
        )
        self.btn_set_active.callback = self.set_active_callback
        self.add_item(self.btn_set_active)


    @staticmethod
    def build_character_embed(char: dict) -> discord.Embed:
        """Construct compact character card embed."""
        level = char["level"]
        xp = char["xp"]
        needed_xp = get_xp_for_level(level)
        rarity = char["rarity"]
        
        stats = calculate_stats(
            char["base_hp"], char["base_atk"], char["base_def"], char["base_spd"],
            level=level, rarity=rarity
        )
        
        active_badge = " ⭐" if char.get("is_active") else ""
        
        embed = discord.Embed(
            title=f"{char['name']}{active_badge}",
            description=f"Class: **{char['class_type']}** | Rarity: **[{rarity}]** | Level: **{level}**\n─────────────────────────────────────",
            color=0x6C5CE7
        )

        embed.add_field(
            name="Attributes",
            value=f"HP: `{stats['hp']}`  |  ATK: `{stats['atk']}`  |  DF: `{stats['def']}`  |  SP: `{stats['spd']}`\n───────────",
            inline=False
        )


        from utils.movesets import get_scaled_moveset, get_class_passive
        passive = get_class_passive(char["class_type"])
        moveset = get_scaled_moveset(char["class_type"], rarity=rarity)

        embed.add_field(
            name=f"Passive — {passive['name']}",
            value=f"*{passive['desc']}*\n───────────",
            inline=False
        )

        basic = moveset["basic"]
        skill = moveset["skill"]
        ult = moveset["ultimate"]

        s_lock = "" if level >= skill[5] else f" *(Unlocks Lvl {skill[5]})*"
        u_lock = "" if level >= ult[5] else f" *(Unlocks Lvl {ult[5]})*"

        embed.add_field(
            name=f"Moveset [{rarity} Tier]",
            value=(
                f"• **{basic[0]}**: {basic[1]} (`{basic[2]}` Pwr)\n"
                f"• **{skill[0]}**: {skill[1]} (`{skill[2]}` Pwr){s_lock}\n"
                f"• **{ult[0]}**: {ult[1]} (`{ult[2]}` Pwr){u_lock}\n───────────"
            ),
            inline=False
        )

        if needed_xp > 0:
            pct = int(min(1.0, xp / needed_xp) * 100)
            xp_str = f"`{xp}/{needed_xp}` ({pct}%)"
        else:
            xp_str = "`MAX`"

        embed.add_field(
            name="Status & Loadout",
            value=(
                f"• Resource: `{char['resource_type']}` (`{char['resource_max']}` Max)\n"
                f"• XP Progress: {xp_str}\n"
                f"• Equipped Weapon: **{char.get('equipped_weapon_name', 'Starter Gear')}**"
            ),
            inline=False
        )

        return embed





    async def set_active_callback(self, interaction: discord.Interaction):
        await db.set_active_character(self.author_id, self.char_data["instance_id"], slot=1)
        self.char_data["is_active"] = 1
        
        self.btn_set_active.disabled = True
        self.btn_set_active.style = discord.ButtonStyle.success
        self.btn_set_active.label = "Active Hero"
        
        embed = self.build_character_embed(self.char_data)
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send("✅ Set as your active hero for battles!", ephemeral=True)


RARITY_COLORS = {
    "D": 0xA0A0A0,
    "C": 0x2ECC71,
    "B": 0x3498DB,
    "A": 0x9B59B6,
    "S": 0xF1C40F,
    "SS": 0xE74C3C
}

RARITY_ORDER = ["D", "C", "B", "A", "S", "SS"]
RARITY_SIGIL_COSTS = {
    "D": 10,
    "C": 15,
    "B": 25,
    "A": 40,
    "S": 60,
    "SS": 100
}

RARITY_FAIL_RATES = {
    "D": 0.10,  # 10% fail
    "C": 0.20,  # 20% fail
    "B": 0.30,  # 30% fail
    "A": 0.40,  # 40% fail
    "S": 0.50,  # 50% fail
    "SS": 0.65  # 65% fail
}

def get_reroll_cost(rarity: str) -> int:
    """Calculate dynamic sigil cost based on hero rarity tier."""
    return RARITY_SIGIL_COSTS.get(rarity.upper(), 25)

def get_reroll_fail_rate(rarity: str) -> float:
    """Calculate dynamic failure rate based on hero rarity tier."""
    return RARITY_FAIL_RATES.get(rarity.upper(), 0.30)

class CharacterRerollView(VeloraView):
    """Interactive view for character rarity rerolls with dynamic sigil costs and failure risk."""


    _active_sessions: set = set()  # Tracks user IDs with pending reroll views

    def __init__(self, author_id: int, target_char: dict, new_rarity: str, failed: bool = False):
        super().__init__(author_id=author_id, timeout=120.0)
        self.target_char = target_char
        self.current_rarity = target_char["rarity"]
        self.new_rarity = new_rarity
        self.failed = failed  # True if this reroll attempt failed
        CharacterRerollView._active_sessions.add(author_id)

        self.btn_accept = discord.ui.Button(label="Accept New Rarity", style=discord.ButtonStyle.success, emoji="✅", row=0)
        self.btn_accept.callback = self.accept_callback
        self.add_item(self.btn_accept)

        cost = get_reroll_cost(self.current_rarity)
        self.btn_reroll = discord.ui.Button(label=f"Reroll ({cost} 🔮)", style=discord.ButtonStyle.primary, emoji="🎲", row=0)
        self.btn_reroll.callback = self.reroll_again_callback
        self.add_item(self.btn_reroll)

        self.btn_keep = discord.ui.Button(label="Keep Original", style=discord.ButtonStyle.secondary, emoji="🛡️", row=0)
        self.btn_keep.callback = self.keep_callback
        self.add_item(self.btn_keep)

    def build_comparison_embed(self) -> discord.Embed:
        from utils.constants import calculate_stats
        old_stats = calculate_stats(
            self.target_char["base_hp"], self.target_char["base_atk"],
            self.target_char["base_def"], self.target_char["base_spd"],
            level=self.target_char["level"], rarity=self.current_rarity
        )
        new_stats = calculate_stats(
            self.target_char["base_hp"], self.target_char["base_atk"],
            self.target_char["base_def"], self.target_char["base_spd"],
            level=self.target_char["level"], rarity=self.new_rarity
        )

        def diff_str(new_val, old_val):
            d = new_val - old_val
            return f"**{new_val}** (`+{d}`)" if d >= 0 else f"**{new_val}** (`{d}`)"

        color = RARITY_COLORS.get(self.new_rarity, 0x6C5CE7)
        cost = get_reroll_cost(self.current_rarity)
        embed = discord.Embed(
            title=f"🎲 Hero Rarity Reroll — {self.target_char['name']}",
            description=(
                f"Class: **{self.target_char['class_type']}** | Level: **{self.target_char['level']}**\n───────────"
            ),
            color=color
        )


        embed.add_field(
            name=f"Current Rarity: [{self.current_rarity}]",
            value=(
                f"HP: `{old_stats['hp']}`\n"
                f"ATK: `{old_stats['atk']}`\n"
                f"DF: `{old_stats['def']}`\n"
                f"SP: `{old_stats['spd']}`"
            ),
            inline=True
        )

        embed.add_field(
            name=f"New Rolled: [{self.new_rarity}]",
            value=(
                f"HP: {diff_str(new_stats['hp'], old_stats['hp'])}\n"
                f"ATK: {diff_str(new_stats['atk'], old_stats['atk'])}\n"
                f"DF: {diff_str(new_stats['def'], old_stats['def'])}\n"
                f"SP: {diff_str(new_stats['spd'], old_stats['spd'])}"
            ),
            inline=True
        )


        embed.set_footer(text="Accept to finalize your rolled rarity tier.")
        return embed

    def _release_session(self):
        CharacterRerollView._active_sessions.discard(self.author_id)

    async def on_timeout(self) -> None:
        self._release_session()
        await super().on_timeout()

    async def accept_callback(self, interaction: discord.Interaction):
        import random
        from utils.db import db
        
        fail_rate = get_reroll_fail_rate(self.current_rarity)
        
        for child in self.children:
            child.disabled = True
        self._release_session()

        # Risk calculation upon clicking Accept
        if random.random() < fail_rate:
            embed = Embeds.error(
                "Reroll Failed",
                f"The magic fizzled! The attempt failed and **{self.target_char['name']}** remained at Rarity **[{self.current_rarity}]**."
            )
        else:
            await db.execute(
                "UPDATE player_characters SET rarity = ? WHERE instance_id = ?",
                (self.new_rarity, self.target_char["instance_id"])
            )
            embed = Embeds.success(
                "Hero Rarity Updated!",
                f"Updated **{self.target_char['name']}** ({self.target_char['class_type']}) to Rarity **[{self.new_rarity}]**!"
            )
            
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def reroll_again_callback(self, interaction: discord.Interaction):
        import random
        from utils.db import db
        cost = get_reroll_cost(self.current_rarity)
        try:
            await db.consume_sigils(interaction.user.id, cost)
        except ValueError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)
            return

        rarities = ["D", "C", "B", "A", "S", "SS"]
        weights = [45, 30, 16, 6.5, 2.0, 0.5]
        self.new_rarity = random.choices(rarities, weights=weights)[0]

        self.btn_reroll.label = f"Reroll ({cost} 🔮)"
        embed = self.build_comparison_embed()
        await interaction.response.edit_message(embed=embed, view=self)




    async def keep_callback(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        self._release_session()
        embed = Embeds.info(
            "Reroll Kept",
            f"Kept original rarity **[{self.current_rarity}]** for **{self.target_char['name']}**."
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()


