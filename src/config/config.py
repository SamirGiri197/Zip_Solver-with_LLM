# =============================
# config.py (updated)
# =============================


# --- Display / layout ---
CELL_SIZE = 80
GRID_MARGIN = 24
FPS = 60
FONT_NAME = "arial"


# --- Adjacency ---
# Default: 4-way (up, down, left, right). Toggle in-game with 'D'.
ADJACENCY_8_WAY = False


# --- Colors (also used by GUI) ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (46, 173, 88)
RED = (220, 60, 60)
PURPLE = (153, 102, 255)
GOLD = (212, 175, 55)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)


# --- Board Sizes ---
BOARD_SIZES = [3, 4, 5, 6, 7, 8, 9, 10, 12, 15] # Available board sizes (n x n)
DEFAULT_BOARD_SIZE = 5


# --- Generator / Solver ---
MAX_GEN_ATTEMPTS = 40 # new random path attempts
SOLVER_TIME_LIMIT = 8.0 # seconds per solve attempt (player solver & uniqueness check)
def get_clue_bounds(n: int):
    """Return (CLUE_START, CLUE_MAX) dynamically based on board size n."""
    # Start with n clues and allow up to n*n clues maximum.
    start = max(4, n) # ensures small boards still have at least 4 clues
    max_clues = min(n * n, n + 8) # cap to avoid trivially filled puzzles
    return start, max_clues

# --- Performance tweaks ---
# When FAST_MODE is True we skip the expensive uniqueness check for large boards.
# This makes 10x10+ puzzles generate almost instantly at the cost of allowing
# multiple valid solutions on those sizes.
FAST_MODE = True
FAST_MODE_THRESHOLD = 10 # apply fast generation for n >= this


# --- Timer ---
TIMER_ENABLED = True
TIMER_WARNING_SECONDS = 60 # Show warning at this many seconds remaining


# --- Leaderboard ---
LEADERBOARD_FILE = "leaderboard.json"
LEADERBOARD_MAX_ENTRIES = 10
DIFFICULTY_MULTIPLIER = {
3: 0.5, # 3x3 = easiest
4: 0.8, # 4x4
5: 1.0, # 5x5 = easy
6: 1.5, # 6x6
7: 2.0, # 7x7 = normal
8: 2.5, # 8x8
9: 3.0, # 9x9 = hard
10: 4.0, # 10x10
12: 5.5, # 12x12 = very hard
15: 8.0, # 15x15 = extreme
}


# --- LLM (optional) ---
# Set to True and configure API key to enable LLMSolver heuristic suggestions
ENABLE_LLM = False