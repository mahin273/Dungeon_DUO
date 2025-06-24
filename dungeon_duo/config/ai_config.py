"""
ai_config.py

Configuration parameters for AI algorithms used in Dungeon Duo: Rough AI.
"""

# Example: A* pathfinding parameters
ASTAR_PARAMS = {
    "heuristic": "manhattan",
    "allow_diagonal": False,
    "weight": 1.0,
}

# Example: Naive Bayes parameters
NAIVE_BAYES_PARAMS = {
    "smoothing": 1.0,
}

# Example: Simulated Annealing parameters
SIM_ANNEALING_PARAMS = {
    "initial_temp": 100.0,
    "cooling_rate": 0.95,
}

# Example: Min-Max parameters
MIN_MAX_PARAMS = {
    "max_depth": 3,
}
