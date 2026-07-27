"""
Interactive Battle Guide View for Velora RPG.
Provides clean category dropdown navigation for combat tactics, roles, scrolls, and loadouts.
"""

import discord
from views.base_view import VeloraView

GUIDE_PAGES = {
    "basics": {
        "title": "⚔️ TACTICAL BATTLE BASICS",
        "color": 0x6C5CE7,
        "fields": [
            ("⚡ Speed Priority", "Highest Speed hero acts first in turn order each round.", False),
            ("🔋 Resource Management", "Manage Stamina, Mana, Energy, Focus, Divine Energy & Faith. Avoid exhaustion!", False),
            ("🔄 Mid-Battle Tag Switching", "Use interactive switch buttons to rotate wounded heroes out and counter enemy types.", False)
        ]
    },
    "roles": {
        "title": "🛡️ CLASS ROLES & SYNERGIES",
        "color": 0x0984E3,
        "fields": [
            ("🛡️ Tanks (Guardian, Paladin)", "Highest DEF & HP. Anchor your frontline to absorb heavy punishment.", True),
            ("⚔️ Frontline (Knight, Valkyrie)", "Balanced HP & ATK. Excellent for breaking frontline armor.", True),
            ("🏹 Speed DPS (Archer, Assassin)", "High Speed & priority turns. Eliminate enemy sorcerers before they cast.", True),
            ("🔮 Sorcerers (Mage, Elementalist, Necromancer)", "Massive elemental spell output & life-drain siphons.", True)
        ]
    },
    "scrolls": {
        "title": "📜 SKILL SCROLL TACTICS",
        "color": 0x00B894,
        "fields": [
            ("⚡ Priority Strikes", "Shadow Strike & Sniper Volley bypass turn order to execute low-HP targets.", False),
            ("🛡️ Shield Barriers", "Sacred Shield & Divine Bulwark reduce incoming damage for the entire party.", False),
            ("🩸 Life-Siphon Spells", "Vampiric Drain & Soul Consumption restore HP while inflicting heavy spell damage.", False)
        ]
    },
    "loadout": {
        "title": "🛠️ GEAR LOADOUT STRATEGY",
        "color": 0xFDCB6E,
        "fields": [
            ("🗡️ Class Weapons", "Equip class-compatible weapons for maximum primary stat gains.", False),
            ("🛡️ Tank Defense", "Stack Heavy Armor & Helmets on Guardians/Paladins for maximum mitigation.", False),
            ("⚡ Speed Boots & Accessories", "Equip Windrider Boots on Assassins/Mages to win turn priority.", False)
        ]
    }
}

class GuideCategorySelect(discord.ui.Select):
    """Dropdown menu for selecting battle guide category."""

    def __init__(self):
        options = [
            discord.SelectOption(label="Combat Basics", value="basics", description="Speed order, resources & switching rules", emoji="⚔️"),
            discord.SelectOption(label="Hero Roles", value="roles", description="Tanks, Frontline, Speed DPS & Sorcerers", emoji="🛡️"),
            discord.SelectOption(label="Skill Scrolls", value="scrolls", description="Priority, barriers & life-siphon tactics", emoji="📜"),
            discord.SelectOption(label="Gear Loadout", value="loadout", description="Weapons, armor & speed accessories", emoji="🛠️")
        ]
        super().__init__(placeholder="📖 Select a category to inspect tactics...", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: BattleGuideView = self.view
        category_key = self.values[0]
        embed = view.build_embed(category_key)
        await interaction.response.edit_message(embed=embed, view=view)


class BattleGuideView(VeloraView):
    """Interactive category-based Battle Guide View."""

    def __init__(self, author_id: int):
        super().__init__(author_id=author_id, timeout=120.0)
        self.add_item(GuideCategorySelect())

    def build_embed(self, category_key: str = "basics") -> discord.Embed:
        cat = GUIDE_PAGES.get(category_key, GUIDE_PAGES["basics"])
        embed = discord.Embed(
            title=cat["title"],
            description="───────────",
            color=cat["color"]
        )

        for name, value, inline in cat["fields"]:
            embed.add_field(name=name, value=value, inline=inline)

        embed.set_footer(text="Use dropdown menu below to switch categories")
        return embed
