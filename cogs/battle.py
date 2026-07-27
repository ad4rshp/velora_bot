"""
Battle Cog for Velora RPG.
Implements vbattle (PvE Monster Encounters & PvP player duels) and integrates with 3v3 engine.
"""


import discord
from discord.ext import commands
from utils.embeds import Embeds
from utils.db import db
from utils.constants import calculate_stats
from utils.battle_engine import Combatant, BattleSide, BattleEngine
from views.battle_view import BattleView

def get_rank_title(rp: int) -> tuple[str, str]:
    """Calculate Velora RPG Ranked Tier title from Rating Points (RP)."""
    if rp >= 3500:
        return "✨ Velora Ascendant", "#6C5CE7"
    elif rp >= 3000:
        return "🔥 Abyssal Monarch", "#E17055"
    elif rp >= 2500:
        return "👑 Mythic Sovereign", "#00CEC9"
    elif rp >= 2000:
        return "🌙 Shadow Conqueror", "#0984E3"
    elif rp >= 1500:
        return "🔮 Arcane Champion", "#FDCB6E"
    elif rp >= 1000:
        return "⚔️ Iron Vanguard", "#B2BEC3"
    elif rp >= 100:
        return "🛡️ Novice Adventurer", "#74B9FF"
    else:
        return "🔰 Unranked Adventurer", "#A0A0A0"



class BattleCog(commands.Cog, name="Battle"):
    """3v3 Turn-Based Battle System & Ranked Progression."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="rank", aliases=["vrank", "rating"])
    async def rank_info(self, ctx: commands.Context, target: discord.User = None):
        """View current Ranked Tier, Rating Points (RP), and rank badge."""
        user = target or ctx.author
        player = await db.get_or_create_player(user.id)
        rp = player["pvp_rating"]
        rank_name, _ = get_rank_title(rp)

        embed = discord.Embed(
            title=f"🏆 Ranked Profile — {user.display_name}",
            description=f"Rank Tier: **{rank_name}**\nRating Points: ⭐ **{rp:,} RP**\n───────────",
            color=0x6C5CE7
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="💡 RP Rules", value="*Earn +25 RP on PvE Victory; lose -15 RP on PvE Defeat.*", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="battleguide", aliases=["vbattleguide", "bg", "guide"])
    async def battle_guide(self, ctx: commands.Context):
        """Display interactive category-based 3v3 tactical battle guide."""
        from views.battle_guide_view import BattleGuideView

        view = BattleGuideView(author_id=ctx.author.id)
        embed = view.build_embed("basics")
        view.message = await ctx.send(embed=embed, view=view)




    @commands.command(name="battle", aliases=["b", "fight"])
    async def battle(self, ctx: commands.Context, target: discord.User = None):
        """Initiate 3v3 battle against Shadow Syndicate monsters or challenge another player."""

        player_id = ctx.author.id

        # 1. Fetch user's hero roster
        player_heroes = await db.get_player_characters(player_id)
        if not player_heroes:
            await ctx.send(embed=Embeds.warning(
                "No Heroes Found",
                "You must claim a starter hero first using `vstart` before entering battle!"
            ))
            return

        # Prepare Player Combatants (up to 3 heroes)
        team_a_combatants = []
        for char in player_heroes[:3]:
            stats = calculate_stats(
                char["base_hp"], char["base_atk"], char["base_def"], char["base_spd"],
                level=char["level"], rarity=char["rarity"]
            )
            c = Combatant(
                instance_id=char["instance_id"],
                name=char["name"],
                class_type=char["class_type"],
                stats=stats,
                resource_type=char["resource_type"],
                resource_max=char["resource_max"]
            )
            c.level = char["level"]
            team_a_combatants.append(c)

        side_a = BattleSide(user_id=player_id, display_name=ctx.author.display_name, team=team_a_combatants)

        # 2. Setup Opponent Side (PvE Dynamic Velora Team or Opponent Player)
        is_pve = False
        if not target or target.id == self.bot.user.id or target.id == player_id:
            is_pve = True
            import random
            catalog_heroes = await db.get_catalog_characters()
            if not catalog_heroes:
                catalog_heroes = [
                    {"character_id": "knight_01", "name": "Arthur", "class_type": "Knight", "resource_type": "Stamina", "resource_max": 100, "base_rarity": "D", "base_hp": 120, "base_atk": 18, "base_def": 15, "base_spd": 10},
                    {"character_id": "mage_01", "name": "Merlin", "class_type": "Mage", "resource_type": "Mana", "resource_max": 120, "base_rarity": "D", "base_hp": 85, "base_atk": 25, "base_def": 8, "base_spd": 12},
                    {"character_id": "assassin_01", "name": "Kage", "class_type": "Assassin", "resource_type": "Energy", "resource_max": 100, "base_rarity": "D", "base_hp": 80, "base_atk": 26, "base_def": 7, "base_spd": 20}
                ]

            # Calculate average level & max rarity of challenger's active team
            avg_lvl = sum(c.level for c in team_a_combatants) // max(1, len(team_a_combatants))
            bot_level = max(1, avg_lvl)

            # Sample 3 random distinct heroes from catalog
            sample_size = min(3, len(catalog_heroes))
            chosen_cat = random.sample(list(catalog_heroes), sample_size)

            bot_combatants = []
            for idx, c_row in enumerate(chosen_cat, start=1):
                c_meta = dict(c_row)
                b_stats = calculate_stats(
                    c_meta["base_hp"], c_meta["base_atk"], c_meta["base_def"], c_meta["base_spd"],
                    level=bot_level, rarity=c_meta.get("base_rarity", "D")
                )

                b_comb = Combatant(
                    instance_id=-idx,
                    name=c_meta["name"],
                    class_type=c_meta["class_type"],
                    stats=b_stats,
                    resource_type=c_meta["resource_type"],
                    resource_max=c_meta["resource_max"]
                )
                b_comb.level = bot_level
                bot_combatants.append(b_comb)

            side_b = BattleSide(user_id=0, display_name="Velora", team=bot_combatants)



        else:
            opp_heroes = await db.get_player_characters(target.id)
            if not opp_heroes:
                await ctx.send(embed=Embeds.error("Opponent Unready", f"**{target.display_name}** does not have any heroes yet."))
                return

            team_b_combatants = []
            for char in opp_heroes[:3]:
                stats = calculate_stats(
                    char["base_hp"], char["base_atk"], char["base_def"], char["base_spd"],
                    level=char["level"], rarity=char["rarity"]
                )
                cb = Combatant(
                    instance_id=char["instance_id"],
                    name=char["name"],
                    class_type=char["class_type"],
                    stats=stats,
                    resource_type=char["resource_type"],
                    resource_max=char["resource_max"]
                )
                cb.level = char["level"]
                team_b_combatants.append(cb)
            side_b = BattleSide(user_id=target.id, display_name=target.display_name, team=team_b_combatants)


        # 3. Instantiate Engine & Battle UI
        engine = BattleEngine(side_a, side_b)
        view = BattleView(engine=engine)

        if not is_pve and target:
            # Send Challenge Invitation View
            from views.battle_challenge_view import BattleChallengeView

            async def start_pvp_battle(interaction: discord.Interaction):
                embed = view.build_battle_embed()
                view.message = await interaction.followup.send(embed=embed, view=view)

            challenge_view = BattleChallengeView(
                challenger_id=player_id,
                target_id=target.id,
                start_callback=start_pvp_battle
            )
            embed_challenge = discord.Embed(
                title="⚔️ PvP Duel Challenge!",
                description=(
                    f"**{ctx.author.display_name}** has challenged **{target.display_name}** to a 3v3 PvP Duel!\n"
                    f"Will **{target.display_name}** accept the challenge?\n───────────"
                ),
                color=0xE74C3C
            )
            embed_challenge.set_thumbnail(url=target.display_avatar.url)
            challenge_view.message = await ctx.send(embed=embed_challenge, view=challenge_view)
        else:
            embed = view.build_battle_embed()
            view.message = await ctx.send(embed=embed, view=view)



async def setup(bot: commands.Bot):
    await bot.add_cog(BattleCog(bot))

