"""
PvP Duel Challenge Accept/Deny View for Velora RPG.
Sends an interactive challenge invitation to a target player before starting a PvP duel.
"""

import discord
from views.base_view import VeloraView
from utils.embeds import Embeds

class BattleChallengeView(VeloraView):
    """Interactive view for accepting or declining a PvP battle duel."""

    def __init__(self, challenger_id: int, target_id: int, start_callback):
        super().__init__(author_id=target_id, timeout=60.0)
        self.challenger_id = challenger_id
        self.target_id = target_id
        self.start_callback = start_callback
        self.accepted = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target_id:
            await interaction.response.send_message(
                "❌ This challenge is for the challenged player to accept or deny.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Accept Duel", style=discord.ButtonStyle.success, emoji="⚔️", row=0)
    async def btn_accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.accepted = True
        for child in self.children:
            child.disabled = True
        
        await interaction.response.send_message("⚔️ **Duel Accepted!** Preparing battle arena...", ephemeral=False)
        self.stop()
        await self.start_callback(interaction)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger, emoji="🛡️", row=0)
    async def btn_deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        
        embed = Embeds.info(
            "Duel Declined",
            f"<@{self.target_id}> declined the PvP battle challenge."
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def on_timeout(self) -> None:
        if not self.accepted and self.message:
            for child in self.children:
                child.disabled = True
            embed = Embeds.warning(
                "Challenge Expired",
                "The PvP duel challenge timed out waiting for a response."
            )
            try:
                await self.message.edit(embed=embed, view=self)
            except Exception:
                pass
