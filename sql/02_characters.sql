-- Velora Starter Character Catalog
-- Editable SQL file. Automatically syncs to database on bot restart.

INSERT INTO characters (character_id, name, class_type, resource_type, resource_max, base_rarity, base_hp, base_atk, base_def, base_spd, description)
VALUES 
('knight_01', 'Arthur', 'Knight', 'Stamina', 100, 'D', 120, 18, 15, 10, 'A frontline warrior who relies on Stamina to unleash powerful Weapon Arts and shield allies.'),
('mage_01', 'Merlin', 'Mage', 'Mana', 120, 'D', 85, 25, 8, 12, 'A master of arcane elementals who channels Mana to cast high-damage Spells from afar.'),
('archer_01', 'Artemis', 'Archer', 'Focus', 100, 'D', 95, 22, 10, 16, 'An agile marksman who channels Focus to deliver precision ranged volleys.'),

('assassin_01', 'Kage', 'Assassin', 'Energy', 100, 'D', 80, 26, 7, 20, 'A lethal shadow striker utilizing rapidly regenerating Energy to land devastating critical blows.'),
('guardian_01', 'Aegis', 'Guardian', 'Stamina', 120, 'D', 150, 14, 24, 8, 'An impenetrable wall absorbing massive damage and protecting the party with high HP and Defense.'),
('necromancer_01', 'Malakor', 'Necromancer', 'Mana', 100, 'D', 90, 21, 11, 11, 'A dark warlock wielding Mana to drain opponent vitality and siphon life back to themselves.'),

('valkyrie_01', 'Freya', 'Valkyrie', 'Divine Energy', 100, 'C', 115, 22, 18, 12, 'A holy spearmaiden from the celestial realm who channels divine light into devastating piercing strikes.'),
('paladin_01', 'Galahad', 'Paladin', 'Faith', 100, 'C', 130, 18, 22, 9, 'An unyielding fortress clad in blessed plate armor, wielding sacred shields to protect allies.'),
('elementalist_01', 'Pyra', 'Elementalist', 'Mana', 120, 'C', 90, 28, 11, 14, 'A master of primal magic capable of unleashing catastrophic flame and tempest storms upon enemies.')



ON CONFLICT(character_id) DO UPDATE SET
    name = excluded.name,
    class_type = excluded.class_type,
    resource_type = excluded.resource_type,
    resource_max = excluded.resource_max,
    base_rarity = excluded.base_rarity,
    base_hp = excluded.base_hp,
    base_atk = excluded.base_atk,
    base_def = excluded.base_def,
    base_spd = excluded.base_spd,
    description = excluded.description;
