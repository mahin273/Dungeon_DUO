"""
skills.py

Skill tree system for Dungeon Duo: Rough AI.
Supports player and monster skill trees, unlockable abilities, and branching choices.
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

@dataclass
class Skill:
    """Represents a skill in the skill tree."""
    id: str
    name: str
    description: str
    tier: int = 1
    max_level: int = 1
    current_level: int = 0
    requirements: List[str] = field(default_factory=list)  # Skill IDs required
    effect: Optional[Callable] = None  # Function to apply skill effect
    unlocked: bool = False

    def can_unlock(self, unlocked_skills: List[str]) -> bool:
        return all(req in unlocked_skills for req in self.requirements)

    def unlock(self):
        if self.current_level < self.max_level:
            self.current_level += 1
            self.unlocked = True
            return True
        return False

@dataclass
class SkillTree:
    """Represents a skill tree for a character."""
    skills: Dict[str, Skill] = field(default_factory=dict)
    skill_points: int = 0
    unlocked_skills: List[str] = field(default_factory=list)

    def add_skill(self, skill: Skill):
        self.skills[skill.id] = skill

    def can_unlock(self, skill_id: str) -> bool:
        skill = self.skills.get(skill_id)
        if not skill or skill.unlocked:
            return False
        return skill.can_unlock(self.unlocked_skills)

    def unlock_skill(self, skill_id: str) -> bool:
        skill = self.skills.get(skill_id)
        if not skill or skill.unlocked or self.skill_points <= 0:
            return False
        if not skill.can_unlock(self.unlocked_skills):
            return False
        if skill.unlock():
            self.skill_points -= 1
            self.unlocked_skills.append(skill_id)
            if skill.effect:
                skill.effect()
            return True
        return False

    def get_unlockable_skills(self) -> List[Skill]:
        return [s for s in self.skills.values() if not s.unlocked and s.can_unlock(self.unlocked_skills)]

    def get_unlocked_skills(self) -> List[Skill]:
        return [s for s in self.skills.values() if s.unlocked]

# Example skill definitions for player

def get_default_player_skills():
    return [
        Skill(
            id="power_strike",
            name="Power Strike",
            description="Increase attack power by 5.",
            tier=1,
            max_level=1,
            requirements=[],
        ),
        Skill(
            id="tough_skin",
            name="Tough Skin",
            description="Increase defense by 3.",
            tier=1,
            max_level=1,
            requirements=[],
        ),
        Skill(
            id="quick_learner",
            name="Quick Learner",
            description="Gain 10% more experience.",
            tier=2,
            max_level=1,
            requirements=["power_strike"],
        ),
        Skill(
            id="adrenaline_rush",
            name="Adrenaline Rush",
            description="Temporarily boost speed after taking damage.",
            tier=2,
            max_level=1,
            requirements=["tough_skin"],
        ),
        Skill(
            id="berserker",
            name="Berserker",
            description="Greatly increase attack when health is low.",
            tier=3,
            max_level=1,
            requirements=["power_strike", "adrenaline_rush"],
        ),
        Skill(
            id="iron_wall",
            name="Iron Wall",
            description="Greatly increase defense when health is low.",
            tier=3,
            max_level=1,
            requirements=["tough_skin", "quick_learner"],
        ),
    ]

# Example skill definitions for monster

def get_default_monster_skills():
    return [
        Skill(
            id="feral_swipe",
            name="Feral Swipe",
            description="Increase attack power by 4.",
            tier=1,
            max_level=1,
            requirements=[],
        ),
        Skill(
            id="thick_hide",
            name="Thick Hide",
            description="Increase defense by 2.",
            tier=1,
            max_level=1,
            requirements=[],
        ),
        Skill(
            id="predator_instinct",
            name="Predator Instinct",
            description="Increase critical hit chance.",
            tier=2,
            max_level=1,
            requirements=["feral_swipe"],
        ),
        Skill(
            id="regeneration",
            name="Regeneration",
            description="Regenerate health over time.",
            tier=2,
            max_level=1,
            requirements=["thick_hide"],
        ),
        Skill(
            id="alpha_predator",
            name="Alpha Predator",
            description="Greatly increase attack and speed when alone.",
            tier=3,
            max_level=1,
            requirements=["feral_swipe", "regeneration"],
        ),
        Skill(
            id="unyielding",
            name="Unyielding",
            description="Greatly increase defense when below 30% health.",
            tier=3,
            max_level=1,
            requirements=["thick_hide", "predator_instinct"],
        ),
    ]
