import pygame
import sys
from config.config import *
from core.generator import generate_unique_puzzle
from core.board import Board
from UI.GUI import Game
from leaderboard.leaderboard import Leaderboard

def show_menu():
    """Display menu to select board size or view leaderboard."""
    pygame.init()
    screen = pygame.display.set_mode((700, 700))
    pygame.display.set_caption("ZIP Puzzle - Main Menu")
    font_title = pygame.font.SysFont(FONT_NAME, 48, bold=True)
    font_button = pygame.font.SysFont(FONT_NAME, 28, bold=True)
    font_small = pygame.font.SysFont(FONT_NAME, 18)
    
    clock = pygame.time.Clock()
    scroll_offset = 0
    button_height = 55
    spacing = 8
    y_start = 140
    
    def get_buttons():
        """Generate button positions based on scroll offset."""
        buttons = {}
        for i, size in enumerate(BOARD_SIZES):
            y_pos = y_start + i * (button_height + spacing) - scroll_offset
            if -button_height < y_pos < 650:  # Only create if visible
                rect = pygame.Rect(100, y_pos, 500, button_height)
                buttons[f"size_{size}"] = (rect, size)
        return buttons
    
    leaderboard_y_offset = len(BOARD_SIZES) * (button_height + spacing) + 20
    exit_y_offset = leaderboard_y_offset + button_height + spacing
    
    max_scroll = max(0, len(BOARD_SIZES) * (button_height + spacing) + 100)
    
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)
            elif e.type == pygame.MOUSEWHEEL:
                scroll_offset = max(0, min(max_scroll, scroll_offset - e.y * 30))
            elif e.type == pygame.MOUSEBUTTONDOWN:
                buttons = get_buttons()
                for key, (rect, size) in buttons.items():
                    if rect.collidepoint(e.pos):
                        pygame.quit()
                        return size
                
                leaderboard_y_display = y_start + leaderboard_y_offset - scroll_offset
                leaderboard_btn_adj = pygame.Rect(100, leaderboard_y_display, 500, button_height)
                if leaderboard_btn_adj.collidepoint(e.pos):
                    show_leaderboard(screen)
                
                exit_y_display = y_start + exit_y_offset - scroll_offset
                exit_btn_adj = pygame.Rect(100, exit_y_display, 500, button_height)
                if exit_btn_adj.collidepoint(e.pos):
                    pygame.quit()
                    sys.exit(0)
        
        screen.fill(WHITE)
        
        # Title
        title = font_title.render("ZIP Puzzle", True, GOLD)
        screen.blit(title, (200, 30))
        
        subtitle = font_small.render("Select Difficulty - Scroll to see more", True, (150, 150, 150))
        screen.blit(subtitle, (150, 100))
        
        # Draw board size buttons
        buttons = get_buttons()
        for key, (rect, size) in buttons.items():
            pygame.draw.rect(screen, (235, 205, 120), rect, border_radius=8)
            pygame.draw.rect(screen, (120, 90, 10), rect, 2, border_radius=8)
            
            difficulty = ["Trivial", "Easy", "Normal", "Hard", "Very Hard", "Extreme"]
            diff_idx = min(len(difficulty) - 1, BOARD_SIZES.index(size) // 2)
            label = font_button.render(f"{size}x{size}  -  {difficulty[diff_idx]}", True, BLACK)
            screen.blit(label, label.get_rect(center=rect.center))
        
        # Leaderboard button
        leaderboard_y_display = y_start + leaderboard_y_offset - scroll_offset
        leaderboard_btn_adj = pygame.Rect(100, leaderboard_y_display, 500, button_height)
        if -button_height < leaderboard_y_display < 650:
            pygame.draw.rect(screen, (100, 150, 200), leaderboard_btn_adj, border_radius=8)
            pygame.draw.rect(screen, (50, 100, 150), leaderboard_btn_adj, 2, border_radius=8)
            label = font_button.render("🏆 Leaderboard", True, WHITE)
            screen.blit(label, label.get_rect(center=leaderboard_btn_adj.center))
        
        # Exit button
        exit_y_display = y_start + exit_y_offset - scroll_offset
        exit_btn_adj = pygame.Rect(100, exit_y_display, 500, button_height)
        if -button_height < exit_y_display < 650:
            pygame.draw.rect(screen, (200, 100, 100), exit_btn_adj, border_radius=8)
            pygame.draw.rect(screen, (150, 50, 50), exit_btn_adj, 2, border_radius=8)
            label = font_button.render("Exit", True, WHITE)
            screen.blit(label, label.get_rect(center=exit_btn_adj.center))
        
        pygame.display.flip()

def show_leaderboard(screen):
    """Display leaderboard."""
    lb = Leaderboard()
    font_title = pygame.font.SysFont(FONT_NAME, 36, bold=True)
    font_entry = pygame.font.SysFont(FONT_NAME, 18)
    
    clock = pygame.time.Clock()
    
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                return
        
        screen.fill(WHITE)
        title = font_title.render("Leaderboard", True, GOLD)
        screen.blit(title, (200, 20))
        
        scores = lb.get_leaderboard()
        if not scores:
            no_scores = font_entry.render("No scores yet!", True, BLACK)
            screen.blit(no_scores, (200, 100))
        else:
            y = 80
            for i, score in enumerate(scores[:10]):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                text = f"{medal} {score.player_name:12} | {score.board_size}x{score.board_size} | {score.time_seconds}s | {score.score():.0f}"
                label = font_entry.render(text, True, BLACK)
                screen.blit(label, (30, y))
                y += 35
        
        hint = font_entry.render("Press ESC to go back", True, (150, 150, 150))
        screen.blit(hint, (150, 450))
        
        pygame.display.flip()

def main():
    # Show menu to select board size
    n = show_menu()
    k = n * n
    
    # Adjust cell size based on board size
    import config.config as config
    config.CELL_SIZE = max(30, min(80, 600 // n))
    
    # Adjust clue density for larger boards
    config.CLUE_START = max(6, n // 2)
    config.CLUE_MAX = min(20, n * 2)

    print(f"[Game] Starting ZIP puzzle with board size {n}x{n}...")
    print(f"[Game] Cell size: {config.CELL_SIZE}px, Clues: ~{config.CLUE_START} to {config.CLUE_MAX}")
    print("[Generator] Creating deterministic ZIP puzzle…")
    
    grid, solution, mapping = generate_unique_puzzle(n=n, diag=ADJACENCY_8_WAY)
    print(f"[Generator] Done. n={n}, k={k}, unique solution ensured.")

    inverse_mapping = {v: k for k, v in mapping.items()}

    board = Board(
        grid=grid,
        k=k,
        diag=ADJACENCY_8_WAY,
        display_to_step=mapping,
        step_to_display=inverse_mapping
    )
    
    game = Game(board, solution=solution, board_size=n)
    game.run()

if __name__ == "__main__":
    main()