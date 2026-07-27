"""
Velora Discord RPG — Main Entry Point.
Subclasses commands.Bot, initializes database connection, dynamic prefix,
and loads cogs modularly.
"""

import asyncio
import os
import sys
import discord
from discord.ext import commands

from config import config
from utils.db import db
from utils.logger import bot_logger, error_logger
from utils.errors import global_on_command_error

async def get_prefix(bot: commands.Bot, message: discord.Message) -> str:
    """Dynamic prefix lookup per guild with fallback to config default."""
    if not message.guild:
        return config.DEFAULT_PREFIX
    return await db.get_guild_prefix(message.guild.id)

class VeloraBot(commands.Bot):
    """Custom Bot Subclass for Velora RPG Monolith Application."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            help_command=None,  # Custom help command implemented in GeneralCog
            owner_ids=set(config.OWNER_IDS) if config.OWNER_IDS else None
        )

    async def setup_hook(self) -> None:
        """Executed during bot startup before connecting to Discord WebSocket."""
        bot_logger.info("Initializing database connection...")
        await db.connect()

        bot_logger.info("Loading cogs...")
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        if os.path.exists(cogs_dir):
            for filename in os.listdir(cogs_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    cog_name = f"cogs.{filename[:-3]}"
                    try:
                        await self.load_extension(cog_name)
                        bot_logger.info(f"Loaded cog extension: '{cog_name}'")
                    except Exception as e:
                        error_logger.error(f"Failed to load cog '{cog_name}': {e}")

        bot_logger.info("Syncing slash command tree (/help)...")
        if self.application_id:
            try:
                synced = await self.tree.sync()
                bot_logger.info(f"Synced {len(synced)} slash commands.")
            except Exception as e:
                error_logger.error(f"Failed to sync slash commands: {e}")


    async def on_ready(self) -> None:
        """Triggered when bot connects to Discord."""
        bot_logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        bot_logger.info(f"Connected to {len(self.guilds)} guilds.")
        activity = discord.Game(name=f"Velora RPG | {config.DEFAULT_PREFIX}help")
        await self.change_presence(activity=activity)

    async def close(self) -> None:
        """Graceful shutdown hook closing database connection."""
        bot_logger.info("Closing database connection...")
        await db.close()
        await super().close()

def main():
    """Bot runner entry point."""
    if not config.TOKEN:
        bot_logger.error("No DISCORD_TOKEN found in environment variables or .env file.")
        print("❌ Error: DISCORD_TOKEN is missing. Please set it in .env file.")
        sys.exit(1)

    bot = VeloraBot()
    bot.add_listener(global_on_command_error, "on_command_error")

    try:
        bot.run(config.TOKEN)
    except KeyboardInterrupt:
        bot_logger.info("Received exit signal (KeyboardInterrupt). Exiting...")

if __name__ == "__main__":
    main()
