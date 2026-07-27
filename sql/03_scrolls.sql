-- Velora Skill Scroll Catalog
-- Editable SQL file. Automatically syncs to database on bot restart.

INSERT INTO scrolls (scroll_id, name, scroll_type, power, cooldown, status_chance, required_class_tags, description)
VALUES 
('scroll_slash', 'Heavy Slash', 'Attack', 35, 1, 0, 'Knight,Guardian', 'A heavy physical strike utilizing weapon momentum.'),
('scroll_fireball', 'Fireball', 'Attack', 45, 2, 20, 'Mage,Necromancer', 'Hurls a fiery orb inflicting high damage with a chance to Burn.'),
('scroll_quickshot', 'Rapid Fire', 'Multi-hit', 20, 2, 10, 'Archer', 'Fires 3 rapid arrows in quick succession.'),
('scroll_shadowstrike', 'Shadow Strike', 'Priority', 40, 3, 30, 'Assassin', 'Strikes instantly before enemy turn with high Critical chance.'),
('scroll_ironwall', 'Iron Bastion', 'Support', 0, 3, 100, 'Knight,Guardian', 'Bolsters party Defense by 30% for 2 turns.'),
('scroll_lifedrain', 'Vampiric Drain', 'Status', 30, 2, 100, 'Necromancer', 'Deals damage and restores HP equal to 50% of damage dealt.'),
('scroll_excalibur', 'Judgement Blade', 'Attack', 65, 3, 15, 'Knight,Guardian', 'Unleashes holy energy slicing through armor.'),
('scroll_meteor', 'Meteor Storm', 'Attack', 70, 4, 35, 'Mage', 'Summons falling meteors dealing massive AoE damage.'),
('scroll_sniper', 'Sniper Volley', 'Priority', 60, 3, 25, 'Archer', 'A deadly precision arrow targeting vulnerable points.'),
('scroll_assassinate', 'Assassinate', 'Attack', 75, 4, 50, 'Assassin', 'Executes a lethal shadow strike with massive damage.'),
('scroll_fortress', 'Divine Bulwark', 'Support', 0, 4, 100, 'Guardian', 'Shields all allies reducing incoming damage by 50%.'),
('scroll_soulreap', 'Soul Consumption', 'Status', 55, 3, 100, 'Necromancer', 'Drains target life force and restores 40% of max HP.'),
('scroll_passive_thickhide', 'Thick Hide', 'Passive', 0, 0, 0, 'Knight,Guardian', 'Permanently increases HP by 15%.'),
('scroll_passive_focus', 'Arcane Focus', 'Passive', 0, 0, 0, 'Mage,Necromancer', 'Permanently increases Magic Attack by 15%.'),

('scroll_valkyrie_thrust', 'Divine Spear Thrust', 'Attack', 55, 3, 25, 'Valkyrie', 'Deliver a radiant spear thrust that pierces enemy defense.'),
('scroll_paladin_barrier', 'Sacred Shield Barrier', 'Support', 0, 4, 100, 'Paladin', 'Fortifies party with a holy light shield reducing incoming damage by 40%.'),
('scroll_elemental_firestorm', 'Cataclysmic Firestorm', 'Attack', 68, 4, 35, 'Elementalist', 'Unleashes an elemental tempest dealing mass damage to all enemies.')


ON CONFLICT(scroll_id) DO UPDATE SET
    name = excluded.name,
    scroll_type = excluded.scroll_type,
    power = excluded.power,
    cooldown = excluded.cooldown,
    status_chance = excluded.status_chance,
    required_class_tags = excluded.required_class_tags,
    description = excluded.description;
