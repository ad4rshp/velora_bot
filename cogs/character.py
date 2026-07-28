"""
Character Cog for Velora RPG.
Implements vstart, vprofile, vinventory, and character inspection commands.
"""

import os
import discord
from discord.ext import commands

from utils.embeds import Embeds
from utils.db import db
from utils.constants import calculate_stats
from views.starter_view import StarterView
from views.character_view import CharacterDetailView
from views.paginator import PaginatorView

class CharacterCog(commands.Cog, name="Character"):
    """Character management, starter claim, profiles, and hero inspection."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="start", aliases=["vstart", "begin"])
    async def start(self, ctx: commands.Context):
        """Begin your adventure and select your starter hero."""
        user_id = ctx.author.id
        
        # Check if user already claimed starter
        if await db.has_claimed_starter(user_id):
            await ctx.send(embed=Embeds.warning(
                "Already Started",
                "You have already chosen your starter hero! Use `vprofile` to view your stats or `vinventory` to see your heroes."
            ))
            return

        catalog_starters = await db.get_catalog_characters()
        startermeta = [dict(row) for row in catalog_starters]

        embed = Embeds.base(
            title="Velora RPG — Starter Hero Selection",
            description=(
                f"Welcome, **{ctx.author.display_name}**!\n\n"
                f"Select a starter hero class from the dropdown menu below.\n"
                f"Inspect attributes, then click **Confirm Choice** to begin your journey."
            ),
            color=0x6C5CE7
        )

        
        view = StarterView(author_id=user_id, startermeta=startermeta)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="profile", aliases=["p", "prof"])
    async def profile(self, ctx: commands.Context, target: discord.User = None):
        """View compact player profile card."""
        from cogs.battle import get_rank_title
        user = target or ctx.author
        player = await db.get_or_create_player(user.id)
        stats = await db.fetchone("SELECT * FROM player_stats WHERE user_id = ?", (user.id,))
        
        # Fetch active hero
        characters = await db.get_player_characters(user.id)
        active_char = next((c for c in characters if c["is_active"]), characters[0] if characters else None)
        title_str = player["title_id"] if player["title_id"] else "Novice Adventurer"
        rank_name, _ = get_rank_title(player["pvp_rating"])

        embed = discord.Embed(
            title=f"{user.display_name} — Player Profile",
            description=(
                f"Title: **[{title_str}]**\n"
                f"Rank: **{rank_name}** (`{player['pvp_rating']:,} RP`)\n"
                f"─────────────────────────────────────"
            ),
            color=0x6C5CE7
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        embed.add_field(
            name="Balance",
            value=f"🪙 `{player['coins']:,}` Coins  |  🔮 `{player['sigils']:,}` Sigils\n───────────",
            inline=False
        )

        if active_char:
            embed.add_field(
                name="Active Hero",
                value=f"**{active_char['name']}** ({active_char['class_type']}) • Lvl `{active_char['level']}` `[{active_char['rarity']}]`\n───────────",
                inline=False
            )
        else:
            embed.add_field(
                name="Active Hero",
                value="*None claimed. Use `vstart` to begin.*\n───────────",
                inline=False
            )

        if stats:
            battles = stats["pvp_battles"]
            wins = stats["pvp_wins"]
            winrate = f"{(wins / battles * 100):.1f}%" if battles > 0 else "0.0%"
            embed.add_field(
                name="Combat Record",
                value=f"Wins: `{wins}/{battles}` (`{winrate}`) | Heroes: `{stats['characters_collected']}` | Gear: `{stats['equipment_collected']}`",
                inline=False
            )

        await ctx.send(embed=embed)



    @commands.command(name="info", aliases=["char"])
    async def hero_info(self, ctx: commands.Context, index_or_name: str = "1"):


        """View hero stats and info."""

        characters = await db.get_player_characters(ctx.author.id)
        if not characters:
            await ctx.send(embed=Embeds.warning("No Heroes", "You don't own any heroes yet! Use `vstart` to choose your hero."))
            return

        target_char = None
        clean_arg = index_or_name.lstrip('#')
        if clean_arg.isdigit():
            idx = int(clean_arg)
            if 1 <= idx <= len(characters):
                target_char = dict(characters[idx - 1])
            else:
                target_char = next((dict(c) for c in characters if c["instance_id"] == idx), None)
        else:
            search_term = index_or_name.lower()
            for c in characters:
                if search_term in c["name"].lower() or search_term in c["class_type"].lower():
                    target_char = dict(c)
                    break

        if not target_char:
            target_char = dict(characters[0])

        # Fetch equipped gear & weapon with rarity for hero
        eq_items = await db.fetchall(
            "SELECT name, slot, rarity, stat_hp, stat_atk, stat_def, stat_spd FROM player_equipment WHERE equipped_character_id = ?",
            (target_char["instance_id"],)
        )
        if eq_items:
            target_char["equipped_gear"] = [dict(e) for e in eq_items]
            weapons = [f"{e['name']} [{e['rarity']}]" for e in eq_items if e["slot"] == "Weapon"]
            target_char["equipped_weapon_name"] = " • ".join(weapons) if weapons else "None"
        else:
            target_char["equipped_gear"] = []
            target_char["equipped_weapon_name"] = "None"

        # Fetch equipped scrolls for hero from character_loadouts
        sc_items = await db.fetchall(
            """
            SELECT s.name, s.scroll_type, s.power
            FROM character_loadouts cl
            JOIN player_scrolls ps ON cl.scroll_instance_id = ps.instance_id
            JOIN scrolls s ON ps.scroll_id = s.scroll_id
            WHERE cl.character_instance_id = ?
            """,
            (target_char["instance_id"],)
        )
        if sc_items:
            target_char["equipped_scrolls_str"] = " • ".join([f"{s['name']} [{s['scroll_type']}]" for s in sc_items])
        else:
            target_char["equipped_scrolls_str"] = "None"

        embed = CharacterDetailView.build_character_embed(target_char)


        
        # Check if 2D character artwork image exists in assets
        class_key = target_char["class_type"].lower()
        asset_path = f"assets/{class_key}.png"
        file = None
        if os.path.exists(asset_path):
            file = discord.File(asset_path, filename=f"{class_key}.png")
            embed.set_image(url=f"attachment://{class_key}.png")

        view = CharacterDetailView(author_id=ctx.author.id, char_row=target_char)
        if file:
            view.message = await ctx.send(file=file, embed=embed, view=view)
        else:
            view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="select", aliases=["vselect", "setactive"])
    async def select_hero(self, ctx: commands.Context, index_or_name: str, slot: int = 1):
        """Set a hero into your battle team slot (1, 2, or 3)."""
        if slot not in (1, 2, 3):
            await ctx.send(embed=Embeds.error("Invalid Slot", "Team slot must be 1, 2, or 3."))
            return

        characters = await db.get_player_characters(ctx.author.id)
        if not characters:
            await ctx.send(embed=Embeds.warning("No Heroes", "You don't own any heroes yet! Use `vstart` to choose your hero."))
            return

        target_char = None
        clean_arg = index_or_name.lstrip('#')
        if clean_arg.isdigit():
            idx = int(clean_arg)
            if 1 <= idx <= len(characters):
                target_char = dict(characters[idx - 1])
            else:
                target_char = next((dict(c) for c in characters if c["instance_id"] == idx), None)
        else:
            search_term = index_or_name.lower()
            for c in characters:
                if search_term in c["name"].lower() or search_term in c["class_type"].lower():
                    target_char = dict(c)
                    break

        if not target_char:
            await ctx.send(embed=Embeds.error("Hero Not Found", f"Could not find hero matching `{index_or_name}` in your inventory."))
            return

        await db.set_active_character(ctx.author.id, target_char["instance_id"], slot=slot)
        slot_badge = "⭐ (Main)" if slot == 1 else f"Slot #{slot}"
        embed = Embeds.success(
            "Battle Team Updated!",
            f"Placed **{target_char['name']}** ({target_char['class_type']}) Lvl **{target_char['level']}** into **{slot_badge}**!"
        )
        await ctx.send(embed=embed)

    @commands.command(name="team", aliases=["vteam", "squad"])
    async def view_team(self, ctx: commands.Context, action: str = None, hero_ref: str = None, slot: int = 1):
        """View or configure your 3v3 battle team slots (vteam / vteam set <hero> <slot>)."""
        team_list = await db.get_player_team(ctx.author.id)
        if not team_list:
            await ctx.send(embed=Embeds.warning("No Heroes", "You don't own any heroes yet! Use `vstart` to claim starter heroes."))
            return

        # If user runs 'vteam set <hero> <slot>'
        if action and action.lower() in ("set", "add", "swap") and hero_ref:
            await ctx.invoke(self.select_hero, index_or_name=hero_ref, slot=slot)
            return

        embed = discord.Embed(
            title=f"Battle Lineup — {ctx.author.display_name}",
            description="─────────────────────────────────────",
            color=0x6C5CE7
        )

        for s in (1, 2, 3):
            hero = next((c for c in team_list if c.get("team_slot") == s), None)
            if hero:
                base_s = calculate_stats(
                    hero["base_hp"], hero["base_atk"], hero["base_def"], hero["base_spd"],
                    level=hero["level"], rarity=hero["rarity"]
                )

                eq_items = await db.fetchall(
                    "SELECT stat_hp, stat_atk, stat_def, stat_spd FROM player_equipment WHERE equipped_character_id = ?",
                    (hero["instance_id"],)
                )
                eff_hp = base_s["hp"] + sum(e["stat_hp"] for e in eq_items)
                eff_atk = base_s["atk"] + sum(e["stat_atk"] for e in eq_items)
                eff_def = base_s["def"] + sum(e["stat_def"] for e in eq_items)
                eff_spd = base_s["spd"] + sum(e["stat_spd"] for e in eq_items)

                embed.add_field(
                    name=f"{s}. {hero['name']} ({hero['class_type']})",
                    value=f"Lvl **{hero['level']}** • **[{hero['rarity']}]** | HP: `{eff_hp}`  ATK: `{eff_atk}`  DF: `{eff_def}`  SP: `{eff_spd}`\n───────────",
                    inline=False
                )

            else:
                embed.add_field(
                    name=f"{s}. Empty",
                    value="*No hero assigned.*\n───────────",
                    inline=False
                )

        await ctx.send(embed=embed)



    @commands.command(name="rerollhero", aliases=["rrh", "cr", "rh"])
    async def reroll_hero(self, ctx: commands.Context, index_or_id_or_name: str = "1"):
        """Reroll a hero's rarity tier (Sigil cost scales with current rarity). ⚠️ 30% chance of failure!"""
        import random
        from views.character_view import CharacterRerollView, get_reroll_cost

        # Block if user already has a pending reroll view open
        if ctx.author.id in CharacterRerollView._active_sessions:
            await ctx.send(embed=Embeds.warning(
                "Reroll In Progress",
                "You already have a pending reroll! Accept, keep, or wait for it to expire before starting another."
            ))
            return

        characters = await db.get_player_characters(ctx.author.id)
        if not characters:
            await ctx.send(embed=Embeds.warning("No Heroes", "You don't own any heroes yet!"))
            return

        target_char = None
        clean_arg = index_or_id_or_name.lstrip('#')
        if clean_arg.isdigit():
            val = int(clean_arg)
            if 1 <= val <= len(characters):
                target_char = dict(characters[val - 1])
            else:
                target_char = next((dict(c) for c in characters if c["instance_id"] == val), None)
        else:
            search_term = index_or_id_or_name.lower()
            for c in characters:
                if search_term in c["name"].lower() or search_term in c["class_type"].lower():
                    target_char = dict(c)
                    break

        if not target_char:
            await ctx.send(embed=Embeds.error("Hero Not Found", f"Could not find hero matching `{index_or_id_or_name}` in your inventory."))
            return

        # Deduct dynamic sigil cost based on current hero rarity
        from views.character_view import get_reroll_fail_rate
        cost = get_reroll_cost(target_char["rarity"])
        fail_rate = get_reroll_fail_rate(target_char["rarity"])
        try:
            await db.consume_sigils(ctx.author.id, cost)
        except ValueError as e:
            await ctx.send(embed=Embeds.error("Reroll Failed", str(e)))
            return

        # Dynamic chance for reroll attempt to FAIL based on current rarity
        fail_roll = random.random()
        failed = False
        if fail_roll < fail_rate:
            new_rarity = target_char["rarity"]
            failed = True
        else:
            rarities = ["D", "C", "B", "A", "S", "SS"]
            weights = [45, 30, 16, 6.5, 2.0, 0.5]
            new_rarity = random.choices(rarities, weights=weights)[0]


        view = CharacterRerollView(
            author_id=ctx.author.id,
            target_char=target_char,
            new_rarity=new_rarity,
            failed=failed
        )
        embed = view.build_comparison_embed()
        view.message = await ctx.send(embed=embed, view=view)




    @commands.command(name="collection", aliases=["col", "gallery"])
    async def collection(self, ctx: commands.Context):
        """View owned hero collection roster with selection IDs (10 heroes per page)."""
        player_heroes = await db.get_player_characters(ctx.author.id)
        all_catalog = await db.get_catalog_characters()
        if not player_heroes:
            await ctx.send(embed=Embeds.warning(
                "No Heroes Found",
                "You don't own any heroes yet! Use `vstart` to claim your starter heroes team."
            ))
            return

        total_catalog = len(all_catalog)
        owned_classes = {c["class_type"].lower() for c in player_heroes}
        owned_count = len(owned_classes)
        pct = int((owned_count / total_catalog * 100)) if total_catalog > 0 else 0

        chunk_size = 10
        pages = []
        total_heroes = len(player_heroes)

        for i in range(0, total_heroes, chunk_size):
            chunk = player_heroes[i:i + chunk_size]
            embed = discord.Embed(
                title=f"Hero Collection — {ctx.author.display_name}",
                description=(
                    f"Discovery: **{owned_count}/{total_catalog}** ({pct}%) | Total Owned: **{total_heroes}**\n"
                    f"─────────────────────────────────────"
                ),
                color=0x6C5CE7
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            for idx, char in enumerate(chunk, start=i+1):
                star_badge = " (Active ⭐)" if char["is_active"] else ""
                embed.add_field(
                    name=f"#{idx}. {char['name']} ({char['class_type']}) • Lvl {char['level']} • [{char['rarity']}]{star_badge}",
                    value="───────────",
                    inline=False
                )


            pages.append(embed)

        for page_idx, page in enumerate(pages, start=1):
            page.set_footer(text=f"Page {page_idx} of {len(pages)} | Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        if len(pages) == 1:
            await ctx.send(embed=pages[0])
        else:
            view = PaginatorView(author_id=ctx.author.id, pages=pages)
            view.message = await ctx.send(embed=pages[0], view=view)

    @commands.command(name="inventory", aliases=["inv", "vinv", "bag"])
    async def inventory(self, ctx: commands.Context):
        """View owned equipment, scrolls, packs, and consumables."""
        user_id = ctx.author.id
        gear_list = await db.get_player_equipment(user_id)
        scroll_rows = await db.fetchall(
            "SELECT ps.instance_id, s.name, s.scroll_type, s.power, s.required_class_tags FROM player_scrolls ps JOIN scrolls s ON ps.scroll_id = s.scroll_id WHERE ps.user_id = ?",
            (user_id,)
        )
        consumables = await db.fetchall(
            "SELECT item_id, quantity FROM player_consumables WHERE user_id = ? AND quantity > 0",
            (user_id,)
        )

        if not gear_list and not scroll_rows and not consumables:
            await ctx.send(embed=Embeds.warning(
                "Empty Inventory",
                "You don't own any gear, scrolls, or consumable items yet!\nVisit `vshop` or use `vforge` to get started."
            ))
            return

        pages = []

        # Page 1: Overview
        embed1 = discord.Embed(
            title=f"Inventory — {ctx.author.display_name}",
            description="─────────────────────────────────────",
            color=0x0984E3
        )
        embed1.set_thumbnail(url=ctx.author.display_avatar.url)

        # 1. Equipment Summary
        if gear_list:
            gear_lines = []
            for eq in gear_list[:6]:
                status = " (Equipped ⭐)" if eq["equipped_character_id"] else ""
                gear_lines.append(f"• **#{eq['equipment_id']} {eq['name']}** [{eq['rarity']}] `{eq['slot']}`{status}")
            if len(gear_list) > 6:
                gear_lines.append(f"*...and {len(gear_list) - 6} more items (page ▶️)*")
            embed1.add_field(name="Equipment & Weapons", value="\n".join(gear_lines) + "\n───────────", inline=False)

        # 2. Skill Scrolls Summary
        if scroll_rows:
            scroll_lines = []
            for sc in scroll_rows[:4]:
                scroll_lines.append(f"• **#{sc['instance_id']} {sc['name']}** [{sc['scroll_type']}] • Pwr `{sc['power']}`")
            if len(scroll_rows) > 4:
                scroll_lines.append(f"*...and {len(scroll_rows) - 4} more scrolls*")
            embed1.add_field(name="Skill Scrolls", value="\n".join(scroll_lines) + "\n───────────", inline=False)

        # 3. Consumables & Packs
        if consumables:
            item_names = {
                "common_chest": "Common Chest",
                "rare_chest": "Rare Chest",
                "blank_scroll": "Blank Scroll",
                "novice_pack": "Novice Hero Pack",
                "pack_novice": "Novice Hero Pack",
                "mythic_pack": "Mythic Hero Pack",
                "pack_mythic": "Mythic Hero Pack",
                "celestial_pack": "Celestial Hero Pack",
                "pack_celestial": "Celestial Hero Pack",
                "repair_kit": "Repair Kit"
            }
            con_lines = []
            for con in consumables:
                name = item_names.get(con["item_id"], con["item_id"].replace('_', ' ').title())
                con_lines.append(f"• **{name}** x`{con['quantity']}`")
            embed1.add_field(name="Consumables & Packs", value="\n".join(con_lines) + "\n───────────", inline=False)

        pages.append(embed1)

        # Additional pages if player has more equipment & weapons
        if len(gear_list) > 6:
            chunk_size = 6
            for i in range(6, len(gear_list), chunk_size):
                chunk = gear_list[i:i + chunk_size]
                eq_embed = discord.Embed(
                    title=f"Equipment & Weapons — {ctx.author.display_name}",
                    description=f"Showing **{i+1}–{min(i+chunk_size, len(gear_list))}** of **{len(gear_list)}** total equipment.\n─────────────────────────────────────",
                    color=0x0984E3
                )
                eq_embed.set_thumbnail(url=ctx.author.display_avatar.url)
                for idx, eq in enumerate(chunk, start=i+1):
                    status = " (Equipped ⭐)" if eq["equipped_character_id"] else ""
                    comp = f" | Class: **{eq['compatible_class']}**" if eq.get('compatible_class') else ""
                    eq_embed.add_field(
                        name=f"#{eq['equipment_id']}. {eq['name']} [{eq['rarity']}]{status}",
                        value=(
                            f"Slot: **{eq['slot']}**{comp} | Quality: **{eq['quality']}%** | Durability: `{eq['durability']}/{eq['max_durability']}`\n"
                            f"HP: `+{eq['stat_hp']}`  ATK: `+{eq['stat_atk']}`  DF: `+{eq['stat_def']}`  SP: `+{eq['stat_spd']}`\n───────────"
                        ),
                        inline=False
                    )
                pages.append(eq_embed)

        for page_idx, page in enumerate(pages, start=1):
            page.set_footer(text=f"Page {page_idx} of {len(pages)} | Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        if len(pages) == 1:
            await ctx.send(embed=pages[0])
        else:
            view = PaginatorView(author_id=ctx.author.id, pages=pages)
            view.message = await ctx.send(embed=pages[0], view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(CharacterCog(bot))

