"""
Single Equipment Reroll View for Velora.
Displays side-by-side comparison of current vs new stats and manages Accept/Keep choices.
"""

import discord
from typing import Dict, Any
from views.base_view import VeloraView
from utils.embeds import Embeds
from utils.db import db
from utils.constants import roll_new_equipment_stats

class RerollView(VeloraView):
    """Interactive view for single equipment rerolls."""


    def __init__(self, author_id: int, equipment_id: int, current_stats: Dict[str, Any], new_stats: Dict[str, Any]):
        super().__init__(author_id=author_id, timeout=120.0)
        self.equipment_id = equipment_id
        self.current_stats = current_stats
        self.new_stats = new_stats

        self.btn_accept = discord.ui.Button(
            label="Accept",
            style=discord.ButtonStyle.success,
            emoji="✅",
            row=0
        )
        self.btn_accept.callback = self.accept_callback
        self.add_item(self.btn_accept)

        self.btn_keep = discord.ui.Button(
            label="Keep",
            style=discord.ButtonStyle.secondary,
            emoji="🛡️",
            row=0
        )
        self.btn_keep.callback = self.keep_callback
        self.add_item(self.btn_keep)

        self.btn_again = discord.ui.Button(
            label="Reroll Again",
            style=discord.ButtonStyle.primary,
            emoji="🔮",
            row=0
        )
        self.btn_again.callback = self.again_callback
        self.add_item(self.btn_again)

    @staticmethod
    def build_comparison_embed(current: Dict[str, Any], rolled: Dict[str, Any]) -> discord.Embed:
        """Construct clean equipment reroll comparison embed."""
        embed = discord.Embed(
            title=f"Equipment Reroll — {current['name']}",
            description="─────────────────────────────────────",
            color=0x6C5CE7
        )

        def diff_str(new_v, old_v):
            d = new_v - old_v
            sign = "+" if d >= 0 else ""
            return f"`+{new_v}` ({sign}{d})"

        embed.add_field(
            name=f"Current Roll [{current['rarity']} - {current['quality']}%]",
            value=(
                f"HP: `+{current['stat_hp']}`  ATK: `+{current['stat_atk']}`  DF: `+{current['stat_def']}`  SP: `+{current['stat_spd']}`\n───────────"
            ),
            inline=False
        )

        embed.add_field(
            name=f"New Rolled [{rolled['rarity']} - {rolled['quality']}%]",
            value=(
                f"HP: {diff_str(rolled['stat_hp'], current['stat_hp'])}  ATK: {diff_str(rolled['stat_atk'], current['stat_atk'])}  DF: {diff_str(rolled['stat_def'], current['stat_def'])}  SP: {diff_str(rolled['stat_spd'], current['stat_spd'])}\n───────────"
            ),
            inline=False
        )

        embed.set_footer(text="Accept to apply the new roll, or Keep to retain current stats.")
        return embed



    async def accept_callback(self, interaction: discord.Interaction):
        """Save new roll stats to database."""
        await db.update_equipment_stats(self.equipment_id, self.new_stats)
        
        for child in self.children:
            child.disabled = True

        embed = Embeds.success(
            "Reroll Accepted!",
            f"Updated **{self.new_stats['name']}** to **[{self.new_stats['rarity']}]** Quality **{self.new_stats['quality']}%**!"
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def keep_callback(self, interaction: discord.Interaction):
        """Keep original stats and discard new roll."""
        for child in self.children:
            child.disabled = True

        embed = Embeds.info(
            "Original Stats Retained",
            f"Kept original stats for **{self.current_stats['name']}**."
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def again_callback(self, interaction: discord.Interaction):
        """Deduct 10 Sigils and roll again."""
        try:
            await db.consume_sigils(self.author_id, 10)
            self.new_stats = roll_new_equipment_stats(self.current_stats["slot"])
            embed = self.build_comparison_embed(self.current_stats, self.new_stats)
            await interaction.response.edit_message(embed=embed, view=self)
        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
