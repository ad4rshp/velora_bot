"""
Equipment Item Detail & Repair UI View for Velora.
Allows equipping gear to heroes and repairing durability.
"""

import discord
from aiosqlite import Row
from views.base_view import VeloraView
from utils.embeds import Embeds
from utils.db import db

class EquipmentDetailView(VeloraView):
    """Interactive view for inspecting, equipping, and repairing an equipment piece."""

    def __init__(self, author_id: int, eq_row: Row):
        super().__init__(author_id=author_id, timeout=120.0)
        self.eq_data = dict(eq_row)
        
        # Repair cost calculation: 10 coins per missing durability point
        missing_dur = self.eq_data["max_durability"] - self.eq_data["durability"]
        self.repair_cost = missing_dur * 10

        self.btn_repair = discord.ui.Button(
            label=f"Repair ({self.repair_cost} Coins)",
            style=discord.ButtonStyle.primary,
            emoji="🛠️",
            disabled=(missing_dur == 0),
            row=0
        )
        self.btn_repair.callback = self.repair_callback
        self.add_item(self.btn_repair)

    @staticmethod
    def build_equipment_embed(eq: dict) -> discord.Embed:
        """Construct equipment detail embed."""
        dur_pct = int((eq["durability"] / eq["max_durability"]) * 100)
        dur_bar = "🟢" if dur_pct > 50 else ("🟡" if dur_pct > 20 else "🔴")

        embed = Embeds.base(
            title=f"🛡️ {eq['name']} [{eq['rarity']}]",
            description=f"Slot: **{eq['slot']}** | Quality: **{eq['quality']}%**",
            color=0x0984E3
        )

        embed.add_field(
            name="📊 Stat Modifiers",
            value=(
                f"❤️ HP: `+{eq['stat_hp']}` | ⚔️ ATK: `+{eq['stat_atk']}`\n"
                f"🛡️ DEF: `+{eq['stat_def']}` | ⚡ SPD: `+{eq['stat_spd']}`"
            ),
            inline=False
        )

        embed.add_field(
            name="🔧 Durability",
            value=f"{dur_bar} `{eq['durability']}/{eq['max_durability']}` ({dur_pct}%)",
            inline=True
        )

        status_str = f"Equipped to Hero #{eq['equipped_character_id']}" if eq.get("equipped_character_id") else "Unequipped"
        embed.add_field(name="Status", value=status_str, inline=True)

        return embed

    async def repair_callback(self, interaction: discord.Interaction):
        try:
            await db.repair_equipment(self.author_id, self.eq_data["equipment_id"], self.repair_cost)
            self.eq_data["durability"] = self.eq_data["max_durability"]
            self.btn_repair.disabled = True
            self.btn_repair.label = "Repaired (100%)"
            
            embed = self.build_equipment_embed(self.eq_data)
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send("✅ Equipment repaired to full durability!", ephemeral=True)
        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
