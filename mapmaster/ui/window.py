import pygame
import sys
from pygame.locals import *

class GameWindow:
    """Manages the Pygame window and input processing."""
    
    def __init__(self, config):
        self.config = config
        self.width = config.get("window_width", 1280)
        self.height = config.get("window_height", 720)
        self.fullscreen = config.get("fullscreen", False)
        
        # Initialize pygame
        pygame.init()
        pygame.font.init()
        
        # Set up display
        self.create_window()
        
        # Set up clock
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # Input state
        self.mouse_pos = (0, 0)
        self.mouse_buttons = (False, False, False)
        self.last_mouse_pos = None
        self.drawing = False
        
        # Event callbacks
        self.event_handlers = {
            QUIT: lambda event: self.quit(),
            KEYDOWN: self.handle_keydown,
            MOUSEBUTTONDOWN: self.handle_mousedown,
            MOUSEBUTTONUP: self.handle_mouseup,
            MOUSEMOTION: self.handle_mousemotion
        }
        
        # Custom event handlers for specific keys and mouse buttons
        self.key_handlers = {}
        self.mouse_handlers = {
            "down": {},
            "up": {},
            "motion": None  # Single handler for motion
        }
        
    def create_window(self):
        """Create or recreate the game window with current settings."""
        flags = pygame.DOUBLEBUF
        if self.fullscreen:
            flags |= pygame.FULLSCREEN
        
        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption("MapMaster")
        
        # Black background
        self.screen.fill((0, 0, 0))
        pygame.display.flip()
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.fullscreen = not self.fullscreen
        self.config.set("fullscreen", self.fullscreen)
        self.create_window()
        
    def set_title(self, title):
        """Set window title."""
        pygame.display.set_caption(title)
        
    def register_key_handler(self, key, handler):
        """Register a handler for a specific key."""
        self.key_handlers[key] = handler
        
    def register_mouse_handler(self, event_type, button, handler):
        """Register a handler for a mouse event.
        
        event_type: 'down', 'up', or 'motion'
        button: 1 for left, 2 for middle, 3 for right, or None for motion
        handler: function to call
        """
        if event_type == 'motion':
            self.mouse_handlers['motion'] = handler
        else:
            self.mouse_handlers[event_type][button] = handler
    
    def handle_keydown(self, event):
        """Handle key down events."""
        if event.key == K_ESCAPE:
            self.quit()
        elif event.key == K_F11:
            self.toggle_fullscreen()
        elif event.key in self.key_handlers:
            return self.key_handlers[event.key](event)
    
    def handle_mousedown(self, event):
        """Handle mouse button down events."""
        self.mouse_buttons = pygame.mouse.get_pressed()
        if event.button in self.mouse_handlers["down"]:
            return self.mouse_handlers["down"][event.button](event)
    
    def handle_mouseup(self, event):
        """Handle mouse button up events."""
        self.mouse_buttons = pygame.mouse.get_pressed()
        if event.button in self.mouse_handlers["up"]:
            return self.mouse_handlers["up"][event.button](event)
    
    def handle_mousemotion(self, event):
        """Handle mouse motion events."""
        self.mouse_pos = event.pos
        
        if self.drawing:
            if self.last_mouse_pos:
                if self.mouse_handlers["motion"]:
                    self.mouse_handlers["motion"](event, self.last_mouse_pos)
            self.last_mouse_pos = event.pos
        
    def process_events(self):
        """Process all pending events."""
        for event in pygame.event.get():
            if event.type in self.event_handlers:
                self.event_handlers[event.type](event)
    
    def clear_screen(self):
        """Clear the screen to black."""
        self.screen.fill((0, 0, 0))
    
    def update_display(self):
        """Update the display."""
        pygame.display.flip()
        self.clock.tick(self.fps)
    
    def quit(self):
        """Clean up and exit."""
        pygame.quit()
        sys.exit()
    
    def get_surface(self):
        """Get the screen surface."""
        return self.screen
    
    def get_size(self):
        """Get the screen size."""
        return self.screen.get_size()
        
    def start_drawing(self):
        """Start tracking mouse for drawing."""
        self.drawing = True
        self.last_mouse_pos = self.mouse_pos
        
    def stop_drawing(self):
        """Stop tracking mouse for drawing."""
        self.drawing = False
        self.last_mouse_pos = None