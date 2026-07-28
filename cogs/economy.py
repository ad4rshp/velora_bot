"""
Economy & Consumables Cog for Velora RPG.
Implements General Store (vshop), Chest opening (vopen), and Blank Scroll usage.
"""

import discord
import random
from discord.ext import commands
from utils.embeds import Embeds
from utils.db import db
from utils.constants import STARTER_SCROLLS, generate_random_equipment
from views.shop_view import ShopView

class EconomyCog(commands.Cog, name="Economy"):
    """General Store, Chest Opening & Consumables."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="shop", aliases=["s", "store"])
    async def shop(self, ctx: commands.Context):

        """Open the General Store."""

        view = ShopView(author_id=ctx.author.id)
        embed = view.build_shop_embed()
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="balance", aliases=["bal", "vbal", "wallet", "money"])
    async def balance(self, ctx: commands.Context, target: discord.Member = None):
        """Check your or another player's wallet balance and currencies."""
        user = target or ctx.author
        player = await db.get_or_create_player(user.id)
        embed = discord.Embed(
            title=f"💰 Balance — {user.display_name}",
            description="─────────────────────────────────────",
            color=0xF1C40F
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        from cogs.battle import get_rank_title
        rank_name, _ = get_rank_title(player['pvp_rating'])
        embed.add_field(
            name="Currencies",
            value=(
                f"🪙 Coins: **{player['coins']:,}**\n"
                f"🔮 Sigils: **{player['sigils']:,}**\n"
                f"🏆 Rank Tier: **{rank_name}** (`{player['pvp_rating']} RP`)"
            ),
            inline=False
        )

        await ctx.send(embed=embed)


    @commands.command(name="open", aliases=["use", "vopen"])
    async def open_item(self, ctx: commands.Context, *, item_id: str = "common_chest"):
        """Open chests, hero packs, or consume items (normal chest, rare chest, hero packs, etc.)."""
        user_id = ctx.author.id
        clean_name = item_id.lower().strip().replace("-", " ").replace("_", " ")

        if clean_name in ("normal", "normal chest", "normalchest", "common", "common chest", "commonchest", "chest"):
            item_key = "common_chest"
            display_name = "Common Chest"
        elif clean_name in ("rare", "rare chest", "rarechest"):
            item_key = "rare_chest"
            display_name = "Rare Chest"
        elif clean_name in ("blank", "blank scroll", "blankscroll", "scroll"):
            item_key = "blank_scroll"
            display_name = "Blank Scroll"
        elif clean_name in ("repair", "repair kit", "repairkit", "kit"):
            item_key = "repair_kit"
            display_name = "Repair Kit"
        elif clean_name in ("novice", "novice pack", "novicepack", "pack novice"):
            item_key = "novice_pack"
            display_name = "Novice Hero Pack"
        elif clean_name in ("mythic", "mythic pack", "mythicpack", "pack mythic"):
            item_key = "mythic_pack"
            display_name = "Mythic Hero Pack"
        elif clean_name in ("celestial", "celestial pack", "celestialpack", "pack celestial"):
            item_key = "celestial_pack"
            display_name = "Celestial Hero Pack"
        else:
            item_key = clean_name.replace(" ", "_")
            display_name = item_key.replace("_", " ").title()

        valid_items = ["normal chest", "rare chest", "blank scroll", "repair kit", "novice pack", "mythic pack", "celestial pack"]
        if item_key not in ("common_chest", "rare_chest", "blank_scroll", "repair_kit", "novice_pack", "mythic_pack", "celestial_pack", "pack_novice", "pack_mythic", "pack_celestial"):
            await ctx.send(embed=Embeds.error("Invalid Item", f"Valid items to open: `{', '.join(valid_items)}`"))
            return

        try:
            used_key = await db.use_consumable(user_id, item_key, 1)
        except ValueError:
            await ctx.send(embed=Embeds.warning("Item Missing", f"You don't own any **{display_name}**! Buy items at `{ctx.prefix}shop`."))
            return

        # Handle chest rewards
        if item_key == "common_chest":
            coins_reward = random.randint(300, 1000)
            await db.execute("UPDATE players SET coins = coins + ? WHERE user_id = ?", (coins_reward, user_id))
            
            # Chance for equipment
            eq_data = generate_random_equipment("Weapon")
            eq_item = await db.add_equipment(user_id, eq_data)

            embed = Embeds.success(
                "Opened Common Chest!",
                f"🎉 You opened a **Common Chest** and found:\n"
                f"🪙 **+{coins_reward:,} Coins**\n"
                f"🛡️ **{eq_item['name']}** [{eq_item['rarity']}]"
            )
            await ctx.send(embed=embed)

        elif item_key == "rare_chest":
            coins_reward = random.randint(2000, 5000)
            sigils_reward = random.randint(5, 15)
            await db.execute("UPDATE players SET coins = coins + ?, sigils = sigils + ? WHERE user_id = ?", (coins_reward, sigils_reward, user_id))

            eq_data = generate_random_equipment("Armor")
            eq_item = await db.add_equipment(user_id, eq_data)

            embed = Embeds.success(
                "Opened Rare Chest!",
                f"🌟 You opened a **Rare Chest** and found:\n"
                f"🪙 **+{coins_reward:,} Coins**\n"
                f"🔮 **+{sigils_reward} Sigils**\n"
                f"🛡️ **{eq_item['name']}** [{eq_item['rarity']}]"
            )
            await ctx.send(embed=embed)

        elif item_key == "blank_scroll":
            random_scroll = random.choice(STARTER_SCROLLS)
            await db.execute("INSERT INTO player_scrolls (user_id, scroll_id) VALUES (?, ?)", (user_id, random_scroll["id"]))
            await db.execute("UPDATE player_stats SET blank_scrolls_used = blank_scrolls_used + 1 WHERE user_id = ?", (user_id,))

            embed = Embeds.success(
                "Blank Scroll Used!",
                f"✨ Your **Blank Scroll** resonated with arcane energy and manifested:\n"
                f"📜 **{random_scroll['name']}** [{random_scroll['scroll_type']}]!"
            )
            await ctx.send(embed=embed)

        elif item_key == "repair_kit":
            await db.execute("UPDATE player_stats SET repair_kits_used = repair_kits_used + 1 WHERE user_id = ?", (user_id,))
            embed = Embeds.info("Repair Kit Ready", "Use `vrepair <Equipment_ID>` to apply repair kits to your damaged equipment.")
            await ctx.send(embed=embed)

        elif item_key in ("novice_pack", "mythic_pack", "celestial_pack", "pack_novice", "pack_mythic", "pack_celestial"):
            all_catalog = await db.fetchall("SELECT * FROM characters")
            cat_char = dict(random.choice(all_catalog))
            
            if "novice" in item_key:
                rarities = ["D", "C", "B", "A"]
                weights = [68, 24, 7, 1]
                lvl = random.randint(1, 5)
                pack_name = "Novice Hero Pack"
            elif "mythic" in item_key:
                rarities = ["D", "C", "B", "A", "S", "SS"]
                weights = [45, 32, 16, 5, 1.9, 0.1]
                lvl = random.randint(5, 15)
                pack_name = "Mythic Hero Pack"
            else:
                rarities = ["C", "B", "A", "S", "SS"]
                weights = [35, 42, 18, 4.6, 0.4]
                lvl = random.randint(10, 20)
                pack_name = "Celestial Hero Pack"


            rarity = random.choices(rarities, weights=weights)[0]
            await db.get_or_create_player(user_id)

            await db.execute(
                """
                INSERT INTO player_characters (user_id, character_id, level, xp, rarity, is_active)
                VALUES (?, ?, ?, 0, ?, 0)
                """,
                (user_id, cat_char["character_id"], lvl, rarity)
            )

            char_inst = await db.fetchone("SELECT last_insert_rowid() as id")
            char_instance_id = char_inst["id"]

            await db.execute(
                "UPDATE player_stats SET characters_collected = characters_collected + 1 WHERE user_id = ?",
                (user_id,)
            )

            # Grant class starter weapon
            class_type = cat_char["class_type"]
            weapon_catalog = await db.get_catalog_equipment(slot="Weapon", class_type=class_type)
            if weapon_catalog:
                w_item = dict(weapon_catalog[0])
                w_data = {
                    "name": w_item["name"], "slot": "Weapon", "compatible_class": w_item["compatible_class"],
                    "rarity": w_item["base_rarity"], "quality": 50, "durability": 100, "max_durability": 100,
                    "stat_hp": w_item["base_hp"], "stat_atk": w_item["base_atk"], "stat_def": w_item["base_def"], "stat_spd": w_item["base_spd"]
                }
                eq_inst = await db.add_equipment(user_id, w_data)
                await db.equip_gear(user_id, eq_inst["equipment_id"], char_instance_id)

            embed = Embeds.success(
                "🎴 Hero Card Unpacked!",
                f"You opened **{pack_name}** and summoned **{cat_char['name']}** ({cat_char['class_type']})!\n"
                f"Rarity: **[{rarity}]** | Level: **{lvl}**\nAdded to your hero inventory (`vinventory`)!"
            )
            await ctx.send(embed=embed)


    @commands.command(name="sell", aliases=["vsell", "disassemble", "salvage"])
    async def sell(self, ctx: commands.Context, target_type: str = None, item_ref: str = None):
        """Sell weapons/gear, scrolls, or heroes for Sigils (🔮) based on Rarity.
        
        Usage:
          • vsell gear <#ID or rarity: D/C/B/A/S/SS> (e.g. vsell gear #1 or vsell gear D)
          • vsell scroll <#ID or all> (e.g. vsell scroll #1 or vsell scroll all)
          • vsell hero <#ID or rarity: D/C/B/A/S/SS> (e.g. vsell hero #2 or vsell hero D)
        """
        if not target_type or not item_ref:
            embed = discord.Embed(
                description=(
                    "─────────────────────────────────────\n"
                    "• `vsell gear <#ID>` ── Sell specific equipment piece\n"
                    "• `vsell gear <tier>` ── Bulk sell unequipped gear by tier (`D`–`SS`)\n"
                    "• `vsell scroll <#ID>` ── Sell specific scroll piece\n"
                    "• `vsell scroll all` ── Bulk sell all owned scrolls\n"
                    "• `vsell hero <#ID>` ── Sell specific inactive hero\n"
                    "• `vsell hero <tier>` ── Bulk sell inactive heroes by tier (`D`–`SS`)\n"
                    "─────────────────────────────────────"
                ),
                color=0x6C5CE7
            )
            await ctx.send(embed=embed)
            return



        user_id = ctx.author.id
        category = target_type.lower()
        arg = item_ref.strip()

        SIGIL_PAYOUT = {
            "D": 2,
            "C": 5,
            "B": 12,
            "A": 25,
            "S": 60,
            "SS": 150
        }

        # 1. GEAR SELLING
        if category in ("gear", "equipment", "weapon", "armor"):
            gear_list = await db.get_player_equipment(user_id)
            if not gear_list:
                await ctx.send(embed=Embeds.warning("No Gear", "You don't own any equipment items to sell!"))
                return

            clean_arg = arg.lstrip('#')
            # Single item sell by ID/Index
            if clean_arg.isdigit():
                val = int(clean_arg)
                target_gear = None
                if 1 <= val <= len(gear_list):
                    target_gear = dict(gear_list[val - 1])
                else:
                    target_gear = next((dict(g) for g in gear_list if g["equipment_id"] == val), None)

                if not target_gear:
                    await ctx.send(embed=Embeds.error("Not Found", f"Could not find gear matching `{arg}`."))
                    return

                if target_gear["equipped_character_id"]:
                    await ctx.send(embed=Embeds.warning("Equipped Item", f"**{target_gear['name']}** is equipped! Unequip it before selling."))
                    return

                rarity = target_gear["rarity"].upper()
                payout = SIGIL_PAYOUT.get(rarity, 2)

                await db.execute("DELETE FROM player_equipment WHERE equipment_id = ?", (target_gear["equipment_id"],))
                await db.execute("UPDATE players SET sigils = sigils + ? WHERE user_id = ?", (payout, user_id))

                embed = Embeds.success(
                    "Equipment Salvaged!",
                    f"Salvaged **{target_gear['name']}** [{rarity}] for 🔮 **+{payout} Sigils**!"
                )
                await ctx.send(embed=embed)
                return

            # Bulk sell by Rarity
            target_rarity = arg.upper()
            if target_rarity in SIGIL_PAYOUT:
                to_sell = [g for g in gear_list if g["rarity"].upper() == target_rarity and not g["equipped_character_id"]]
                if not to_sell:
                    await ctx.send(embed=Embeds.warning("No Matching Gear", f"No unequipped **[{target_rarity}]** gear found to sell."))
                    return

                total_payout = sum(SIGIL_PAYOUT.get(g["rarity"].upper(), 2) for g in to_sell)
                eq_ids = tuple(g["equipment_id"] for g in to_sell)

                if len(eq_ids) == 1:
                    await db.execute("DELETE FROM player_equipment WHERE equipment_id = ?", (eq_ids[0],))
                else:
                    await db.execute(f"DELETE FROM player_equipment WHERE equipment_id IN {eq_ids}")

                await db.execute("UPDATE players SET sigils = sigils + ? WHERE user_id = ?", (total_payout, user_id))

                embed = Embeds.success(
                    "Bulk Gear Salvaged!",
                    f"Salvaged **{len(to_sell)}** `[{target_rarity}]` equipment pieces for 🔮 **+{total_payout:,} Sigils**!"
                )
                await ctx.send(embed=embed)
                return

            await ctx.send(embed=Embeds.error("Invalid Argument", "Specify a gear #ID (e.g. `#1`) or rarity (`D`, `C`, `B`, `A`, `S`, `SS`)."))

        # 2. SCROLL SELLING
        elif category in ("scroll", "scrolls"):
            scroll_rows = await db.fetchall(
                "SELECT ps.instance_id, s.name, s.scroll_type FROM player_scrolls ps JOIN scrolls s ON ps.scroll_id = s.scroll_id WHERE ps.user_id = ?",
                (user_id,)
            )
            if not scroll_rows:
                await ctx.send(embed=Embeds.warning("No Scrolls", "You don't own any scrolls to sell!"))
                return

            clean_arg = arg.lstrip('#')
            if clean_arg.lower() == "all":
                total_payout = len(scroll_rows) * 4
                await db.execute("DELETE FROM player_scrolls WHERE user_id = ?", (user_id,))
                await db.execute("UPDATE players SET sigils = sigils + ? WHERE user_id = ?", (total_payout, user_id))
                embed = Embeds.success(
                    "Bulk Scrolls Sold!",
                    f"Sold all **{len(scroll_rows)}** skill scrolls for 🔮 **+{total_payout:,} Sigils**!"
                )
                await ctx.send(embed=embed)
                return

            if clean_arg.isdigit():
                val = int(clean_arg)
                target_sc = None
                if 1 <= val <= len(scroll_rows):
                    target_sc = dict(scroll_rows[val - 1])
                else:
                    target_sc = next((dict(s) for s in scroll_rows if s["instance_id"] == val), None)

                if not target_sc:
                    await ctx.send(embed=Embeds.error("Not Found", f"Could not find scroll matching `{arg}`."))
                    return

                payout = 4
                await db.execute("DELETE FROM player_scrolls WHERE instance_id = ?", (target_sc["instance_id"],))
                await db.execute("UPDATE players SET sigils = sigils + ? WHERE user_id = ?", (payout, user_id))

                embed = Embeds.success(
                    "Scroll Sold!",
                    f"Sold **{target_sc['name']}** [{target_sc['scroll_type']}] for 🔮 **+{payout} Sigils**!"
                )
                await ctx.send(embed=embed)
                return

            await ctx.send(embed=Embeds.error("Invalid Argument", "Specify a scroll #ID (e.g. `#1`) or `all` to bulk sell all scrolls."))

        # 3. HERO SELLING
        elif category in ("hero", "character", "char"):
            player_heroes = await db.get_player_characters(user_id)
            if len(player_heroes) <= 3:
                await ctx.send(embed=Embeds.warning("Min Roster Reached", "You must keep at least 3 heroes for your 3v3 battle roster!"))
                return

            clean_arg = arg.lstrip('#')
            # Single hero sell
            if clean_arg.isdigit():
                val = int(clean_arg)
                target_char = None
                if 1 <= val <= len(player_heroes):
                    target_char = dict(player_heroes[val - 1])
                else:
                    target_char = next((dict(c) for c in player_heroes if c["instance_id"] == val), None)

                if not target_char:
                    await ctx.send(embed=Embeds.error("Not Found", f"Could not find hero matching `{arg}`."))
                    return

                if target_char["is_active"]:
                    await ctx.send(embed=Embeds.warning("Active Hero", f"**{target_char['name']}** is active in your battle team! Swap them out before selling."))
                    return

                rarity = target_char["rarity"].upper()
                payout = SIGIL_PAYOUT.get(rarity, 2)

                await db.execute("DELETE FROM player_characters WHERE instance_id = ?", (target_char["instance_id"],))
                await db.execute("UPDATE players SET sigils = sigils + ? WHERE user_id = ?", (payout, user_id))

                embed = Embeds.success(
                    "Hero Released!",
                    f"Released **{target_char['name']}** ({target_char['class_type']}) [{rarity}] for 🔮 **+{payout} Sigils**!"
                )
                await ctx.send(embed=embed)
                return

            # Bulk sell inactive heroes by rarity
            target_rarity = arg.upper()
            if target_rarity in SIGIL_PAYOUT:
                to_sell = [c for c in player_heroes if c["rarity"].upper() == target_rarity and not c["is_active"]]
                max_can_sell = len(player_heroes) - 3
                if max_can_sell <= 0:
                    await ctx.send(embed=Embeds.warning("Roster Limit", "You must keep at least 3 heroes for your 3v3 battle roster!"))
                    return

                to_sell = to_sell[:max_can_sell]
                if not to_sell:
                    await ctx.send(embed=Embeds.warning("No Matching Heroes", f"No inactive **[{target_rarity}]** heroes found to sell."))
                    return

                total_payout = sum(SIGIL_PAYOUT.get(c["rarity"].upper(), 2) for c in to_sell)
                c_ids = tuple(c["instance_id"] for c in to_sell)

                if len(c_ids) == 1:
                    await db.execute("DELETE FROM player_characters WHERE instance_id = ?", (c_ids[0],))
                else:
                    await db.execute(f"DELETE FROM player_characters WHERE instance_id IN {c_ids}")

                await db.execute("UPDATE players SET sigils = sigils + ? WHERE user_id = ?", (total_payout, user_id))


                embed = Embeds.success(
                    "Bulk Heroes Released!",
                    f"Released **{len(to_sell)}** `[{target_rarity}]` heroes for 🔮 **+{total_payout:,} Sigils**!"
                )
                await ctx.send(embed=embed)
                return

            await ctx.send(embed=Embeds.error("Invalid Argument", "Specify a hero #ID (e.g. `#2`) or rarity (`D`, `C`, `B`, `A`, `S`, `SS`)."))

        else:
            await ctx.send(embed=Embeds.error("Invalid Category", "Valid sell categories: `gear`, `scroll`, `hero`."))


async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
