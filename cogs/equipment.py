"""
Equipment & Scroll Cog for Velora RPG.
Implements equipment management, durability repairs, scroll inspection,
and OwO-style single rerolls.
"""

import discord
from discord.ext import commands
from utils.embeds import Embeds
from utils.db import db
from utils.constants import generate_random_equipment, roll_new_equipment_stats
from views.equipment_view import EquipmentDetailView
from views.reroll_view import RerollView
from views.paginator import PaginatorView

class EquipmentCog(commands.Cog, name="Equipment"):
    """Equipment, Scrolls, Repair & Rerolls."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="equipment", aliases=["eqp", "gear"])
    async def equipment(self, ctx: commands.Context, slot: str = None):
        """View owned equipment inventory (Optionally filter by slot: Weapon, Armor, Boots, etc.)."""
        gear_list = await db.get_player_equipment(ctx.author.id, slot_filter=slot.capitalize() if slot else None)

        if not gear_list:
            msg = f"You don't own any {slot.capitalize()} equipment!" if slot else "You don't own any equipment yet!"
            await ctx.send(embed=Embeds.warning("No Equipment Found", f"{msg}\nUse `vforge` to create test equipment."))
            return

        chunk_size = 6
        pages = []
        total_gear = len(gear_list)
        for i in range(0, total_gear, chunk_size):
            chunk = gear_list[i:i + chunk_size]
            embed = discord.Embed(
                title=f"Equipment Inventory — {ctx.author.display_name}",
                description=f"Showing **{i+1}–{min(i+chunk_size, total_gear)}** of **{total_gear}** total items.\n─────────────────────────────────────",
                color=0x0984E3
            )

            for idx, eq in enumerate(chunk, start=i+1):
                status = " (Equipped ⭐)" if eq["equipped_character_id"] else ""
                comp = f" | Class: **{eq['compatible_class']}**" if eq.get('compatible_class') else ""
                embed.add_field(
                    name=f"#{idx}. {eq['name']} [{eq['rarity']}]{status}",
                    value=(
                        f"Slot: **{eq['slot']}**{comp} | Quality: **{eq['quality']}%** | Durability: `{eq['durability']}/{eq['max_durability']}`\n"
                        f"HP: `+{eq['stat_hp']}`  ATK: `+{eq['stat_atk']}`  DF: `+{eq['stat_def']}`  SP: `+{eq['stat_spd']}`\n───────────"
                    ),
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

    @commands.command(name="equip", aliases=["vequip", "eq"])
    async def equip(self, ctx: commands.Context, gear_index_or_id: str, hero_index_or_name: str = None):
        """Equip a weapon or scroll to a compatible hero."""
        user_id = ctx.author.id
        gear_list = await db.get_player_equipment(user_id)
        if not gear_list:
            await ctx.send(embed=Embeds.warning("No Equipment", "You don't own any equipment items yet!"))
            return

        # Find target gear
        gear = None
        clean_g = gear_index_or_id.lstrip('#')
        if clean_g.isdigit():
            val = int(clean_g)
            if 1 <= val <= len(gear_list):
                gear = dict(gear_list[val - 1])
            else:
                gear = next((dict(g) for g in gear_list if g["equipment_id"] == val), None)

        if not gear:
            await ctx.send(embed=Embeds.error("Equipment Not Found", f"Could not find equipment matching `{gear_index_or_id}` in your inventory."))
            return

        # Find target character
        heroes = await db.get_player_characters(user_id)
        if not heroes:
            await ctx.send(embed=Embeds.warning("No Heroes", "You don't own any heroes yet! Use `vstart`."))
            return

        target_char = None
        if hero_index_or_name:
            clean_h = hero_index_or_name.lstrip('#')
            if clean_h.isdigit():
                val = int(clean_h)
                if 1 <= val <= len(heroes):
                    target_char = dict(heroes[val - 1])
                else:
                    target_char = next((dict(c) for c in heroes if c["instance_id"] == val), None)
            else:
                st = hero_index_or_name.lower()
                for c in heroes:
                    if st in c["name"].lower() or st in c["class_type"].lower():
                        target_char = dict(c)
                        break
        else:
            # Default to active main hero
            target_char = next((dict(c) for c in heroes if c["is_active"]), dict(heroes[0]))

        if not target_char:
            await ctx.send(embed=Embeds.error("Hero Not Found", f"Could not find hero matching `{hero_index_or_name}`."))
            return

        # Check compatibility
        comp_class = gear.get("compatible_class", "All")
        if comp_class and comp_class != "All" and comp_class.lower() != target_char["class_type"].lower():
            await ctx.send(embed=Embeds.warning(
                "Incompatible Equipment",
                f"**{gear['name']}** requires class **{comp_class}**, but **{target_char['name']}** is a **{target_char['class_type']}**!"
            ))
            return

        # Equip gear to hero
        await db.equip_gear(user_id, gear["equipment_id"], target_char["instance_id"])
        embed = Embeds.success(
            "Equipment Equipped!",
            f"Equipped **{gear['name']}** [{gear['rarity']}] ({gear['slot']}) to **{target_char['name']}** ({target_char['class_type']})!"
        )
        await ctx.send(embed=embed)

    @commands.command(name="unequip", aliases=["uneqp", "dequip"])
    async def unequip_gear(self, ctx: commands.Context, gear_index_or_id: str):
        """Unequip a piece of equipment by index number or ID (e.g. `vunequip #1`)."""
        user_id = ctx.author.id
        gear_list = await db.get_player_equipment(user_id)
        if not gear_list:
            await ctx.send(embed=Embeds.warning("No Equipment", "You don't own any equipment!"))
            return

        gear = None
        clean_g = gear_index_or_id.lstrip('#')
        if clean_g.isdigit():
            val = int(clean_g)
            if 1 <= val <= len(gear_list):
                gear = dict(gear_list[val - 1])
            else:
                gear = next((dict(g) for g in gear_list if g["equipment_id"] == val), None)

        if not gear:
            await ctx.send(embed=Embeds.error("Equipment Not Found", f"Could not find equipment matching `{gear_index_or_id}` in your inventory."))
            return

        if not gear["equipped_character_id"]:
            await ctx.send(embed=Embeds.warning("Not Equipped", f"**{gear['name']}** is not currently equipped to any hero!"))
            return

        await db.execute("UPDATE player_equipment SET equipped_character_id = NULL WHERE equipment_id = ?", (gear["equipment_id"],))
        embed = Embeds.success(
            "Equipment Unequipped!",
            f"Unequipped **{gear['name']}** [{gear['rarity']}] ({gear['slot']})!"
        )
        await ctx.send(embed=embed)

    @commands.command(name="forge", aliases=["craft"])

    async def forge(self, ctx: commands.Context, slot_or_class: str = "Weapon", slot_input: str = None):
        """Forge a class-compatible equipment piece (Costs 500 Coins + 2 Sigils)."""
        import random
        from utils.constants import RARITY_MULTIPLIERS

        user_id = ctx.author.id
        cost_coins = 500
        cost_sigils = 2

        # Check player currency
        player = await db.get_or_create_player(user_id)
        if player["coins"] < cost_coins or player["sigils"] < cost_sigils:
            await ctx.send(embed=Embeds.error(
                "Insufficient Funds",
                f"Forging costs 🪙 **{cost_coins:,} Coins** and 🔮 **{cost_sigils} Sigils**!\n"
                f"Your balance: 🪙 `{player['coins']:,}` | 🔮 `{player['sigils']}`"
            ))
            return

        # Determine target slot and class
        slots = ["Weapon", "Helmet", "Armor", "Boots", "Ring", "Necklace", "Artifact", "Pet"]
        
        target_slot = "Weapon"
        target_class = None

        if slot_or_class.capitalize() in slots:
            target_slot = slot_or_class.capitalize()
            if slot_input:
                target_class = slot_input.capitalize()
        else:
            target_class = slot_or_class.capitalize()
            if slot_input and slot_input.capitalize() in slots:
                target_slot = slot_input.capitalize()

        # If class not specified, check player's active hero
        if not target_class:
            chars = await db.get_player_characters(user_id)
            active = next((c for c in chars if c["is_active"]), chars[0] if chars else None)
            if active:
                target_class = active["class_type"]

        # Deduct forging cost
        await db.execute("UPDATE players SET coins = coins - ?, sigils = sigils - ? WHERE user_id = ?", (cost_coins, cost_sigils, user_id))

        # Query catalog
        catalog_items = await db.get_catalog_equipment(slot=target_slot, class_type=target_class)
        
        if catalog_items:
            chosen = dict(random.choice(catalog_items))
            name = chosen["name"]
            comp_class = chosen["compatible_class"]
        else:
            name = f"{target_class or 'Hero'}'s {target_slot}"
            comp_class = target_class or "All"

        rarities = ["D", "C", "B", "A", "S", "SS"]
        weights = [50, 25, 15, 7, 2.5, 0.5]
        rarity = random.choices(rarities, weights=weights)[0]
        quality = random.randint(1, 100)

        q_mult = 0.5 + (quality / 100) * 0.75
        r_mult = RARITY_MULTIPLIERS.get(rarity, 1.0)

        base_val = int(10 * r_mult * q_mult)
        hp = base_val * 4 if target_slot in ("Helmet", "Armor", "Pet") else base_val * 2
        atk = base_val * 3 if target_slot in ("Weapon", "Artifact", "Ring") else base_val
        defense = base_val * 3 if target_slot in ("Armor", "Helmet", "Boots") else base_val
        spd = base_val * 2 if target_slot in ("Boots", "Necklace") else base_val // 2

        eq_data = {
            "name": name,
            "slot": target_slot,
            "compatible_class": comp_class,
            "rarity": rarity,
            "quality": quality,
            "durability": 100,
            "max_durability": 100,
            "stat_hp": hp,
            "stat_atk": atk,
            "stat_def": defense,
            "stat_spd": spd
        }

        item = await db.add_equipment(user_id, eq_data)
        await db.update_quest_progress(user_id, "Blacksmith", 1)

        embed = Embeds.success(
            "Equipment Forged!",
            f"Forged **{item['name']}** [{item['rarity']}] Quality **{item['quality']}%** for **{comp_class}** (Cost: 🪙 {cost_coins:,} | 🔮 {cost_sigils})!\n"
            f"❤️ `+{item['stat_hp']}` | ⚔️ `+{item['stat_atk']}` | 🛡️ `+{item['stat_def']}` | ⚡ `+{item['stat_spd']}`"
        )
        await ctx.send(embed=embed)



    @commands.command(name="reroll", aliases=["rr"])
    async def reroll(self, ctx: commands.Context, index_or_id: str):
        """Perform a single equipment reroll (Costs 10 Sigils)."""
        gear_list = await db.get_player_equipment(ctx.author.id)
        if not gear_list:
            await ctx.send(embed=Embeds.warning("No Equipment", "You don't own any equipment items yet!"))
            return

        gear = None
        clean_arg = index_or_id.lstrip('#')
        if clean_arg.isdigit():
            val = int(clean_arg)
            if 1 <= val <= len(gear_list):
                gear = dict(gear_list[val - 1])
            else:
                gear = next((dict(g) for g in gear_list if g["equipment_id"] == val), None)

        if not gear:
            await ctx.send(embed=Embeds.error("Item Not Found", f"No equipment item matching `{index_or_id}` found in your inventory."))
            return

        current_stats = dict(gear)
        
        # Deduct 10 Sigils
        try:
            await db.consume_sigils(ctx.author.id, 10)
        except ValueError as e:
            await ctx.send(embed=Embeds.error("Reroll Failed", str(e)))
            return

        new_stats = roll_new_equipment_stats(current_stats["slot"])

        embed = RerollView.build_comparison_embed(current_stats, new_stats)
        view = RerollView(
            author_id=ctx.author.id,
            equipment_id=gear["equipment_id"],
            current_stats=current_stats,
            new_stats=new_stats
        )
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="repair", aliases=["vrepair", "r", "rp"])
    async def repair(self, ctx: commands.Context, *, index_or_id: str = None):
        """Inspect & repair targeted equipment durability (e.g. `vrepair #1` or `vrepair Iron Longsword`)."""
        user_id = ctx.author.id
        gear_list = await db.get_player_equipment(user_id)
        if not gear_list:
            await ctx.send(embed=Embeds.warning("No Equipment", "You don't own any equipment items yet!"))
            return

        if not index_or_id:
            gear = min([dict(g) for g in gear_list], key=lambda g: g["durability"] / max(1, g["max_durability"]))
        else:
            gear = None
            clean_arg = index_or_id.strip().lstrip('#')
            if clean_arg.isdigit():
                val = int(clean_arg)
                if 1 <= val <= len(gear_list):
                    gear = dict(gear_list[val - 1])
                else:
                    gear = next((dict(g) for g in gear_list if g["equipment_id"] == val), None)

            if not gear:
                st = index_or_id.lower()
                gear = next((dict(g) for g in gear_list if st in g["name"].lower() or st in g["slot"].lower()), None)

        if not gear:
            await ctx.send(embed=Embeds.error("Item Not Found", f"No equipment item matching `{index_or_id}` found in your inventory."))
            return

        missing_dur = gear["max_durability"] - gear["durability"]
        if missing_dur == 0:
            await ctx.send(embed=Embeds.info("Fully Repaired", f"**{gear['name']}** [{gear['rarity']}] is already at full durability (`100%`)!"))
            return

        # Check if player owns a Repair Kit consumable
        repair_kits_owned = await db.get_consumable_quantity(user_id, "repair_kit")
        if repair_kits_owned > 0:
            await db.use_consumable(user_id, "repair_kit", 1)
            await db.execute("UPDATE player_equipment SET durability = max_durability WHERE equipment_id = ?", (gear["equipment_id"],))
            await db.execute("UPDATE player_stats SET repair_kits_used = repair_kits_used + 1 WHERE user_id = ?", (user_id,))
            embed = Embeds.success(
                "Equipment Repaired!",
                f"🛠️ Used **1x Repair Kit** to restore **{gear['name']}** [{gear['rarity']}] ({gear['slot']}) to **100% Durability** (`{gear['max_durability']}/{gear['max_durability']}`)!"
            )
            await ctx.send(embed=embed)
        else:
            cost_coins = missing_dur * 10
            player = await db.get_or_create_player(user_id)
            if player["coins"] < cost_coins:
                await ctx.send(embed=Embeds.error(
                    "Insufficient Coins",
                    f"Repairing **{gear['name']}** costs 🪙 **{cost_coins:,} Coins** (or 1x Repair Kit)!\n"
                    f"Your balance: 🪙 `{player['coins']:,}`"
                ))
                return

    @commands.command(name="winfo", aliases=["vwinfo", "weaponinfo", "gearinfo"])
    async def weapon_info(self, ctx: commands.Context, index_or_id: str):
        """Inspect detailed weapon/equipment stats and durability (e.g. `vwinfo #1`)."""
        user_id = ctx.author.id
        gear_list = await db.get_player_equipment(user_id)
        if not gear_list:
            await ctx.send(embed=Embeds.warning("No Equipment", "You don't own any equipment items yet!"))
            return

        gear = None
        clean_arg = index_or_id.strip().lstrip('#')
        if clean_arg.isdigit():
            val = int(clean_arg)
            if 1 <= val <= len(gear_list):
                gear = dict(gear_list[val - 1])
            else:
                gear = next((dict(g) for g in gear_list if g["equipment_id"] == val), None)

        if not gear:
            st = index_or_id.lower()
            gear = next((dict(g) for g in gear_list if st in g["name"].lower()), None)

        if not gear:
            await ctx.send(embed=Embeds.error("Item Not Found", f"Could not find equipment matching `{index_or_id}` in your inventory."))
            return

        embed = EquipmentDetailView.build_equipment_embed(dict(gear))
        view = EquipmentDetailView(author_id=ctx.author.id, eq_row=gear)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="scrollinfo", aliases=["vscrollinfo", "scinfo"])
    async def scroll_info(self, ctx: commands.Context, index_or_id: str):
        """Inspect detailed skill scroll attributes, level requirements & power (e.g. `vscrollinfo #1`)."""
        user_id = ctx.author.id
        scroll_rows = await db.fetchall(
            """
            SELECT ps.instance_id, ps.scroll_id, s.name, s.scroll_type, s.power, s.cooldown,
                   s.required_class_tags, s.min_level, s.resource_cost, s.description
            FROM player_scrolls ps
            JOIN scrolls s ON ps.scroll_id = s.scroll_id
            WHERE ps.user_id = ?
            """,
            (user_id,)
        )
        if not scroll_rows:
            scroll_rows = await db.fetchall("SELECT * FROM scrolls")

        target_scroll = None
        clean_s = index_or_id.strip().lstrip('#')
        if clean_s.isdigit():
            val = int(clean_s)
            if 1 <= val <= len(scroll_rows):
                target_scroll = dict(scroll_rows[val - 1])
            else:
                target_scroll = next((dict(s) for s in scroll_rows if s.get("instance_id") == val), None)

        if not target_scroll:
            st = index_or_id.lower()
            target_scroll = next((dict(s) for s in scroll_rows if st in s["name"].lower() or st in s["scroll_type"].lower()), None)

        if not target_scroll:
            await ctx.send(embed=Embeds.error("Scroll Not Found", f"Could not find skill scroll matching `{index_or_id}`."))
            return

        embed = discord.Embed(
            title=f"📜 Scroll Info — {target_scroll['name']}",
            description="─────────────────────────────────────",
            color=0x0984E3
        )
        embed.add_field(name="Scroll Details", value=f"Type: **{target_scroll['scroll_type']}**\nPower Rating: `⚡ {target_scroll['power']}`\nCooldown: `⏳ {target_scroll['cooldown']} turns`", inline=True)
        embed.add_field(name="Requirements", value=f"Required Level: `Lvl {target_scroll.get('min_level', 1)}`\nResource Cost: `{target_scroll.get('resource_cost', 20)}` Power\nCompatible Classes: **{target_scroll['required_class_tags']}**", inline=True)
        embed.add_field(name="Effect Description", value=f"*{target_scroll['description']}*", inline=False)
        embed.set_footer(text=f"Use 'vlearn #{target_scroll.get('instance_id', 1)} <hero>' to equip this scroll.")
        await ctx.send(embed=embed)




    @commands.command(name="scrolls", aliases=["sc"])
    async def scrolls(self, ctx: commands.Context):
        """View available skill scrolls in catalog."""
        scrolls = await db.fetchall("SELECT * FROM scrolls")
        if not scrolls:
            await ctx.send(embed=Embeds.info("Catalog Empty", "No skill scrolls available in catalog."))
            return

        chunk_size = 5
        pages = []
        total_scrolls = len(scrolls)

        for i in range(0, total_scrolls, chunk_size):
            chunk = scrolls[i:i + chunk_size]
            embed = discord.Embed(
                title="📜 Skill Scroll Catalog",
                description=(
                    f"Scrolls teach active and passive battle skills to compatible hero classes.\n"
                    f"Showing scrolls **{i+1}–{min(i+chunk_size, total_scrolls)}** of **{total_scrolls}** total.\n───────────"
                ),
                color=0x0984E3
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            for s in chunk:
                embed.add_field(
                    name=f"✨ {s['name']} [{s['scroll_type']}]",
                    value=(
                        f"⚡ Power: `{s['power']}`  |  ⏳ Cooldown: `{s['cooldown']} turns`  |  🎯 Status: `{s['status_chance']}%`\n"
                        f"🛡️ Compatible Classes: **{s['required_class_tags']}**\n"
                        f"*{s['description']}*\n"
                    ),
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


    @commands.command(name="equipscroll", aliases=["vlearn", "vequipscroll", "learnscroll"])
    async def equip_scroll(self, ctx: commands.Context, scroll_index_or_id: str, hero_index_or_name: str = None):
        """Learn and equip a skill scroll to a compatible hero at required level (e.g. `vlearn #1 #1`)."""
        user_id = ctx.author.id

        scroll_rows = await db.fetchall(
            """
            SELECT ps.instance_id, ps.scroll_id, s.name, s.scroll_type, s.power, s.cooldown,
                   s.required_class_tags, s.min_level, s.resource_cost, s.description
            FROM player_scrolls ps
            JOIN scrolls s ON ps.scroll_id = s.scroll_id
            WHERE ps.user_id = ?
            """,
            (user_id,)
        )
        if not scroll_rows:
            await ctx.send(embed=Embeds.warning("No Scrolls", "You don't own any skill scrolls! Open blank scrolls (`vopen blank`) or buy items at `vshop`."))
            return

        target_scroll = None
        clean_s = scroll_index_or_id.strip().lstrip('#')
        if clean_s.isdigit():
            val = int(clean_s)
            if 1 <= val <= len(scroll_rows):
                target_scroll = dict(scroll_rows[val - 1])
            else:
                target_scroll = next((dict(s) for s in scroll_rows if s["instance_id"] == val), None)

        if not target_scroll:
            await ctx.send(embed=Embeds.error("Scroll Not Found", f"Could not find skill scroll matching `{scroll_index_or_id}` in your inventory."))
            return

        heroes = await db.get_player_characters(user_id)
        if not heroes:
            await ctx.send(embed=Embeds.warning("No Heroes", "You don't own any heroes yet! Use `vstart`."))
            return

        target_hero = None
        if hero_index_or_name:
            clean_h = hero_index_or_name.strip().lstrip('#')
            if clean_h.isdigit():
                val = int(clean_h)
                if 1 <= val <= len(heroes):
                    target_hero = dict(heroes[val - 1])
                else:
                    target_hero = next((dict(c) for c in heroes if c["instance_id"] == val), None)
            else:
                st = hero_index_or_name.lower()
                target_hero = next((dict(c) for c in heroes if st in c["name"].lower() or st in c["class_type"].lower()), None)
        else:
            target_hero = next((dict(c) for c in heroes if c["is_active"]), dict(heroes[0]))

        if not target_hero:
            await ctx.send(embed=Embeds.error("Hero Not Found", f"Could not find hero matching `{hero_index_or_name}`."))
            return

        # Check level requirement
        min_lvl = target_scroll.get("min_level", 1)
        if target_hero["level"] < min_lvl:
            await ctx.send(embed=Embeds.warning(
                "Level Requirement Unmet",
                f"**{target_hero['name']}** is Level **{target_hero['level']}**, but **{target_scroll['name']}** requires Level **{min_lvl}**!"
            ))
            return

        # Check class tag compatibility
        req_tags = target_scroll.get("required_class_tags", "All")
        if req_tags and req_tags != "All":
            allowed_classes = [c.strip().lower() for c in req_tags.split(",")]
            if target_hero["class_type"].lower() not in allowed_classes:
                await ctx.send(embed=Embeds.warning(
                    "Incompatible Class",
                    f"**{target_scroll['name']}** requires class **{req_tags}**, but **{target_hero['name']}** is a **{target_hero['class_type']}**!"
                ))
                return

        # Assign into character_loadouts
        current_loadout = await db.fetchall("SELECT * FROM character_loadouts WHERE character_instance_id = ?", (target_hero["instance_id"],))
        slot_idx = len(current_loadout) + 1
        if slot_idx > 2:
            slot_idx = 1  # Swap slot 1 if full

        await db.execute(
            """
            INSERT INTO character_loadouts (character_instance_id, slot_index, scroll_instance_id)
            VALUES (?, ?, ?)
            ON CONFLICT(character_instance_id, slot_index) DO UPDATE SET
                scroll_instance_id = excluded.scroll_instance_id
            """,
            (target_hero["instance_id"], slot_idx, target_scroll["instance_id"])
        )

        embed = Embeds.success(
            "Skill Scroll Learned & Equipped!",
            f"📜 **{target_hero['name']}** ({target_hero['class_type']}) learned **{target_scroll['name']}** [{target_scroll['scroll_type']}] (Slot #{slot_idx})!\n"
            f"Cost: `{target_scroll.get('resource_cost', 20)}` {target_hero['resource_type']} | Required Lvl: `{min_lvl}`"
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(EquipmentCog(bot))

