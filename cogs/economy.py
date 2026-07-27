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

    @commands.command(name="open", aliases=["use", "vopen"])
    async def open_item(self, ctx: commands.Context, item_id: str = "common_chest"):
        """Open chests or consume items (common_chest, rare_chest, blank_scroll, repair_kit)."""
        user_id = ctx.author.id
        item_key = item_id.lower()

        valid_items = ["common_chest", "rare_chest", "blank_scroll", "repair_kit"]
        if item_key not in valid_items:
            await ctx.send(embed=Embeds.error("Invalid Item", f"Valid items to open: `{', '.join(valid_items)}`"))
            return

        try:
            await db.use_consumable(user_id, item_key, 1)
        except ValueError as e:
            await ctx.send(embed=Embeds.warning("Item Missing", f"You don't own any `{item_key}`! Buy one at `{ctx.prefix}shop`."))
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
            # Generate random scroll from catalog
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

async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
