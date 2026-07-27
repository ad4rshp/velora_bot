"""
Reusable Discord Embed Factory for Velora RPG.
Enforces consistent color palette, layout, and visual formatting across commands.
"""

import discord
from typing import Optional
from config import config

class Embeds:
    """Embed factory providing consistent rich formatting for all UI interfaces."""

    @staticmethod
    def base(
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: int = config.COLOR_PRIMARY,
        footer_text: str = "Velora RPG",
        footer_icon: Optional[str] = None
    ) -> discord.Embed:
        """Construct standard base embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        embed.set_footer(text=footer_text, icon_url=footer_icon)
        return embed

    @staticmethod
    def success(title: str, description: str) -> discord.Embed:
        """Success notification embed (Green)."""
        return Embeds.base(
            title=f"✅ {title}",
            description=description,
            color=config.COLOR_SUCCESS
        )

    @staticmethod
    def error(title: str = "Error", description: str = "That action couldn't be completed.") -> discord.Embed:
        """User-friendly error notification embed (Red/Coral)."""
        return Embeds.base(
            title=f"❌ {title}",
            description=description,
            color=config.COLOR_ERROR
        )

    @staticmethod
    def warning(title: str, description: str) -> discord.Embed:
        """Warning notification embed (Amber)."""
        return Embeds.base(
            title=f"⚠️ {title}",
            description=description,
            color=config.COLOR_WARNING
        )

    @staticmethod
    def info(title: str, description: str) -> discord.Embed:
        """Information embed (Blue)."""
        return Embeds.base(
            title=f"ℹ️ {title}",
            description=description,
            color=config.COLOR_INFO
        )

    @staticmethod
    def battle(title: str, description: str) -> discord.Embed:
        """Battle system embed (Crimson Red)."""
        return Embeds.base(
            title=f"⚔️ {title}",
            description=description,
            color=config.COLOR_BATTLE
        )
