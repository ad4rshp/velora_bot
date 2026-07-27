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
        """View recently listed items in the marketplace."""
        listings = await db.get_active_market_listings()

        if not listings:
            embed = discord.Embed(
                description=(
                    "─────────────────────────────────────\n"
                    "No items currently listed for sale in the marketplace!\n"
                    "Use `vmarket add <#gear_id> <price>` to list an item.\n"
                    "─────────────────────────────────────"
                ),
                color=0x00B894
            )
            await ctx.send(embed=embed)
            return

        chunk_size = 5
        pages = []
        for i in range(0, len(listings), chunk_size):
            chunk = listings[i:i + chunk_size]
            embed = discord.Embed(
                title="🏪 Player Marketplace — Recent Listings",
                description=f"Showing **{i+1}–{min(i+chunk_size, len(listings))}** of **{len(listings)}** active listings.\n─────────────────────────────────────",
                color=0x00B894
            )

            for item in chunk:
                seller = self.bot.get_user(item['seller_id'])
                seller_name = seller.display_name if seller else f"User {item['seller_id']}"
                item_data = json.loads(item['item_data_json']) if isinstance(item['item_data_json'], str) else item['item_data_json']
                rarity = item_data.get('rarity', 'D')
                quality = item_data.get('quality', 50)

                embed.add_field(
                    name=f"#{item['listing_id']}. {item['item_name']} [{rarity}] • {quality}%",
                    value=f"Price: 🪙 **{item['price_coins']:,} Coins** | Seller: **{seller_name}**\n───────────",
                    inline=False
                )

            pages.append(embed)

        if len(pages) == 1:
            await ctx.send(embed=pages[0])
        else:
            view = PaginatorView(author_id=ctx.author.id, pages=pages)
            view.message = await ctx.send(embed=pages[0], view=view)

    @market.command(name="add", aliases=["list"])
    async def market_add(self, ctx: commands.Context, equipment_id: str, price: int):
        """List an equipment piece for sale on the marketplace (e.g. `vmarket add #1 2500`)."""
        clean_id = equipment_id.lstrip('#')
        if not clean_id.isdigit():
            await ctx.send(embed=Embeds.error("Invalid ID", "Please specify a valid equipment ID (e.g. `vmarket add #1 2500`)."))
            return

        eq_id = int(clean_id)
        if price <= 0:
            await ctx.send(embed=Embeds.error("Invalid Price", "Listing price must be greater than 0 coins."))
            return

        gear = await db.get_equipment_by_id(eq_id)
        if not gear or gear["user_id"] != ctx.author.id:
            await ctx.send(embed=Embeds.error("Item Not Found", f"Could not find equipment #{eq_id} in your inventory."))
            return

        if gear["equipped_character_id"]:
            await ctx.send(embed=Embeds.warning("Item Equipped", f"**{gear['name']}** is currently equipped! Unequip it before listing."))
            return

        data_json = json.dumps(dict(gear))
        listing = await db.create_market_listing(ctx.author.id, gear["name"], "equipment", data_json, price)
        await db.update_quest_progress(ctx.author.id, "Merchant", 1)

        embed = Embeds.success(
            "Item Listed for Sale!",
            f"Listed **{gear['name']}** [{gear['rarity']}] Quality **{gear['quality']}%** for 🪙 **{price:,} Coins**!\n(Listing ID: **#{listing['id']}**)"
        )
        await ctx.send(embed=embed)

    @market.command(name="buy")
    async def market_buy(self, ctx: commands.Context, listing_id: str):
        """Purchase an item listing from the marketplace (e.g. `vmarket buy #1`)."""
        clean_id = listing_id.lstrip('#')
        if not clean_id.isdigit():
            await ctx.send(embed=Embeds.error("Invalid ID", "Please specify a valid listing ID (e.g. `vmarket buy #1`)."))
            return

        l_id = int(clean_id)
        try:
            bought = await db.buy_market_listing(ctx.author.id, l_id)
            item_data = json.loads(bought["item_data_json"])
            
            # Transfer equipment ownership to buyer
            await db.execute("UPDATE player_equipment SET user_id = ? WHERE equipment_id = ?", (ctx.author.id, item_data["equipment_id"]))

            embed = Embeds.success(
                "Market Purchase Successful!",
                f"Purchased **{bought['item_name']}** for 🪙 **{bought['price_coins']:,} Coins**!"
            )
            await ctx.send(embed=embed)
        except ValueError as e:
            await ctx.send(embed=Embeds.error("Purchase Failed", str(e)))

    @market.command(name="info", aliases=["inspect"])
    async def market_info(self, ctx: commands.Context, listing_id: str):
        """Inspect detailed item stats for a marketplace listing (e.g. `vmarket info #1`)."""
        clean_id = listing_id.lstrip('#')
        if not clean_id.isdigit():
            await ctx.send(embed=Embeds.error("Invalid ID", "Please specify a valid listing ID (e.g. `vmarket info #1`)."))
            return

        l_id = int(clean_id)
        listing = await db.fetchone("SELECT * FROM market_listings WHERE listing_id = ?", (l_id,))
        if not listing:
            await ctx.send(embed=Embeds.error("Listing Not Found", f"No active market listing found with ID #{l_id}."))
            return

        seller = self.bot.get_user(listing["seller_id"])
        seller_name = seller.display_name if seller else f"User {listing['seller_id']}"
        item_data = json.loads(listing["item_data_json"]) if isinstance(listing["item_data_json"], str) else listing["item_data_json"]

        embed = discord.Embed(
            title=f"🔎 Market Listing #{listing['listing_id']} — {listing['item_name']}",
            description="─────────────────────────────────────",
            color=0x00B894
        )
        embed.add_field(
            name="Item Overview",
            value=(
                f"Slot: **{item_data.get('slot', 'Equipment')}** | Class: **{item_data.get('compatible_class', 'All')}**\n"
                f"Rarity: **[{item_data.get('rarity', 'D')}]** | Quality: **{item_data.get('quality', 50)}%**\n"
                f"Durability: `{item_data.get('durability', 100)}/{item_data.get('max_durability', 100)}`\n"
                f"HP: `+{item_data.get('stat_hp', 0)}`  ATK: `+{item_data.get('stat_atk', 0)}`  DF: `+{item_data.get('stat_def', 0)}`  SP: `+{item_data.get('stat_spd', 0)}`\n───────────"
            ),
            inline=False
        )
        embed.add_field(
            name="Listing Details",
            value=f"Price: 🪙 **{listing['price_coins']:,} Coins**\nSeller: **{seller_name}**",
            inline=False
        )
        embed.set_footer(text=f"Use 'vmarket buy #{listing['listing_id']}' to purchase.")
        await ctx.send(embed=embed)

    @market.command(name="remove", aliases=["cancel", "del"])
    async def market_remove(self, ctx: commands.Context, listing_id: str):
        """Remove/cancel your active marketplace listing (e.g. `vmarket remove #1`)."""
        clean_id = listing_id.lstrip('#')
        if not clean_id.isdigit():
            await ctx.send(embed=Embeds.error("Invalid ID", "Please specify a valid listing ID (e.g. `vmarket remove #1`)."))
            return

        l_id = int(clean_id)
        listing = await db.fetchone("SELECT * FROM market_listings WHERE listing_id = ?", (l_id,))
        if not listing:
            await ctx.send(embed=Embeds.error("Listing Not Found", f"No active market listing found with ID #{l_id}."))
            return

        if listing["seller_id"] != ctx.author.id:
            await ctx.send(embed=Embeds.error("Permission Denied", "You can only remove your own market listings!"))
            return

        await db.execute("DELETE FROM market_listings WHERE listing_id = ?", (l_id,))
        embed = Embeds.success(
            "Listing Removed!",
            f"Removed your listing for **{listing['item_name']}** (Listing #{l_id}) from the market."
        )
        await ctx.send(embed=embed)


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
