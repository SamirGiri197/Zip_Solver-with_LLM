import pygame
import sys
import os
from config.config import *
from core.generator import generate_unique_puzzle
from core.board import Board
from UI.GUI import Game

# Try to import the improved menu system
try:
    from UI.menu import show_modern_menu
    USE_MODERN_MENU = True
except ImportError:
    USE_MODERN_MENU = False
    print("Modern menu not available, using fallback")

def start_game_with_settings(board_size, mode_or_provider):
    """Start game with specific settings"""
    n = board_size
    k = n * n
    
    if mode_or_provider == "human":
        game_mode = "human"
        llm_provider = None
    else:
        game_mode = "llm"
        llm_provider = mode_or_provider
    
    # Dynamic cell sizing logic from config
    import config.config as config
    if n <= 4:
        config.CELL_SIZE = 80
    else:
        config.CELL_SIZE = max(40, min(100, 800 // n))
    
    if hasattr(config, 'get_clue_bounds'):
        config.CLUE_START, config.CLUE_MAX = config.get_clue_bounds(n)

    print(f"[Game] Starting {n}x{n} {game_mode} game...")
    
    # Generate puzzle
    grid, solution, mapping = generate_unique_puzzle(n=n, diag=ADJACENCY_8_WAY)
    inverse_mapping = {v: k for k, v in mapping.items()}

    board = Board(
        grid=grid, k=k, diag=ADJACENCY_8_WAY,
        display_to_step=mapping, step_to_display=inverse_mapping
    )
    
    game = Game(board, solution=solution, board_size=n, game_mode=game_mode, llm_provider=llm_provider)
    
    if llm_provider:
        import threading
        threading.Timer(1.0, lambda: game.solve_with_llm(llm_provider)).start()
    
    game.run()

def main():
    # Check if this is a subprocess call for board selection (from GUI victory "Select Board Size" button)
   # Check if this is a subprocess call for board selection (from GUI victory)  
    if os.environ.get('ZIP_SHOW_BOARD_SELECTION'):
    # DON'T delete the environment variable here - let menu.py handle it
    # Just continue to the normal menu system below
        pass

    # Normal startup OR "Select Board Size" button clicked - show existing menu
    if USE_MODERN_MENU:
        result = show_modern_menu()
        if result and len(result) == 2:
            n, mode = result
            if n and mode:
                start_game_with_settings(n, mode)

if __name__ == "__main__":
    main()