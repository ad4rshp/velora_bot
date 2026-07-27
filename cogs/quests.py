"""
Quests, Leaderboards, Titles & Statistics Cog for Velora RPG.
Implements vquests, vstats, vtitle, and vleaderboard/vtop.
"""

import discord
from discord.ext import commands
from utils.embeds import Embeds
from utils.db import db

COSMETIC_TITLES = {
    "champion": {"name": "Arena Champion", "desc": "Awarded for dominating PvP battles."},
    "collector": {"name": "Collector", "desc": "Awarded for assembling a massive hero roster."},
    "explorer": {"name": "Explorer", "desc": "Awarded to brave adventurers."},
    "legend": {"name": "Legend", "desc": "Awarded to mythical players."},
    "completionist": {"name": "Completionist", "desc": "Awarded for achieving 100% mastery."}
}

class QuestsCog(commands.Cog, name="Quests & Progress"):
    """Quests, Leaderboards, Cosmetic Titles & Statistics."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

import random
import datetime
from zoneinfo import ZoneInfo
from discord.ext import tasks

QUEST_POOL = [
    # Daily Quests
    {"key": "daily_battles", "type": "daily", "title": "⚔️ Arena Gladiator", "desc": "Participate in 3 Battles", "target": 3, "reward_coins": 600, "reward_sigils": 3},
    {"key": "daily_wins", "type": "daily", "title": "🏆 Victorious Streak", "desc": "Win 2 Arena Battles", "target": 2, "reward_coins": 800, "reward_sigils": 4},
    {"key": "daily_forge", "type": "daily", "title": "🔨 Master Blacksmith", "desc": "Forge 2 Equipment Pieces", "target": 2, "reward_coins": 500, "reward_sigils": 2},
    {"key": "daily_reroll", "type": "daily", "title": "🎲 Rune Weaver", "desc": "Perform 2 Rerolls", "target": 2, "reward_coins": 400, "reward_sigils": 3},
    {"key": "daily_trade", "type": "daily", "title": "🤝 Merchant Spirit", "desc": "Complete 1 Player Trade or Listing", "target": 1, "reward_coins": 500, "reward_sigils": 2},

    # Weekly Quests
    {"key": "weekly_battles", "type": "weekly", "title": "🛡️ Veteran Warrior", "desc": "Participate in 15 Battles", "target": 15, "reward_coins": 3000, "reward_sigils": 15},
    {"key": "weekly_wins", "type": "weekly", "title": "👑 Conquest Master", "desc": "Win 10 Arena Battles", "target": 10, "reward_coins": 5000, "reward_sigils": 25},
    {"key": "weekly_collector", "type": "weekly", "title": "🎒 Master Collector", "desc": "Collect 10 Equipment Items", "target": 10, "reward_coins": 4000, "reward_sigils": 20},
]

class QuestsCog(commands.Cog, name="Quests & Progress"):
    """Quests, Leaderboards, Cosmetic Titles & Statistics."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ist_tz = ZoneInfo("Asia/Kolkata")
        self.daily_quest_refresh_task.start()

    def cog_unload(self):
        self.daily_quest_refresh_task.cancel()

    @tasks.loop(time=datetime.time(hour=12, minute=0, second=0, tzinfo=ZoneInfo("Asia/Kolkata")))
    async def daily_quest_refresh_task(self):
        """Automated background loop triggering daily quest reset at 12:00 PM IST (06:30 UTC)."""
        await db.execute("DELETE FROM player_quests WHERE quest_type = 'daily'")
        print("[Quests]: Daily quests refreshed successfully at 12:00 PM IST.")

    async def get_or_generate_user_quests(self, user_id: int):
        """Fetch or assign active daily and weekly quests for a player."""
        rows = await db.fetchall("SELECT * FROM player_quests WHERE user_id = ?", (user_id,))
        if not rows:
            await db.get_or_create_player(user_id)
            # Pick 2 daily quests and 1 weekly quest

            daily_candidates = [q for q in QUEST_POOL if q["type"] == "daily"]
            weekly_candidates = [q for q in QUEST_POOL if q["type"] == "weekly"]

            chosen_dailies = random.sample(daily_candidates, 2)
            chosen_weekly = random.sample(weekly_candidates, 1)

            for q in chosen_dailies + chosen_weekly:
                await db.execute(
                    """
                    INSERT INTO player_quests (user_id, quest_type, title, description, target_count, current_count, reward_coins, reward_sigils, is_claimed)
                    VALUES (?, ?, ?, ?, ?, 0, ?, ?, 0)
                    """,
                    (user_id, q["type"], q["title"], q["desc"], q["target"], q["reward_coins"], q["reward_sigils"])
                )
            rows = await db.fetchall("SELECT * FROM player_quests WHERE user_id = ?", (user_id,))
        return rows

    @commands.command(name="quests", aliases=["q"])
    async def quests(self, ctx: commands.Context):
        """View active Daily and Weekly Quests."""
        user_id = ctx.author.id
        quest_rows = await self.get_or_generate_user_quests(user_id)

        # Calculate time remaining until 12:00 PM IST
        now_ist = datetime.datetime.now(self.ist_tz)
        next_refresh = now_ist.replace(hour=12, minute=0, second=0, microsecond=0)
        if now_ist >= next_refresh:
            next_refresh += datetime.timedelta(days=1)
        time_left = next_refresh - now_ist
        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)

        embed = discord.Embed(
            title="Quests Roster",
            description=f"Reset in: **{hours}h {minutes}m** (12:00 PM IST)\n─────────────────────────────────────",
            color=0xFDCB6E
        )

        for q in quest_rows:
            curr = q["current_count"]
            target = q["target_count"]
            status = "Claimed" if q["is_claimed"] else ("Ready (`vclaim <#>`)" if curr >= target else f"({curr}/{target})")
            tag = "Daily" if q["quest_type"] == "daily" else "Weekly"

            embed.add_field(
                name=f"#{q['quest_id']}. [{tag}] {q['title']}",
                value=(
                    f"{q['description']}\n"
                    f"Status: **{status}** | Reward: 🪙 `{q['reward_coins']:,}` Coins  🔮 `{q['reward_sigils']}` Sigils\n───────────"
                ),
                inline=False
            )

        embed.set_footer(text=f"Use 'vclaim <quest_id>' to collect rewards.")
        await ctx.send(embed=embed)


    @commands.command(name="claim", aliases=["claimquest"])
    async def claim_quest(self, ctx: commands.Context, quest_id: int):
        """Claim rewards for a completed quest."""
        user_id = ctx.author.id
        q = await db.fetchone("SELECT * FROM player_quests WHERE quest_id = ? AND user_id = ?", (quest_id, user_id))
        if not q:
            await ctx.send(embed=Embeds.error("Quest Not Found", f"Could not find quest #{quest_id} in your active list."))
            return

        if q["is_claimed"]:
            await ctx.send(embed=Embeds.warning("Already Claimed", "You have already claimed this quest's rewards!"))
            return

        if q["current_count"] < q["target_count"]:
            await ctx.send(embed=Embeds.warning("Incomplete Quest", f"You haven't completed this quest yet! Progress: `{q['current_count']}/{q['target_count']}`."))
            return

        # Grant rewards
        await db.execute("UPDATE players SET coins = coins + ?, sigils = sigils + ? WHERE user_id = ?", (q["reward_coins"], q["reward_sigils"], user_id))
        await db.execute("UPDATE player_quests SET is_claimed = 1 WHERE quest_id = ?", (quest_id,))

        embed = Embeds.success(
            "Quest Claimed!",
            f"Claimed **{q['title']}** rewards:\n🪙 **+{q['reward_coins']:,} Coins**\n🔮 **+{q['reward_sigils']} Sigils**"
        )
        await ctx.send(embed=embed)


    @commands.command(name="stats", aliases=["statistics"])
    async def statistics(self, ctx: commands.Context, target: discord.User = None):
        """View comprehensive gameplay and lifetime statistics."""
        user = target or ctx.author
        stats = await db.fetchone("SELECT * FROM player_stats WHERE user_id = ?", (user.id,))
        player = await db.get_or_create_player(user.id)

        if not stats:
            await ctx.send(embed=Embeds.info("No Statistics", f"No gameplay stats recorded yet for {user.display_name}."))
            return

        battles = stats["pvp_battles"]
        wins = stats["pvp_wins"]
        winrate = f"{(wins / battles * 100):.1f}%" if battles > 0 else "0.0%"

        embed = Embeds.base(
            title="📊 Lifetime Statistics — " + user.display_name,
            color=0x6C5CE7
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        embed.add_field(
            name="⚔️ PvP Combat",
            value=(
                f"Rating: **{player['pvp_rating']}**\n"
                f"Battles: `{battles}` | Wins: `{wins}` | Losses: `{stats['pvp_losses']}`\n"
                f"Win Rate: `{winrate}` | Streak: `{stats['win_streak']}` (Max: `{stats['highest_win_streak']}`)"
            ),
            inline=False
        )

        embed.add_field(
            name="💰 Economy & Trades",
            value=(
                f"Coins Balance: `🪙 {player['coins']:,}`\n"
                f"Sigils Balance: `🔮 {player['sigils']:,}`\n"
                f"Market Sales: `{stats['market_sales']}` | Direct Trades: `{stats['trades']}`"
            ),
            inline=True
        )

        embed.add_field(
            name="📦 Collections & Consumables",
            value=(
                f"Heroes Collected: `{stats['characters_collected']}`\n"
                f"Gear Collected: `{stats['equipment_collected']}`\n"
                f"Blank Scrolls Used: `{stats['blank_scrolls_used']}` | Repair Kits Used: `{stats['repair_kits_used']}`"
            ),
            inline=True
        )

        await ctx.send(embed=embed)

    @commands.command(name="title", aliases=["titles"])
    async def title(self, ctx: commands.Context, title_key: str = None):
        """View or equip unlocked cosmetic titles."""
        user_id = ctx.author.id

        if not title_key:
            # Grant default Explorer title for testing
            await db.unlock_title(user_id, "explorer")
            unlocked = await db.get_unlocked_titles(user_id)
            unlocked_keys = [t["title_id"] for t in unlocked]

            embed = Embeds.base(
                title="🏷️ Cosmetic Titles Catalog",
                description="Equip a title to show off on your profile! Titles are cosmetic only.",
                color=0xFDCB6E
            )

            for key, t in COSMETIC_TITLES.items():
                status = "✅ Unlocked" if key in unlocked_keys else "🔒 Locked"
                embed.add_field(name=f"{t['name']} ({status})", value=f"*{t['desc']}*\nEquip: `{ctx.prefix}title {key}`", inline=False)

            await ctx.send(embed=embed)
            return

        key = title_key.lower()
        if key not in COSMETIC_TITLES:
            await ctx.send(embed=Embeds.error("Invalid Title", f"Available titles: `{', '.join(COSMETIC_TITLES.keys())}`"))
            return

        await db.unlock_title(user_id, key)
        t_data = COSMETIC_TITLES[key]
        await db.set_active_title(user_id, t_data["name"])

        embed = Embeds.success("Title Equipped!", f"Equipped cosmetic title: **[{t_data['name']}]**!")
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard", aliases=["vtop", "top", "lb"])
    async def leaderboard(self, ctx: commands.Context, category: str = "pvp"):
        """View top players leaderboard (Category: pvp or coins)."""
        cat = category.lower()

        if cat == "coins":
            rows = await db.get_leaderboard_coins(limit=10)
            embed = Embeds.base(title="🏆 Richest Players Leaderboard", color=0xFDCB6E)
            for idx, r in enumerate(rows, start=1):
                user = self.bot.get_user(r["user_id"])
                if not user:
                    try:
                        user = await self.bot.fetch_user(r["user_id"])
                    except Exception:
                        user = None
                display_name = user.display_name if user else f"Player #{r['user_id']}"
                embed.add_field(name=f"#{idx}. {display_name}", value=f"🪙 **{r['coins']:,} Coins** | 🔮 **{r['sigils']} Sigils**", inline=False)
        else:
            rows = await db.get_leaderboard_pvp(limit=10)
            embed = Embeds.base(title="🏆 PvP Rating Leaderboard", color=0xFDCB6E)
            for idx, r in enumerate(rows, start=1):
                user = self.bot.get_user(r["user_id"])
                if not user:
                    try:
                        user = await self.bot.fetch_user(r["user_id"])
                    except Exception:
                        user = None
                display_name = user.display_name if user else f"Player #{r['user_id']}"
                embed.add_field(name=f"#{idx}. {display_name}", value=f"⭐ **{r['pvp_rating']:,} RP** | 🪙 **{r['coins']:,} Coins**", inline=False)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(QuestsCog(bot))
