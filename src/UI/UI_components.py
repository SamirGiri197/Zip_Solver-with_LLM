"""
Modern UI Components for ZIP Puzzle Game
Provides high-quality, anti-aliased UI elements with modern design
"""

import pygame
import math
from typing import Tuple, List, Optional, Callable
from enum import Enum


class ButtonState(Enum):
    NORMAL = "normal"
    HOVER = "hover"
    PRESSED = "pressed"
    DISABLED = "disabled"


class ModernButton:
    """High-quality button with hover effects, shadows, and modern styling"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                 font: pygame.font.Font, 
                 bg_color: Tuple[int, int, int] = (59, 130, 246),
                 hover_color: Tuple[int, int, int] = (37, 99, 235),
                 text_color: Tuple[int, int, int] = (255, 255, 255),
                 border_radius: int = 12,
                 shadow: bool = True,
                 callback: Optional[Callable] = None):
        
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_radius = border_radius
        self.shadow = shadow
        self.callback = callback
        self.state = ButtonState.NORMAL
        self.hover_animation = 0.0
        self.press_animation = 0.0
        
    def update(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update button state and animations"""
        is_hovering = self.rect.collidepoint(mouse_pos)
        
        if is_hovering:
            if mouse_pressed and self.state != ButtonState.PRESSED:
                self.state = ButtonState.PRESSED
                self.press_animation = 1.0
            elif not mouse_pressed and self.state == ButtonState.PRESSED:
                # Button was clicked
                if self.callback:
                    self.callback()
                self.state = ButtonState.HOVER
            elif not mouse_pressed:
                self.state = ButtonState.HOVER
        else:
            self.state = ButtonState.NORMAL
            
        # Animate hover effect
        target_hover = 1.0 if self.state in [ButtonState.HOVER, ButtonState.PRESSED] else 0.0
        self.hover_animation += (target_hover - self.hover_animation) * dt * 8.0
        self.hover_animation = max(0.0, min(1.0, self.hover_animation))
        
        # Animate press effect
        if self.state != ButtonState.PRESSED:
            self.press_animation *= 1.0 - dt * 12.0
            self.press_animation = max(0.0, self.press_animation)
    
    def draw(self, surface: pygame.Surface):
        """Draw the button with all effects"""
        # Calculate current colors based on animation
        current_bg = self._lerp_color(self.bg_color, self.hover_color, self.hover_animation)
        
        # Calculate position with press effect
        press_offset = int(self.press_animation * 2)
        draw_rect = pygame.Rect(
            self.rect.x + press_offset,
            self.rect.y + press_offset,
            self.rect.width,
            self.rect.height
        )
        
        # Draw shadow
        if self.shadow and press_offset < 2:
            shadow_rect = pygame.Rect(
                draw_rect.x + 3 - press_offset,
                draw_rect.y + 3 - press_offset,
                draw_rect.width,
                draw_rect.height
            )
            self._draw_rounded_rect(surface, shadow_rect, (0, 0, 0, 60), self.border_radius)
        
        # Draw button background
        self._draw_rounded_rect(surface, draw_rect, current_bg, self.border_radius)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=draw_rect.center)
        surface.blit(text_surface, text_rect)
    
    def _lerp_color(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
        """Linear interpolation between two colors"""
        return (
            int(color1[0] + (color2[0] - color1[0]) * t),
            int(color1[1] + (color2[1] - color1[1]) * t),
            int(color1[2] + (color2[2] - color1[2]) * t)
        )
    
    def _draw_rounded_rect(self, surface: pygame.Surface, rect: pygame.Rect, 
                          color: Tuple[int, int, int], border_radius: int):
        """Draw a rounded rectangle with anti-aliasing"""
        if len(color) == 4:  # RGBA
            # Create a temporary surface for alpha blending
            temp_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(temp_surface, color, (0, 0, rect.width, rect.height), border_radius=border_radius)
            surface.blit(temp_surface, rect.topleft)
        else:  # RGB
            pygame.draw.rect(surface, color, rect, border_radius=border_radius)


class ModernCard:
    """Modern card component with shadow and rounded corners"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 bg_color: Tuple[int, int, int] = (255, 255, 255),
                 border_radius: int = 16,
                 shadow: bool = True):
        
        self.rect = pygame.Rect(x, y, width, height)
        self.bg_color = bg_color
        self.border_radius = border_radius
        self.shadow = shadow
    
    def draw(self, surface: pygame.Surface):
        """Draw the card with shadow"""
        if self.shadow:
            # Draw shadow
            shadow_rect = pygame.Rect(
                self.rect.x + 4,
                self.rect.y + 4,
                self.rect.width,
                self.rect.height
            )
            self._draw_rounded_rect(surface, shadow_rect, (0, 0, 0, 40), self.border_radius)
        
        # Draw card background
        self._draw_rounded_rect(surface, self.rect, self.bg_color, self.border_radius)
    
    def _draw_rounded_rect(self, surface: pygame.Surface, rect: pygame.Rect, 
                          color: Tuple[int, int, int], border_radius: int):
        """Draw a rounded rectangle with alpha support"""
        if len(color) == 4:  # RGBA
            temp_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(temp_surface, color, (0, 0, rect.width, rect.height), border_radius=border_radius)
            surface.blit(temp_surface, rect.topleft)
        else:  # RGB
            pygame.draw.rect(surface, color, rect, border_radius=border_radius)


class GridLayout:
    """Helper class for creating grid-based layouts"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 rows: int, cols: int, padding: int = 10):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rows = rows
        self.cols = cols
        self.padding = padding
        
        self.cell_width = (width - padding * (cols + 1)) // cols
        self.cell_height = (height - padding * (rows + 1)) // rows
    
    def get_cell_rect(self, row: int, col: int) -> pygame.Rect:
        """Get the rectangle for a specific grid cell"""
        x = self.x + self.padding + col * (self.cell_width + self.padding)
        y = self.y + self.padding + row * (self.cell_height + self.padding)
        return pygame.Rect(x, y, self.cell_width, self.cell_height)


class AnimatedBackground:
    """Animated gradient background for modern look"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.time = 0.0
    
    def update(self, dt: float):
        """Update animation"""
        self.time += dt
    
    def draw(self, surface: pygame.Surface):
        """Draw animated background"""
        # Create gradient from top to bottom
        for y in range(self.height):
            progress = y / self.height
            wave = math.sin(self.time * 0.5 + progress * 2) * 0.1
            
            # Interpolate between two colors
            color1 = (245, 246, 248)  # Light gray
            color2 = (229, 231, 235)  # Slightly darker gray
            
            r = int(color1[0] + (color2[0] - color1[0]) * (progress + wave))
            g = int(color1[1] + (color2[1] - color1[1]) * (progress + wave))
            b = int(color1[2] + (color2[2] - color1[2]) * (progress + wave))
            
            pygame.draw.line(surface, (r, g, b), (0, y), (self.width, y))


def draw_text_with_shadow(surface: pygame.Surface, text: str, font: pygame.font.Font,
                         pos: Tuple[int, int], color: Tuple[int, int, int],
                         shadow_color: Tuple[int, int, int] = (0, 0, 0, 100),
                         shadow_offset: Tuple[int, int] = (2, 2)):
    """Draw text with a subtle shadow for better readability"""
    # Draw shadow
    shadow_surface = font.render(text, True, shadow_color[:3])
    if len(shadow_color) == 4:
        shadow_surface.set_alpha(shadow_color[3])
    surface.blit(shadow_surface, (pos[0] + shadow_offset[0], pos[1] + shadow_offset[1]))
    
    # Draw main text
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, pos)


def create_fade_surface(width: int, height: int, start_alpha: int = 0, end_alpha: int = 255) -> pygame.Surface:
    """Create a surface with vertical alpha fade effect"""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    for y in range(height):
        alpha = start_alpha + int((end_alpha - start_alpha) * (y / height))
        color = (0, 0, 0, alpha)
        pygame.draw.line(surface, color, (0, y), (width, y))
    
    return surface