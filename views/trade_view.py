"""
Dual-Confirmation Interactive Player Trading View for Velora.
Allows two players to safely trade coins and items with mutual confirmation.
"""

import discord
from views.base_view import VeloraView
from utils.embeds import Embeds
from utils.db import db

class TradeView(VeloraView):
    """Interactive trade confirmation view for 2 players."""

    def __init__(self, sender_id: int, receiver_id: int, coins: int):
        super().__init__(author_id=sender_id, timeout=120.0)
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.coins = coins

        self.sender_confirmed = False
        self.receiver_confirmed = False

        self.btn_confirm = discord.ui.Button(
            label="Confirm Trade",
            style=discord.ButtonStyle.success,
            emoji="🤝",
            row=0
        )
        self.btn_confirm.callback = self.confirm_callback
        self.add_item(self.btn_confirm)

        self.btn_cancel = discord.ui.Button(
            label="Cancel Trade",
            style=discord.ButtonStyle.danger,
            emoji="✖️",
            row=0
        )
        self.btn_cancel.callback = self.cancel_callback
        self.add_item(self.btn_cancel)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in (self.sender_id, self.receiver_id):
            await interaction.response.send_message("❌ You are not a participant in this trade.", ephemeral=True)
            return False
        return True

    def build_trade_embed(self, sender: discord.User, receiver: discord.User) -> discord.Embed:
        embed = discord.Embed(
            title="🤝 Direct Trade",
            description=f"Offer: **{self.coins:,} Coins**\n───────────",
            color=0x00B894
        )
        
        status_sender = "✅ Ready" if self.sender_confirmed else "⏳ Waiting"
        status_receiver = "✅ Ready" if self.receiver_confirmed else "⏳ Waiting"

        embed.add_field(name=sender.display_name, value=status_sender, inline=True)
        embed.add_field(name=receiver.display_name, value=status_receiver, inline=True)
        return embed


    async def confirm_callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.sender_id:
            self.sender_confirmed = True
        elif interaction.user.id == self.receiver_id:
            self.receiver_confirmed = True

        if self.sender_confirmed and self.receiver_confirmed:
            # Transfer coins
            try:
                sender_p = await db.get_or_create_player(self.sender_id)
                if sender_p["coins"] < self.coins:
                    raise ValueError("Sender lacks sufficient coins for this trade!")

                await db.execute("UPDATE players SET coins = coins - ? WHERE user_id = ?", (self.coins, self.sender_id))
                await db.execute("UPDATE players SET coins = coins + ? WHERE user_id = ?", (self.coins, self.receiver_id))
                await db.execute("UPDATE player_stats SET trades = trades + 1 WHERE user_id = ?", (self.sender_id,))
                await db.execute("UPDATE player_stats SET trades = trades + 1 WHERE user_id = ?", (self.receiver_id,))
                await db.update_quest_progress(self.sender_id, "Merchant", 1)
                await db.update_quest_progress(self.receiver_id, "Merchant", 1)

                for child in self.children:
                    child.disabled = True

                embed = Embeds.success("Trade Finalized!", f"Successfully transferred **{self.coins:,} Coins**!")
                await interaction.response.edit_message(embed=embed, view=self)
                self.stop()

            except ValueError as e:
                await interaction.response.send_message(f"❌ {e}", ephemeral=True)
        else:
            await interaction.response.send_message("✅ You confirmed the trade! Waiting for other player...", ephemeral=True)

    async def cancel_callback(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True

        embed = Embeds.error("Trade Cancelled", "The trade offer was cancelled.")
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
