import sys
import os  # Added import os
import pygame
import random
import math
from typing import List, Optional, Tuple

from core.board import Board, Coord, validate_path
from core.solver import solve_backtracking
from UI.animation import Animator
from UI.style import draw_cell_circle, draw_gradient_polyline, random_gradient_colors
from config.config import *

ARROW_COLOR = (255, 215, 0)
TOP_BAR = 48  

class Particle:
    """Particle for fireworks and ribbon animations"""
    def __init__(self, x, y, vx, vy, color, particle_type="firework", gravity=0.2):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.type = particle_type
        self.gravity = gravity
        self.life = 120  # Increased life for slower animation
        self.max_life = 120
        self.size = random.randint(2, 4)
        self.trail = []  # For ribbon trail effect
    
    def update(self):
        self.x += self.vx * 0.7  # Slower movement
        self.y += self.vy * 0.7  # Slower movement
        
        if self.type == "firework":
            self.vy += self.gravity * 0.6  # Slower gravity effect
            self.vx *= 0.995  # Slower air resistance
            self.life -= 0.8  # Slower decay
        elif self.type == "ribbon":
            self.vx *= 0.99  # Slower decay for ribbons
            self.vy += self.gravity * 0.3  # Much slower gravity for ribbons
            self.trail.append((self.x, self.y))
            if len(self.trail) > 15:  # Longer trail
                self.trail.pop(0)
            self.life -= 0.4  # Much longer life for ribbons
    
    def draw(self, screen):
        if self.life <= 0:
            return
        
        alpha = int(255 * (self.life / self.max_life))
        if alpha <= 0:
            return
        
        if self.type == "ribbon":
            # Draw ribbon trail
            for i, (tx, ty) in enumerate(self.trail):
                trail_alpha = int(alpha * (i / len(self.trail)))
                if trail_alpha > 0:
                    trail_color = (*self.color, trail_alpha)
                    trail_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(trail_surface, trail_color, (self.size, self.size), self.size)
                    screen.blit(trail_surface, (int(tx - self.size), int(ty - self.size)))
        
        # Draw main particle
        particle_color = (*self.color, alpha)
        particle_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, particle_color, (self.size, self.size), self.size)
        screen.blit(particle_surface, (int(self.x - self.size), int(self.y - self.size)))
    
    def is_alive(self):
        return self.life > 0

class VictoryAnimation:
    """Manages the victory celebration animation"""
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particles = []
        self.animation_time = 0
        self.firework_timer = 0
        self.ribbon_timer = 0
        
        # Victory colors
        self.celebration_colors = [
            (255, 215, 0),    # Gold
            (255, 105, 180),  # Hot Pink
            (0, 255, 255),    # Cyan
            (255, 165, 0),    # Orange
            (50, 205, 50),    # Lime Green
            (138, 43, 226),   # Blue Violet
            (255, 20, 147),   # Deep Pink
            (0, 191, 255),    # Deep Sky Blue
        ]
    
    def create_firework(self, x, y):
        """Create a firework explosion at position (x, y)"""
        color = random.choice(self.celebration_colors)
        num_particles = random.randint(15, 25)  # Fewer particles for slower effect
        
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)  # Slower speed
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            particle = Particle(x, y, vx, vy, color, "firework")
            self.particles.append(particle)
    
    def create_ribbon_burst(self, x, y):
        """Create a ribbon burst effect"""
        colors = random.sample(self.celebration_colors, 2)  # Fewer colors
        
        for color in colors:
            for _ in range(6):  # Fewer ribbons
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1.5, 3.5)  # Slower speed
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed - 1.5  # Slight upward bias
                
                particle = Particle(x, y, vx, vy, color, "ribbon", gravity=0.05)
                self.particles.append(particle)
    
    def update(self):
        """Update animation state"""
        self.animation_time += 1
        
        # Create fireworks less frequently (slower)
        self.firework_timer += 1
        if self.firework_timer > 60:  # Every 60 frames (1 second at 60fps)
            self.firework_timer = 0
            # Random position for firework
            x = random.randint(100, self.screen_width - 100)
            y = random.randint(80, self.screen_height // 3)
            self.create_firework(x, y)
        
        # Create ribbon bursts much less frequently
        self.ribbon_timer += 1
        if self.ribbon_timer > 90:  # Every 90 frames (1.5 seconds)
            self.ribbon_timer = 0
            x = random.randint(150, self.screen_width - 150)
            y = random.randint(60, self.screen_height // 4)
            self.create_ribbon_burst(x, y)
        
        # Update all particles
        for particle in self.particles[:]:
            particle.update()
            if not particle.is_alive():
                self.particles.remove(particle)
    
    def draw(self, screen):
        """Draw all particles"""
        for particle in self.particles:
            particle.draw(screen)

class Game:
    def __init__(self, board: Board, solution: Optional[List[Coord]] = None, board_size: int = 5, game_mode: str = "human", llm_provider: str = None):
        pygame.init()
        self.board = board
        self.diag = board.diag
        self.board_size = board_size
        self.game_mode = game_mode  # "human" or "llm"
        self.llm_provider = llm_provider  # Store LLM provider for play again

        # Gradient palette
        self.line_color_start, self.line_color_end = random_gradient_colors()

        # Layout - calculate responsive sizes with minimum window size
        self.cell = CELL_SIZE
        self.margin = GRID_MARGIN
        
        # Grid dimensions
        grid_width = self.cell * board.n + 2 * self.margin
        grid_height = self.cell * board.n + 2 * self.margin
        
        # Button area dimensions (responsive to board size)
        self.button_height = max(45, int(self.cell * 0.9))
        self.button_area_height = self.button_height + 40  # Extra space for modern buttons
        
        # Ensure minimum window size for UI elements AND victory screen
        min_window_width = 600  # Minimum width for buttons to fit
        min_window_height = 700  # Increased minimum height for victory screen buttons (added button)
        
        # For small board sizes, ensure the window is tall enough for victory screen
        victory_buttons_height = 5 * 55 + 4 * 15 + 200  # 5 buttons + spacing + text area
        required_height = max(min_window_height, victory_buttons_height)
        
        # Total window size with minimums
        w = max(min_window_width, grid_width)
        h = max(required_height, TOP_BAR + grid_height + self.button_area_height)
        
        self.screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption(f"ZIP Puzzle - {board_size}x{board_size}")
        
        # Victory celebration and transition
        self.victory_animation = VictoryAnimation(w, h)
        self.showing_victory = False
        self.victory_start_time = 0
        self.victory_transition_alpha = 0  # For smooth transition
        self.victory_transition_speed = 3  # How fast the transition happens
        self.in_victory_transition = False
        
        # Timer
        self.start_time = pygame.time.get_ticks()
        self.elapsed_seconds = 0
        self.final_time = 0

        # Fonts - scale based on cell size
        font_size = max(16, int(self.cell * 0.42))
        button_font_size = max(12, int(self.cell * 0.35))
        self.bigfont = pygame.font.SysFont(FONT_NAME, font_size, bold=True)
        self.infofont = pygame.font.SysFont(FONT_NAME, button_font_size)
        self.timer_font = pygame.font.SysFont(FONT_NAME, max(14, int(self.cell * 0.3)))
        
        # Victory screen fonts
        self.victory_title_font = pygame.font.SysFont('Segoe UI', 42, bold=True)  # Slightly smaller for small windows
        self.victory_time_font = pygame.font.SysFont('Segoe UI', 22, bold=True)
        self.victory_button_font = pygame.font.SysFont('Segoe UI', 16, bold=True)  # Smaller button font

        # State
        self.path: List[Coord] = []
        g = board.givens()
        if 1 in g:
            self.path = [g[1]]
        self.dragging = False
        self.status_msg = ""
        self.solution: Optional[List[Coord]] = solution
        self.animator: Optional[Animator] = None
        self.hover_cell: Optional[Coord] = None
        self.is_won = False

        # Modern buttons setup - mode specific
        self._setup_modern_buttons()
        
        self.hint_segment: Optional[Tuple[Tuple[int,int], Tuple[int,int]]] = None
        self.hint_expire_at = 0

        self.clock = pygame.time.Clock()

        # ---- LLM batch / automation controls ----
        # These let an external script (like zip_llm_tests) run multiple GUI games in sequence.
        # Defaults keep normal interactive behavior unchanged.
        self.llm_auto_quit: bool = False       # if True and game_mode == "llm", run() returns when LLM finishes
        self.llm_finished: bool = False        # set True at end of solve_with_llm
        self.llm_max_moves: int = self.board.k * 2  # safety cap for LLM iterations (can be overridden externally)

    def _setup_modern_buttons(self):
        """Setup modern button positions - different buttons based on game mode."""
        # Different buttons for different modes
        if self.game_mode == "human":
            button_names = ["Back", "Reset", "Hint"]
        else:  # LLM mode
            button_names = ["Back", "Reset", "Hint", "LLM"]
        
        # Modern button styling
        button_width = max(80, int(self.cell * 1.1))  # Responsive width
        button_height = max(45, int(self.cell * 0.9))  # Responsive height
        button_spacing = 15
        
        # Calculate total width needed for all buttons
        total_buttons_width = len(button_names) * button_width + (len(button_names) - 1) * button_spacing
        
        # Ensure buttons fit in window
        available_width = self.screen.get_width() - 40  # 20px margin on each side
        if total_buttons_width > available_width:
            # Reduce button width to fit
            button_width = (available_width - (len(button_names) - 1) * button_spacing) // len(button_names)
            total_buttons_width = len(button_names) * button_width + (len(button_names) - 1) * button_spacing
        
        # Center buttons horizontally
        start_x = (self.screen.get_width() - total_buttons_width) // 2
        
        # Position buttons at bottom with proper spacing
        button_y = self.screen.get_height() - button_height - 20  # 20px from bottom
        
        # Modern button colors
        button_colors = {
            "Back": ((107, 114, 128), (75, 85, 99)),         # Gray
            "Reset": ((245, 158, 11), (217, 119, 6)),        # Orange
            "Hint": ((59, 130, 246), (37, 99, 235)),         # Blue
            "LLM": ((168, 85, 247), (124, 58, 237))          # Purple
        }
        
        self.buttons = {}
        for i, name in enumerate(button_names):
            x = start_x + i * (button_width + button_spacing)
            self.buttons[name] = {
                'rect': pygame.Rect(x, button_y, button_width, button_height),
                'colors': button_colors.get(name, ((107, 114, 128), (75, 85, 99))),
                'hovered': False
            }

    def _setup_victory_buttons(self):
        """Setup victory screen buttons - vertical layout with proper spacing for small windows"""
        # Leaderboard button
        button_names = ["Play Again", "Select Board Size", "Leaderboard", "Main Menu", "Exit"]
        button_width = min(220, self.screen.get_width() - 80)  # Responsive width
        button_height = 50
        button_spacing = 12  # Reduced spacing
        
        # Center buttons horizontally
        start_x = (self.screen.get_width() - button_width) // 2
        
        # Calculate available space and position buttons accordingly
        available_height = self.screen.get_height() - 240  # Reserve space for title and timer
        total_buttons_height = len(button_names) * button_height + (len(button_names) - 1) * button_spacing
        
        # Start position - centered in available space
        start_y = 240 + (available_height - total_buttons_height) // 2
        
        # Ensure buttons don't go too low
        max_start_y = self.screen.get_height() - total_buttons_height - 20
        start_y = min(start_y, max_start_y)
        
        # Victory button colors
        victory_button_colors = {
            "Play Again": ((34, 197, 94), (22, 163, 74)),        # Green
            "Select Board Size": ((168, 85, 247), (124, 58, 237)),  # Purple
            "Leaderboard": ((245, 158, 11), (217, 119, 6)),      # Orange
            "Main Menu": ((59, 130, 246), (37, 99, 235)),        # Blue
            "Exit": ((239, 68, 68), (220, 38, 38))               # Red
        }
        
        self.victory_buttons = {}
        for i, name in enumerate(button_names):
            y = start_y + i * (button_height + button_spacing)
            self.victory_buttons[name] = {
                'rect': pygame.Rect(start_x, y, button_width, button_height),
                'colors': victory_button_colors.get(name, ((107, 114, 128), (75, 85, 99))),
                'hovered': False
            }

    # ---------- helpers ----------
    def to_screen(self, r: int, c: int) -> Tuple[int,int,int,int]:
        # Calculate grid position (centered if window is larger than grid)
        grid_width = self.board.n * self.cell + 2 * self.margin
        grid_start_x = max(self.margin, (self.screen.get_width() - grid_width) // 2)
        
        x = grid_start_x + c * self.cell
        y = TOP_BAR + self.margin + r * self.cell
        return x, y, self.cell, self.cell

    def cell_at(self, pos: Tuple[int,int]) -> Optional[Coord]:
        x, y = pos
        y -= TOP_BAR
        
        # Calculate grid position (centered if window is larger than grid)
        grid_width = self.board.n * self.cell + 2 * self.margin
        grid_start_x = max(self.margin, (self.screen.get_width() - grid_width) // 2)
        
        # Adjust x coordinate for centered grid
        x -= grid_start_x
        y -= self.margin
        
        r = y // self.cell
        c = x // self.cell
        
        if 0 <= r < self.board.n and 0 <= c < self.board.n:
            return (r, c)
        return None

    def ensure_solution(self):
        if not self.solution:
            self.solution = solve_backtracking(self.board, self.diag, time_limit=SOLVER_TIME_LIMIT)

    def next_step_index(self) -> int:
        """Return the actual step number (not display number)."""
        return len(self.path) + 1

    def can_extend_to(self, cell: Coord) -> bool:
        if len(self.path) >= self.board.k or cell in self.path:
            return False
        if self.path and cell not in self.board.neighbors(self.path[-1][0], self.path[-1][1], self.diag):
            return False
        return True

    def reset_path(self):
        g = self.board.givens()
        self.path = [g[1]] if 1 in g else []
        self.animator = None
        self.status_msg = "Path reset. Start from cell 1."
        self.hint_segment = None
        self.is_won = False
        self.showing_victory = False
        self.in_victory_transition = False
        self.victory_transition_alpha = 0

    def go_back_to_menu(self):
        """Go back to main menu"""
        pygame.quit()
        
        # Launch a subprocess to restart the game cleanly
        import subprocess
        import sys
        import os
        
        python = sys.executable
        script = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        
        # Clean environment variables that might trigger auto-start
        env = os.environ.copy()
        for key in ['ZIP_BOARD_SIZE', 'ZIP_GAME_MODE', 'ZIP_LLM_PROVIDER', 'ZIP_SHOW_BOARD_SELECTION']:
            if key in env:
                del env[key]
        
        subprocess.Popen([python, script], env=env)
        sys.exit(0)

    def play_again(self):
        """Start a new game with same settings (board size and LLM provider)"""
        pygame.quit()
        # Import the main function and start new game with same parameters
        import subprocess
        import sys
        
        # Restart the program with same parameters
        python = sys.executable
        script = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        
        # Pass current settings as environment variables for the new process
        env = os.environ.copy()
        env['ZIP_BOARD_SIZE'] = str(self.board_size)
        env['ZIP_GAME_MODE'] = self.game_mode
        
        # Clean up board selection flag if present
        if 'ZIP_SHOW_BOARD_SELECTION' in env:
            del env['ZIP_SHOW_BOARD_SELECTION']
            
        if self.llm_provider:
            env['ZIP_LLM_PROVIDER'] = self.llm_provider
        
        pygame.quit()
        subprocess.Popen([python, script], env=env)
        sys.exit(0)

    def force_exit(self):
        """Force exit - kill everything"""
        print("[FORCE EXIT] Terminating process...")
        pygame.quit()
        
        # Kill environment variables
        import os
        for key in list(os.environ.keys()):
            if key.startswith('ZIP_'):
                del os.environ[key]
        
        # Nuclear option: kill current process
        import os
        os._exit(1)  # Force immediate termination

    def select_board_size(self):
        """Go to board size selection menu"""
        pygame.quit()
        
        # Launch a subprocess that will show board size selection
        import subprocess
        import sys
        
        # Restart the program in board size selection mode
        python = sys.executable
        script = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        
        # Set environment variable to indicate board size selection mode
        env = os.environ.copy()
        env['ZIP_SHOW_BOARD_SELECTION'] = '1'
        
        # IMPORTANT: Remove any persistence of board size/mode to prevent auto-start
        for key in ['ZIP_BOARD_SIZE', 'ZIP_GAME_MODE', 'ZIP_LLM_PROVIDER']:
            if key in env:
                del key
        
        pygame.quit()
        subprocess.Popen([python, script], env=env)
        sys.exit(0)

    def view_leaderboard(self):
        """Show leaderboard then return to victory screen"""
        from leaderboard.leaderboard_display import show_enhanced_leaderboard
        
        # Show leaderboard (this blocks until user goes back)
        show_enhanced_leaderboard()
        
        # Restore game screen (as show_enhanced_leaderboard changes display mode)
        self.screen = pygame.display.set_mode((self.screen.get_width(), self.screen.get_height()))
        pygame.display.set_caption(f"ZIP Puzzle - {self.board_size}x{self.board_size}")
        
        # Re-initialize victory animation to prevent errors if surface context was lost
        # (Though pygame surface objects usually survive display mode changes if dimensions match,
        # it's safer to just rely on the existing object state)

    # ---------- modern buttons ----------
    def draw_buttons(self):
        """Draw modern styled buttons"""
        mouse_pos = pygame.mouse.get_pos()
        
        for name, button_data in self.buttons.items():
            rect = button_data['rect']
            base_color, hover_color = button_data['colors']
            
            # Check hover state
            is_hovered = rect.collidepoint(mouse_pos)
            button_data['hovered'] = is_hovered
            
            # Choose color based on hover state
            color = hover_color if is_hovered else base_color
            
            # Draw modern button with shadow effect
            # Shadow
            shadow_rect = pygame.Rect(rect.x + 3, rect.y + 3, rect.width, rect.height)
            shadow_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, 50), (0, 0, rect.width, rect.height), border_radius=8)
            self.screen.blit(shadow_surface, (shadow_rect.x, shadow_rect.y))
            
            # Main button
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            
            # Subtle highlight border
            highlight_color = tuple(min(255, c + 30) for c in color)
            pygame.draw.rect(self.screen, highlight_color, rect, 2, border_radius=8)
            
            # Button text with proper font sizing
            font_size = max(12, min(18, rect.height // 3))
            font = pygame.font.SysFont('Segoe UI', font_size, bold=True)
            
            text_surface = font.render(name, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)

    def draw_victory_buttons(self):
        """Draw victory screen buttons - vertical layout"""
        mouse_pos = pygame.mouse.get_pos()
        
        for name, button_data in self.victory_buttons.items():
            rect = button_data['rect']
            base_color, hover_color = button_data['colors']
            
            # Check hover state
            is_hovered = rect.collidepoint(mouse_pos)
            button_data['hovered'] = is_hovered
            
            # Choose color based on hover state
            color = hover_color if is_hovered else base_color
            
            # Draw modern button with shadow effect
            shadow_rect = pygame.Rect(rect.x + 4, rect.y + 4, rect.width, rect.height)
            shadow_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, 80), (0, 0, rect.width, rect.height), border_radius=12)
            self.screen.blit(shadow_surface, (shadow_rect.x, shadow_rect.y))
            
            # Main button
            pygame.draw.rect(self.screen, color, rect, border_radius=12)
            
            # Highlight border
            highlight_color = tuple(min(255, c + 40) for c in color)
            pygame.draw.rect(self.screen, highlight_color, rect, 3, border_radius=12)
            
            # Button text
            text_surface = self.victory_button_font.render(name, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)

    def handle_button_click(self, pos):
        """Handle modern button clicks"""
        if self.showing_victory:
            # Handle victory screen buttons
            for name, button_data in self.victory_buttons.items():
                if button_data['rect'].collidepoint(pos):
                    if name == "Play Again":
                        self.play_again()
                    elif name == "Select Board Size":
                        self.select_board_size()
                    elif name == "Leaderboard":
                        self.view_leaderboard()
                    elif name == "Main Menu":
                        self.go_back_to_menu()
                    elif name == "Exit":
                        self.force_exit() 
                    return True
        else:
            # Handle regular game buttons
            for name, button_data in self.buttons.items():
                if button_data['rect'].collidepoint(pos):
                    if name == "Back":
                        self.go_back_to_menu()
                    elif name == "Reset":
                        self.reset_path()
                    elif name == "Hint":
                        self.give_hint()
                    elif name == "LLM":
                        self.show_llm_provider_menu()
                    return True
        return False
    
    def show_llm_provider_menu(self):
        """Show LLM provider selection."""
        from config.llm_config import LLM_PROVIDERS
        import threading
        
        providers = [(name, config) for name, config in LLM_PROVIDERS.items() if config.get("enabled")]
        
        if not providers:
            self.status_msg = "No LLM providers available"
            return
        
        modal_width, modal_height = 400, 200 + len(providers) * 50
        modal_x = (self.screen.get_width() - modal_width) // 2
        modal_y = (self.screen.get_height() - modal_height) // 2
        
        selecting = True
        selected_provider = None
        
        while selecting:
            self.clock.tick(FPS)
            
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.force_exit()  # ← Replace pygame.quit(); sys.exit(0)
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    selecting = False
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    for i, (name, config) in enumerate(providers):
                        btn_rect = pygame.Rect(modal_x + 20, modal_y + 80 + i * 50, modal_width - 40, 40)
                        if btn_rect.collidepoint(e.pos):
                            selected_provider = name
                            selecting = False
            
            self.draw_grid()
            
            # Modern modal design
            pygame.draw.rect(self.screen, (50, 50, 50), (modal_x, modal_y, modal_width, modal_height), border_radius=12)
            pygame.draw.rect(self.screen, GOLD, (modal_x, modal_y, modal_width, modal_height), 3, border_radius=12)
            
            title = self.infofont.render("Select LLM Provider", True, WHITE)
            self.screen.blit(title, (modal_x + 50, modal_y + 20))
            
            for i, (name, config) in enumerate(providers):
                btn_rect = pygame.Rect(modal_x + 20, modal_y + 80 + i * 50, modal_width - 40, 40)
                
                # Modern provider button
                mouse_pos = pygame.mouse.get_pos()
                is_hovered = btn_rect.collidepoint(mouse_pos)
                btn_color = (100, 150, 200) if not is_hovered else (120, 170, 220)
                
                pygame.draw.rect(self.screen, btn_color, btn_rect, border_radius=8)
                pygame.draw.rect(self.screen, (200, 200, 200), btn_rect, 2, border_radius=8)
                
                display_name = config.get("name", name)
                label = self.infofont.render(display_name, True, WHITE)
                self.screen.blit(label, label.get_rect(center=btn_rect.center))
            
            pygame.display.flip()
        
        if selected_provider:
            thread = threading.Thread(
                target=self.solve_with_llm,
                args=(selected_provider,),
                daemon=True
            )
            thread.start()
    
    def solve_with_llm(self, provider: str):
        """Solve puzzle using LLM with enhanced evaluation metrics."""
        from LLM_configuration.llm_manager import llm_solver
        from evaluation.eval import llm_metrics_collector
        from core.solver import solve_backtracking
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Store LLM provider and model info for leaderboard
        self.llm_provider = provider
        
        # Set the provider and get model name
        try:
            llm_solver.set_provider(provider)
            if hasattr(llm_solver, 'model') and llm_solver.model:
                self._current_model = llm_solver.model
            else:
                self._current_model = "unknown"
        except Exception as e:
            logger.error(f"Error setting LLM provider: {e}")
            self._current_model = "unknown"
        
        # Get the solver's optimal path for evaluation (not exposed to LLM)
        solver_path = solve_backtracking(self.board, self.diag, time_limit=8.0)
        if not solver_path:
            logger.warning("Could not generate solver path for evaluation")
            solver_path = []
        
        # Initialize enhanced metrics
        llm_metrics_collector.start_game(self.board_size, solver_path)
        llm_provider = provider
        
        self.status_msg = f"Auto-solving with {provider}..."
        self.is_won = False
        
        # Use configurable move cap for batch runs (falls back to k*2)
        max_iterations = getattr(self, "llm_max_moves", self.board.k * 2)
        iteration = 0
        stuck_count = 0
        max_stuck = 3
        
        while not self.is_won and iteration < max_iterations and stuck_count < max_stuck:
            iteration += 1
            
            try:
                llm_solver.set_provider(provider)
                next_number = len(self.path) + 1
                
                llm_metrics_collector.start_move()
                result = llm_solver.solve(self.board, self.path, next_number)
                
                if result and "next_move" in result:
                    move = result["next_move"]
                    cell = (move["row"], move["col"])
                    reason = result.get("reason", "")
                    confidence = result.get("confidence", 0.5)
                    parsing_success = result.get("parsing_success", True)
                    response_length = result.get("response_length", 0)
                    
                    # Check if move is valid according to game rules
                    is_valid = self.can_extend_to(cell)
                    
                    # Record comprehensive move metrics
                    llm_metrics_collector.record_move(
                        cell[0], cell[1], 
                        is_valid, 
                        self.path.copy(),  # Current path for validation
                        reason, 
                        confidence,
                        parsing_success,
                        response_length
                    )
                    
                    # Update clue information if move was valid
                    if is_valid:
                        display_val = self.board.grid[cell[0]][cell[1]]
                        is_on_clue = display_val > 0
                        clue_number = None
                        if is_on_clue and self.board.display_to_step:
                            clue_number = self.board.display_to_step.get(display_val)
                        
                        # Update the last recorded move with clue info
                        if llm_metrics_collector.game_metrics and llm_metrics_collector.game_metrics.moves:
                            last_move_idx = len(llm_metrics_collector.game_metrics.moves) - 1
                            llm_metrics_collector.update_move_clue_info(last_move_idx, is_on_clue, clue_number)
                    
                    if is_valid:
                        stuck_count = 0
                        self.path.append(cell)
                        self.status_msg = f"Move {iteration}: {cell} ✓"
                        logger.info(f"Move {iteration}: {cell} - Valid")
                        
                        if len(self.path) == self.board.k:
                            ok, msg = validate_path(self.board, self.path, self.diag)
                            if ok:
                                self.is_won = True
                                self.status_msg = f"AUTO-SOLVED in {iteration} moves!"
                    else:
                        stuck_count += 1
                        self.status_msg = f"Move {iteration}: {cell} ✗ ({stuck_count}/{max_stuck})"
                        logger.warning(f"Invalid move: {cell} (stuck: {stuck_count}/{max_stuck})")
                else:
                    stuck_count += 1
                    self.status_msg = f"Parse error ({stuck_count}/{max_stuck})"
                    logger.warning(f"No move from LLM (stuck: {stuck_count}/{max_stuck})")
                    
                    # Record failed parsing attempt
                    llm_metrics_collector.record_move(
                        -1, -1, False, self.path.copy(), 
                        "Parsing failed", 0.0, False, 
                        result.get("response_length", 0) if result else 0
                    )
                
                self.draw_grid()
                pygame.display.flip()
                self.clock.tick(1)
            
            except Exception as e:
                self.status_msg = f"Error: {str(e)[:50]}"
                logger.error(f"LLM auto-solve error: {e}")
                stuck_count += 1
                
                # Record error as failed move
                llm_metrics_collector.record_move(
                    -1, -1, False, self.path.copy(),
                    f"Error: {str(e)[:50]}", 0.0, False, 0
                )
        
        # End game and generate comprehensive metrics
        game_metrics = llm_metrics_collector.end_game(self.is_won)
        
        # Log to wandb with provider and model info
        model_name = llm_solver.model if llm_solver.model else ""
        llm_metrics_collector.log_to_wandb(llm_provider, model_name)
        
        # Print detailed performance analysis
        try:
            detailed_summary = llm_metrics_collector.get_detailed_summary()
            logger.info("=== GAME PERFORMANCE ANALYSIS ===")
            logger.info(detailed_summary)
            print(detailed_summary)
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            
        # Update final status message with key metrics
        if game_metrics:
            self.status_msg = (f"Game ended: {game_metrics.get_performance_grade()} grade, "
                             f"{game_metrics.move_efficiency:.1%} efficiency, "
                             f"{game_metrics.path_accuracy:.1%} accuracy")

        # Mark LLM as finished so batch controller can exit run()
        self.llm_finished = True

    # ---------- hint ----------
    def give_hint(self):
        self.ensure_solution()
        if not self.solution:
            self.status_msg = "No solution available for hint."
            return

        i = 0
        while i < len(self.path) and i < len(self.solution) and self.path[i] == self.solution[i]:
            i += 1

        if i < len(self.path):
            if i == 0:
                self.path = []
                self.status_msg = "Start on the '1' cell."
                return
            self.path = self.solution[:i]

        if i == 0:
            self.status_msg = "Start on the '1' cell."
            return
        if i >= len(self.solution):
            self.status_msg = "Already complete!"
            return

        from_cell = self.solution[i-1]
        to_cell = self.solution[i]

        # Calculate grid position (centered if window is larger than grid)
        grid_width = self.board.n * self.cell + 2 * self.margin
        grid_start_x = max(self.margin, (self.screen.get_width() - grid_width) // 2)

        fx = grid_start_x + from_cell[1]*self.cell + self.cell//2
        fy = TOP_BAR + self.margin + from_cell[0]*self.cell + self.cell//2
        tx = grid_start_x + to_cell[1]*self.cell + self.cell//2
        ty = TOP_BAR + self.margin + to_cell[0]*self.cell + self.cell//2
        self.hint_segment = ((fx, fy), (tx, ty))
        self.hint_expire_at = pygame.time.get_ticks() + 1800
        self.status_msg = "Hint: follow the arrow."

    # ---------- check / animate ----------
    def check_path(self):
        if not self.path:
            self.status_msg = "No path drawn."
            return
        
        if len(self.path) != self.board.k:
            self.status_msg = f"Incomplete. Fill all cells ({len(self.path)}/{self.board.k})."
            return
        
        ok, msg = validate_path(self.board, self.path, self.diag)
        if ok:
            self.trigger_victory()
        else:
            self.status_msg = f"Invalid: {msg}"

    def auto_check_win(self):
        """Auto-check for win after each move"""
        if self.is_won or len(self.path) != self.board.k:
            return
        ok, msg = validate_path(self.board, self.path, self.diag)
        if ok:
            self.trigger_victory()
        else:
            print(f"[DEBUG] Path invalid: {msg}")

    def trigger_victory(self):
        """Trigger victory celebration with smooth transition"""
        self.is_won = True
        self.final_time = self.elapsed_seconds
        self.in_victory_transition = True  # Start transition instead of immediate victory screen
        self.victory_transition_alpha = 0
        
        self.on_win()

    def update_victory_transition(self):
        """Handle smooth transition to victory screen"""
        if self.in_victory_transition:
            self.victory_transition_alpha += self.victory_transition_speed
            
            if self.victory_transition_alpha >= 255:
                # Transition complete, show victory screen
                self.victory_transition_alpha = 255
                self.showing_victory = True
                self.in_victory_transition = False
                self.victory_start_time = pygame.time.get_ticks()
                self._setup_victory_buttons()
                
                # Add initial celebration burst (slower and fewer)
                center_x = self.screen.get_width() // 2
                center_y = self.screen.get_height() // 4
                for _ in range(2):  # Fewer initial bursts
                    self.victory_animation.create_firework(center_x + random.randint(-80, 80), center_y)
                    self.victory_animation.create_ribbon_burst(center_x + random.randint(-120, 120), center_y - 40)
    
    def on_win(self):
        """Handle win: submit score to enhanced leaderboard."""
        from leaderboard.leaderboard_enhanced import enhanced_leaderboard
        
        if self.game_mode == "human":
            rank = enhanced_leaderboard.add_human_score("Player", self.board_size, self.final_time)
        else:
            # LLM mode - extract metrics for enhanced scoring
            move_efficiency = 0.8  # Default efficiency
            path_accuracy = 0.8    # Default accuracy
            
            # Get actual metrics if available
            try:
                from evaluation.eval import llm_metrics_collector
                if llm_metrics_collector.game_metrics:
                    metrics = llm_metrics_collector.game_metrics
                    move_efficiency = metrics.move_efficiency
                    path_accuracy = metrics.path_accuracy
            except:
                pass
            
            # Get model name from LLM solver
            model_name = ""
            try:
                from LLM_configuration.llm_manager import llm_solver
                if llm_solver.model:
                    model_name = llm_solver.model
            except:
                pass
            
            rank = enhanced_leaderboard.add_llm_score(
                player_type=self.llm_provider,
                model_name=model_name,
                board_size=self.board_size,
                time_seconds=self.final_time,
                move_efficiency=move_efficiency,
                path_accuracy=path_accuracy
            )
        
        # Show rank message
        if rank > 0:
            self.status_msg = f"🎉 SOLVED! Rank #{rank} | Time: {self.final_time}s"
        else:
            self.status_msg = f"🎉 SOLVED! Time: {self.final_time}s"

    def animate_solution(self):
        self.ensure_solution()
        if not self.solution:
            self.status_msg = "No solution to animate."
            return
        self.path = [self.solution[0]]
        self.animator = Animator(self.solution, delay_ms=140)
        self.animator.start()
        self.status_msg = "Animating solution..."

    # ---------- drawing ----------
    def draw_victory_screen(self):
        """Draw the victory celebration screen"""
        # Dark background with slight transparency for fireworks to pop
        background = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        background.fill((20, 25, 40))  # Dark blue background
        background.set_alpha(240)
        self.screen.blit(background, (0, 0))
        
        # Update and draw victory animation
        self.victory_animation.update()
        self.victory_animation.draw(self.screen)
        
        # Animated congratulations text (smaller for small windows)
        time_offset = (pygame.time.get_ticks() - self.victory_start_time) / 1000.0
        bounce = int(8 * math.sin(time_offset * 2.5))  # Slower bounce
        
        # Main congratulations text with rainbow effect
        congrats_text = "Congratulations!"
        char_width = max(20, self.screen.get_width() // 25)  # Responsive character width
        for i, char in enumerate(congrats_text):
            color_index = (i + int(time_offset * 3)) % len(self.victory_animation.celebration_colors)  # Slower color change
            char_color = self.victory_animation.celebration_colors[color_index]
            char_surface = self.victory_title_font.render(char, True, char_color)
            char_x = self.screen.get_width() // 2 - len(congrats_text) * char_width // 2 + i * char_width
            char_y = 60 + bounce + int(4 * math.sin(time_offset * 3 + i * 0.3))  # Slower wave
            self.screen.blit(char_surface, (char_x, char_y))
        
        # Timer display
        mins = self.final_time // 60
        secs = self.final_time % 60
        time_text = f"Time: {mins}:{secs:02d}"
        time_surface = self.victory_time_font.render(time_text, True, GOLD)
        time_rect = time_surface.get_rect(center=(self.screen.get_width() // 2, 140))
        
        # Add glow effect to timer
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            glow_surface = self.victory_time_font.render(time_text, True, (255, 215, 0, 100))
            glow_rect = glow_surface.get_rect(center=(time_rect.centerx + offset[0], time_rect.centery + offset[1]))
            self.screen.blit(glow_surface, glow_rect)
        
        self.screen.blit(time_surface, time_rect)
        
        # Victory buttons - now vertical and properly positioned
        self.draw_victory_buttons()

    def draw_victory_transition(self):
        """Draw the transition overlay to victory screen"""
        # Draw the game grid first
        self.draw_grid()
        
        # Then draw a fading overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.fill((20, 25, 40))  # Same color as victory background
        overlay.set_alpha(self.victory_transition_alpha)
        self.screen.blit(overlay, (0, 0))
        
        # Show "SOLVED!" text during transition
        if self.victory_transition_alpha > 100:  # Show text after some fade
            solved_font = pygame.font.SysFont('Segoe UI', 60, bold=True)
            solved_text = solved_font.render("SOLVED!", True, GOLD)
            solved_rect = solved_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
            
            # Text alpha based on transition progress
            text_alpha = min(255, max(0, self.victory_transition_alpha - 100))
            solved_text.set_alpha(text_alpha)
            self.screen.blit(solved_text, solved_rect)

    def draw_grid(self):
        n = self.board.n
        self.screen.fill(WHITE)
        
        # Calculate grid position (centered if window is larger than grid)
        grid_width = n * self.cell + 2 * self.margin
        grid_height = n * self.cell + 2 * self.margin
        grid_start_x = max(self.margin, (self.screen.get_width() - grid_width) // 2)
        
        # Draw grid background cells
        for r in range(n):
            for c in range(n):
                x = grid_start_x + c * self.cell
                y = TOP_BAR + self.margin + r * self.cell
                rect = pygame.Rect(x, y, self.cell, self.cell)
                color = (245, 245, 245) if (r + c) % 2 == 0 else (250, 250, 250)
                if self.hover_cell == (r, c):
                    color = (230, 240, 255)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (220, 220, 220), rect, 1)

        # Draw path with original line width but smooth
        if len(self.path) > 1:
            line_width = int(self.cell * 0.6)  # Keep original line width
            centers = [
                (grid_start_x + c*self.cell + self.cell//2,
                 TOP_BAR + self.margin + r*self.cell + self.cell//2)
                for (r, c) in self.path
            ]
            draw_gradient_polyline(self.screen, centers, line_width,
                                   self.line_color_start, self.line_color_end)

        # Draw hint arrow
        if self.hint_segment and pygame.time.get_ticks() < self.hint_expire_at:
            (fx, fy), (tx, ty) = self.hint_segment
            pygame.draw.line(self.screen, ARROW_COLOR, (fx, fy), (tx, ty), 6)
            pygame.draw.circle(self.screen, ARROW_COLOR, (tx, ty), 8)
        else:
            self.hint_segment = None

        # Draw givens as circles
        for r in range(n):
            for c in range(n):
                val = self.board.grid[r][c]
                if val:
                    x = grid_start_x + c * self.cell
                    y = TOP_BAR + self.margin + r * self.cell
                    draw_cell_circle(self.screen, x, y, self.cell, val, self.bigfont, line_width_ratio=0.6)

        # Draw timer in top-right corner
        if TIMER_ENABLED and not self.showing_victory and not self.in_victory_transition:
            mins = self.elapsed_seconds // 60
            secs = self.elapsed_seconds % 60
            timer_color = RED if self.elapsed_seconds > TIMER_WARNING_SECONDS else GREEN
            timer_text = self.timer_font.render(f"Time: {mins}:{secs:02d}", True, timer_color)
            timer_rect = timer_text.get_rect()
            timer_rect.topright = (self.screen.get_width() - self.margin, 6)
            self.screen.blit(timer_text, timer_rect)

        # Draw modern buttons
        if not self.in_victory_transition:  # Hide buttons during transition
            self.draw_buttons()
        
        # Draw only status message (no unnecessary keyboard shortcuts)
        if self.status_msg and not self.showing_victory and not self.in_victory_transition:
            button_y = list(self.buttons.values())[0]['rect'].y if self.buttons else self.screen.get_height() - 80
            status_y = button_y - 40
            
            color = RED if "invalid" in self.status_msg.lower() or "error" in self.status_msg.lower() else GREEN
            status_surface = self.infofont.render(self.status_msg, True, color)
            status_rect = status_surface.get_rect(center=(self.screen.get_width() // 2, status_y))
            self.screen.blit(status_surface, status_rect)

    # ---------- loop ----------
    def run(self):
        while True:
            self.clock.tick(FPS)
            
            if not self.is_won and TIMER_ENABLED:
                self.elapsed_seconds = (pygame.time.get_ticks() - self.start_time) // 1000
            
            # Update victory transition
            self.update_victory_transition()
            
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit(0)

                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        if self.showing_victory or self.in_victory_transition:
                            self.go_back_to_menu()
                        else:
                            self.go_back_to_menu()
                    elif e.key == pygame.K_SPACE and not self.showing_victory and not self.in_victory_transition:
                        self.check_path()
                    elif e.key == pygame.K_r and not self.showing_victory and not self.in_victory_transition:
                        self.reset_path()
                    elif e.key == pygame.K_d and not self.showing_victory and not self.in_victory_transition:
                        self.diag = not self.diag
                        self.board.diag = self.diag
                        self.status_msg = f"Adjacency: {'8-way' if self.diag else '4-way'}"
                    elif e.key == pygame.K_a and not self.showing_victory and not self.in_victory_transition:
                        self.animate_solution()

                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if not self.in_victory_transition:  # Disable clicks during transition
                        if self.handle_button_click(e.pos):
                            continue
                        
                        if self.showing_victory:
                            continue  # Don't handle grid clicks during victory screen
                        
                        cell = self.cell_at(e.pos)
                        if not cell:
                            continue
                        
                        if not self.path:
                            if self.can_extend_to(cell):
                                self.path = [cell]
                                self.status_msg = f"Started path at {cell}."
                            else:
                                self.status_msg = "Start on the '1' cell."
                        elif self.can_extend_to(cell):
                            self.path.append(cell)
                            self.status_msg = f"Extended path to {cell}."
                        else:
                            self.status_msg = f"Cannot move to {cell}."
                        
                        self.dragging = True
                        self.auto_check_win()

                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    self.dragging = False

                elif e.type == pygame.MOUSEMOTION:
                    if not self.showing_victory and not self.in_victory_transition:
                        self.hover_cell = self.cell_at(e.pos)
                        if self.dragging and self.hover_cell:
                            cell = self.hover_cell
                            if len(self.path) >= 2 and cell == self.path[-2]:
                                # Backtrack
                                self.path.pop()
                                self.status_msg = f"Backtracked to {self.path[-1] if self.path else 'start'}."
                            elif self.can_extend_to(cell):
                                self.path.append(cell)
                                self.status_msg = f"Extended path to {cell}."
                                self.auto_check_win()

                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                    # Right click to backtrack
                    if not self.showing_victory and not self.in_victory_transition and self.path:
                        g = self.board.givens()
                        if 1 in g and self.path == [g[1]]:
                            pass  # Don't remove starting cell
                        else:
                            removed = self.path.pop()
                            self.status_msg = f"Removed {removed} from path."

            # --- AUTO-QUIT FOR LLM BATCH MODE ---
            # If an external controller (like zip_llm_tests) set llm_auto_quit=True,
            # and solve_with_llm has finished, exit the run() loop so the next game can start.
            if self.game_mode == "llm" and getattr(self, "llm_auto_quit", False) and getattr(self, "llm_finished", False):
                # Optionally draw one last frame before quitting
                if self.showing_victory:
                    self.draw_victory_screen()
                    pygame.display.flip()
                    pygame.time.delay(300)
                return

            if self.animator:
                self.animator.update(pygame.time.get_ticks(), self.path)

            # Draw appropriate screen
            if self.showing_victory:
                self.draw_victory_screen()
            elif self.in_victory_transition:
                self.draw_victory_transition()
            else:
                self.draw_grid()
                
            pygame.display.flip()
