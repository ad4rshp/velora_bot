"""
Player Marketplace & Direct Trading Cog for Velora RPG.
Implements vmarket (listing, buying, searching) and vtrade (2-player interactive trading).
"""

import discord
import json
from discord.ext import commands
from utils.embeds import Embeds
from utils.db import db
from views.trade_view import TradeView
from views.paginator import PaginatorView

class MarketCog(commands.Cog, name="Market"):
    """Player Marketplace & Direct Trading System."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="market", aliases=["m", "mkt"], invoke_without_command=True)
    async def market(self, ctx: commands.Context):


        """View active marketplace listings."""
        listings = await db.get_active_market_listings()

        if not listings:
            await ctx.send(embed=Embeds.info("Player Marketplace", "No items listed for sale currently!\nUse `vmarket list <equipment_id> <price>` to list an item."))
            return

        chunk_size = 5
        pages = []
        for i in range(0, len(listings), chunk_size):
            chunk = listings[i:i + chunk_size]
            embed = discord.Embed(
                title="🏪 Player Marketplace",
                description=f"Showing listings {i+1}-{min(i+chunk_size, len(listings))} of {len(listings)}\n───────────",
                color=0x00B894
            )

            for item in chunk:
                seller = self.bot.get_user(item['seller_id'])
                seller_name = seller.display_name if seller else f"User {item['seller_id']}"
                embed.add_field(
                    name=f"#{item['listing_id']}. {item['item_name']}",
                    value=f"🪙 **{item['price_coins']:,}** Coins • Seller: **{seller_name}**",
                    inline=False
                )

            pages.append(embed)


        if len(pages) == 1:
            await ctx.send(embed=pages[0])
        else:
            view = PaginatorView(author_id=ctx.author.id, pages=pages)
            view.message = await ctx.send(embed=pages[0], view=view)

    @market.command(name="list")
    async def market_list(self, ctx: commands.Context, equipment_id: int, price: int):
        """List an equipment piece on the marketplace for Coins."""
        if price <= 0:
            await ctx.send(embed=Embeds.error("Invalid Price", "Listing price must be greater than 0 coins."))
            return

        gear = await db.get_equipment_by_id(equipment_id)
        if not gear or gear["user_id"] != ctx.author.id:
            await ctx.send(embed=Embeds.error("Item Not Found", f"No equipment item with ID #{equipment_id} in your inventory."))
            return

        if gear["equipped_character_id"]:
            await ctx.send(embed=Embeds.warning("Item Equipped", "Unequip this item from your hero before listing it on the market."))
            return

        data_json = json.dumps(dict(gear))
        listing_id = await db.create_market_listing(ctx.author.id, gear["name"], "equipment", data_json, price)
        await db.update_quest_progress(ctx.author.id, "Merchant", 1)

        embed = Embeds.success(
            "Item Listed!",
            f"Listed **{gear['name']}** [{gear['rarity']}] on the marketplace for **{price:,} Coins**!\n(Listing #{listing_id['id']})"
        )
        await ctx.send(embed=embed)


    @market.command(name="buy")
    async def market_buy(self, ctx: commands.Context, listing_id: int):
        """Purchase an item listing from the marketplace."""
        try:
            bought = await db.buy_market_listing(ctx.author.id, listing_id)
            item_data = json.loads(bought["item_data_json"])
            
            # Transfer equipment to buyer
            await db.execute("UPDATE player_equipment SET user_id = ? WHERE equipment_id = ?", (ctx.author.id, item_data["equipment_id"]))

            embed = Embeds.success(
                "Purchase Finalized!",
                f"Purchased **{bought['item_name']}** for **{bought['price_coins']:,} Coins**!"
            )
            await ctx.send(embed=embed)
        except ValueError as e:
            await ctx.send(embed=Embeds.error("Market Error", str(e)))

    @commands.command(name="trade", aliases=["t"])
    async def trade(self, ctx: commands.Context, target: discord.User, coins: int = 100):


        """Initiate direct 2-player trade offer."""
        if target.id == ctx.author.id or target.bot:
            await ctx.send(embed=Embeds.error("Invalid Target", "You cannot trade with yourself or a bot."))
            return

        if coins <= 0:
            await ctx.send(embed=Embeds.error("Invalid Trade", "Trade coins amount must be positive."))
            return

        view = TradeView(sender_id=ctx.author.id, receiver_id=target.id, coins=coins)
        embed = view.build_trade_embed(ctx.author, target)
        view.message = await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(MarketCog(bot))
