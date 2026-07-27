"""
Interactive Starter Character Selection UI View for Velora.
Allows new players to inspect classes and choose their starter hero.
"""

import discord
from typing import List, Dict, Any, Optional
from views.base_view import VeloraView
from utils.embeds import Embeds
from utils.db import db
from utils.constants import calculate_stats

class StarterSelect(discord.ui.Select):
    """Dropdown menu listing available starter character classes."""

    def __init__(self, startermeta: List[Dict[str, Any]]):
        options = [
            discord.SelectOption(
                label=char["name"],
                value=char.get("character_id", char.get("id")),
                description=f"Class: {char['class_type']} | Resource: {char['resource_type']}",
                emoji=self._get_emoji(char["class_type"])
            )
            for char in startermeta
        ]
        target_count = min(3, len(options))
        super().__init__(
            placeholder=f"⚔️ Select your 3 starter heroes (pick {target_count})...",
            min_values=target_count,
            max_values=target_count,
            options=options,
            row=0
        )
        self.startermeta = {char.get("character_id", char.get("id")): char for char in startermeta}


    def _get_emoji(self, class_type: str) -> str:
        emojis = {
            "Knight": "⚔️",
            "Mage": "🔮",
            "Archer": "🏹",
            "Assassin": "🗡️",
            "Guardian": "🛡️",
            "Necromancer": "💀",
            "Valkyrie": "⚡",
            "Paladin": "✝️",
            "Elementalist": "🔥"
        }
        return emojis.get(class_type, "✨")


    async def callback(self, interaction: discord.Interaction):
        view: StarterView = self.view
        view.selected_ids = self.values
        
        embed = discord.Embed(
            title="⚔️ 3-Hero Team Choice Preview",
            description="You have selected the following 3 starter heroes for your 3v3 battle team:\n───────────",
            color=0x6C5CE7
        )
        for char_id in view.selected_ids:
            char = self.startermeta[char_id]
            embed.add_field(
                name=f"{self._get_emoji(char['class_type'])} {char['name']}",
                value=f"Class: **{char['class_type']}** | Resource: **{char['resource_type']}**",
                inline=True
            )

        view.confirm_btn.disabled = False
        await interaction.response.edit_message(embed=embed, view=view)


class StarterView(VeloraView):
    """Container view for 3-hero starter team selection."""

    def __init__(self, author_id: int, startermeta: List[Dict[str, Any]]):
        super().__init__(author_id=author_id, timeout=180.0)
        self.startermeta = startermeta
        self.selected_ids: List[str] = []
        
        self.select_menu = StarterSelect(startermeta)
        self.add_item(self.select_menu)
        
        self.confirm_btn = discord.ui.Button(
            label="Confirm 3-Hero Team",
            style=discord.ButtonStyle.success,
            emoji="✅",
            disabled=True,
            row=1
        )
        self.confirm_btn.callback = self.confirm_callback
        self.add_item(self.confirm_btn)

    async def confirm_callback(self, interaction: discord.Interaction):
        if not self.selected_ids:
            return

        try:
            claimed_list = await db.claim_starter_characters(self.author_id, self.selected_ids)
            for child in self.children:
                child.disabled = True

            hero_names = ", ".join(f"**{c['name']}** ({c['class_type']})" for c in claimed_list)
            embed = Embeds.success(
                "🎉 3-Hero Team Claimed!",
                f"Your 3v3 starter battle team is ready:\n{hero_names}\n\n"
                f"Starter weapons have been automatically equipped for all 3 heroes!\n"
                f"Use `vbattle` to fight or `vprofile` to check your team."
            )
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()

        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)

