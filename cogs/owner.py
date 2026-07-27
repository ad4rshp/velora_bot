"""
Owner Utility Cog for Velora.
Restricted commands for bot maintainers (reload cogs, backup DB, shutdown).
"""

import discord
from discord.ext import commands
import shutil
from datetime import datetime
from pathlib import Path
from utils.embeds import Embeds
from utils.logger import admin_logger
from config import config

class OwnerCog(commands.Cog, name="Owner"):
    """Bot Owner Maintenance & Administration."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Check if user is bot owner."""
        return await self.bot.is_owner(ctx.author)

    async def cog_command_error(self, ctx: commands.Context, error: Exception):
        """Silently ignore command invocations by non-owners with zero response."""
        if isinstance(error, (commands.CheckFailure, commands.NotOwner, commands.MissingPermissions)):
            return  # Silently ignore for regular players!


    @commands.command(name="reload")
    async def reload_cog(self, ctx: commands.Context, extension: str = "all"):
        """Reload one or all cogs."""
        if extension.lower() == "all":
            reloaded = []
            for ext in list(self.bot.extensions.keys()):
                await self.bot.reload_extension(ext)
                reloaded.append(ext)
            admin_logger.info(f"Owner {ctx.author} reloaded all extensions: {reloaded}")
            await ctx.send(embed=Embeds.success("Reload Complete", f"Reloaded `{len(reloaded)}` cogs."))
        else:
            target = f"cogs.{extension}" if not extension.startswith("cogs.") else extension
            await self.bot.reload_extension(target)
            admin_logger.info(f"Owner {ctx.author} reloaded extension '{target}'")
            await ctx.send(embed=Embeds.success("Reload Complete", f"Reloaded `{target}`."))

    @commands.command(name="backupdb")
    async def backup_database(self, ctx: commands.Context):
        """Create a timestamped backup of the database file."""
        db_file = Path(config.DATABASE_PATH)
        if not db_file.exists():
            await ctx.send(embed=Embeds.error("Backup Failed", "Database file does not exist yet."))
            return

        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"database_{timestamp}.db"

        shutil.copy2(db_file, backup_path)
        admin_logger.info(f"Owner {ctx.author} created database backup at '{backup_path}'")
        await ctx.send(embed=Embeds.success("Backup Created", f"Saved copy to `{backup_path}`"))

    @commands.command(name="getdb", aliases=["vdb", "fetchdb", "downloaddb"])
    async def fetch_database(self, ctx: commands.Context):
        """Fetch and attach the live database.db file directly in Discord."""
        db_file = Path(config.DATABASE_PATH)
        if not db_file.exists():
            await ctx.send(embed=Embeds.error("DB Fetch Failed", "Database file does not exist."))
            return

        file = discord.File(str(db_file), filename="database.db")
        embed = Embeds.success(
            "Live Database Export",
            f"Attached live SQLite database file (`{db_file.name}`)."
        )
        try:
            await ctx.author.send(embed=embed, file=file)
            await ctx.send(embed=Embeds.info("Database Sent", "Sent live database export to your direct messages!"))
        except discord.Forbidden:
            await ctx.send(embed=embed, file=file)

    @commands.command(name="shutdown")

    async def shutdown_bot(self, ctx: commands.Context):
        """Gracefully close connections and shut down the bot."""
        admin_logger.info(f"Owner {ctx.author} requested bot shutdown.")
        await ctx.send(embed=Embeds.warning("Shutdown", "Velora is shutting down gracefully..."))
        await self.bot.close()

    @commands.command(name="ban")
    async def ban_user(self, ctx: commands.Context, user: discord.User, *, reason: str = "Violation of terms"):
        """Ban a user from interacting with Velora."""
        from utils.db import db
        await db.execute("INSERT INTO banned_users (user_id, reason) VALUES (?, ?) ON CONFLICT DO NOTHING", (user.id, reason))
        admin_logger.info(f"Owner {ctx.author} banned user {user} ({user.id}): {reason}")
        await ctx.send(embed=Embeds.success("User Banned", f"Banned **{user.display_name}** ({user.id}) from using Velora."))

    @commands.command(name="unban")
    async def unban_user(self, ctx: commands.Context, user: discord.User):
        """Unban a user."""
        from utils.db import db
        await db.execute("DELETE FROM banned_users WHERE user_id = ?", (user.id,))
        admin_logger.info(f"Owner {ctx.author} unbanned user {user} ({user.id})")
        await ctx.send(embed=Embeds.success("User Unbanned", f"Unbanned **{user.display_name}** ({user.id})."))

    @commands.command(name="blacklist")
    async def blacklist_server(self, ctx: commands.Context, guild_id: int, *, reason: str = "Restricted server"):
        """Blacklist a server from using Velora."""
        from utils.db import db
        await db.execute("INSERT INTO blacklisted_guilds (guild_id, reason) VALUES (?, ?) ON CONFLICT DO NOTHING", (guild_id, reason))
        admin_logger.info(f"Owner {ctx.author} blacklisted guild {guild_id}: {reason}")
        await ctx.send(embed=Embeds.success("Server Blacklisted", f"Blacklisted Guild ID `{guild_id}`."))

    @commands.command(name="unblacklist")
    async def unblacklist_server(self, ctx: commands.Context, guild_id: int):
        """Unblacklist a server."""
        from utils.db import db
        await db.execute("DELETE FROM blacklisted_guilds WHERE guild_id = ?", (guild_id,))
        admin_logger.info(f"Owner {ctx.author} unblacklisted guild {guild_id}")
        await ctx.send(embed=Embeds.success("Server Unblacklisted", f"Unblacklisted Guild ID `{guild_id}`."))

    @commands.command(name="givecoins")
    async def give_coins(self, ctx: commands.Context, target: discord.User, amount: int):
        """Grant coins to a player."""
        from utils.db import db
        await db.get_or_create_player(target.id)
        await db.execute("UPDATE players SET coins = coins + ? WHERE user_id = ?", (amount, target.id))
        admin_logger.info(f"Owner {ctx.author} gave {amount} coins to {target} ({target.id})")
        await ctx.send(embed=Embeds.success("Coins Granted", f"Granted **{amount:,} Coins** to **{target.display_name}**."))

    @commands.command(name="givesigils")
    async def give_sigils(self, ctx: commands.Context, target: discord.User, amount: int):
        """Grant sigils to a player."""
        from utils.db import db
        await db.get_or_create_player(target.id)
        await db.execute("UPDATE players SET sigils = sigils + ? WHERE user_id = ?", (amount, target.id))
        admin_logger.info(f"Owner {ctx.author} gave {amount} sigils to {target} ({target.id})")
        await ctx.send(embed=Embeds.success("Sigils Granted", f"Granted **{amount:,} Sigils** to **{target.display_name}**."))

    @commands.command(name="givehero")
    async def give_hero(self, ctx: commands.Context, target: discord.User, character_id: str):
        """Grant any catalog hero to a player."""
        from utils.db import db
        cat_char = await db.get_catalog_character_by_id(character_id.lower() + "_01" if not character_id.endswith("_01") else character_id.lower())
        if not cat_char:
            await ctx.send(embed=Embeds.error("Invalid Character", f"Character ID `{character_id}` not found in catalog."))
            return

        await db.execute(
            """
            INSERT INTO player_characters (user_id, character_id, level, xp, rarity, is_active)
            VALUES (?, ?, 1, 0, ?, 0)
            """,
            (target.id, cat_char["character_id"], cat_char["base_rarity"])
        )
        admin_logger.info(f"Owner {ctx.author} gave hero {cat_char['name']} to {target} ({target.id})")
        await ctx.send(embed=Embeds.success("Hero Granted", f"Granted **{cat_char['name']}** ({cat_char['class_type']}) to **{target.display_name}**."))

    @commands.command(name="givegear")
    async def give_gear(self, ctx: commands.Context, target: discord.User, slot: str = "Weapon"):
        """Grant forged gear item to a player."""
        from utils.db import db
        from utils.constants import generate_random_equipment
        new_eq = generate_random_equipment(slot.capitalize())
        item = await db.add_equipment(target.id, new_eq)
        admin_logger.info(f"Owner {ctx.author} gave {item['name']} gear to {target} ({target.id})")
        await ctx.send(embed=Embeds.success("Gear Granted", f"Granted **{item['name']}** [{item['rarity']}] (ID #{item['equipment_id']}) to **{target.display_name}**."))

    @commands.command(name="resetplayer")
    async def reset_player(self, ctx: commands.Context, target: discord.User):
        """Reset a player's profile data."""
        from utils.db import db
        await db.execute("DELETE FROM player_characters WHERE user_id = ?", (target.id,))
        await db.execute("DELETE FROM player_equipment WHERE user_id = ?", (target.id,))
        await db.execute("DELETE FROM player_consumables WHERE user_id = ?", (target.id,))
        await db.execute("DELETE FROM player_stats WHERE user_id = ?", (target.id,))
        await db.execute("DELETE FROM players WHERE user_id = ?", (target.id,))
        admin_logger.info(f"Owner {ctx.author} reset player data for {target} ({target.id})")
        await ctx.send(embed=Embeds.warning("Player Reset", f"Reset all profile, hero, and equipment data for **{target.display_name}**."))

    @commands.command(name="adminhelp", aliases=["ahelp", "vadmin"])
    async def admin_help(self, ctx: commands.Context):
        """Display the administrator command directory board."""
        prefix = ctx.prefix if hasattr(ctx, "prefix") else "v"
        embed = discord.Embed(
            title="⚙️ ADMINISTRATOR CONTROL DIRECTORY",
            description="Restricted commands for bot owners and maintainers.\n───────────",
            color=0x6C5CE7
        )

        embed.add_field(
            name="💰 **ECONOMY & CURRENCY**",
            value=(
                f"• `{prefix}givecoins @User <amount>` — Grant coins to player\n"
                f"• `{prefix}givesigils @User <amount>` — Grant sigils to player\n"
                f"• `{prefix}spawnchest @User <common/rare>` — Spawn chest items"
            ),
            inline=False
        )

        embed.add_field(
            name="⚔️ **HERO & GEAR MANAGEMENT**",
            value=(
                f"• `{prefix}givehero @User <class>` — Grant hero from catalog\n"
                f"• `{prefix}givegear @User [slot]` — Grant forged gear piece\n"
                f"• `{prefix}setlevel @User <1-100>` — Set active hero level\n"
                f"• `{prefix}setrarity @User <D-SS>` — Set active hero rarity\n"
                f"• `{prefix}addtitle @User <title>` — Unlock custom cosmetic title"
            ),
            inline=False
        )

        embed.add_field(
            name="🛡️ **MODERATION & SYSTEM**",
            value=(
                f"• `{prefix}ban @User [reason]` — Bot ban user\n"
                f"• `{prefix}unban @User` — Bot unban user\n"
                f"• `{prefix}blacklist <guild_id>` — Blacklist server\n"
                f"• `{prefix}resetplayer @User` — Reset player profile\n"
                f"• `{prefix}reload [cog/all]` — Dynamic cog reload\n"
                f"• `{prefix}backupdb` — Create timestamped DB backup\n"
                f"• `{prefix}botstats` — System resource statistics"
            ),
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name="setlevel")
    async def set_level(self, ctx: commands.Context, target: discord.User, level: int):
        """Set player's active hero level (1-100)."""
        if not (1 <= level <= 100):
            await ctx.send(embed=Embeds.error("Invalid Level", "Level must be between 1 and 100."))
            return

        from utils.db import db
        chars = await db.get_player_characters(target.id)
        active = next((c for c in chars if c["is_active"]), chars[0] if chars else None)
        if not active:
            await ctx.send(embed=Embeds.error("No Hero", f"**{target.display_name}** does not own any heroes."))
            return

        await db.execute("UPDATE player_characters SET level = ? WHERE instance_id = ?", (level, active["instance_id"]))
        admin_logger.info(f"Owner {ctx.author} set level {level} for {target} hero {active['name']}")
        await ctx.send(embed=Embeds.success("Level Updated", f"Set **{target.display_name}**'s active hero **{active['name']}** to Level **{level}**."))

    @commands.command(name="setrarity")
    async def set_rarity(self, ctx: commands.Context, target: discord.User, rarity: str):
        """Set player's active hero rarity (D, C, B, A, S, SS)."""
        valid_rarities = ["D", "C", "B", "A", "S", "SS"]
        target_rarity = rarity.upper()
        if target_rarity not in valid_rarities:
            await ctx.send(embed=Embeds.error("Invalid Rarity", f"Rarity must be one of: {', '.join(valid_rarities)}."))
            return

        from utils.db import db
        chars = await db.get_player_characters(target.id)
        active = next((c for c in chars if c["is_active"]), chars[0] if chars else None)
        if not active:
            await ctx.send(embed=Embeds.error("No Hero", f"**{target.display_name}** does not own any heroes."))
            return

        await db.execute("UPDATE player_characters SET rarity = ? WHERE instance_id = ?", (target_rarity, active["instance_id"]))
        admin_logger.info(f"Owner {ctx.author} set rarity {target_rarity} for {target} hero {active['name']}")
        await ctx.send(embed=Embeds.success("Rarity Updated", f"Set **{target.display_name}**'s active hero **{active['name']}** to **[{target_rarity}]**."))

    @commands.command(name="spawnchest")
    async def spawn_chest(self, ctx: commands.Context, target: discord.User, chest_type: str = "common"):
        """Spawn a common or rare chest in player inventory."""
        from utils.db import db
        item_id = "rare_chest" if chest_type.lower() == "rare" else "common_chest"
        await db.add_consumable(target.id, item_id, 1)
        admin_logger.info(f"Owner {ctx.author} spawned 1x {item_id} for {target}")
        await ctx.send(embed=Embeds.success("Chest Spawned", f"Spawned **1x {item_id.replace('_', ' ').title()}** in **{target.display_name}**'s inventory."))

    @commands.command(name="addtitle")
    async def add_title(self, ctx: commands.Context, target: discord.User, *, title_name: str):
        """Grant a custom cosmetic title to a player."""
        from utils.db import db
        await db.unlock_title(target.id, title_name)
        admin_logger.info(f"Owner {ctx.author} unlocked title '{title_name}' for {target}")
        await ctx.send(embed=Embeds.success("Title Unlocked", f"Unlocked title **[{title_name}]** for **{target.display_name}**."))

    @commands.command(name="botstats")
    async def sys_botstats(self, ctx: commands.Context):
        """Display system and database statistics for developers."""

        from utils.db import db
        players_cnt = await db.fetchone("SELECT count(*) as cnt FROM players")
        chars_cnt = await db.fetchone("SELECT count(*) as cnt FROM player_characters")
        eq_cnt = await db.fetchone("SELECT count(*) as cnt FROM player_equipment")
        mkt_cnt = await db.fetchone("SELECT count(*) as cnt FROM market_listings")

        embed = discord.Embed(
            title="⚙️ Velora System Statistics",
            color=0x6C5CE7
        )
        embed.add_field(name="Connected Guilds", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="Registered Players", value=f"`{players_cnt['cnt']}`", inline=True)
        embed.add_field(name="Heroes In Existence", value=f"`{chars_cnt['cnt']}`", inline=True)
        embed.add_field(name="Equipment Items", value=f"`{eq_cnt['cnt']}`", inline=True)
        embed.add_field(name="Market Listings", value=f"`{mkt_cnt['cnt']}`", inline=True)
        embed.add_field(name="Websocket Latency", value=f"`{round(self.bot.latency * 1000)} ms`", inline=True)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCog(bot))


