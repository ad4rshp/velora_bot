-- Velora Equipment Catalog (Class-Compatible Weapons & Gear)
-- Editable SQL file. Automatically syncs to database on bot restart.

INSERT INTO equipment_catalog (item_id, name, slot, compatible_class, base_rarity, base_hp, base_atk, base_def, base_spd, description)
VALUES 
-- Knight Weapons
('eq_knight_sword1', 'Iron Longsword', 'Weapon', 'Knight', 'D', 10, 25, 10, 5, 'A standard knightly sword forged from durable iron.'),
('eq_knight_sword2', 'Paladin Greatsword', 'Weapon', 'Knight', 'B', 25, 45, 20, 8, 'A heavy holy blade that cleaves through enemy defenses.'),
('eq_knight_sword3', 'Excalibur Holy Sword', 'Weapon', 'Knight', 'S', 60, 95, 40, 15, 'A legendary blade infused with divine radiance.'),

-- Mage Weapons
('eq_mage_wand1', 'Apprentice Wand', 'Weapon', 'Mage', 'D', 5, 30, 5, 10, 'Focuses raw Mana into elemental bolts.'),
('eq_mage_staff2', 'Starlight Crystal Staff', 'Weapon', 'Mage', 'B', 15, 55, 10, 12, 'Imbued with celestial arcane magic.'),
('eq_mage_staff3', 'Archmage Staff of Eternity', 'Weapon', 'Mage', 'S', 30, 115, 20, 25, 'Channels catastrophic elemental tempests.'),

-- Archer Weapons
('eq_archer_bow1', 'Hunting Bow', 'Weapon', 'Archer', 'D', 5, 24, 5, 15, 'A lightweight bow designed for rapid marksmanship.'),
('eq_archer_bow2', 'Windrunner Composite Bow', 'Weapon', 'Archer', 'B', 15, 48, 10, 22, 'Fires arrows with the speed of howling winds.'),
('eq_archer_bow3', 'Artemis Celestial Longbow', 'Weapon', 'Archer', 'S', 35, 105, 20, 40, 'Fires divine light arrows that never miss.'),

-- Assassin Weapons
('eq_assassin_dagger1', 'Shadow Daggers', 'Weapon', 'Assassin', 'D', 0, 32, 2, 18, 'Dual lethal daggers coated with paralyzing venom.'),
('eq_assassin_blade2', 'Nightstalker Katana', 'Weapon', 'Assassin', 'B', 10, 58, 5, 25, 'Strikes from the shadows with high critical precision.'),
('eq_assassin_blade3', 'Eclipse Death Blades', 'Weapon', 'Assassin', 'S', 20, 120, 10, 50, 'Forged from dark matter to deliver instant execution strikes.'),

-- Guardian Weapons
('eq_guardian_hammer1', 'Iron Warhammer', 'Weapon', 'Guardian', 'D', 30, 15, 25, 2, 'A bludgeoning hammer designed to disrupt enemy formations.'),
('eq_guardian_shield2', 'Bulwark Tower Shield', 'Weapon', 'Guardian', 'B', 60, 20, 50, 0, 'A massive fortress shield absorbing immense punishment.'),
('eq_guardian_shield3', 'Aegis of the Immortal', 'Weapon', 'Guardian', 'S', 140, 45, 110, 5, 'An unbreakable mythical bulwark forged by ancients.'),

-- Necromancer Weapons
('eq_necromancer_scythe1', 'Bone Reaper Scythe', 'Weapon', 'Necromancer', 'D', 15, 28, 8, 8, 'A curved scythe that harvests enemy soul essence.'),
('eq_necromancer_grimoire2', 'Grimoire of Souls', 'Weapon', 'Necromancer', 'B', 25, 52, 12, 10, 'Contains ancient dark chants of life drain.'),
('eq_necromancer_scythe3', 'Death God Reaper Scythe', 'Weapon', 'Necromancer', 'S', 50, 110, 25, 20, 'Harvests soul essence and drains life force.'),

-- Valkyrie Weapons
('eq_valkyrie_spear1', 'Radiant Spear', 'Weapon', 'Valkyrie', 'D', 15, 26, 12, 10, 'A celestial spear forged for divine combat.'),
('eq_valkyrie_spear2', 'Lance of the Valkyrie', 'Weapon', 'Valkyrie', 'B', 30, 50, 22, 14, 'A heavy holy lance piercing dark armor.'),
('eq_valkyrie_spear3', 'Gungnir Divine Spear', 'Weapon', 'Valkyrie', 'S', 65, 105, 35, 22, 'The legendary spear of celestial maidens.'),

-- Paladin Weapons
('eq_paladin_mace1', 'Blessed Warhammer', 'Weapon', 'Paladin', 'D', 25, 20, 20, 5, 'A consecrated warhammer delivering holy strikes.'),
('eq_paladin_mace2', 'Sacred Bastion Shield', 'Weapon', 'Paladin', 'B', 50, 32, 45, 8, 'A heavy blessed shield reflecting incoming attacks.'),
('eq_paladin_mace3', 'Mjolnir Holy Bulwark', 'Weapon', 'Paladin', 'S', 120, 60, 95, 12, 'A sacred bulwark forged by archangels.'),

-- Elementalist Weapons
('eq_elemental_staff1', 'Primal Elemental Staff', 'Weapon', 'Elementalist', 'D', 10, 28, 6, 12, 'Channels fire and tempest energies.'),
('eq_elemental_staff2', 'Tempest Crystal Orb', 'Weapon', 'Elementalist', 'B', 20, 56, 10, 16, 'Resonates with catastrophic elemental storms.'),
('eq_elemental_staff3', 'Aetherial Primordial Staff', 'Weapon', 'Elementalist', 'S', 40, 118, 18, 28, 'Unleashes devastation across all elemental realms.'),


-- Universal Armor & Helmets
('eq_helm_iron', 'Iron Helm', 'Helmet', 'All', 'D', 20, 0, 15, 0, 'Sturdy iron headpiece protecting against bludgeoning attacks.'),
('eq_helm_crown', 'Crown of Kings', 'Helmet', 'All', 'S', 80, 20, 50, 10, 'A royal golden crown boosting all combat attributes.'),
('eq_armor_plate', 'Steel Plate Armor', 'Armor', 'All', 'D', 40, 0, 30, -2, 'Heavy chest plate offering solid defense.'),
('eq_armor_dragon', 'Dragon Scale Mail', 'Armor', 'All', 'S', 150, 25, 90, 5, 'Forged from elder dragon scales granting elemental resistance.'),
('eq_boots_swift', 'Windrider Boots', 'Boots', 'All', 'D', 10, 0, 5, 15, 'Enchanted boots boosting movement speed.'),
('eq_boots_hermes', 'Hermes Winged Sandals', 'Boots', 'All', 'S', 45, 15, 20, 45, 'Legendary winged sandals enabling blinding combat speed.'),

-- Universal Accessories & Pets
('eq_ring_ruby', 'Ruby Ring of Power', 'Ring', 'All', 'C', 10, 18, 5, 5, 'Increases physical and magic damage.'),
('eq_ring_archmage', 'Ring of the Archmage', 'Ring', 'All', 'S', 40, 45, 20, 20, 'Increases attack power and skill effectiveness.'),
('eq_necklace_amber', 'Amber Charm', 'Necklace', 'All', 'C', 15, 10, 10, 10, 'A defensive amulet conferring stat balance.'),
('eq_necklace_phoenix', 'Phoenix Feather Amulet', 'Necklace', 'All', 'S', 70, 30, 30, 25, 'Radiates life energy.'),
('eq_artifact_relic', 'Ancient Relic', 'Artifact', 'All', 'B', 30, 25, 25, 10, 'An ancient relic radiating elemental power.'),
('eq_artifact_heart', 'Heart of the Titan', 'Artifact', 'All', 'SS', 200, 60, 60, 30, 'A mythical core pulsating with primordial power.'),
('eq_pet_wolf', 'Shadow Wolf Companion', 'Pet', 'All', 'B', 35, 20, 15, 15, 'A loyal shadow wolf hunting by your side.'),
('eq_pet_dragon', 'Celestial Baby Dragon', 'Pet', 'All', 'SS', 120, 50, 40, 35, 'A legendary dragon pet breathing starlight flames.')


ON CONFLICT(item_id) DO UPDATE SET
    name = excluded.name,
    slot = excluded.slot,
    compatible_class = excluded.compatible_class,
    base_rarity = excluded.base_rarity,
    base_hp = excluded.base_hp,
    base_atk = excluded.base_atk,
    base_def = excluded.base_def,
    base_spd = excluded.base_spd,
    description = excluded.description;
