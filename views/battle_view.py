"""
Interactive Battle UI Components for Velora RPG.
Conducts 3v3 battles using buttons and select menus with zero text commands.
"""

import discord
from typing import List, Optional, Any

from utils.battle_engine import BattleEngine, BattleSide
from utils.embeds import Embeds


class AttackSelect(discord.ui.Select):
    """Select menu listing active combatant attack options based on class moveset and level."""

    def __init__(self, engine: BattleEngine):
        active_hero = engine.current_side.active_hero
        hero_lvl = getattr(active_hero, "level", 1)
        hero_rarity = getattr(active_hero, "rarity", "D")

        from utils.movesets import get_scaled_moveset
        moveset = get_scaled_moveset(active_hero.class_type, rarity=hero_rarity)

        b_name, b_desc, b_pwr, b_cost, b_emoji, _ = moveset["basic"]
        s_name, s_desc, s_pwr, s_cost, s_emoji, s_lvl = moveset["skill"]
        u_name, u_desc, u_pwr, u_cost, u_emoji, u_lvl = moveset["ultimate"]

        options = [
            discord.SelectOption(
                label=b_name,
                value="basic",
                description=f"{b_desc} ({b_pwr} Pwr | {b_cost} {active_hero.resource_type})",
                emoji=b_emoji
            )
        ]

        if hero_lvl >= s_lvl:
            options.append(discord.SelectOption(
                label=s_name,
                value="skill",
                description=f"{s_desc} ({s_pwr} Pwr | {s_cost} {active_hero.resource_type})",
                emoji=s_emoji
            ))
        else:
            options.append(discord.SelectOption(
                label=f"🔒 {s_name} (Lvl {s_lvl})",
                value="locked_skill",
                description=f"Requires Level {s_lvl} to unlock.",
                emoji="🔒"
            ))

        if hero_lvl >= u_lvl:
            options.append(discord.SelectOption(
                label=u_name,
                value="ultimate",
                description=f"{u_desc} ({u_pwr} Pwr | {u_cost} {active_hero.resource_type})",
                emoji=u_emoji
            ))
        else:
            options.append(discord.SelectOption(
                label=f"🔒 {u_name} (Lvl {u_lvl})",
                value="locked_ult",
                description=f"Requires Level {u_lvl} to unlock.",
                emoji="🔒"
            ))

        super().__init__(placeholder=f"⚔️ Select move for {active_hero.name}...", options=options, row=0)
        self.engine = engine
        self.moveset = moveset

    async def callback(self, interaction: discord.Interaction):
        view: BattleView = self.view
        if interaction.user.id != self.engine.current_side.user_id:
            await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
            return

        move_key = self.values[0]
        if move_key.startswith("locked"):
            await interaction.response.send_message("🔒 That skill is locked! Gain XP in battles to level up your hero.", ephemeral=True)
            return

        if move_key == "basic":
            move_name, _, power, cost, _, _ = self.moveset["basic"]
        elif move_key == "skill":
            move_name, _, power, cost, _, _ = self.moveset["skill"]
        else:
            move_name, _, power, cost, _, _ = self.moveset["ultimate"]

        result = self.engine.execute_attack(
            self.engine.current_side, self.engine.opponent_side,
            move_name, power, resource_cost=cost
        )

        # If opponent is bot (user_id == 0), automatically execute smart bot turn ONLY IF it is the bot's turn to attack
        if not result.get("finished") and self.engine.current_side.user_id == 0:
            bot_side = self.engine.current_side
            bot_active = bot_side.active_hero
            # Ensure bot active hero is not KO'd and engine turn points to bot
            if not bot_active.is_ko:
                import random
                from utils.movesets import get_scaled_moveset

                # Smart Bot Decision 1: Low HP tactical switch if bench has full HP hero
                hp_pct = bot_active.current_hp / max(1, bot_active.max_hp)
                switched = False
                if hp_pct < 0.25 and random.random() < 0.60:
                    for idx, hero in enumerate(bot_side.team):
                        if idx != bot_side.active_index and not hero.is_ko and (hero.current_hp / hero.max_hp) > 0.5:
                            switched = self.engine.switch_active(bot_side, idx, consumes_turn=True)
                            if switched:
                                break

                # Smart Bot Decision 2: Tactical move selection
                if not switched and self.engine.current_side.user_id == 0:
                    bot_lvl = getattr(bot_active, "level", 1)
                    bot_rarity = getattr(bot_active, "rarity", "D")
                    bot_ms = get_scaled_moveset(bot_active.class_type, rarity=bot_rarity)
                    
                    basic_move = bot_ms["basic"]
                    skill_move = bot_ms["skill"]
                    ult_move = bot_ms["ultimate"]

                    # Prioritize Ultimate if unlocked and resource available
                    if bot_lvl >= 10 and bot_active.current_resource >= ult_move[3]:
                        bot_choice = ult_move
                    # Else Skill move if unlocked and resource available
                    elif bot_lvl >= 5 and bot_active.current_resource >= skill_move[3] and random.random() < 0.70:
                        bot_choice = skill_move
                    else:
                        bot_choice = basic_move

                    self.engine.execute_attack(bot_side, self.engine.opponent_side, bot_choice[0], bot_choice[2], resource_cost=bot_choice[3])






        embed = view.build_battle_embed()
        if self.engine.is_finished:
            for child in view.children:
                child.disabled = True
            view.stop()

        await interaction.response.edit_message(embed=embed, view=view)



class SwitchSelect(discord.ui.Select):
    """Select menu listing available bench heroes to switch into battle."""

    def __init__(self, engine: BattleEngine, side: BattleSide):
        options = []
        for idx, hero in enumerate(side.team):
            if idx != side.active_index and not hero.is_ko:
                options.append(discord.SelectOption(
                    label=hero.name,
                    value=str(idx),
                    description=f"Class: {hero.class_type} | HP: {hero.current_hp}/{hero.max_hp}",
                    emoji="🛡️"
                ))
        if not options:
            options.append(discord.SelectOption(label="No Bench Heroes Available", value="none", description="All bench heroes KO'd or active."))


        super().__init__(placeholder="🔄 Choose a bench hero to switch...", options=options, row=0)
        self.engine = engine
        self.side = side

    async def callback(self, interaction: discord.Interaction):
        view: BattleView = self.view
        if interaction.user.id != self.engine.current_side.user_id:
            await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
            return

        val = self.values[0]
        if val == "none":
            await interaction.response.send_message("❌ No bench heroes available!", ephemeral=True)
            return

        new_idx = int(val)
        success = self.engine.switch_active(self.side, new_idx, consumes_turn=True)
        if success:
            # If opponent is bot (user_id == 0), automatically execute smart bot turn after player switches hero
            if not self.engine.is_finished and self.engine.current_side.user_id == 0:
                bot_side = self.engine.current_side
                bot_active = bot_side.active_hero
                if not bot_active.is_ko:
                    import random
                    from utils.movesets import get_scaled_moveset

                    bot_lvl = getattr(bot_active, "level", 1)
                    bot_rarity = getattr(bot_active, "rarity", "D")
                    bot_ms = get_scaled_moveset(bot_active.class_type, rarity=bot_rarity)
                    
                    basic_move = bot_ms["basic"]
                    skill_move = bot_ms["skill"]
                    ult_move = bot_ms["ultimate"]

                    if bot_lvl >= 10 and bot_active.current_resource >= ult_move[3]:
                        bot_choice = ult_move
                    elif bot_lvl >= 5 and bot_active.current_resource >= skill_move[3] and random.random() < 0.70:
                        bot_choice = skill_move
                    else:
                        bot_choice = basic_move

                    self.engine.execute_attack(bot_side, self.engine.opponent_side, bot_choice[0], bot_choice[2], resource_cost=bot_choice[3])




            embed = view.build_battle_embed()
            if self.engine.is_finished:
                for child in view.children:
                    child.disabled = True
                view.stop()

            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("❌ Cannot switch to that hero!", ephemeral=True)


class BattleView(discord.ui.View):
    """Interactive container view for conducting 3v3 battles."""

    def __init__(self, engine: BattleEngine, cog: Any = None, timeout: float = 300.0):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.cog = cog
        self.message: Optional[discord.Message] = None

    async def on_timeout(self) -> None:
        if self.cog:
            if self.engine.side_a.user_id > 0:
                self.cog.active_battles.discard(self.engine.side_a.user_id)
            if self.engine.side_b.user_id > 0:
                self.cog.active_battles.discard(self.engine.side_b.user_id)
        return await super().on_timeout()


    def build_battle_embed(self) -> discord.Embed:
        """Construct current battle status embed with clean layout."""
        side_a = self.engine.side_a
        side_b = self.engine.side_b
        active_a = side_a.active_hero
        active_b = side_b.active_hero

        color = 0x6C5CE7 if not self.engine.is_finished else 0x00B894
        current_name = self.engine.current_side.display_name.lstrip('- ')
        
        embed = discord.Embed(
            title=f"⚔️ Battle Arena — Turn {self.engine.round_number}",
            description=f"Field: **[{self.engine.active_terrain}]** | Active Turn: **{current_name}**\n─────────────────────────────────────",
            color=color
        )

        def bench_str(side):
            heroes_status = []
            for idx, h in enumerate(side.team):
                short_name = h.name[:12] + "…" if len(h.name) > 12 else h.name
                if idx == side.active_index:
                    heroes_status.append(f"**{short_name}**")
                elif h.is_ko:
                    heroes_status.append(f"~{short_name}~")
                else:
                    heroes_status.append(short_name)
            return " • ".join(heroes_status)

        display_a = side_a.display_name.lstrip('- ')
        display_b = side_b.display_name.lstrip('- ')

        tag_a = f"🔵 **{display_a}** (Active)" if self.engine.current_side == side_a else f"🔵 **{display_a}**"
        tag_b = f"🔴 **{display_b}** (Active)" if self.engine.current_side == side_b else f"🔴 **{display_b}**"

        embed.add_field(
            name=tag_a,
            value=(
                f"**{active_a.name}** (`{active_a.class_type}`)\n"
                f"{active_a.hp_bar()}\n"
                f"{active_a.resource_bar()}\n"
                f"{bench_str(side_a)}"
            ),
            inline=True
        )

        embed.add_field(
            name=tag_b,
            value=(
                f"**{active_b.name}** (`{active_b.class_type}`)\n"
                f"{active_b.hp_bar()}\n"
                f"{active_b.resource_bar()}\n"
                f"{bench_str(side_b)}"
            ),
            inline=True
        )

        # Recent 3 log messages with clean plain text formatting inside codeblock
        import re
        clean_logs = []
        for l in self.engine.battle_logs[-3:]:
            # Strip markdown double asterisks so it doesn't print raw ** in text codeblocks
            clean_l = re.sub(r'\*\*(.*?)\*\*', r'\1', l)
            clean_logs.append(clean_l)

        logs_summary = "\n".join(clean_logs) if clean_logs else "Battle initialized."
        embed.add_field(name="📜 Combat Log", value=f"```text\n{logs_summary}\n```", inline=False)

        if self.engine.is_finished:
            embed.title = f"🏆 Victory — {self.engine.winner_side.display_name}"

            # Clear active battle status from cog tracker
            if self.cog:
                if side_a.user_id > 0:
                    self.cog.active_battles.discard(side_a.user_id)
                if side_b.user_id > 0:
                    self.cog.active_battles.discard(side_b.user_id)

            # Increment battle quest progress & rewards
            from utils.db import db
            import asyncio
            
            winner_side = self.engine.winner_side
            loser_side = self.engine.side_b if winner_side == self.engine.side_a else self.engine.side_a

            for side in (side_a, side_b):
                if side.user_id > 0:
                    asyncio.create_task(db.update_quest_progress(side.user_id, "Battles", 1))

            if winner_side.user_id > 0:
                asyncio.create_task(db.update_quest_progress(winner_side.user_id, "Victorious", 1))
                asyncio.create_task(db.update_quest_progress(winner_side.user_id, "Conquest", 1))
                # PVE / PVP Rewards
                coins_won = 250
                sigils_won = 2
                rp_won = 15
                asyncio.create_task(db.execute(
                    "UPDATE players SET coins = coins + ?, sigils = sigils + ?, pvp_rating = pvp_rating + ? WHERE user_id = ?",
                    (coins_won, sigils_won, rp_won, winner_side.user_id)
                ))
                # Update player combat stats
                asyncio.create_task(db.execute(
                    """
                    UPDATE player_stats
                    SET pvp_battles = pvp_battles + 1,
                        pvp_wins = pvp_wins + 1,
                        win_streak = win_streak + 1,
                        highest_win_streak = MAX(highest_win_streak, win_streak + 1)
                    WHERE user_id = ?
                    """,
                    (winner_side.user_id,)
                ))
                embed.add_field(
                    name="🎁 Victory Rewards",
                    value=f"🪙 **+{coins_won} Coins** | 🔮 **+{sigils_won} Sigils** | 🏆 **+{rp_won} RP**",
                    inline=False
                )

            if loser_side.user_id > 0:
                rp_loss = 8
                asyncio.create_task(db.execute(
                    "UPDATE players SET pvp_rating = MAX(0, pvp_rating - ?) WHERE user_id = ?",
                    (rp_loss, loser_side.user_id)
                ))
                # Update player combat stats for defeat
                asyncio.create_task(db.execute(
                    """
                    UPDATE player_stats
                    SET pvp_battles = pvp_battles + 1,
                        pvp_losses = pvp_losses + 1,
                        win_streak = 0
                    WHERE user_id = ?
                    """,
                    (loser_side.user_id,)
                ))

        return embed





    @discord.ui.button(label="Attack Move", style=discord.ButtonStyle.danger, emoji="⚔️", row=1)
    async def btn_attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.engine.current_side.user_id:
            await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
            return

        # Replace row 0 with AttackSelect
        self.clear_selects()
        self.add_item(AttackSelect(self.engine))
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Switch Hero", style=discord.ButtonStyle.primary, emoji="🔄", row=1)
    async def btn_switch(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.engine.current_side.user_id:
            await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
            return

        # Replace row 0 with SwitchSelect
        self.clear_selects()
        self.add_item(SwitchSelect(self.engine, self.engine.current_side))
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Battle Log", style=discord.ButtonStyle.secondary, emoji="📜", row=1)
    async def btn_log(self, interaction: discord.Interaction, button: discord.ui.Button):
        full_logs = "\n".join(self.engine.battle_logs[-10:])
        await interaction.response.send_message(f"📜 **Recent Battle Logs:**\n{full_logs}", ephemeral=True)

    @discord.ui.button(label="Surrender", style=discord.ButtonStyle.secondary, emoji="🏳️", row=1)
    async def btn_surrender(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id not in (self.engine.side_a.user_id, self.engine.side_b.user_id):
            await interaction.response.send_message("❌ You are not a combatant in this battle!", ephemeral=True)
            return

        surrendering = self.engine.side_a if user_id == self.engine.side_a.user_id else self.engine.side_b
        winner = self.engine.side_b if surrendering == self.engine.side_a else self.engine.side_a
        
        self.engine.is_finished = True
        self.engine.winner_side = winner
        self.engine.log(f"🏳️ **{surrendering.display_name}** surrendered!")

        for child in self.children:
            child.disabled = True

        embed = self.build_battle_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    def clear_selects(self) -> None:
        """Helper to remove select menus from row 0."""
        items_to_remove = [item for item in self.children if isinstance(item, discord.ui.Select)]
        for item in items_to_remove:
            self.remove_item(item)
