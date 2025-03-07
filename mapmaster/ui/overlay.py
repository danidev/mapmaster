"""
Overlay module for MapMaster UI.
Handles UI overlays like command help, color selection, and notifications.
"""

import pygame
import time
import os

class OverlayManager:
    """
    Manages UI overlays for the MapMaster application.
    This includes help text, color selectors, and temporary notifications.
    """
    
    def __init__(self, screen):
        """Initialize the overlay manager."""
        self.screen = screen
        self.font = pygame.font.SysFont('Arial', 18)
        self.heading_font = pygame.font.SysFont('Arial', 22, bold=True)
        
        # State variables
        self.show_help = False
        self.show_color_selector = False
        self.show_token_selector = False
        self.show_filename = True
        self.notifications = []  # List of (text, expiry_time) tuples
        
        # Colors
        self.overlay_bg_color = (30, 30, 30, 180)  # Dark semi-transparent background
        self.text_color = (255, 255, 255)  # White text
        self.highlight_color = (255, 255, 0)  # Yellow for highlights
        self.selected_bg_color = (60, 60, 180, 200)  # Blue-ish for selections
        
        # Command help text
        self.help_text = []
        
        # Currently selected color and brush size
        self.current_color = None
        self.current_brush_size = None
        self.colors = {}
        self.brush_sizes = {}
        
    def set_help_text(self, help_text):
        """Set the help text to display when help overlay is shown."""
        self.help_text = help_text if isinstance(help_text, list) else [help_text]
    
    def set_colors(self, colors):
        """Set available annotation colors."""
        self.colors = colors
        if not self.current_color and colors:
            self.current_color = list(colors.keys())[0]
    
    def set_brush_sizes(self, brush_sizes):
        """Set available brush sizes."""
        self.brush_sizes = brush_sizes
        if not self.current_brush_size and brush_sizes:
            self.current_brush_size = list(brush_sizes.keys())[0]
    
    def toggle_help(self):
        """Toggle the help overlay visibility."""
        self.show_help = not self.show_help
        self.show_color_selector = False  # Hide other overlays
        self.show_token_selector = False
    
    def toggle_color_selector(self):
        """Toggle the color selector overlay visibility."""
        self.show_color_selector = not self.show_color_selector
        self.show_help = False  # Hide other overlays
        self.show_token_selector = False
    
    def toggle_token_selector(self):
        """Toggle the token selector overlay visibility."""
        self.show_token_selector = not self.show_token_selector
        self.show_help = False  # Hide other overlays
        self.show_color_selector = False
    
    def toggle_filename(self):
        """Toggle whether to show the current filename."""
        self.show_filename = not self.show_filename
    
    def add_notification(self, text, duration=3.0):
        """Add a temporary notification to display."""
        self.notifications.append((text, time.time() + duration))
    
    def select_color(self, color_name):
        """Select a color by name."""
        if color_name in self.colors:
            self.current_color = color_name
            self.add_notification(f"Selected color: {color_name}")
    
    def select_brush_size(self, size_name):
        """Select a brush size by name."""
        if size_name in self.brush_sizes:
            self.current_brush_size = size_name
            self.add_notification(f"Selected brush: {size_name}")
    
    def get_current_color(self):
        """Get the current selected color value."""
        return self.colors.get(self.current_color, (255, 255, 255))
    
    def get_current_brush_size(self):
        """Get the current selected brush size value."""
        return self.brush_sizes.get(self.current_brush_size, 1)
    
    def _draw_text_block(self, text_lines, x, y, width=None, height=None, max_height=None):
        """Draw a block of text with a semi-transparent background."""
        if not text_lines:
            return y
        
        # Calculate text block dimensions if not provided
        if width is None or height is None:
            line_heights = [self.font.size(line)[1] for line in text_lines]
            text_width = max(self.font.size(line)[0] for line in text_lines)
            text_height = sum(line_heights)
            
            width = width or text_width + 20  # Add padding
            height = height or text_height + 20  # Add padding
        
        # Check if we need to cap the height
        if max_height and height > max_height:
            height = max_height
        
        # Create a transparent surface for the background
        bg_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        bg_surface.fill(self.overlay_bg_color)
        self.screen.blit(bg_surface, (x, y))
        
        # Draw text
        text_y = y + 10  # Start with some padding
        for line in text_lines:
            if line.startswith("==") and line.endswith("=="):
                # Section heading - use heading font
                text_surface = self.heading_font.render(line.strip("="), True, self.highlight_color)
            else:
                # Normal text
                text_surface = self.font.render(line, True, self.text_color)
                
            self.screen.blit(text_surface, (x + 10, text_y))
            text_y += text_surface.get_height() + 2
            
            # Check if we've exceeded the max height
            if max_height and (text_y - y) > max_height - 10:
                break
        
        return text_y + 10  # Return the Y position after the text block
    
    def draw_help_overlay(self):
        """Draw the help overlay."""
        if not self.show_help or not self.help_text:
            return
            
        screen_width, screen_height = self.screen.get_size()
        overlay_width = min(400, screen_width - 40)
        
        # Center the overlay
        x = (screen_width - overlay_width) // 2
        y = 40
        
        # Draw the help text
        self._draw_text_block(self.help_text, x, y, width=overlay_width, max_height=screen_height - 80)
    
    def draw_color_selector(self):
        """Draw the color and brush size selector overlay."""
        if not self.show_color_selector:
            return
        
        screen_width = self.screen.get_size()[0]
        
        # Prepare content
        title = ["== Color and Brush Selection ==", ""]
        color_lines = [f"Color: {name}" for name in self.colors.keys()]
        brush_lines = ["", "== Brush Size ==", ""] + [f"Size: {name}" for name in self.brush_sizes.keys()]
        
        all_lines = title + color_lines + brush_lines
        
        # Calculate dimensions
        overlay_width = 250
        x = (screen_width - overlay_width) // 2
        y = 40
        
        # Draw background
        self._draw_text_block(all_lines, x, y, width=overlay_width)
        
        # Draw color swatches
        swatch_y = y + 50  # Position after title
        for i, (name, color) in enumerate(self.colors.items()):
            # Draw color swatch
            swatch_rect = pygame.Rect(x + 160, swatch_y + i * 25, 30, 20)
            pygame.draw.rect(self.screen, color, swatch_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), swatch_rect, 1)  # White border
            
            # Highlight selected color
            if name == self.current_color:
                highlight_rect = pygame.Rect(x + 10, swatch_y + i * 25 - 2, overlay_width - 20, 24)
                pygame.draw.rect(self.screen, self.selected_bg_color, highlight_rect)
                text = self.font.render(f"Color: {name}", True, self.highlight_color)
                self.screen.blit(text, (x + 20, swatch_y + i * 25))
        
        # Draw brush size indicators
        brush_y = swatch_y + len(self.colors) * 25 + 50  # Position after colors and sub-header
        for i, (name, size) in enumerate(self.brush_sizes.items()):
            # Draw brush size indicator
            center_x = x + 175
            center_y = brush_y + i * 25 + 10
            pygame.draw.circle(self.screen, (255, 255, 255), (center_x, center_y), size // 2)
            
            # Highlight selected brush size
            if name == self.current_brush_size:
                highlight_rect = pygame.Rect(x + 10, brush_y + i * 25 - 2, overlay_width - 20, 24)
                pygame.draw.rect(self.screen, self.selected_bg_color, highlight_rect)
                text = self.font.render(f"Size: {name}", True, self.highlight_color)
                self.screen.blit(text, (x + 20, brush_y + i * 25))

    def draw_token_selector(self):
        """Draw the token selector overlay."""
        if not self.show_token_selector or not hasattr(self, 'token_manager'):
            return
            
        screen_width, screen_height = self.screen.get_size()
        
        # Get available tokens
        available_tokens = self.token_manager.available_tokens
        
        if not available_tokens:
            self.show_token_selector = False
            return
            
        # Store click position if not already set
        if not hasattr(self, 'token_click_pos'):
            self.token_click_pos = None
        
        # Prepare content
        title = ["== Select Token ==", ""]
        
        # Calculate dimensions
        overlay_width = 300
        token_display_size = 50
        padding = 10
        tokens_per_row = 4
        
        # Calculate height based on number of tokens plus space for close button
        num_rows = (len(available_tokens) + tokens_per_row - 1) // tokens_per_row
        tokens_height = (token_display_size + padding) * num_rows + token_display_size // 2
        
        # Add extra space for close button
        overlay_height = 60 + tokens_height + 40  # 60px for title, 40px for close button area
        
        # Center the overlay
        x = (screen_width - overlay_width) // 2
        y = (screen_height - overlay_height) // 2
        
        # Draw background
        bg_surface = pygame.Surface((overlay_width, overlay_height), pygame.SRCALPHA)
        bg_surface.fill(self.overlay_bg_color)
        self.screen.blit(bg_surface, (x, y))
        
        # Draw title
        title_surface = self.heading_font.render(title[0], True, self.highlight_color)
        self.screen.blit(title_surface, (x + (overlay_width - title_surface.get_width()) // 2, y + 10))
        
        # Draw token grid
        token_y = y + 50  # Start after title
        token_x = x + padding
        
        for i, token_path in enumerate(available_tokens):
            # Calculate position in grid
            row = i // tokens_per_row
            col = i % tokens_per_row
            
            token_pos_x = token_x + col * (token_display_size + padding)
            token_pos_y = token_y + row * (token_display_size + padding)
            
            # Extract token name for display
            token_name = os.path.splitext(os.path.basename(token_path))[0]
            
            # Try to load and display token image
            try:
                token_img = pygame.image.load(token_path)
                token_img = pygame.transform.smoothscale(token_img, (token_display_size, token_display_size))
                
                # Create circular mask
                mask = pygame.Surface((token_display_size, token_display_size), pygame.SRCALPHA)
                pygame.draw.circle(mask, (255, 255, 255, 255), 
                                 (token_display_size // 2, token_display_size // 2), 
                                 token_display_size // 2)
                
                # Apply mask
                circular_img = pygame.Surface((token_display_size, token_display_size), pygame.SRCALPHA)
                circular_img.blit(token_img, (0, 0))
                circular_img.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                
                self.screen.blit(circular_img, (token_pos_x, token_pos_y))
                
                # Draw border
                pygame.draw.circle(self.screen, (200, 200, 200), 
                                 (token_pos_x + token_display_size // 2, token_pos_y + token_display_size // 2),
                                 token_display_size // 2, 1)
            except:
                # If image loading fails, draw a placeholder circular token
                pygame.draw.circle(self.screen, (150, 50, 50),
                                 (token_pos_x + token_display_size // 2, token_pos_y + token_display_size // 2),
                                 token_display_size // 2)
                pygame.draw.circle(self.screen, (255, 255, 255),
                                 (token_pos_x + token_display_size // 2, token_pos_y + token_display_size // 2),
                                 token_display_size // 2, 1)
            
            # Draw token name below the image
            name_surface = self.font.render(token_name[:10], True, self.text_color)
            name_x = token_pos_x + (token_display_size - name_surface.get_width()) // 2
            self.screen.blit(name_surface, (name_x, token_pos_y + token_display_size + 2))
        
        # Calculate position for close button (below all tokens)
        close_button_y = y + 60 + tokens_height
        
        # Draw close button
        close_text = self.font.render("Close", True, self.text_color)
        close_width = close_text.get_width() + 20
        close_rect = pygame.Rect(
            x + (overlay_width - close_width) // 2, 
            close_button_y,
            close_width, 25
        )
        pygame.draw.rect(self.screen, (80, 80, 80), close_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), close_rect, 1)
        self.screen.blit(close_text, (close_rect.x + 10, close_rect.y + 5))
    
    def draw_notifications(self):
        """Draw any active notifications."""
        current_time = time.time()
        active_notifications = []
        
        for text, expiry_time in self.notifications:
            if current_time < expiry_time:
                active_notifications.append((text, expiry_time))
        
        # Update the notifications list to only include active ones
        self.notifications = active_notifications
        
        if not active_notifications:
            return
            
        # Draw notifications at the bottom of the screen
        screen_width, screen_height = self.screen.get_size()
        notification_y = screen_height - 40
        
        for text, _ in reversed(active_notifications[-3:]):  # Show at most 3 notifications
            text_surface = self.font.render(text, True, self.text_color)
            notification_width = text_surface.get_width() + 20
            
            # Draw background
            bg_surface = pygame.Surface((notification_width, 30), pygame.SRCALPHA)
            bg_surface.fill(self.overlay_bg_color)
            self.screen.blit(bg_surface, ((screen_width - notification_width) // 2, notification_y - 30))
            
            # Draw text
            self.screen.blit(text_surface, ((screen_width - text_surface.get_width()) // 2, notification_y - 25))
            notification_y -= 35
    
    def draw_filename(self, filename):
        """Draw the current filename if enabled."""
        if not self.show_filename or not filename:
            return
            
        screen_width, screen_height = self.screen.get_size()
        
        # Extract the base filename without path
        base_filename = filename.split('/')[-1]
        
        text_surface = self.font.render(base_filename, True, self.text_color)
        text_width = text_surface.get_width() + 20
        
        # Draw background
        bg_surface = pygame.Surface((text_width, 30), pygame.SRCALPHA)
        bg_surface.fill(self.overlay_bg_color)
        self.screen.blit(bg_surface, (10, 10))
        
        # Draw text
        self.screen.blit(text_surface, (20, 15))
    
    def handle_click(self, pos):
        """Handle mouse clicks on overlays and return True if handled."""
        x, y = pos
        
        # Handle color selector clicks
        if self.show_color_selector:
            # Calculate positions (must match those in draw_color_selector)
            overlay_width = 250
            screen_width = self.screen.get_size()[0]
            selector_x = (screen_width - overlay_width) // 2
            selector_y = 40
            
            swatch_y = selector_y + 50
            # Check color clicks
            for i, name in enumerate(self.colors.keys()):
                color_rect = pygame.Rect(selector_x + 10, swatch_y + i * 25 - 2, overlay_width - 20, 24)
                if color_rect.collidepoint(x, y):
                    self.select_color(name)
                    return True
            
            # Check brush size clicks
            brush_y = swatch_y + len(self.colors) * 25 + 50
            for i, name in enumerate(self.brush_sizes.keys()):
                brush_rect = pygame.Rect(selector_x + 10, brush_y + i * 25 - 2, overlay_width - 20, 24)
                if brush_rect.collidepoint(x, y):
                    self.select_brush_size(name)
                    return True
                    
            # Click outside closes the selector
            selector_rect = pygame.Rect(selector_x, selector_y, overlay_width, 
                                       brush_y + len(self.brush_sizes) * 25 + 20 - selector_y)
            if not selector_rect.collidepoint(x, y):
                self.show_color_selector = False
                return True
            
            return True  # Handled click in the color selector area
        
        # Handle token selector clicks
        if self.show_token_selector and hasattr(self, 'token_manager'):
            # Calculate positions (must match those in draw_token_selector)
            screen_width, screen_height = self.screen.get_size()
            overlay_width = 300
            token_display_size = 50
            padding = 10
            tokens_per_row = 4
            
            available_tokens = self.token_manager.available_tokens
            num_rows = (len(available_tokens) + tokens_per_row - 1) // tokens_per_row
            tokens_height = (token_display_size + padding) * num_rows + token_display_size // 2
            
            # Add extra space for close button
            overlay_height = 60 + tokens_height + 40
            
            # Overlay position
            overlay_x = (screen_width - overlay_width) // 2
            overlay_y = (screen_height - overlay_height) // 2
            
            # Close button click?
            close_button_y = overlay_y + 60 + tokens_height
            close_width = 80
            close_rect = pygame.Rect(
                overlay_x + (overlay_width - close_width) // 2, 
                close_button_y,
                close_width, 25
            )
            if close_rect.collidepoint(x, y):
                self.show_token_selector = False
                return True
            
            # Check if clicked on a token
            token_y = overlay_y + 50
            token_x = overlay_x + padding
            
            for i, token_path in enumerate(available_tokens):
                # Calculate position in grid
                row = i // tokens_per_row
                col = i % tokens_per_row
                
                token_pos_x = token_x + col * (token_display_size + padding)
                token_pos_y = token_y + row * (token_display_size + padding)
                
                # Using a circular hit detection
                center_x = token_pos_x + token_display_size // 2
                center_y = token_pos_y + token_display_size // 2
                dist_squared = (x - center_x)**2 + (y - center_y)**2
                
                if dist_squared <= (token_display_size // 2)**2:
                    # Selected this token - place it at the stored click position
                    placement_pos = self.token_click_pos if self.token_click_pos else pygame.mouse.get_pos()
                    self.token_manager.add_token(token_path, placement_pos)
                    self.add_notification(f"Added token: {os.path.basename(token_path)}")
                    self.show_token_selector = False
                    return True
            
            # Click outside closes the selector
            overlay_rect = pygame.Rect(overlay_x, overlay_y, overlay_width, overlay_height)
            if not overlay_rect.collidepoint(x, y):
                self.show_token_selector = False
                return True
            
            return True  # Handled click in the token selector area
            
        # Help overlay consumes clicks while visible
        if self.show_help:
            self.show_help = False
            return True
            
        return False  # Click not handled by overlays

    def draw(self, current_filename=None):
        """Draw all active overlays."""
        self.draw_help_overlay()
        self.draw_token_selector()
        self.draw_notifications()
        
        if current_filename:
            self.draw_filename(current_filename)