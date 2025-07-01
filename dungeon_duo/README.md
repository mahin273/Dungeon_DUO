# Dungeon Duo: Rough AI 🎮

A Python-based roguelike game featuring advanced AI systems including A\* pathfinding, Simulated Annealing optimization, and Naive Bayes behavior prediction. The game pits a player against an intelligent monster that learns and adapts to the player's strategies.

![Game Screenshot](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)
![AI](https://img.shields.io/badge/AI-Advanced-orange.svg)

## 🎯 Features

### Core Gameplay

- **Procedural Dungeon Generation**: Unique dungeons with walls, floors, traps, and treasure chests
- **Real-time Combat System**: Dynamic combat with weapons, armor, and special abilities
- **Environmental Hazards**: Traps and obstacles that affect gameplay
- **Treasure Collection**: Find and collect items throughout the dungeon

### Advanced AI Systems

- **A\* Pathfinding**: Intelligent monster movement through complex dungeon layouts
- **Simulated Annealing Optimization**: Monster adapts its stats based on player behavior
- **Naive Bayes Behavior Prediction**: AI learns and predicts player actions
- **Adaptive Difficulty**: Monster becomes smarter and more challenging over time
- **Tactical Decision Making**: AI makes strategic choices in combat and movement

### Technical Features

- **Smooth 60 FPS Gameplay**: Optimized rendering and game loop
- **Modern UI**: Clean interface with health bars, minimap, and status indicators
- **Debug Information**: Real-time AI metrics and performance monitoring
- **Modular Architecture**: Well-organized codebase for easy extension

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/dungeon-duo-rough-ai.git
   cd dungeon-duo-rough-ai
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the game**
   ```bash
   python main.py
   ```

## 🎮 How to Play

### Controls

- **WASD** or **Arrow Keys**: Move player
- **SPACE**: Attack monster
- **ESC**: Exit game
- **R**: Regenerate dungeon (new layout and monster)

### Objective

- Navigate through the procedurally generated dungeon
- Collect treasure chests while avoiding traps
- Defeat the AI monster before it defeats you
- The monster learns from your actions and becomes more challenging!

### Game Mechanics

- **Health System**: Both player and monster have health that decreases when taking damage
- **Combat**: Engage in real-time combat with the monster
- **Adaptation**: The monster's AI improves based on your playstyle
- **Victory Conditions**: Win by defeating the monster or collecting all treasures

## 🤖 AI Systems Explained

### A\* Pathfinding

The monster uses A\* algorithm to find optimal paths through the dungeon:

- Calculates shortest route to the player
- Avoids walls and obstacles
- Updates path dynamically as the player moves
- Falls back to direct movement if pathfinding fails

### Simulated Annealing Optimization

The monster optimizes its combat stats using simulated annealing:

- **Attack Power**: Adapts based on player's defensive strategies
- **Speed**: Adjusts movement speed based on player's mobility
- **Defense**: Optimizes armor and evasion based on player's attack patterns
- **Health**: Balances survivability with other stats

### Naive Bayes Behavior Prediction

The AI predicts player actions using machine learning:

- **Movement Patterns**: Learns preferred movement directions
- **Combat Style**: Predicts aggressive vs defensive playstyles
- **Item Usage**: Anticipates when player will use items
- **Tactical Decisions**: Adapts strategy based on predicted player actions

### Adaptation System

- **Learning Rate**: Monster improves its AI over time
- **Memory**: Remembers successful strategies against the player
- **Counter-Strategies**: Develops responses to player tactics
- **Difficulty Scaling**: Becomes more challenging as it learns

## 📁 Project Structure

```
dungeon_duo/
├── main.py                 # Main game entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── assets/                # Game assets
│   ├── data/             # Game data files
│   ├── sounds/           # Audio files
│   └── sprites/          # Image assets
├── config/               # Configuration files
│   ├── __init__.py
│   └── ai_config.py      # AI system settings
├── src/                  # Source code
│   ├── ai/              # AI systems
│   │   ├── behavior_prediction.py    # Naive Bayes predictor
│   │   ├── optimization.py          # Simulated Annealing
│   │   ├── pathfinding.py           # A* algorithm
│   │   └── tactical_ai.py           # Strategic decision making
│   ├── game/            # Core game logic
│   │   ├── combat/      # Combat system
│   │   ├── items/       # Item system
│   │   ├── player.py    # Player class
│   │   ├── monster.py   # Monster AI class
│   │   └── game_engine.py # Main game loop
│   ├── ui/              # User interface
│   │   ├── hud.py       # Heads-up display
│   │   └── renderer.py  # Graphics rendering
│   └── world/           # World generation
│       ├── dungeon_generator.py # Procedural generation
│       ├── environment.py       # Environmental effects
│       └── tile.py             # Tile system
└── monster_learning.json # AI learning data persistence
```

## 🔧 Configuration

### AI Settings

Edit `config/ai_config.py` to adjust AI behavior:

- **Learning Rate**: How quickly the monster adapts
- **Pathfinding Aggressiveness**: Monster's pursuit behavior
- **Adaptation Threshold**: When the monster should change strategies
- **Memory Size**: How much past data the AI remembers

### Game Settings

Modify game parameters in the main files:

- **Dungeon Size**: Change the size of generated dungeons
- **Monster Speed**: Adjust AI movement speed
- **Combat Balance**: Tune damage and health values
- **Visual Settings**: Modify rendering options

## 🧪 Development

### Adding New Features

1. **New AI Behaviors**: Extend the AI classes in `src/ai/`
2. **Game Mechanics**: Add new features in `src/game/`
3. **UI Elements**: Modify the renderer in `src/ui/`
4. **World Generation**: Enhance the dungeon generator in `src/world/`

### Testing AI Systems

- Monitor AI performance metrics in the console
- Use debug keys to test specific AI features
- Analyze the `monster_learning.json` file for AI learning data

## 📊 Performance

The game is optimized for smooth 60 FPS gameplay:

- **Efficient Pathfinding**: A\* algorithm with caching
- **Smart Rendering**: Only renders visible areas
- **Memory Management**: Proper cleanup of game objects
- **AI Optimization**: Balanced computation vs responsiveness

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Areas for Improvement

- **New AI Algorithms**: Implement different machine learning approaches
- **Enhanced Graphics**: Add more visual effects and animations
- **Sound System**: Implement audio feedback and music
- **Multiplayer**: Add cooperative or competitive multiplayer modes
- **More Content**: Additional items, abilities, and dungeon types

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Pygame Community**: For the excellent game development framework
- **AI Research**: Inspired by various machine learning and pathfinding algorithms
- **Roguelike Community**: For design inspiration and best practices


---

**Enjoy playing Dungeon Duo: Rough AI!** 🎮✨

_Challenge the AI, adapt your strategies, and see if you can outsmart the learning monster!_
