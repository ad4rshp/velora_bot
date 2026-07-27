"""
Base UI View with Interaction Ownership Validation for Velora.
Ensures only the initiating user can click buttons or select items.
"""

import discord
from typing import Optional

class VeloraView(discord.ui.View):
    """
    Standard Base View for Velora UI components.
    Enforces interaction ownership checks and timeout cleanup.
    """

    def __init__(self, author_id: int, timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.author_id: int = author_id
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Validate if interaction was triggered by the view's author."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ This UI menu belongs to another player.",
                ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        """Disable all interactive items when view times out."""
        if self.message:
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(view=self)
            except (discord.NotFound, discord.HTTPException):
                pass
