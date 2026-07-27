"""
Reusable Button Paginator UI for Velora.
Allows paging through a list of embeds using Discord UI buttons.
"""

import discord
from typing import List
from views.base_view import VeloraView

class PaginatorView(VeloraView):
    """Interactive button paginator for displaying multi-page embeds."""

    def __init__(self, author_id: int, pages: List[discord.Embed], timeout: float = 120.0):
        super().__init__(author_id=author_id, timeout=timeout)
        self.pages: List[discord.Embed] = pages
        self.current_page: int = 0
        self._update_buttons()

    def _update_buttons(self) -> None:
        """Update button enabled states and page indicator label."""
        total = len(self.pages)
        self.btn_first.disabled = self.current_page == 0
        self.btn_prev.disabled = self.current_page == 0
        self.btn_indicator.label = f"{self.current_page + 1} / {total}"
        self.btn_next.disabled = self.current_page >= total - 1
        self.btn_last.disabled = self.current_page >= total - 1

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, row=0)
    async def btn_first(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.primary, row=0)
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.secondary, disabled=True, row=0)
    async def btn_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.primary, row=0)
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, row=0)
    async def btn_last(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = len(self.pages) - 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
