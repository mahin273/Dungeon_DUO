from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class QuestType(Enum):
    KILL = "kill"
    COLLECTION = "collection"
    LEVEL = "level"
    EXPLORATION = "exploration"

class QuestStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class QuestObjective:
    """Represents a single objective within a quest."""
    description: str
    target: int
    current: int = 0
    completed: bool = False

    def update_progress(self, amount: int = 1) -> bool:
        """Update progress and return True if completed."""
        self.current = min(self.current + amount, self.target)
        if self.current >= self.target and not self.completed:
            self.completed = True
            return True
        return False

@dataclass
class Quest:
    """Represents a quest with objectives and rewards."""
    id: str
    name: str
    description: str
    quest_type: QuestType
    objectives: List[QuestObjective]
    rewards: Dict[str, Any] = field(default_factory=dict)
    status: QuestStatus = QuestStatus.ACTIVE
    level_requirement: int = 1

    def is_completed(self) -> bool:
        """Check if all objectives are completed."""
        return all(obj.completed for obj in self.objectives)

    def update_objective(self, objective_index: int, amount: int = 1) -> bool:
        """Update a specific objective and return True if quest is completed."""
        if 0 <= objective_index < len(self.objectives):
            self.objectives[objective_index].update_progress(amount)
            if self.is_completed():
                self.status = QuestStatus.COMPLETED
                return True
        return False

    def get_progress_text(self) -> str:
        """Get a formatted progress text for the quest."""
        progress_parts = []
        for obj in self.objectives:
            progress_parts.append(f"{obj.description}: {obj.current}/{obj.target}")
        return " | ".join(progress_parts)

class QuestManager:
    """Manages all quests in the game."""

    def __init__(self):
        self.active_quests: Dict[str, Quest] = {}
        self.completed_quests: Dict[str, Quest] = {}
        self.failed_quests: Dict[str, Quest] = {}

    def add_quest(self, quest: Quest):
        """Add a new quest to the active quests."""
        self.active_quests[quest.id] = quest

    def remove_quest(self, quest_id: str):
        """Remove a quest from active quests."""
        if quest_id in self.active_quests:
            del self.active_quests[quest_id]

    def update_kill_quest(self, monster_type: str = None, amount: int = 1):
        """Update kill quests when a monster is defeated."""
        for quest in self.active_quests.values():
            if quest.quest_type == QuestType.KILL:
                for i, objective in enumerate(quest.objectives):
                    if monster_type is None or monster_type.lower() in objective.description.lower():
                        if quest.update_objective(i, amount):
                            self._complete_quest(quest)

    def update_collection_quest(self, item_type: str, amount: int = 1):
        """Update collection quests when items are collected."""
        for quest in self.active_quests.values():
            if quest.quest_type == QuestType.COLLECTION:
                for i, objective in enumerate(quest.objectives):
                    if item_type.lower() in objective.description.lower():
                        if quest.update_objective(i, amount):
                            self._complete_quest(quest)

    def update_level_quest(self, player_level: int):
        """Update level quests when player levels up."""
        for quest in self.active_quests.values():
            if quest.quest_type == QuestType.LEVEL:
                for i, objective in enumerate(quest.objectives):
                    if quest.update_objective(i, player_level):
                        self._complete_quest(quest)

    def _complete_quest(self, quest: Quest):
        """Handle quest completion."""
        quest.status = QuestStatus.COMPLETED
        self.completed_quests[quest.id] = quest
        self.remove_quest(quest.id)
        print(f"Quest completed: {quest.name}!")
        if quest.rewards:
            print(f"Rewards: {quest.rewards}")

    def get_active_quests(self) -> List[Quest]:
        """Get all active quests."""
        return list(self.active_quests.values())

    def get_completed_quests(self) -> List[Quest]:
        """Get all completed quests."""
        return list(self.completed_quests.values())

    def get_quest_status(self) -> Dict[str, Any]:
        """Get a summary of quest status."""
        return {
            "active_count": len(self.active_quests),
            "completed_count": len(self.completed_quests),
            "active_quests": [{"name": q.name, "progress": q.get_progress_text()}
                             for q in self.active_quests.values()]
        }

def create_sample_quests() -> List[Quest]:
    """Create some sample quests for testing."""
    quests = []

    # Kill quest
    kill_quest = Quest(
        id="kill_monsters_1",
        name="Monster Hunter",
        description="Defeat monsters to prove your worth",
        quest_type=QuestType.KILL,
        objectives=[QuestObjective("Defeat monsters", 5)],
        rewards={"experience": 100, "gold": 50}
    )
    quests.append(kill_quest)

    # Collection quest
    collection_quest = Quest(
        id="collect_items_1",
        name="Item Collector",
        description="Gather items from defeated monsters",
        quest_type=QuestType.COLLECTION,
        objectives=[QuestObjective("Collect health potions", 3)],
        rewards={"experience": 75, "gold": 25}
    )
    quests.append(collection_quest)

    # Level quest
    level_quest = Quest(
        id="reach_level_1",
        name="Rising Star",
        description="Reach a higher level",
        quest_type=QuestType.LEVEL,
        objectives=[QuestObjective("Reach level", 3)],
        rewards={"experience": 200, "gold": 100}
    )
    quests.append(level_quest)

    return quests
