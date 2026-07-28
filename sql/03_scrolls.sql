-- Velora Skill Scroll Catalog
-- Editable SQL file. Automatically syncs to database on bot restart.

INSERT INTO scrolls (scroll_id, name, scroll_type, power, cooldown, status_chance, required_class_tags, min_level, resource_cost, description)
VALUES 
('scroll_slash', 'Heavy Slash', 'Attack', 35, 1, 0, 'Knight,Guardian', 1, 15, 'A heavy physical strike utilizing weapon momentum.'),
('scroll_fireball', 'Fireball', 'Attack', 45, 2, 20, 'Mage,Necromancer,Elementalist', 1, 20, 'Hurls a fiery orb inflicting high damage with a chance to Burn.'),
('scroll_quickshot', 'Rapid Fire', 'Multi-hit', 20, 2, 10, 'Archer', 1, 15, 'Fires 3 rapid arrows in quick succession.'),
('scroll_shadowstrike', 'Shadow Strike', 'Priority', 40, 3, 30, 'Assassin', 1, 20, 'Strikes instantly before enemy turn with high Critical chance.'),
('scroll_ironwall', 'Iron Bastion', 'Support', 0, 3, 100, 'Knight,Guardian', 2, 25, 'Bolsters party Defense by 30% for 2 turns.'),
('scroll_lifedrain', 'Vampiric Drain', 'Status', 30, 2, 100, 'Necromancer', 2, 25, 'Deals damage and restores HP equal to 50% of damage dealt.'),

-- Healing Scrolls
('scroll_heal', 'Healing Light', 'Heal', 40, 2, 0, 'Mage,Paladin,Valkyrie,Guardian', 3, 25, 'Channels divine radiance restoring health to lowest HP ally.'),
('scroll_sanctuary', 'Divine Sanctuary', 'Heal', 75, 4, 0, 'Paladin,Valkyrie', 8, 40, 'Unleashes holy light restoring massive HP to the party.'),
('scroll_arcanerestore', 'Arcane Restoration', 'Heal', 55, 3, 0, 'Mage,Elementalist', 5, 35, 'Weaves arcane magic to regenerate health and restore power.'),
('scroll_vitalitydrain', 'Siphon Vitality', 'Heal', 50, 3, 100, 'Necromancer', 5, 30, 'Siphons target health directly to restore caster HP.'),

-- High Tier Moves
('scroll_excalibur', 'Judgement Blade', 'Attack', 65, 3, 15, 'Knight,Guardian', 5, 30, 'Unleashes holy energy slicing through armor.'),
('scroll_meteor', 'Meteor Storm', 'Attack', 70, 4, 35, 'Mage', 7, 45, 'Summons falling meteors dealing massive AoE damage.'),
('scroll_sniper', 'Sniper Volley', 'Priority', 60, 3, 25, 'Archer', 5, 30, 'A deadly precision arrow targeting vulnerable points.'),
('scroll_assassinate', 'Assassinate', 'Attack', 75, 4, 50, 'Assassin', 7, 40, 'Executes a lethal shadow strike with massive damage.'),
('scroll_fortress', 'Divine Bulwark', 'Support', 0, 4, 100, 'Guardian', 6, 35, 'Shields all allies reducing incoming damage by 50%.'),
('scroll_soulreap', 'Soul Consumption', 'Status', 55, 3, 100, 'Necromancer', 6, 35, 'Drains target life force and restores 40% of max HP.'),
('scroll_passive_thickhide', 'Thick Hide', 'Passive', 0, 0, 0, 'Knight,Guardian', 1, 0, 'Permanently increases HP by 15%.'),
('scroll_passive_focus', 'Arcane Focus', 'Passive', 0, 0, 0, 'Mage,Necromancer', 1, 0, 'Permanently increases Magic Attack by 15%.'),
('scroll_valkyrie_thrust', 'Divine Spear Thrust', 'Attack', 55, 3, 25, 'Valkyrie', 4, 25, 'Deliver a radiant spear thrust that pierces enemy defense.'),
('scroll_paladin_barrier', 'Sacred Shield Barrier', 'Support', 0, 4, 100, 'Paladin', 6, 35, 'Fortifies party with a holy light shield reducing incoming damage by 40%.'),
('scroll_elemental_firestorm', 'Cataclysmic Firestorm', 'Attack', 68, 4, 35, 'Elementalist', 7, 40, 'Unleashes an elemental tempest dealing mass damage to all enemies.')

ON CONFLICT(scroll_id) DO UPDATE SET
    name = excluded.name,
    scroll_type = excluded.scroll_type,
    power = excluded.power,
    cooldown = excluded.cooldown,
    status_chance = excluded.status_chance,
    required_class_tags = excluded.required_class_tags,
    min_level = excluded.min_level,
    resource_cost = excluded.resource_cost,
    description = excluded.description;

