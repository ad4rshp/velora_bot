"""
General Utility Cog for Velora RPG.
Contains prefix commands: ping, prefix management, and help interfaces.
"""

import discord
from discord.ext import commands
from utils.embeds import Embeds
from utils.db import db
from views.paginator import PaginatorView

class GeneralCog(commands.Cog, name="General"):
    """Server & general utility commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping", aliases=["latency"])
    async def ping(self, ctx: commands.Context):

        """Check bot latency."""
        latency_ms = round(self.bot.latency * 1000)
        embed = Embeds.info(
            "Velora Latency",
            f"📡 Websocket Latency: **{latency_ms} ms**"
        )
        await ctx.send(embed=embed)

    @commands.command(name="prefix")
    @commands.has_permissions(manage_guild=True)
    async def set_prefix(self, ctx: commands.Context, new_prefix: str = None):
        """View or change server command prefix (Requires Manage Server permission)."""
        if not ctx.guild:
            await ctx.send(embed=Embeds.error("Server Only", "Prefix can only be changed inside a Discord server."))
            return

        if not new_prefix:
            current_prefix = await db.get_guild_prefix(ctx.guild.id)
            await ctx.send(embed=Embeds.info("Server Prefix", f"Current prefix in this server is: `{current_prefix}`"))
            return

        if len(new_prefix) > 5:
            await ctx.send(embed=Embeds.warning("Prefix Too Long", "Prefix cannot exceed 5 characters."))
            return

        await db.set_guild_prefix(ctx.guild.id, new_prefix)
        await ctx.send(embed=Embeds.success("Prefix Updated", f"Server prefix changed to `{new_prefix}`"))

    @commands.command(name="settings", aliases=["vsettings", "config", "vconfig", "setup"])
    @commands.has_permissions(manage_guild=True)
    async def server_settings(self, ctx: commands.Context, key: str = None, *, value: str = None):
        """Inspect or configure server settings (Requires Manage Server permission)."""
        if not ctx.guild:
            await ctx.send(embed=Embeds.error("Server Only", "Settings can only be configured inside a Discord server."))
            return

        from settings import settings_manager
        guild_settings = await settings_manager.get_guild_settings(ctx.guild.id)

        if not key:
            embed = discord.Embed(
                title=f"⚙️ Server Setup & Settings — {ctx.guild.name}",
                description="Use `vsettings <key> <value>` to update settings.\n───────────",
                color=0x6C5CE7
            )
            embed.add_field(name="`prefix`", value=f"`{guild_settings['prefix']}`", inline=True)
            embed.add_field(name="`auto_clean_market`", value=f"`{'Enabled' if guild_settings.get('auto_clean_market') else 'Disabled'}`", inline=True)
            embed.set_footer(text="Requires Manage Server permission.")
            await ctx.send(embed=embed)
            return

        key_lower = key.lower()
        if key_lower == "prefix":
            if not value:
                await ctx.send(embed=Embeds.error("Missing Value", f"Usage: `{guild_settings['prefix']}settings prefix <new_prefix>`"))
                return
            await settings_manager.update_setting(ctx.guild.id, "prefix", value.strip())
            await db.set_guild_prefix(ctx.guild.id, value.strip())
            await ctx.send(embed=Embeds.success("Prefix Updated", f"Updated server prefix to `{value.strip()}`"))
        else:
            await ctx.send(embed=Embeds.error("Invalid Key", f"Unknown setting key `{key}`. Valid keys: `prefix`, `auto_clean_market`."))


    @commands.command(name="help", aliases=["h"])
    async def help_prefix(self, ctx: commands.Context):
        """Display interactive paginated help menu."""
        prefix = ctx.prefix if hasattr(ctx, "prefix") else "v"
        pages = self._build_help_pages(prefix, ctx.author)
        view = PaginatorView(author_id=ctx.author.id, pages=pages)
        view.message = await ctx.send(embed=pages[0], view=view)

    @discord.app_commands.command(name="help", description="Discover Velora RPG commands and systems.")
    async def help_slash(self, interaction: discord.Interaction):
        """Slash command version of /help for discoverability."""
        prefix = "v"
        if interaction.guild_id:
            prefix = await db.get_guild_prefix(interaction.guild_id)
        pages = self._build_help_pages(prefix, interaction.user)
        view = PaginatorView(author_id=interaction.user.id, pages=pages)
        await interaction.response.send_message(embed=pages[0], view=view, ephemeral=True)

    def _build_help_pages(self, prefix: str, user: discord.User) -> list[discord.Embed]:
        """Construct clean, relevant multi-page help guide."""
        # Page 1: Overview
        p1 = discord.Embed(

            title="⚔️ VELORA RPG — COMMAND DIRECTORY",
            description=(
                f"Prefix: `{prefix}` | Server Prefix Setting: `{prefix}prefix <new>`\n"
                f"─────────────────────────────────────\n\n"
                f"**🚀 Quick Start Commands:**\n\n"
                f"• `{prefix}start` ── Claim starter hero squad & weapons\n\n"
                f"• `{prefix}profile` ── View wallet balance & main hero\n\n"
                f"• `{prefix}info [hero]` ── View hero attributes & stats\n\n"
                f"• `{prefix}select <hero> [slot]` ── Configure active battle roster\n\n"
                f"• `{prefix}battle` ── Enter turn-based combat arena\n"
                f"─────────────────────────────────────"
            ),
            color=0x6C5CE7
        )

        # Page 2: Heroes & Roster
        p2 = discord.Embed(
            title="⚔️ HEROES & ROSTER COMMANDS",
            description=f"─────────────────────────────────────",
            color=0x6C5CE7
        )
        p2.add_field(name=f"`{prefix}start`", value="Claim starter hero squad & weapons.\n───────────", inline=False)
        p2.add_field(name=f"`{prefix}profile` (alias: `{prefix}p`, `{prefix}prof`)", value="View player wallet, rating, and lead hero.\n───────────", inline=False)
        p2.add_field(name=f"`{prefix}info [hero]` (alias: `{prefix}char`)", value="Inspect detailed hero attributes & movesets.\n───────────", inline=False)
        p2.add_field(name=f"`{prefix}team` (alias: `{prefix}vteam`, `{prefix}squad`)", value="Manage your active 3-hero battle roster.\n───────────", inline=False)
        p2.add_field(name=f"`{prefix}select <hero> [slot]` (alias: `{prefix}vselect`)", value="Assign a hero to battle lineup slot (1, 2, or 3).\n───────────", inline=False)
        p2.add_field(name=f"`{prefix}rerollhero [hero]` (alias: `{prefix}rrh`, `{prefix}rh`)", value="Reroll hero rarity tier.\n───────────", inline=False)

        p2.add_field(name=f"`{prefix}collection` (alias: `{prefix}col`, `{prefix}gallery`)", value="View class discovery gallery & completion stats.\n───────────", inline=False)
        p2.add_field(name=f"`{prefix}inventory` (alias: `{prefix}inv`, `{prefix}bag`)", value="View owned equipment, scrolls, packs, and items.", inline=False)

        # Page 3: Gear & Crafting
        p3 = discord.Embed(
            title="🛡️ GEAR, SCROLLS & CRAFTING",
            description=f"─────────────────────────────────────",
            color=0x0984E3
        )
        p3.add_field(name=f"`{prefix}equipment [slot]` (alias: `{prefix}eqp`, `{prefix}gear`)", value="Inspect gear inventory.\n───────────", inline=False)
        p3.add_field(name=f"`{prefix}equip <gear_#> [hero]` (alias: `{prefix}vequip`, `{prefix}eq`)", value="Equip weapon or armor piece to a hero.\n───────────", inline=False)
        p3.add_field(name=f"`{prefix}forge [slot]` (alias: `{prefix}craft`)", value="Forge class-compatible gear (500 Coins + 2 Sigils).\n───────────", inline=False)
        p3.add_field(name=f"`{prefix}reroll <ID>` (alias: `{prefix}rr`)", value="Reroll equipment stats (10 Sigils).\n───────────", inline=False)
        p3.add_field(name=f"`{prefix}repair <ID>` (alias: `{prefix}r`, `{prefix}rp`)", value="Repair equipment durability.\n───────────", inline=False)
        p3.add_field(name=f"`{prefix}scrolls` (alias: `{prefix}sc`)", value="Browse skill scroll catalog.", inline=False)

        # Page 4: Economy & Market
        p4 = discord.Embed(
            title="🏪 STORE & MARKETPLACE",
            description=f"─────────────────────────────────────",
            color=0x00B894
        )
        p4.add_field(name=f"`{prefix}shop` (alias: `{prefix}s`, `{prefix}store`)", value="Browse General Store for Hero Packs & supplies.\n───────────", inline=False)
        p4.add_field(name=f"`{prefix}sell <gear/hero/scroll> <#ID or rarity>` (alias: `{prefix}vsell`)", value="Salvage gear, scrolls, or heroes for Sigils (🔮).\n───────────", inline=False)
        p4.add_field(name=f"`{prefix}open <item>`", value="Open chests and packs for rewards.\n───────────", inline=False)
        p4.add_field(name=f"`{prefix}market` (alias: `{prefix}m`, `{prefix}mkt`)", value="Player marketplace (`list <id> <price>`, `buy <id>`, `search`).\n───────────", inline=False)
        p4.add_field(name=f"`{prefix}trade @User <coins>` (alias: `{prefix}t`)", value="Direct player-to-player trade with mutual confirmation.", inline=False)


        # Page 5: Combat & Progression
        p5 = discord.Embed(
            title="🏆 COMBAT & PROGRESSION",
            description=f"─────────────────────────────────────",
            color=0xFDCB6E
        )
        p5.add_field(name=f"`{prefix}battle [@User]` (alias: `{prefix}b`, `{prefix}fight`)", value="Initiate turn-based battle against Abyssal Vanguard or challenge a player.\n───────────", inline=False)
        p5.add_field(name=f"`{prefix}battleguide` (alias: `{prefix}bg`, `{prefix}guide`)", value="Tactical combat guide covering roles, elemental fields, and skills.\n───────────", inline=False)
        p5.add_field(name=f"`{prefix}rank [@User]` (alias: `{prefix}vrank`, `{prefix}rating`)", value="View Ranked Tier progress (Unranked to Ascendant) & RP.\n───────────", inline=False)
        p5.add_field(name=f"`{prefix}quests` (alias: `{prefix}q`)", value="View Daily & Weekly Quest progression.\n───────────", inline=False)
        p5.add_field(name=f"`{prefix}stats`", value="View lifetime combat statistics and win rates.\n───────────", inline=False)
        p5.add_field(name=f"`{prefix}top [pvp/coins]` (alias: `{prefix}lb`, `{prefix}leaderboard`)", value="View global leaderboards.\n───────────", inline=False)
        p5.add_field(name=f"`{prefix}title [name]`", value="Equip earned titles.", inline=False)

        for page in (p1, p2, p3, p4, p5):
            page.set_footer(text=f"Requested by {user.display_name}", icon_url=user.display_avatar.url)

        return [p1, p2, p3, p4, p5]




        for page in (p1, p2, p3, p4, p5):
            page.set_footer(text=f"Requested by {user.display_name}", icon_url=user.display_avatar.url)

        return [p1, p2, p3, p4, p5]








async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
