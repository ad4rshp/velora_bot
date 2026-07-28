import random
import discord
from views.base_view import VeloraView
from utils.embeds import Embeds
from utils.db import db

SHOP_ITEMS = {
    "novice_pack": {"name": "Novice Hero Pack", "cost_type": "coins", "cost": 500, "desc": "Summons a starter hero card to your roster."},
    "mythic_pack": {"name": "Mythic Hero Pack", "cost_type": "coins", "cost": 2500, "desc": "Summons an upgraded hero card with high level potential."},
    "celestial_pack": {"name": "Celestial Hero Pack", "cost_type": "sigils", "cost": 20, "desc": "Summons an ultra rare hero card to your roster."},
    "xp_booster": {"name": "XP Booster", "cost_type": "coins", "cost": 500, "desc": "Doubles all Chat and Battle XP earned for 24h."},
    "repair_kit": {"name": "Repair Kit", "cost_type": "coins", "cost": 300, "desc": "Restores full durability to an equipment piece."}
}





class ShopSelect(discord.ui.Select):
    """Dropdown menu for General Store items."""

    def __init__(self):
        options = [
            discord.SelectOption(label=item["name"], value=key, description=f"{item['cost']:,} {item['cost_type'].capitalize()} — {item['desc']}", emoji="🛒")
            for key, item in SHOP_ITEMS.items()
        ]
        super().__init__(placeholder="🛒 Select a pack or item to purchase...", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: ShopView = self.view
        view.selected_item = self.values[0]
        item = SHOP_ITEMS[view.selected_item]
        
        embed = view.build_shop_embed(selected_item=item)
        view.btn_buy.disabled = False
        await interaction.response.edit_message(embed=embed, view=view)


class ShopView(VeloraView):
    """Interactive General Store view."""


    def __init__(self, author_id: int):
        super().__init__(author_id=author_id, timeout=120.0)
        self.selected_item = None

        self.add_item(ShopSelect())

        self.btn_buy = discord.ui.Button(
            label="Buy & Unpack",
            style=discord.ButtonStyle.success,
            emoji="💰",
            disabled=True,
            row=1
        )
        self.btn_buy.callback = self.buy_callback
        self.add_item(self.btn_buy)

    def build_shop_embed(self, selected_item: dict = None) -> discord.Embed:
        embed = discord.Embed(
            title="🏪 General Store — Hero Packs & Supplies",
            description="Select a Hero Pack below to purchase & summon cards directly to your inventory.\n───────────",
            color=0x00B894
        )

        for key, item in SHOP_ITEMS.items():
            cost_emoji = "🪙" if item["cost_type"] == "coins" else "🔮"
            highlight = " ⭐" if selected_item and selected_item["name"] == item["name"] else ""
            embed.add_field(
                name=f"{item['name']}{highlight}",
                value=f"{cost_emoji} **{item['cost']:,}** {item['cost_type'].capitalize()} • {item['desc']}",
                inline=False
            )

        return embed


    async def buy_callback(self, interaction: discord.Interaction):
        if not self.selected_item:
            return

        item = SHOP_ITEMS[self.selected_item]
        user_id = self.author_id

        try:
            player = await db.get_or_create_player(user_id)
            if item["cost_type"] == "coins":
                if player["coins"] < item["cost"]:
                    raise ValueError(f"Insufficient Coins! You need {item['cost']:,} coins.")
                await db.execute("UPDATE players SET coins = coins - ? WHERE user_id = ?", (item["cost"], user_id))
            else:
                if player["sigils"] < item["cost"]:
                    raise ValueError(f"Insufficient Sigils! You need {item['cost']:,} sigils.")
                await db.execute("UPDATE players SET sigils = sigils - ? WHERE user_id = ?", (item["cost"], user_id))

            if self.selected_item in ("novice_pack", "mythic_pack", "celestial_pack"):
                all_catalog = await db.fetchall("SELECT * FROM characters")
                cat_char = dict(random.choice(all_catalog))
                
                if self.selected_item == "novice_pack":
                    rarities = ["D", "C", "B", "A"]
                    weights = [68, 24, 7, 1]
                    lvl = random.randint(1, 5)
                elif self.selected_item == "mythic_pack":
                    rarities = ["D", "C", "B", "A", "S", "SS"]
                    weights = [45, 32, 16, 5, 1.9, 0.1]
                    lvl = random.randint(5, 15)
                else: # celestial_pack
                    rarities = ["C", "B", "A", "S", "SS"]
                    weights = [35, 42, 18, 4.6, 0.4]
                    lvl = random.randint(10, 20)



                rarity = random.choices(rarities, weights=weights)[0]

                # Ensure player profile exists in players table
                await db.get_or_create_player(user_id)

                # Insert player character
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
                    f"You opened **{item['name']}** and summoned **{cat_char['name']}** ({cat_char['class_type']})!\n"
                    f"Rarity: **[{rarity}]** | Level: **{lvl}**\nAdded to your hero inventory (`vinventory`)!"
                )
            else:
                await db.add_consumable(user_id, self.selected_item, 1)
                embed = Embeds.success(
                    "Purchase Successful!",
                    f"Purchased **1x {item['name']}** for **{item['cost']:,} {item['cost_type'].capitalize()}**!"
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
