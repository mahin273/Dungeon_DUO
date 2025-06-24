"""
hud.py

Heads-Up Display (HUD) logic for Dungeon Duo: Rough AI.
Displays player stats, AI feedback, and combat information.
"""

import pygame
import pygame_gui
import math
from typing import Dict, Any, Optional, List
from ..game.player import Player
from ..game.monster import Monster
from ..game.quests import QuestManager
from ..game.achievements import AchievementManager, Achievement, AchievementStatus

class ModernSkillTreePanel:
    """Modern skill tree UI panel with enhanced visuals."""

    def __init__(self, manager: pygame_gui.UIManager, player: Player):
        self.manager = manager
        self.player = player
        self.visible = False
        self.panel = None
        self.skill_labels = []
        self.unlock_buttons = []
        self.skill_point_label = None
        self.description_label = None
        self.skill_id_to_skill = {}
        self.skill_icons = []
        self.animation_time = 0
        self.hovered_skill = None

    def show(self):
        """Show the skill tree panel with modern design."""
        if not self.visible:
            # Create a larger, more modern panel
            self.panel = pygame_gui.elements.UIPanel(
                relative_rect=pygame.Rect((50, 50), (600, 500)),
                starting_height=1,
                manager=self.manager
            )
            self._populate()
            self.visible = True

    def hide(self):
        """Hide the skill tree panel."""
        if self.visible and self.panel:
            for label in self.skill_labels:
                label.kill()
            for btn in self.unlock_buttons:
                btn.kill()
            for icon in self.skill_icons:
                icon.kill()
            if self.skill_point_label:
                self.skill_point_label.kill()
            if self.description_label:
                self.description_label.kill()
            self.panel.kill()
            self.panel = None
            self.visible = False
            self.skill_labels = []
            self.unlock_buttons = []
            self.skill_point_label = None
            self.description_label = None
            self.skill_id_to_skill = {}
            self.skill_icons = []

    def toggle(self):
        """Toggle the skill tree panel visibility."""
        if self.visible:
            self.hide()
        else:
            self.show()

    def update(self, delta_time: float):
        """Update animations."""
        self.animation_time += delta_time

    def _populate(self):
        """Populate the skill tree panel with modern design."""
        # Modern title with gradient effect
        title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 10), (580, 40)),
            text="⚔️ SKILL TREE ⚔️",
            manager=self.manager,
            container=self.panel
        )

        # Enhanced skill points display
        skill_points = self.player.skill_tree.skill_points
        self.skill_point_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 60), (280, 30)),
            text=f"🎯 Skill Points: {skill_points}",
            manager=self.manager,
            container=self.panel
        )

        # List all skills with modern layout
        skills = list(self.player.skill_tree.skills.values())
        y = 100
        for skill in skills:
            status = "Unlocked" if skill.unlocked else ("Unlockable" if self.player.skill_tree.can_unlock(skill.id) else "Locked")

            # Modern color coding
            if status == "Unlocked":
                color = '#4CAF50'  # Modern green
                icon_text = "✅"
            elif status == "Unlockable":
                color = '#FF9800'  # Modern orange
                icon_text = "🔓"
            else:
                color = '#9E9E9E'  # Modern gray
                icon_text = "🔒"

            # Skill icon with emoji
            icon = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect((10, y+5), (30, 30)),
                text=icon_text,
                manager=self.manager,
                container=self.panel
            )
            self.skill_icons.append(icon)

            # Enhanced skill label with status
            status_emoji = "✅" if status == "Unlocked" else "🔓" if status == "Unlockable" else "🔒"
            label = pygame_gui.elements.UITextBox(
                html_text=f'<font color="{color}"><b>{skill.name}</b> {status_emoji}</font>',
                relative_rect=pygame.Rect((50, y), (400, 40)),
                manager=self.manager,
                container=self.panel,
                object_id=pygame_gui.core.ObjectID(class_id='@skill_label', object_id=skill.id)
            )
            self.skill_labels.append(label)
            self.skill_id_to_skill[skill.id] = skill

            # Modern unlock button if unlockable
            if status == "Unlockable":
                btn = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect((460, y+5), (120, 30)),
                    text="🔓 Unlock",
                    manager=self.manager,
                    container=self.panel,
                    object_id=pygame_gui.core.ObjectID(class_id='@skill_unlock', object_id=skill.id)
                )
                self.unlock_buttons.append(btn)
            y += 50

        # Enhanced description area
        self.description_label = pygame_gui.elements.UITextBox(
            html_text="<b>📖 Skill Description:</b> Hover over a skill to see details.",
            relative_rect=pygame.Rect((10, 420), (570, 70)),
            manager=self.manager,
            container=self.panel
        )

    def process_event(self, event):
        """Process UI events for the skill tree panel."""
        if event.type == pygame_gui.UI_BUTTON_PRESSED and self.visible:
            for btn in self.unlock_buttons:
                if event.ui_element == btn:
                    skill_id = btn.object_id.object_id
                    if self.player.unlock_skill(skill_id):
                        self.hide()
                        self.show()
                    break

        # Enhanced hover effects
        if event.type == pygame_gui.UI_BUTTON_ON_HOVERED:
            if hasattr(event.ui_element, 'object_id') and event.ui_element.object_id is not None:
                skill_id = event.ui_element.object_id.object_id
                skill = self.skill_id_to_skill.get(skill_id)
                if skill and self.description_label:
                    prereq = f"<br><i>🔗 Requires: {', '.join(skill.prerequisites) if skill.prerequisites else 'None'}</i>"
                    self.description_label.set_text(f"<b>⚔️ {skill.name}</b><br>💡 {skill.description}{prereq}")

        # Reset description on mouse leave
        if event.type == pygame_gui.UI_BUTTON_ON_UNHOVERED:
            if self.description_label:
                self.description_label.set_text("<b>📖 Skill Description:</b> Hover over a skill to see details.")

class ModernQuestPanel:
    """Modern quest display panel with enhanced visuals."""

    def __init__(self, manager: pygame_gui.UIManager, quest_manager: QuestManager):
        self.manager = manager
        self.quest_manager = quest_manager
        self.visible = False
        self.panel = None
        self.quest_labels = []
        self.animation_time = 0

    def show(self):
        """Show the quest panel with modern design."""
        if not self.visible:
            self.panel = pygame_gui.elements.UIPanel(
                relative_rect=pygame.Rect((700, 50), (400, 400)),
                starting_height=1,
                manager=self.manager
            )
            self._populate()
            self.visible = True

    def hide(self):
        """Hide the quest panel."""
        if self.visible and self.panel:
            for label in self.quest_labels:
                label.kill()
            self.panel.kill()
            self.panel = None
            self.visible = False
            self.quest_labels = []

    def toggle(self):
        """Toggle the quest panel visibility."""
        if self.visible:
            self.hide()
        else:
            self.show()

    def update(self, delta_time: float):
        """Update animations."""
        self.animation_time += delta_time

    def _populate(self):
        """Populate the quest panel with modern design."""
        # Modern title
        title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 10), (380, 40)),
            text="📜 ACTIVE QUESTS 📜",
            manager=self.manager,
            container=self.panel
        )

        # List active quests
        active_quests = self.quest_manager.get_active_quests()
        y = 60

        if not active_quests:
            no_quests_label = pygame_gui.elements.UITextBox(
                html_text="<i>🎯 No active quests. Explore the dungeon to find new challenges!</i>",
                relative_rect=pygame.Rect((10, y), (370, 60)),
                manager=self.manager,
                container=self.panel
            )
            self.quest_labels.append(no_quests_label)
        else:
            for quest in active_quests:
                # Quest status
                progress = quest.get_progress_text()
                # completion = quest.get_completion_percentage()  # This method doesn't exist

                if progress == "Completed":
                    status_emoji = "✅"
                    status_color = "#4CAF50"
                elif progress == "In Progress":
                    status_emoji = "🔄"
                    status_color = "#FF9800"
                else:
                    status_emoji = "⏳"
                    status_color = "#9E9E9E"

                # Quest title and progress
                quest_text = f"<b>{status_emoji} {quest.name}</b><br>"
                quest_text += f"📊 Progress: {progress}<br>"
                quest_text += f"🎯 {quest.description}<br>"
                quest_text += f"<font color='{status_color}'>{progress}</font>"

                quest_label = pygame_gui.elements.UITextBox(
                    html_text=quest_text,
                    relative_rect=pygame.Rect((10, y), (370, 80)),
                    manager=self.manager,
                    container=self.panel
                )
                self.quest_labels.append(quest_label)
                y += 90

class ModernAchievementPanel:
    """Modern achievement display panel with enhanced visuals."""

    def __init__(self, manager: pygame_gui.UIManager, achievement_manager: AchievementManager):
        self.manager = manager
        self.achievement_manager = achievement_manager
        self.visible = False
        self.panel = None
        self.achievement_labels = []
        self.animation_time = 0

    def show(self):
        """Show the achievement panel with modern design."""
        if not self.visible:
            self.panel = pygame_gui.elements.UIPanel(
                relative_rect=pygame.Rect((200, 100), (500, 400)),
                starting_height=1,
                manager=self.manager
            )
            self._populate()
            self.visible = True

    def hide(self):
        """Hide the achievement panel."""
        if self.visible and self.panel:
            for label in self.achievement_labels:
                label.kill()
            self.panel.kill()
            self.panel = None
            self.visible = False
            self.achievement_labels = []

    def toggle(self):
        """Toggle the achievement panel visibility."""
        if self.visible:
            self.hide()
        else:
            self.show()

    def update(self, delta_time: float):
        """Update animations."""
        self.animation_time += delta_time

    def _populate(self):
        """Populate the achievement panel with modern design."""
        # Modern title
        title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 10), (480, 40)),
            text="🏆 ACHIEVEMENTS 🏆",
            manager=self.manager,
            container=self.panel
        )

        # List achievements
        achievements = self.achievement_manager.get_all_achievements()
        y = 60

        if not achievements:
            no_achievements_label = pygame_gui.elements.UITextBox(
                html_text="<i>🎯 No achievements unlocked yet. Keep playing to earn rewards!</i>",
                relative_rect=pygame.Rect((10, y), (470, 60)),
                manager=self.manager,
                container=self.panel
            )
            self.achievement_labels.append(no_achievements_label)
        else:
            for achievement in achievements:
                # Achievement status
                if achievement.status == AchievementStatus.UNLOCKED:
                    status_emoji = "🏆"
                    status_color = "#FFD700"
                    unlock_date = f"<br><font color='#4CAF50'>✅ Unlocked: {achievement.unlocked_time}</font>"
                else:
                    status_emoji = "🔒"
                    status_color = "#9E9E9E"
                    unlock_date = ""

                # Achievement display
                achievement_text = f"<b>{status_emoji} {achievement.name}</b><br>"
                achievement_text += f"💡 {achievement.description}<br>"
                # The points system can be re-added later if needed
                # achievement_text += f"<font color='{status_color}'>{achievement.points} points</font>{unlock_date}"
                achievement_text += unlock_date

                achievement_label = pygame_gui.elements.UITextBox(
                    html_text=achievement_text,
                    relative_rect=pygame.Rect((10, y), (470, 70)),
                    manager=self.manager,
                    container=self.panel
                )
                self.achievement_labels.append(achievement_label)
                y += 80

class ModernHUDManager:
    """Modern HUD manager with enhanced UI components."""

    def __init__(self, manager: pygame_gui.UIManager, player: Player, quest_manager: QuestManager):
        self.manager = manager
        self.player = player
        self.quest_manager = quest_manager

        # Only keep quest panel
        self.quest_panel = ModernQuestPanel(manager, quest_manager)

        # Notification system
        self.notifications = []
        self.notification_duration = 3.0  # seconds

        # Animation time
        self.animation_time = 0

    def process_event(self, event):
        """Process UI events for all HUD components."""
        # Only process quest panel events
        pass

    def update(self, delta_time: float):
        """Update HUD animations and notifications."""
        self.animation_time += delta_time
        self.quest_panel.update(delta_time)
        self.update_notifications(delta_time)

    def toggle_quest_panel(self):
        """Toggle the quest panel visibility."""
        self.quest_panel.toggle()

    def add_notification(self, message: str, notification_type: str = "info"):
        """Add a modern notification."""
        notification = {
            'message': message,
            'type': notification_type,
            'time': 0.0,
            'duration': self.notification_duration
        }
        self.notifications.append(notification)

    def update_notifications(self, delta_time: float):
        """Update notification timers."""
        for notification in self.notifications:
            notification['time'] += delta_time
        self.notifications = [n for n in self.notifications if n['time'] < n['duration']]

    def render_notifications(self, screen: pygame.Surface):
        """Render modern notifications."""
        notification_y = 50
        for notification in self.notifications:
            time_ratio = notification['time'] / notification['duration']
            if time_ratio > 0.8:
                alpha = int(255 * (1.0 - (time_ratio - 0.8) / 0.2))
            else:
                alpha = 255
            if notification['type'] == "success":
                color = (76, 175, 80)
                icon = "✅"
            elif notification['type'] == "warning":
                color = (255, 152, 0)
                icon = "⚠️"
            elif notification['type'] == "error":
                color = (244, 67, 54)
                icon = "❌"
            else:
                color = (33, 150, 243)
                icon = "ℹ️"
            font = pygame.font.Font(None, 20)
            text = f"{icon} {notification['message']}"
            text_surface = font.render(text, True, color)
            bg_surface = pygame.Surface((text_surface.get_width() + 20, text_surface.get_height() + 10))
            bg_surface.set_alpha(alpha)
            bg_surface.fill((40, 40, 60))
            screen.blit(bg_surface, (10, notification_y))
            screen.blit(text_surface, (20, notification_y + 5))
            notification_y += 40
