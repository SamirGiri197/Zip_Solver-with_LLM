import pygame
import sys
from typing import List, Dict, Optional, Tuple
from leaderboard.leaderboard_enhanced import enhanced_leaderboard, EnhancedScore
from config.config import BOARD_SIZES

class EnhancedLeaderboardDisplay:
    """Displays leaderboard in tabular format with selectable board sizes and categories"""
    
    def __init__(self, screen_width: int = 1200, screen_height: int = 800):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = None
        self.clock = pygame.time.Clock()
        
        # Colors
        self.colors = {
            'bg': (245, 246, 248),
            'card': (255, 255, 255),
            'header': (59, 130, 246),
            'text_primary': (17, 24, 39),
            'text_secondary': (107, 114, 128),
            'border': (229, 231, 235),
            'table_header': (243, 244, 246),
            'table_alt': (249, 250, 251),
            # Button Colors
            'btn_back': (107, 114, 128),
            'btn_menu': (59, 130, 246),
            'btn_exit': (239, 68, 68),
            # Category colors
            'overall': (59, 130, 246),
            'human': (34, 197, 94),
            'openai': (16, 163, 127),
            'claude': (168, 85, 247),
            'gemini': (239, 68, 68),
            'ollama': (245, 158, 11)
        }
        
        self._init_fonts()
    
    def _init_fonts(self):
        font_names = ['Segoe UI', 'Arial', 'Liberation Sans', 'sans-serif']
        self.fonts = {}
        for name in font_names:
            try:
                self.fonts = {
                    'title': pygame.font.SysFont(name, 32, bold=True),
                    'header': pygame.font.SysFont(name, 20, bold=True),
                    'table_head': pygame.font.SysFont(name, 14, bold=True),
                    'table_row': pygame.font.SysFont(name, 14),
                    'button': pygame.font.SysFont(name, 16, bold=True),
                    'small': pygame.font.SysFont(name, 12)
                }
                break
            except:
                continue
        if not self.fonts:
            self.fonts = {
                'title': pygame.font.Font(None, 32),
                'header': pygame.font.Font(None, 24),
                'table_head': pygame.font.Font(None, 18),
                'table_row': pygame.font.Font(None, 18),
                'button': pygame.font.Font(None, 20),
                'small': pygame.font.Font(None, 16)
            }

    def draw_rounded_rect(self, surface, rect, color, radius=8, border_color=None, width=0):
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        if border_color and width > 0:
            pygame.draw.rect(surface, border_color, rect, width, border_radius=radius)

    def draw_button(self, rect, text, base_color, mouse_pos):
        """Helper to draw interactive buttons"""
        hover = rect.collidepoint(mouse_pos)
        color = tuple(min(255, c + 20) for c in base_color) if hover else base_color
        
        self.draw_rounded_rect(self.screen, rect, color, radius=8)
        
        txt_surf = self.fonts['button'].render(text, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(center=rect.center)
        self.screen.blit(txt_surf, txt_rect)
        
        return hover

    def show_board_selection(self) -> Optional[int]:
        """Show grid of buttons to select board size"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Leaderboard - Select Board Size")
        
        available = enhanced_leaderboard.get_available_board_sizes()
        display_sizes = BOARD_SIZES
        
        running = True
        while running:
            self.clock.tick(60)
            self.screen.fill(self.colors['bg'])
            mx, my = pygame.mouse.get_pos()
            
            # Title
            title = self.fonts['title'].render("Select Board Size", True, self.colors['text_primary'])
            self.screen.blit(title, title.get_rect(center=(400, 80)))
            
            click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    click = True

            # Grid of sizes
            cols = 3
            w, h = 140, 60
            gap = 20
            start_x = (800 - (cols * w + (cols-1)*gap)) // 2
            start_y = 150
            
            for i, size in enumerate(display_sizes):
                r, c = i // cols, i % cols
                rect = pygame.Rect(start_x + c*(w+gap), start_y + r*(h+gap), w, h)
                
                has_data = size in available
                base_color = self.colors['header'] if has_data else (200, 200, 200)
                
                if self.draw_button(rect, f"{size}x{size}", base_color, (mx, my)):
                    if click:
                        return size
            
            # Bottom Buttons
            btn_w, btn_h = 160, 50
            menu_rect = pygame.Rect(400 - btn_w - 10, 500, btn_w, btn_h)
            exit_rect = pygame.Rect(400 + 10, 500, btn_w, btn_h)
            
            if self.draw_button(menu_rect, "Back to Menu", self.colors['btn_back'], (mx, my)):
                if click: return None
            
            if self.draw_button(exit_rect, "Exit Game", self.colors['btn_exit'], (mx, my)):
                if click:
                    pygame.quit()
                    sys.exit(0)
            
            pygame.display.flip()
        return None

    def show_results(self, board_size: int) -> str:
        """
        Show tabular results for the selected board size.
        Returns action string: 'back', 'menu', 'exit'
        """
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption(f"Leaderboard - {board_size}x{board_size}")
        
        data = enhanced_leaderboard.get_leaderboard_data(board_size)
        
        # Layout config
        scroll_y = 0
        section_order = [
            ("Overall Top 5", "overall"),
            ("Human Players", "human"),
            ("ChatGPT (OpenAI)", "openai"),
            ("Claude (Anthropic)", "claude"),
            ("Gemini (Google)", "gemini"),
            ("Ollama (Local)", "ollama")
        ]
        
        footer_height = 80
        view_height = self.screen_height - footer_height
        
        running = True
        while running:
            self.clock.tick(60)
            mx, my = pygame.mouse.get_pos()
            
            # Calculate content height
            total_content_height = 100 + len(section_order) * 200
            max_scroll = max(0, total_content_height - view_height)
            
            click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "back"
                    elif event.key == pygame.K_UP:
                        scroll_y = max(0, scroll_y - 20)
                    elif event.key == pygame.K_DOWN:
                        scroll_y = min(max_scroll, scroll_y + 20)
                if event.type == pygame.MOUSEWHEEL:
                    scroll_y = max(0, min(max_scroll, scroll_y - event.y * 30))
                if event.type == pygame.MOUSEBUTTONDOWN:
                    click = True
            
            self.screen.fill(self.colors['bg'])
            
            # --- Draw Content ---
            content_surface = pygame.Surface((self.screen_width, view_height))
            content_surface.fill(self.colors['bg'])
            
            current_y = 20 - scroll_y
            
            # Main Title
            title = self.fonts['title'].render(f"{board_size}x{board_size} Leaderboard", True, self.colors['text_primary'])
            content_surface.blit(title, (40, current_y))
            current_y += 60
            
            # Draw Sections
            for title_text, key in section_order:
                scores = data.get(key, [])
                color = self.colors.get(key, self.colors['header'])
                current_y = self._draw_section(content_surface, current_y, title_text, scores, color)
                current_y += 30 # Spacing
            
            # Blit content
            self.screen.blit(content_surface, (0, 0))
            
            # Scrollbar
            if max_scroll > 0:
                sb_h = max(30, int(view_height * (view_height / total_content_height)))
                sb_y = int((scroll_y / max_scroll) * (view_height - sb_h))
                pygame.draw.rect(self.screen, (200, 200, 200), (self.screen_width-10, sb_y, 8, sb_h), border_radius=4)
            
            # --- Footer Buttons ---
            pygame.draw.rect(self.screen, self.colors['card'], (0, view_height, self.screen_width, footer_height))
            pygame.draw.line(self.screen, self.colors['border'], (0, view_height), (self.screen_width, view_height), 1)
            
            btn_w, btn_h = 180, 50
            btn_y = view_height + (footer_height - btn_h) // 2
            
            # Buttons: [Back] [Main Menu] [Exit]
            spacing = 20
            total_w = 3 * btn_w + 2 * spacing
            start_x = (self.screen_width - total_w) // 2
            
            rect_back = pygame.Rect(start_x, btn_y, btn_w, btn_h)
            rect_menu = pygame.Rect(start_x + btn_w + spacing, btn_y, btn_w, btn_h)
            rect_exit = pygame.Rect(start_x + 2 * (btn_w + spacing), btn_y, btn_w, btn_h)
            
            if self.draw_button(rect_back, "< Select Board Size", self.colors['btn_back'], (mx, my)):
                if click: return "back"
            
            if self.draw_button(rect_menu, "Main Menu", self.colors['btn_menu'], (mx, my)):
                if click: return "menu"
                
            if self.draw_button(rect_exit, "Exit", self.colors['btn_exit'], (mx, my)):
                if click: return "exit"

            pygame.display.flip()
        
        return "back"

    def _draw_section(self, surface, y: int, title: str, scores: List[EnhancedScore], color: Tuple[int,int,int]) -> int:
        """Draw a single category table onto the given surface"""
        # Header
        self.draw_rounded_rect(surface, pygame.Rect(40, y, self.screen_width-80, 30), color, radius=5)
        txt = self.fonts['header'].render(title, True, (255,255,255))
        surface.blit(txt, (50, y+5))
        
        y += 35
        
        # Table Background
        table_h = 30 + 5 * 25 # Header + 5 rows
        pygame.draw.rect(surface, self.colors['card'], (40, y, self.screen_width-80, table_h))
        pygame.draw.rect(surface, self.colors['border'], (40, y, self.screen_width-80, table_h), 1)
        
        # Columns: Rank, Player, Model, Time, Score
        cols = [
            ("Rank", 60), ("Player", 200), ("Model/Details", 200), 
            ("Time", 100), ("Score", 100), ("Efficiency", 100)
        ]
        
        # Draw Column Headers
        cx = 50
        pygame.draw.rect(surface, self.colors['table_header'], (41, y+1, self.screen_width-82, 24))
        for name, w in cols:
            surf = self.fonts['table_head'].render(name, True, self.colors['text_primary'])
            surface.blit(surf, (cx, y+5))
            cx += w
        
        y += 25
        
        # Draw Rows (Max 5)
        if not scores:
            none_txt = self.fonts['table_row'].render("No scores recorded yet", True, self.colors['text_secondary'])
            surface.blit(none_txt, (50, y+10))
            return y + 5 * 25
            
        for i in range(5):
            if i < len(scores):
                s = scores[i]
                row_y = y + i * 25
                if i % 2 == 1:
                    pygame.draw.rect(surface, self.colors['table_alt'], (41, row_y, self.screen_width-82, 25))
                
                cx = 50
                # Rank
                surface.blit(self.fonts['table_row'].render(f"#{i+1}", True, self.colors['text_primary']), (cx, row_y+5))
                cx += cols[0][1]
                # Player
                surface.blit(self.fonts['table_row'].render(s.player_name[:20], True, self.colors['text_primary']), (cx, row_y+5))
                cx += cols[1][1]
                # Model
                mod = s.model_name if s.model_name else "-"
                surface.blit(self.fonts['table_row'].render(mod[:25], True, self.colors['text_secondary']), (cx, row_y+5))
                cx += cols[2][1]
                # Time
                surface.blit(self.fonts['table_row'].render(f"{s.time_seconds}s", True, self.colors['text_primary']), (cx, row_y+5))
                cx += cols[3][1]
                # Score
                surface.blit(self.fonts['table_row'].render(f"{s.score():.0f}", True, self.colors['text_primary']), (cx, row_y+5))
                cx += cols[4][1]
                # Efficiency
                eff = f"{s.move_efficiency:.0%}" if s.move_efficiency else "-"
                surface.blit(self.fonts['table_row'].render(eff, True, self.colors['text_secondary']), (cx, row_y+5))

        return y + 5 * 25

def show_enhanced_leaderboard(screen=None):
    """Entry point with navigation loop"""
    display = EnhancedLeaderboardDisplay()
    
    while True:
        # Step 1: Select Board Size
        size = display.show_board_selection()
        
        if size is None:
            # User clicked "Back" or ESC in selection screen
            return
            
        # Step 2: Show Results for selected size
        action = display.show_results(size)
        
        if action == "menu":
            return
        elif action == "exit":
            pygame.quit()
            sys.exit(0)
        # If action == "back", loop continues to show_board_selection again

# Backwards compatibility alias
Leaderboard = EnhancedLeaderboardDisplay