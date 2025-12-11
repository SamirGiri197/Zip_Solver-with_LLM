"""
Improved Main Menu for ZIP Puzzle Game
"""

import pygame
import sys
from typing import Optional, Tuple, List
from enum import Enum
from config.config import BOARD_SIZES
from config.llm_config import LLM_PROVIDERS

# Import the new display function
from leaderboard.leaderboard_display import show_enhanced_leaderboard

class MenuState(Enum):
    MAIN_MENU = "main_menu"
    HUMAN_BOARD_SELECT = "human_board_select"
    LLM_BOARD_SELECT = "llm_board_select"
    LLM_PROVIDER_SELECT = "llm_provider_select"

class ImprovedMenu:
    """Modern, high-quality menu system for ZIP Puzzle"""
    
    def __init__(self):
        pygame.init()
        self.screen_width = getattr(sys.modules.get('config.config'), 'MENU_WIDTH', 1000)
        self.screen_height = getattr(sys.modules.get('config.config'), 'MENU_HEIGHT', 700)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("ZIP Puzzle - Enhanced Edition")
        
        self.setup_fonts()
        self.clock = pygame.time.Clock()
        self.buttons = []
        
        import os
        if os.environ.get('ZIP_SHOW_BOARD_SELECTION'):
            del os.environ['ZIP_SHOW_BOARD_SELECTION']
            self.current_state = MenuState.HUMAN_BOARD_SELECT  # Default to human mode
        else:
            self.current_state = MenuState.MAIN_MENU
        self.selected_board_size: Optional[int] = None
        self.selected_llm_provider: Optional[str] = None
        self.game_result: Optional[Tuple[int, str]] = None
        
        # Mouse state
        self.mouse_pos = (0, 0)
        self.mouse_pressed = False
        self.prev_mouse_pressed = False
        self.click_consumed = False
        self.state_transition_time = 0
        self.transition_delay = 200

    def setup_fonts(self):
        font_names = ['Segoe UI', 'Arial', 'Liberation Sans']
        self.fonts = {}
        for font_name in font_names:
            try:
                self.fonts['title'] = pygame.font.SysFont(font_name, 40, bold=True)
                self.fonts['subtitle'] = pygame.font.SysFont(font_name, 24)
                self.fonts['button'] = pygame.font.SysFont(font_name, 20, bold=True)
                self.fonts['small'] = pygame.font.SysFont(font_name, 16)
                break
            except:
                continue
        if 'title' not in self.fonts:
            self.fonts = {
                'title': pygame.font.Font(None, 40),
                'subtitle': pygame.font.Font(None, 24),
                'button': pygame.font.Font(None, 20),
                'small': pygame.font.Font(None, 16)
            }
    
    def is_click_allowed(self) -> bool:
        return (pygame.time.get_ticks() - self.state_transition_time) > self.transition_delay
    
    def consume_click(self):
        self.click_consumed = True
    
    def is_fresh_click(self) -> bool:
        return (self.mouse_pressed and not self.prev_mouse_pressed and 
                not self.click_consumed and self.is_click_allowed())
    
    def create_main_menu_buttons(self):
        self.buttons.clear()
        button_width, button_height, spacing = 320, 80, 20
        start_y = (self.screen_height - (4 * button_height + 3 * spacing)) // 2
        center_x = self.screen_width // 2 - button_width // 2
        
        colors = {
            'play_human': ((34, 197, 94), (22, 163, 74)),
            'play_llm': ((59, 130, 246), (37, 99, 235)),
            'leaderboard': ((168, 85, 247), (124, 58, 237)),
            'exit': ((239, 68, 68), (220, 38, 38))
        }
        
        configs = [
            ("Play as Human", lambda: self.transition_to_state(MenuState.HUMAN_BOARD_SELECT), colors['play_human']),
            ("Play by LLM", lambda: self.transition_to_state(MenuState.LLM_BOARD_SELECT), colors['play_llm']),
            ("Leaderboard", self.launch_leaderboard, colors['leaderboard']),
            ("Exit", self.quit_game, colors['exit'])
        ]
        
        for i, (text, callback, (bg, hover)) in enumerate(configs):
            y = start_y + i * (button_height + spacing)
            self.buttons.append(self.create_simple_button(center_x, y, button_width, button_height, text, callback, bg))

    def create_simple_button(self, x, y, width, height, text, callback, color):
        class SimpleButton:
            def __init__(self, x, y, width, height, text, callback, color):
                self.rect = pygame.Rect(x, y, width, height)
                self.text = text
                self.callback = callback
                self.color = color
                self.hover_color = tuple(min(255, c + 30) for c in color)
                self.is_hovered = False
            
            def update(self, mouse_pos):
                self.is_hovered = self.rect.collidepoint(mouse_pos)
            
            def draw(self, surface, font):
                c = self.hover_color if self.is_hovered else self.color
                pygame.draw.rect(surface, c, self.rect, border_radius=8)
                txt = font.render(self.text, True, (255,255,255))
                surface.blit(txt, txt.get_rect(center=self.rect.center))
        
        return SimpleButton(x, y, width, height, text, callback, color)

    def launch_leaderboard(self):
        """Switch to leaderboard display"""
        self.consume_click()
        # This function handles its own loop
        show_enhanced_leaderboard(self.screen)
        # When it returns, we are back in main menu loop
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.create_main_menu_buttons()

    def create_board_size_buttons(self):
        self.buttons.clear()
        cols, w, h, gap = 2, 200, 60, 20
        rows = (len(BOARD_SIZES) + 1) // 2
        grid_w = cols * w + (cols-1)*gap
        grid_h = rows * h + (rows-1)*gap
        start_x = (self.screen_width - grid_w) // 2
        start_y = (self.screen_height - grid_h) // 2
        
        for i, size in enumerate(BOARD_SIZES):
            r, c = i // cols, i % cols
            x = start_x + c*(w+gap)
            y = start_y + r*(h+gap)
            color = ((59, 130, 246), (37, 99, 235)) # Simple blue
            cb = lambda s=size: self.select_board_size(s)
            self.buttons.append(self.create_simple_button(x, y, w, h, f"{size}x{size}", cb, color[0]))
            
        # Back button
        self.buttons.append(self.create_simple_button(
            (self.screen_width-150)//2, start_y + grid_h + 40, 150, 50, "< Back", 
            lambda: self.transition_to_state(MenuState.MAIN_MENU), (107, 114, 128)
        ))

    def create_llm_provider_buttons(self):
        self.buttons.clear()
        providers = [(n, c) for n, c in LLM_PROVIDERS.items() if c.get("enabled")]
        if not providers: return
        
        cols, w, h, gap = 2, 280, 90, 20
        rows = (len(providers)+1)//2
        start_x = (self.screen_width - (cols*w+(cols-1)*gap)) // 2
        start_y = (self.screen_height - (rows*h+(rows-1)*gap)) // 2 - 40
        
        for i, (name, config) in enumerate(providers):
            r, c = i // cols, i % cols
            x = start_x + c*(w+gap)
            y = start_y + r*(h+gap)
            
            dname = config.get('name', name)
            model = config.get('model', '')[:22]
            text = f"{dname}" # Simple text for simple button
            
            color = ((168, 85, 247), (124, 58, 237))
            cb = lambda p=name: self.select_llm_provider(p)
            self.buttons.append(self.create_simple_button(x, y, w, h, text, cb, color[0]))
            
        # Back
        self.buttons.append(self.create_simple_button(
            (self.screen_width-150)//2, start_y + (rows*h+(rows-1)*gap) + 40, 150, 50, "< Back", 
            lambda: self.transition_to_state(MenuState.LLM_BOARD_SELECT), (107, 114, 128)
        ))

    def transition_to_state(self, new_state: MenuState):
        self.consume_click()
        self.state_transition_time = pygame.time.get_ticks()
        self.current_state = new_state
        
        if new_state == MenuState.MAIN_MENU:
            self.selected_board_size = None
            self.create_main_menu_buttons()
        elif new_state in [MenuState.HUMAN_BOARD_SELECT, MenuState.LLM_BOARD_SELECT]:
            self.create_board_size_buttons()
        elif new_state == MenuState.LLM_PROVIDER_SELECT:
            self.create_llm_provider_buttons()

    def select_board_size(self, size: int):
        if not self.is_click_allowed(): return
        self.consume_click()
        self.selected_board_size = size
        if self.current_state == MenuState.HUMAN_BOARD_SELECT:
            self.game_result = (size, "human")
        else:
            self.transition_to_state(MenuState.LLM_PROVIDER_SELECT)

    def select_llm_provider(self, provider: str):
        if not self.is_click_allowed(): return
        self.consume_click()
        self.game_result = (self.selected_board_size, provider)

    def quit_game(self):
        pygame.quit()
        sys.exit(0)

    def draw(self):
        self.screen.fill((245, 246, 248))
        
        # Title
        ttext = "ZIP Puzzle"
        if self.current_state == MenuState.HUMAN_BOARD_SELECT: ttext = "Select Size (Human)"
        elif self.current_state == MenuState.LLM_BOARD_SELECT: ttext = "Select Size (LLM)"
        elif self.current_state == MenuState.LLM_PROVIDER_SELECT: ttext = "Select Provider"
        
        title = self.fonts['title'].render(ttext, True, (17, 24, 39))
        self.screen.blit(title, title.get_rect(center=(self.screen_width//2, 80)))
        
        for b in self.buttons:
            b.draw(self.screen, self.fonts['button'])

    def run(self) -> Tuple[Optional[int], Optional[str]]:
        if self.current_state == MenuState.MAIN_MENU:
            self.create_main_menu_buttons()
        elif self.current_state == MenuState.HUMAN_BOARD_SELECT:
            self.create_board_size_buttons()
        elif self.current_state == MenuState.LLM_BOARD_SELECT:
            self.create_board_size_buttons()
        elif self.current_state == MenuState.LLM_PROVIDER_SELECT:
            self.create_llm_provider_buttons()
        while True:
            self.clock.tick(60)
            
            self.prev_mouse_pressed = self.mouse_pressed
            self.mouse_pos = pygame.mouse.get_pos()
            self.mouse_pressed = pygame.mouse.get_pressed()[0]
            if not self.mouse_pressed: self.click_consumed = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.quit_game()
            
            # Button hover updates
            for b in self.buttons: b.update(self.mouse_pos)
            
            # Clicks
            if self.is_fresh_click():
                for b in self.buttons:
                    if b.rect.collidepoint(self.mouse_pos):
                        b.callback()
                        break
            
            if self.game_result:
                pygame.quit()
                return self.game_result
            
            self.draw()
            pygame.display.flip()

def show_modern_menu() -> Tuple[Optional[int], Optional[str]]:
    menu = ImprovedMenu()
    try:
        return menu.run()
    except Exception as e:
        print(f"Menu Error: {e}")
        return None, None