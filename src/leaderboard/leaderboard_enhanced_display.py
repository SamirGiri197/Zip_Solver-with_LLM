import pygame
import sys
from typing import List, Dict, Optional
from leaderboard.leaderboard_enhanced import enhanced_leaderboard, EnhancedScore

class EnhancedLeaderboardDisplay:
    """Enhanced leaderboard display with board size selection and categorized results"""
    
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
            'header_text': (255, 255, 255),
            'primary': (59, 130, 246),
            'primary_hover': (37, 99, 235),
            'success': (34, 197, 94),
            'warning': (245, 158, 11),
            'danger': (239, 68, 68),
            'text_primary': (17, 24, 39),
            'text_secondary': (107, 114, 128),
            'shadow': (0, 0, 0, 40),
            'border': (229, 231, 235),
            'table_header': (243, 244, 246),
            'table_row_alt': (249, 250, 251)
        }
        
        # Fonts
        self.fonts = {}
        self._init_fonts()
        
        # State
        self.current_board_size = None
        self.leaderboard_data = {}
    
    def _init_fonts(self):
        """Initialize fonts with fallbacks"""
        font_names = ['Segoe UI', 'Arial', 'Liberation Sans', 'DejaVu Sans', 'sans-serif']
        
        for font_name in font_names:
            try:
                self.fonts = {
                    'title': pygame.font.SysFont(font_name, 32, bold=True),
                    'section_header': pygame.font.SysFont(font_name, 24, bold=True),
                    'table_header': pygame.font.SysFont(font_name, 16, bold=True),
                    'table_data': pygame.font.SysFont(font_name, 14),
                    'button': pygame.font.SysFont(font_name, 18, bold=True),
                    'small': pygame.font.SysFont(font_name, 12)
                }
                break
            except:
                continue
        
        # Fallback if no fonts work
        if not self.fonts:
            self.fonts = {
                'title': pygame.font.Font(None, 32),
                'section_header': pygame.font.Font(None, 24),
                'table_header': pygame.font.Font(None, 16),
                'table_data': pygame.font.Font(None, 14),
                'button': pygame.font.Font(None, 18),
                'small': pygame.font.Font(None, 12)
            }
    
    def draw_rounded_rect(self, surface, rect, color, border_radius=8, border_color=None, border_width=0):
        """Draw rounded rectangle with optional border"""
        pygame.draw.rect(surface, color, rect, border_radius=border_radius)
        if border_color and border_width > 0:
            pygame.draw.rect(surface, border_color, rect, border_width, border_radius=border_radius)
    
    def show_board_size_selection(self) -> Optional[int]:
        """Show board size selection interface"""
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("ZIP Puzzle - Select Board Size for Leaderboard")
        
        # Get available board sizes
        available_sizes = enhanced_leaderboard.get_available_board_sizes()
        from config.config import BOARD_SIZES
        all_sizes = BOARD_SIZES
        
        if not available_sizes:
            # No scores yet, show message
            self._show_no_scores_message()
            return None
        
        selected_size = None
        
        while selected_size is None:
            self.clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    selected_size = self._handle_size_selection_click(mouse_pos, available_sizes)
            
            self._draw_size_selection_screen(available_sizes, all_sizes)
            pygame.display.flip()
        
        return selected_size
    
    def _show_no_scores_message(self):
        """Show message when no scores are available"""
        for _ in range(180):  # Show for 3 seconds at 60fps
            self.clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    return
            
            self.screen.fill(self.colors['bg'])
            
            # Title
            title = self.fonts['title'].render("Leaderboard", True, self.colors['text_primary'])
            title_rect = title.get_rect(center=(400, 200))
            self.screen.blit(title, title_rect)
            
            # Message
            message = self.fonts['section_header'].render("No scores recorded yet!", True, self.colors['text_secondary'])
            message_rect = message.get_rect(center=(400, 280))
            self.screen.blit(message, message_rect)
            
            hint = self.fonts['table_data'].render("Play some games to see results here", True, self.colors['text_secondary'])
            hint_rect = hint.get_rect(center=(400, 320))
            self.screen.blit(hint, hint_rect)
            
            pygame.display.flip()
    
    def _draw_size_selection_screen(self, available_sizes: List[int], all_sizes: List[int]):
        """Draw the board size selection screen"""
        self.screen.fill(self.colors['bg'])
        
        # Title
        title = self.fonts['title'].render("Select Board Size", True, self.colors['text_primary'])
        title_rect = title.get_rect(center=(400, 80))
        self.screen.blit(title, title_rect)
        
        subtitle = self.fonts['table_data'].render("Choose a board size to view leaderboard", True, self.colors['text_secondary'])
        subtitle_rect = subtitle.get_rect(center=(400, 120))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Board size buttons
        cols = 3
        button_width = 150
        button_height = 60
        spacing = 20
        start_y = 200
        
        mouse_pos = pygame.mouse.get_pos()
        
        for i, size in enumerate(all_sizes):
            row = i // cols
            col = i % cols
            
            # Center the grid
            total_width = cols * button_width + (cols - 1) * spacing
            start_x = (800 - total_width) // 2
            
            x = start_x + col * (button_width + spacing)
            y = start_y + row * (button_height + spacing)
            
            button_rect = pygame.Rect(x, y, button_width, button_height)
            
            # Button state
            is_available = size in available_sizes
            is_hovered = button_rect.collidepoint(mouse_pos) and is_available
            
            # Button colors
            if not is_available:
                bg_color = self.colors['border']
                text_color = self.colors['text_secondary']
            elif is_hovered:
                bg_color = self.colors['primary_hover']
                text_color = self.colors['header_text']
            else:
                bg_color = self.colors['primary']
                text_color = self.colors['header_text']
            
            # Draw button
            self.draw_rounded_rect(self.screen, button_rect, bg_color, border_radius=8)
            
            # Button text
            text = self.fonts['button'].render(f"{size}x{size}", True, text_color)
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)
            
            # Score count for available sizes
            if is_available:
                count = len(enhanced_leaderboard.get_scores_by_board_size(size))
                count_text = self.fonts['small'].render(f"{count} scores", True, text_color)
                count_rect = count_text.get_rect(center=(button_rect.centerx, button_rect.bottom - 15))
                self.screen.blit(count_text, count_rect)
        
        # Instructions
        instruction = self.fonts['table_data'].render("Blue buttons have recorded scores | Gray buttons have no scores yet", 
                                                     True, self.colors['text_secondary'])
        instruction_rect = instruction.get_rect(center=(400, 500))
        self.screen.blit(instruction, instruction_rect)
        
        back_instruction = self.fonts['table_data'].render("Press ESC to go back", True, self.colors['text_secondary'])
        back_rect = back_instruction.get_rect(center=(400, 530))
        self.screen.blit(back_instruction, back_rect)
    
    def _handle_size_selection_click(self, mouse_pos: tuple, available_sizes: List[int]) -> Optional[int]:
        """Handle clicks on board size selection"""
        from config.config import BOARD_SIZES
        all_sizes = BOARD_SIZES
        
        cols = 3
        button_width = 150
        button_height = 60
        spacing = 20
        start_y = 200
        
        for i, size in enumerate(all_sizes):
            if size not in available_sizes:
                continue
                
            row = i // cols
            col = i % cols
            
            total_width = cols * button_width + (cols - 1) * spacing
            start_x = (800 - total_width) // 2
            
            x = start_x + col * (button_width + spacing)
            y = start_y + row * (button_height + spacing)
            
            button_rect = pygame.Rect(x, y, button_width, button_height)
            
            if button_rect.collidepoint(mouse_pos):
                return size
        
        return None
    
    def show_leaderboard(self, board_size: int):
        """Show the comprehensive leaderboard for selected board size"""
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption(f"ZIP Puzzle - Leaderboard ({board_size}x{board_size})")
        
        self.current_board_size = board_size
        self.leaderboard_data = enhanced_leaderboard.get_leaderboard_data(board_size)
        
        scroll_y = 0
        max_scroll = self._calculate_content_height() - self.screen_height + 100
        scroll_speed = 30
        
        running = True
        while running:
            self.clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_UP:
                        scroll_y = max(0, scroll_y - scroll_speed)
                    elif event.key == pygame.K_DOWN:
                        scroll_y = min(max_scroll, scroll_y + scroll_speed)
                elif event.type == pygame.MOUSEWHEEL:
                    scroll_y = max(0, min(max_scroll, scroll_y - event.y * scroll_speed))
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self._handle_leaderboard_click(event.pos):
                        running = False
            
            self._draw_leaderboard_screen(scroll_y)
            pygame.display.flip()
        
        pygame.quit()
    
    def _calculate_content_height(self) -> int:
        """Calculate total content height for scrolling"""
        base_height = 150  # Header
        section_height = 220  # Each section (header + table + spacing)
        sections = 6  # Overall, Human, ChatGPT, Claude, Gemini, Ollama
        return base_height + sections * section_height
    
    def _draw_leaderboard_screen(self, scroll_y: int):
        """Draw the main leaderboard screen"""
        self.screen.fill(self.colors['bg'])
        
        current_y = -scroll_y
        
        # Header
        current_y = self._draw_header(current_y)
        
        # Sections
        sections = [
            ("Overall Leaderboard", "overall", self.colors['header']),
            ("Human Players", "human", self.colors['success']),
            ("ChatGPT (OpenAI)", "openai", (255, 165, 0)),  # Orange
            ("Claude (Anthropic)", "claude", (138, 43, 226)),  # Purple  
            ("Gemini (Google)", "gemini", (66, 165, 245)),  # Blue
            ("Ollama (Local)", "ollama", (76, 175, 80))  # Green
        ]
        
        for title, key, color in sections:
            current_y = self._draw_section(title, self.leaderboard_data[key], current_y, color)
        
        # Scrollbar
        self._draw_scrollbar(scroll_y)
    
    def _draw_header(self, y: int) -> int:
        """Draw the leaderboard header"""
        if y > self.screen_height or y + 150 < 0:
            return y + 150
        
        # Background
        header_rect = pygame.Rect(0, y, self.screen_width, 150)
        pygame.draw.rect(self.screen, self.colors['card'], header_rect)
        
        # Title
        title = self.fonts['title'].render(f"Leaderboard - {self.current_board_size}x{self.current_board_size}", 
                                          True, self.colors['text_primary'])
        title_rect = title.get_rect(center=(self.screen_width // 2, y + 40))
        self.screen.blit(title, title_rect)
        
        # Stats
        total_scores = len(enhanced_leaderboard.get_scores_by_board_size(self.current_board_size))
        stats_text = self.fonts['table_data'].render(f"Total Scores: {total_scores}", 
                                                     True, self.colors['text_secondary'])
        stats_rect = stats_text.get_rect(center=(self.screen_width // 2, y + 80))
        self.screen.blit(stats_text, stats_rect)
        
        # Instructions
        instruction = self.fonts['small'].render("Use mouse wheel or arrow keys to scroll | ESC to close", 
                                                True, self.colors['text_secondary'])
        instruction_rect = instruction.get_rect(center=(self.screen_width // 2, y + 110))
        self.screen.blit(instruction, instruction_rect)
        
        # Border
        pygame.draw.line(self.screen, self.colors['border'], (0, y + 149), (self.screen_width, y + 149), 2)
        
        return y + 150
    
    def _draw_section(self, title: str, scores: List[EnhancedScore], y: int, color: tuple) -> int:
        """Draw a leaderboard section"""
        section_height = 220
        
        if y > self.screen_height or y + section_height < 0:
            return y + section_height
        
        # Section header
        header_rect = pygame.Rect(40, y + 20, self.screen_width - 80, 40)
        self.draw_rounded_rect(self.screen, header_rect, color, border_radius=8)
        
        header_text = self.fonts['section_header'].render(title, True, self.colors['header_text'])
        header_text_rect = header_text.get_rect(center=header_rect.center)
        self.screen.blit(header_text, header_text_rect)
        
        # Table
        table_y = y + 70
        self._draw_table(scores, table_y)
        
        return y + section_height
    
    def _draw_table(self, scores: List[EnhancedScore], y: int):
        """Draw a scores table"""
        if not scores:
            # No scores message
            no_scores = self.fonts['table_data'].render("No scores recorded yet", 
                                                       True, self.colors['text_secondary'])
            no_scores_rect = no_scores.get_rect(center=(self.screen_width // 2, y + 60))
            self.screen.blit(no_scores, no_scores_rect)
            return
        
        # Table dimensions
        table_rect = pygame.Rect(40, y, self.screen_width - 80, 130)
        self.draw_rounded_rect(self.screen, table_rect, self.colors['card'], border_radius=8, 
                              border_color=self.colors['border'], border_width=1)
        
        # Table header
        header_rect = pygame.Rect(40, y, self.screen_width - 80, 30)
        self.draw_rounded_rect(self.screen, header_rect, self.colors['table_header'], border_radius=8)
        
        # Column headers
        col_widths = [60, 250, 120, 100, 100, 120, 120]  # Rank, Player, Model, Time, Score, Efficiency, Accuracy
        col_x = 50
        
        headers = ["Rank", "Player", "Model", "Time", "Score", "Efficiency", "Accuracy"]
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            if col_x + width <= self.screen_width - 50:
                text = self.fonts['table_header'].render(header, True, self.colors['text_primary'])
                text_rect = pygame.Rect(col_x, y + 5, width, 20)
                self.screen.blit(text, (col_x + 5, y + 8))
                col_x += width
        
        # Table rows
        for i, score in enumerate(scores):
            if i >= 5:  # Max 5 entries per table
                break
            
            row_y = y + 30 + (i + 1) * 20
            row_rect = pygame.Rect(40, row_y, self.screen_width - 80, 20)
            
            # Alternating row colors
            if i % 2 == 1:
                pygame.draw.rect(self.screen, self.colors['table_row_alt'], row_rect)
            
            # Row data
            col_x = 50
            
            # Rank
            rank_text = self.fonts['table_data'].render(f"#{i+1}", True, self.colors['text_primary'])
            self.screen.blit(rank_text, (col_x + 5, row_y + 3))
            col_x += col_widths[0]
            
            # Player
            player_text = self.fonts['table_data'].render(score.display_name()[:25], True, self.colors['text_primary'])
            self.screen.blit(player_text, (col_x + 5, row_y + 3))
            col_x += col_widths[1]
            
            # Model
            model_text = score.model_name if score.model_name else "Human"
            model_display = self.fonts['table_data'].render(model_text[:15], True, self.colors['text_secondary'])
            self.screen.blit(model_display, (col_x + 5, row_y + 3))
            col_x += col_widths[2]
            
            # Time
            time_text = self.fonts['table_data'].render(f"{score.time_seconds}s", True, self.colors['text_primary'])
            self.screen.blit(time_text, (col_x + 5, row_y + 3))
            col_x += col_widths[3]
            
            # Score
            score_text = self.fonts['table_data'].render(f"{score.score():.1f}", True, self.colors['text_primary'])
            self.screen.blit(score_text, (col_x + 5, row_y + 3))
            col_x += col_widths[4]
            
            # Efficiency (for LLMs)
            if score.player_type != "human":
                eff_text = self.fonts['table_data'].render(f"{score.move_efficiency:.1%}", True, self.colors['text_secondary'])
                self.screen.blit(eff_text, (col_x + 5, row_y + 3))
            col_x += col_widths[5]
            
            # Accuracy (for LLMs)
            if score.player_type != "human":
                acc_text = self.fonts['table_data'].render(f"{score.path_accuracy:.1%}", True, self.colors['text_secondary'])
                self.screen.blit(acc_text, (col_x + 5, row_y + 3))
    
    def _draw_scrollbar(self, scroll_y: int):
        """Draw scrollbar"""
        max_scroll = self._calculate_content_height() - self.screen_height + 100
        if max_scroll <= 0:
            return
        
        # Scrollbar background
        scrollbar_rect = pygame.Rect(self.screen_width - 20, 0, 20, self.screen_height)
        pygame.draw.rect(self.screen, self.colors['border'], scrollbar_rect)
        
        # Scrollbar thumb
        thumb_height = max(30, int(self.screen_height * (self.screen_height / (max_scroll + self.screen_height))))
        thumb_y = int((scroll_y / max_scroll) * (self.screen_height - thumb_height))
        thumb_rect = pygame.Rect(self.screen_width - 18, thumb_y, 16, thumb_height)
        pygame.draw.rect(self.screen, self.colors['text_secondary'], thumb_rect, border_radius=8)
    
    def _handle_leaderboard_click(self, pos: tuple) -> bool:
        """Handle clicks in leaderboard (for future expansion)"""
        # Could add click handlers for sorting, filtering, etc.
        return False

# Convenience function
def show_enhanced_leaderboard():
    """Show the enhanced leaderboard with board size selection"""
    display = EnhancedLeaderboardDisplay()
    board_size = display.show_board_size_selection()
    
    if board_size:
        display.show_leaderboard(board_size)