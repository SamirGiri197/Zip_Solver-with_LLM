import sys
import pygame
from typing import List, Optional, Tuple

from core.board import Board, Coord, validate_path
from core.solver import solve_backtracking
from UI.animation import Animator
from UI.style import draw_cell_circle, draw_gradient_polyline, random_gradient_colors
from config.config import *

ARROW_COLOR = (255, 215, 0)
TOP_BAR = 48  

class Game:
    def __init__(self, board: Board, solution: Optional[List[Coord]] = None, board_size: int = 5):
        pygame.init()
        self.board = board
        self.diag = board.diag
        self.board_size = board_size

        # Gradient palette
        self.line_color_start, self.line_color_end = random_gradient_colors()

        # Layout - calculate responsive sizes
        self.cell = CELL_SIZE
        self.margin = GRID_MARGIN
        
        # Grid dimensions
        grid_width = self.cell * board.n + 2 * self.margin
        grid_height = self.cell * board.n + 2 * self.margin
        
        # Button area dimensions (responsive to board size)
        self.button_height = max(40, int(self.cell * 0.8))
        self.button_area_height = self.button_height + 2 * self.margin
        
        # Total window size
        w = grid_width
        h = TOP_BAR + grid_height + self.button_area_height
        
        self.screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption(f"ZIP Puzzle - {board_size}x{board_size}")
        
        # Timer
        self.start_time = pygame.time.get_ticks()
        self.elapsed_seconds = 0

        # Fonts - scale based on cell size
        font_size = max(16, int(self.cell * 0.42))
        button_font_size = max(12, int(self.cell * 0.35))
        self.bigfont = pygame.font.SysFont(FONT_NAME, font_size, bold=True)
        self.infofont = pygame.font.SysFont(FONT_NAME, button_font_size)
        self.timer_font = pygame.font.SysFont(FONT_NAME, max(14, int(self.cell * 0.3)))

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

        # Buttons - positioned at bottom with responsive sizing
        self._setup_buttons()
        
        self.hint_segment: Optional[Tuple[Tuple[int,int], Tuple[int,int]]] = None
        self.hint_expire_at = 0

        self.clock = pygame.time.Clock()

    def _setup_buttons(self):
        """Setup button positions at the bottom, evenly spaced and centered."""
        button_names = ["Exit", "Reset", "Hint", "LLM"]
        button_width = max(60, int(self.cell * 0.9))
        button_spacing = 15
        
        # Calculate total width needed for all buttons
        total_buttons_width = len(button_names) * button_width + (len(button_names) - 1) * button_spacing
        
        # Center buttons horizontally
        start_x = (self.screen.get_width() - total_buttons_width) // 2
        
        # Position buttons at bottom
        grid_height = self.cell * self.board.n + 2 * self.margin
        button_y = TOP_BAR + grid_height + self.margin
        
        self.buttons = {}
        for i, name in enumerate(button_names):
            x = start_x + i * (button_width + button_spacing)
            self.buttons[name] = pygame.Rect(x, button_y, button_width, self.button_height)

    # ---------- helpers ----------
    def to_screen(self, r: int, c: int) -> Tuple[int,int,int,int]:
        x = self.margin + c * self.cell
        y = TOP_BAR + self.margin + r * self.cell
        return x, y, self.cell, self.cell

    def cell_at(self, pos: Tuple[int,int]) -> Optional[Coord]:
        x, y = pos
        y -= TOP_BAR
        r = (y - self.margin) // self.cell
        c = (x - self.margin) // self.cell
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
        self.status_msg = "Reset path."
        self.hint_segment = None
        self.is_won = False

    # ---------- buttons ----------
    def draw_buttons(self):
        for name, rect in self.buttons.items():
            # Button background with border
            pygame.draw.rect(self.screen, (235, 205, 120), rect, border_radius=8)
            pygame.draw.rect(self.screen, (120, 90, 10), rect, 2, border_radius=8)
            
            # Button text
            label = self.infofont.render(name, True, (0, 0, 0))
            label_rect = label.get_rect(center=rect.center)
            self.screen.blit(label, label_rect)

    def handle_button_click(self, pos):
        for name, rect in self.buttons.items():
            if rect.collidepoint(pos):
                if name == "Exit":
                    pygame.quit(); sys.exit(0)
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
                    pygame.quit(); sys.exit(0)
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    selecting = False
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    for i, (name, config) in enumerate(providers):
                        btn_rect = pygame.Rect(modal_x + 20, modal_y + 80 + i * 50, modal_width - 40, 40)
                        if btn_rect.collidepoint(e.pos):
                            selected_provider = name
                            selecting = False
            
            self.draw_grid()
            
            pygame.draw.rect(self.screen, (50, 50, 50), (modal_x, modal_y, modal_width, modal_height))
            pygame.draw.rect(self.screen, GOLD, (modal_x, modal_y, modal_width, modal_height), 3)
            
            title = self.infofont.render("Select LLM Provider", True, WHITE)
            self.screen.blit(title, (modal_x + 50, modal_y + 20))
            
            for i, (name, config) in enumerate(providers):
                btn_rect = pygame.Rect(modal_x + 20, modal_y + 80 + i * 50, modal_width - 40, 40)
                pygame.draw.rect(self.screen, (100, 150, 200), btn_rect, border_radius=5)
                pygame.draw.rect(self.screen, (50, 100, 150), btn_rect, 2)
                label = self.infofont.render(config.get("name"), True, WHITE)
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
        """Solve puzzle using LLM - continuous auto-solve."""
        from LLM_configuration.llm_manager import llm_solver
        from evaluation.eval import metrics_collector
        import logging
        
        logger = logging.getLogger(__name__)
        metrics_collector.start_game(self.board_size)
        llm_provider = provider
        
        self.status_msg = f"Auto-solving with {provider}..."
        self.is_won = False
        
        max_iterations = self.board.k * 2
        iteration = 0
        stuck_count = 0
        max_stuck = 3
        
        while not self.is_won and iteration < max_iterations and stuck_count < max_stuck:
            iteration += 1
            
            try:
                llm_solver.set_provider(provider)
                next_number = len(self.path) + 1
                
                metrics_collector.start_move()
                result = llm_solver.solve(self.board, self.path, next_number)
                
                if result and "next_move" in result:
                    move = result["next_move"]
                    cell = (move["row"], move["col"])
                    reason = result.get("reason", "")
                    
                    is_valid = self.can_extend_to(cell)
                    display_val = self.board.grid[cell[0]][cell[1]]
                    is_on_clue = display_val > 0
                    clue_number = None
                    if is_on_clue and self.board.display_to_step:
                        clue_number = self.board.display_to_step.get(display_val)
                    
                    metrics_collector.record_move(
                        cell[0], cell[1], is_valid, is_on_clue,
                        clue_number, reason, 0.9
                    )
                    
                    if is_valid:
                        stuck_count = 0
                        self.path.append(cell)
                        self.status_msg = f"Move {iteration}: {cell}"
                        logger.info(f"Move {iteration}: {cell} - Valid")
                        
                        if len(self.path) == self.board.k:
                            ok, msg = validate_path(self.board, self.path, self.diag)
                            if ok:
                                self.is_won = True
                                self.status_msg = f"AUTO-SOLVED in {iteration} moves!"
                    else:
                        stuck_count += 1
                        self.status_msg = f"Stuck: Invalid move {stuck_count}/{max_stuck}"
                        logger.warning(f"Invalid move: {cell} (stuck: {stuck_count}/{max_stuck})")
                else:
                    stuck_count += 1
                    self.status_msg = f"Stuck: LLM failed {stuck_count}/{max_stuck}"
                    logger.warning(f"No move from LLM (stuck: {stuck_count}/{max_stuck})")
                
                self.draw_grid()
                pygame.display.flip()
                self.clock.tick(1)
            
            except Exception as e:
                self.status_msg = f"Error: {str(e)[:50]}"
                logger.error(f"LLM auto-solve error: {e}")
                stuck_count += 1
        
        clue_count = len(self.board.givens())
        game_metrics = metrics_collector.end_game(self.is_won, clue_count)
        metrics_collector.log_to_wandb(llm_provider)
        
        try:
            summary = metrics_collector.get_summary()
            logger.info("Game ended")
            print(summary)
        except:
            pass

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

        fx = self.margin + from_cell[1]*self.cell + self.cell//2
        fy = TOP_BAR + self.margin + from_cell[0]*self.cell + self.cell//2
        tx = self.margin + to_cell[1]*self.cell + self.cell//2
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
            self.status_msg = "🎉 SOLVED! Perfect 1..k path!"
            self.is_won = True
        else:
            self.status_msg = f"Invalid: {msg}"

    def auto_check_win(self):
        """Auto-check for win after each move"""
        if self.is_won or len(self.path) != self.board.k:
            return
        ok, msg = validate_path(self.board, self.path, self.diag)
        if ok:
            self.status_msg = "🎉 SOLVED! Perfect 1..k path!"
            self.is_won = True
            self.on_win()
        else:
            print(f"[DEBUG] Path invalid: {msg}")
    
    def on_win(self):
        """Handle win: submit score to leaderboard."""
        from leaderboard.leaderboard import Leaderboard
        lb = Leaderboard()
        rank = lb.add_score("Player", self.board_size, self.elapsed_seconds)
        if rank > 0:
            self.status_msg = f"🎉 SOLVED! Rank #{rank} on Leaderboard! Time: {self.elapsed_seconds}s"
        else:
            self.status_msg = f"🎉 SOLVED! Time: {self.elapsed_seconds}s"

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
    def draw_grid(self):
        n = self.board.n
        self.screen.fill(WHITE)
        
        # Draw grid background cells
        for r in range(n):
            for c in range(n):
                x, y, w, h = self.to_screen(r, c)
                rect = pygame.Rect(x, y, w, h)
                color = (245, 245, 245) if (r + c) % 2 == 0 else (250, 250, 250)
                if self.hover_cell == (r, c):
                    color = (230, 240, 255)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (220, 220, 220), rect, 1)

        # Draw path
        if len(self.path) > 1:
            line_width = int(self.cell * 0.6)
            centers = [
                (self.margin + c*self.cell + self.cell//2,
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
                    x, y, _, _ = self.to_screen(r, c)
                    draw_cell_circle(self.screen, x, y, self.cell, val, self.bigfont, line_width_ratio=0.6)

        # Draw timer in top-right corner
        if TIMER_ENABLED:
            mins = self.elapsed_seconds // 60
            secs = self.elapsed_seconds % 60
            timer_color = RED if self.elapsed_seconds > TIMER_WARNING_SECONDS else GREEN
            timer_text = self.timer_font.render(f"Time: {mins}:{secs:02d}", True, timer_color)
            timer_rect = timer_text.get_rect()
            timer_rect.topright = (self.screen.get_width() - self.margin, 6)
            self.screen.blit(timer_text, timer_rect)

        # Draw buttons
        self.draw_buttons()
        
        # Draw info and status
        grid_height = n * self.cell + 2 * self.margin
        info_y = TOP_BAR + grid_height + self.button_area_height + 5
        info = "SPACE=Check | R=Reset | A=Animate | D=Adjacency | ESC=Exit"
        self.screen.blit(self.infofont.render(info, True, (0,0,0)), (self.margin, info_y))
        
        if self.status_msg:
            color = RED if "invalid" in self.status_msg.lower() or "error" in self.status_msg.lower() else GREEN
            self.screen.blit(self.infofont.render(self.status_msg, True, color), (self.margin, info_y + 20))

    # ---------- loop ----------
    def run(self):
        while True:
            self.clock.tick(FPS)
            
            if not self.is_won and TIMER_ENABLED:
                self.elapsed_seconds = (pygame.time.get_ticks() - self.start_time) // 1000
            
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit(0)

                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit(0)
                    elif e.key == pygame.K_SPACE:
                        self.check_path()
                    elif e.key == pygame.K_r:
                        self.reset_path()
                    elif e.key == pygame.K_d:
                        self.diag = not self.diag
                        self.board.diag = self.diag
                        self.status_msg = f"Adjacency: {'8-way' if self.diag else '4-way'}"
                    elif e.key == pygame.K_a:
                        self.animate_solution()

                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if self.handle_button_click(e.pos):
                        continue
                    cell = self.cell_at(e.pos)
                    if not cell:
                        continue
                    if not self.path:
                        if self.can_extend_to(cell):
                            self.path = [cell]
                        else:
                            self.status_msg = "Start on the '1' cell."
                    elif self.can_extend_to(cell):
                        self.path.append(cell)
                    self.dragging = True
                    self.auto_check_win()

                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    self.dragging = False

                elif e.type == pygame.MOUSEMOTION:
                    self.hover_cell = self.cell_at(e.pos)
                    if self.dragging and self.hover_cell:
                        cell = self.hover_cell
                        if len(self.path) >= 2 and cell == self.path[-2]:
                            self.path.pop()
                        elif self.can_extend_to(cell):
                            self.path.append(cell)
                            self.auto_check_win()

                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                    if self.path:
                        g = self.board.givens()
                        if 1 in g and self.path == [g[1]]:
                            pass
                        else:
                            self.path.pop()

            if self.animator:
                self.animator.update(pygame.time.get_ticks(), self.path)

            self.draw_grid()
            pygame.display.flip()