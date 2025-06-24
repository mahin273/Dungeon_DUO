from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import time

class AchievementType(Enum):
    COMBAT = "combat"
    SKILL = "skill"
    QUEST = "quest"
    EXPLORATION = "exploration"
    COLLECTION = "collection"

class AchievementStatus(Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    HIDDEN = "hidden"

@dataclass
class Achievement:
    """Represents an achievement with conditions and rewards."""
    id: str
    name: str
    description: str
    achievement_type: AchievementType
    condition: Callable[[Dict[str, Any]], bool]
    progress_tracker: Callable[[Dict[str, Any]], int]
    target_value: int
    rewards: Dict[str, Any] = field(default_factory=dict)
    status: AchievementStatus = AchievementStatus.LOCKED
    unlocked_time: Optional[float] = None
    icon: str = "🏆"  # Default trophy emoji

    def check_condition(self, game_state: Dict[str, Any]) -> bool:
        """Check if the achievement condition is met."""
        return self.condition(game_state)

    def get_progress(self, game_state: Dict[str, Any]) -> int:
        """Get current progress towards the achievement."""
        return min(self.progress_tracker(game_state), self.target_value)

    def unlock(self):
        """Mark the achievement as unlocked."""
        if self.status == AchievementStatus.LOCKED:
            self.status = AchievementStatus.UNLOCKED
            self.unlocked_time = time.time()
            return True
        return False

    def get_progress_text(self, game_state: Dict[str, Any] = None) -> str:
        """Get formatted progress text."""
        if game_state is None:
            game_state = {}
        return f"{self.get_progress(game_state)}/{self.target_value}"

class AchievementManager:
    """Manages all achievements in the game."""

    def __init__(self):
        self.achievements: Dict[str, Achievement] = {}
        self.game_state: Dict[str, Any] = {
            'monsters_killed': 0,
            'total_damage_dealt': 0,
            'skills_unlocked': 0,
            'skill_points_spent': 0,
            'quests_completed': 0,
            'dungeon_levels_cleared': 0,
            'items_collected': 0,
            'gold_earned': 0,
            'player_level': 1
        }

    def add_achievement(self, achievement: Achievement):
        """Add an achievement to the manager."""
        self.achievements[achievement.id] = achievement

    def update_game_state(self, key: str, value: Any):
        """Update the game state and check for achievements."""
        self.game_state[key] = value
        self.check_achievements()

    def increment_game_state(self, key: str, amount: int = 1):
        """Increment a game state value and check for achievements."""
        if key in self.game_state:
            self.game_state[key] += amount
        else:
            self.game_state[key] = amount
        self.check_achievements()

    def check_achievements(self):
        """Check all locked achievements for completion."""
        for achievement in self.achievements.values():
            if achievement.status == AchievementStatus.LOCKED:
                if achievement.check_condition(self.game_state):
                    if achievement.unlock():
                        self._award_achievement(achievement)

    def _award_achievement(self, achievement: Achievement):
        """Handle achievement unlocking."""
        print(f"🏆 Achievement Unlocked: {achievement.name}!")
        print(f"   {achievement.description}")
        if achievement.rewards:
            print(f"   Rewards: {achievement.rewards}")

    def get_unlocked_achievements(self) -> List[Achievement]:
        """Get all unlocked achievements."""
        return [a for a in self.achievements.values() if a.status == AchievementStatus.UNLOCKED]

    def get_locked_achievements(self) -> List[Achievement]:
        """Get all locked achievements."""
        return [a for a in self.achievements.values() if a.status == AchievementStatus.LOCKED]

    def get_achievement_status(self) -> Dict[str, Any]:
        """Get a summary of achievement status."""
        unlocked = self.get_unlocked_achievements()
        locked = self.get_locked_achievements()

        return {
            "total_achievements": len(self.achievements),
            "unlocked_count": len(unlocked),
            "locked_count": len(locked),
            "unlocked_achievements": [{"name": a.name, "description": a.description, "unlocked_time": a.unlocked_time}
                                    for a in unlocked],
            "locked_achievements": [{"name": a.name, "description": a.description, "progress": a.get_progress_text(self.game_state)}
                                  for a in locked]
        }

    def get_all_achievements(self) -> List['Achievement']:
        """Get all achievements (locked and unlocked)."""
        return list(self.achievements.values())

def create_sample_achievements() -> List[Achievement]:
    """Create sample achievements for testing."""
    achievements = []

    # Combat achievements
    first_kill = Achievement(
        id="first_kill",
        name="First Blood",
        description="Defeat your first monster",
        achievement_type=AchievementType.COMBAT,
        condition=lambda state: state.get('monsters_killed', 0) >= 1,
        progress_tracker=lambda state: state.get('monsters_killed', 0),
        target_value=1,
        rewards={"experience": 50, "gold": 25},
        icon="⚔️"
    )
    achievements.append(first_kill)

    monster_slayer = Achievement(
        id="monster_slayer",
        name="Monster Slayer",
        description="Defeat 10 monsters",
        achievement_type=AchievementType.COMBAT,
        condition=lambda state: state.get('monsters_killed', 0) >= 10,
        progress_tracker=lambda state: state.get('monsters_killed', 0),
        target_value=10,
        rewards={"experience": 200, "gold": 100},
        icon="🗡️"
    )
    achievements.append(monster_slayer)

    # Skill achievements
    skill_learner = Achievement(
        id="skill_learner",
        name="Skill Learner",
        description="Unlock your first skill",
        achievement_type=AchievementType.SKILL,
        condition=lambda state: state.get('skills_unlocked', 0) >= 1,
        progress_tracker=lambda state: state.get('skills_unlocked', 0),
        target_value=1,
        rewards={"skill_points": 2},
        icon="📚"
    )
    achievements.append(skill_learner)

    skill_master = Achievement(
        id="skill_master",
        name="Skill Master",
        description="Unlock 5 skills",
        achievement_type=AchievementType.SKILL,
        condition=lambda state: state.get('skills_unlocked', 0) >= 5,
        progress_tracker=lambda state: state.get('skills_unlocked', 0),
        target_value=5,
        rewards={"skill_points": 5, "experience": 300},
        icon="🎓"
    )
    achievements.append(skill_master)

    # Quest achievements
    quest_starter = Achievement(
        id="quest_starter",
        name="Quest Starter",
        description="Complete your first quest",
        achievement_type=AchievementType.QUEST,
        condition=lambda state: state.get('quests_completed', 0) >= 1,
        progress_tracker=lambda state: state.get('quests_completed', 0),
        target_value=1,
        rewards={"experience": 100, "gold": 50},
        icon="📜"
    )
    achievements.append(quest_starter)

    # Exploration achievements
    dungeon_explorer = Achievement(
        id="dungeon_explorer",
        name="Dungeon Explorer",
        description="Clear 5 dungeon levels",
        achievement_type=AchievementType.EXPLORATION,
        condition=lambda state: state.get('dungeon_levels_cleared', 0) >= 5,
        progress_tracker=lambda state: state.get('dungeon_levels_cleared', 0),
        target_value=5,
        rewards={"experience": 500, "gold": 250},
        icon="🏰"
    )
    achievements.append(dungeon_explorer)

    # Collection achievements
    collector = Achievement(
        id="collector",
        name="Collector",
        description="Collect 10 items",
        achievement_type=AchievementType.COLLECTION,
        condition=lambda state: state.get('items_collected', 0) >= 10,
        progress_tracker=lambda state: state.get('items_collected', 0),
        target_value=10,
        rewards={"experience": 150, "gold": 75},
        icon="📦"
    )
    achievements.append(collector)

    return achievements
