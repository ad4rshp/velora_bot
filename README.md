# Velora RPG — Discord Bot

Velora is a Discord RPG bot featuring 9 character classes, 3v3 team battles, gear crafting, rarity rerolls, and player economy.

---

## 🚀 Features

- **9 Character Classes**: Knight, Mage, Archer, Assassin, Guardian, Necromancer, Valkyrie, Paladin, Elementalist.
- **3v3 Battle Roster**: Strategic turn-based combat with active status conditions (Burn, Poison, Stun, Shield).
- **Rarity Rerolls**: Reroll hero and equipment rarity with failure risk mechanics.
- **Crafting & Equipment**: Forge gear with quality multipliers and repair durability.
- **Player Economy**: General Store, Marketplace, direct trading, and daily quests.

---

## 🛠️ Setup & Installation

### 1. Requirements
- Python 3.10+
- Discord Bot Token

### 2. Installation

```bash
# Clone Repository
git clone https://github.com/ad4rshp/velora_bot.git
cd velora_bot

# Install Dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:

```env
DISCORD_TOKEN=your_bot_token_here
COMMAND_PREFIX=v
```

### 4. Run the Bot

```bash
python bot.py
```

---

## 📜 Core Commands

| Command | Description |
| :--- | :--- |
| `vstart` | Begin adventure and claim starter hero team |
| `vprofile` | View wallet balance, rank tier, and active hero |
| `vinfo [hero]` | Inspect hero attributes, passives, and moveset |
| `vteam` | Configure your 3v3 active battle roster |
| `vbattle [@user]` | Initiate turn-based battle |
| `vshop` | Browse General Store for packs and supplies |
| `vquests` | View daily & weekly quest progress |
| `vhelp` | Open full command directory |
