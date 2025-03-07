"""
Token management module for MapMaster.
Handles character and monster tokens on the battlefield.
"""

import os
import pygame
import json
from ..utils.image import load_image, get_image_files

class Token:
    """
    Represents a game token that can be placed on the map.
    """
    
    def __init__(self, token_id, image_path, position, size=None, name=""):
        """Initialize a new token."""
        self.token_id = token_id
        self.image_path = image_path
        self.position = position
        self.original_image = load_image(image_path)
        self.size = size if size else 50  # Default to 50 if no size given
        self.name = name or os.path.splitext(os.path.basename(image_path))[0]
        self.selected = False
        self.visible = True
        self.drag_offset = (0, 0)
        self.dragging = False  # Initialize dragging state
        
        # Create scaled and circular image
        self.create_circular_image()
    
    def create_circular_image(self):
        """Create a circular token image."""
        if not self.original_image:
            # Create a fallback image if loading fails
            self.image = self.create_fallback_image(self.size)
            return
            
        # Create a surface for the circular token
        size = self.size
        circular_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Scale original image to size
        scaled_image = pygame.transform.smoothscale(self.original_image, (size, size))
        
        # Create a circle mask
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (size // 2, size // 2), size // 2)
        
        # Apply the circular mask to the image
        # First blit the scaled image, then apply the mask
        circular_surface.blit(scaled_image, (0, 0))
        circular_surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Add a border to the token
        border_color = (0, 0, 0)  # Black border for non-selected tokens
        pygame.draw.circle(circular_surface, border_color, (size // 2, size // 2), size // 2, 2)
        
        self.image = circular_surface
    
    def resize(self, size):
        """Resize the token to match the grid size."""
        if size <= 0:
            return self
            
        self.size = size
        self.create_circular_image()  # Recreate circular image at new size
        return self
        
    def create_fallback_image(self, size):
        """Create a fallback image if loading the original fails."""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))  # Transparent background
        
        # Draw a simple colored circle
        color = (255, 0, 0)  # Red
        pygame.draw.circle(surface, color, (size // 2, size // 2), size // 2)
        pygame.draw.circle(surface, (255, 255, 255), (size // 2, size // 2), size // 2, 2)  # White outline
        
        return surface
    
    def set_position(self, position):
        """Set the token position (center point)."""
        self.position = position
    
    def set_size(self, size):
        """Set the token size and update image."""
        self.size = max(10, min(200, size))  # Clamp between 10 and 200
        self.resize(self.size)
    
    def set_name(self, name):
        """Set the token name."""
        self.name = name
    
    def toggle_visibility(self):
        """Toggle token visibility."""
        self.visible = not self.visible
        return self.visible
    
    def contains_point(self, point):
        """Check if a point is within this circular token."""
        if not self.visible or not self.image:
            return False
            
        # Calculate distance from token center to point
        dx = self.position[0] - point[0]
        dy = self.position[1] - point[1]
        distance_squared = dx*dx + dy*dy
        
        # Check if distance is less than radius
        radius = self.size // 2
        return distance_squared <= radius*radius
    
    def start_drag(self, mouse_pos):
        """Start dragging this token."""
        if not self.visible:
            return False
            
        self.dragging = True
        # Calculate offset between mouse position and token center
        self.drag_offset = (
            self.position[0] - mouse_pos[0],
            self.position[1] - mouse_pos[1]
        )
        return True
    
    def update_drag(self, mouse_pos):
        """Update token position during dragging."""
        if not self.dragging:
            return False
            
        self.position = (
            mouse_pos[0] + self.drag_offset[0],
            mouse_pos[1] + self.drag_offset[1]
        )
        return True
    
    def end_drag(self):
        """End dragging this token."""
        self.dragging = False
        return True
    
    def draw(self, screen):
        """Draw the token on the screen."""
        if not self.visible or not self.image:
            return
            
        # Calculate token rectangle
        token_rect = pygame.Rect(
            self.position[0] - self.size // 2, 
            self.position[1] - self.size // 2,
            self.size, self.size
        )
        
        # Draw the token (circular)
        screen.blit(self.image, token_rect.topleft)
        
        # Draw selection indicator if selected (as a circle)
        if self.selected:
            # Draw yellow selection border
            pygame.draw.circle(
                screen, 
                (255, 255, 0),  # Yellow
                self.position, 
                self.size // 2,  # Same size as token
                2  # Line width
            )
            
            # Draw token name if selected
            if self.name:
                font = pygame.font.SysFont('Arial', 14)
                name_text = font.render(self.name, True, (255, 255, 255))
                text_rect = name_text.get_rect()
                text_rect.midtop = (self.position[0], self.position[1] + self.size // 2 + 5)
                
                # Draw background for text
                bg_rect = text_rect.copy()
                bg_rect.inflate_ip(6, 6)
                pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect)
                
                # Draw text
                screen.blit(name_text, text_rect)
    
    def to_dict(self):
        """Convert token to dictionary for serialization."""
        return {
            "image_path": self.image_path,
            "position": self.position,
            "size": self.size,
            "name": self.name,
            "visible": self.visible
        }
    
    @classmethod
    def from_dict(cls, data, token_id=None):
        """Create a token from dictionary data."""
        # Generate a token ID if none provided
        if token_id is None:
            import uuid
            token_id = f"token_{uuid.uuid4().hex[:8]}"
            
        token = cls(
            token_id,
            data["image_path"],
            tuple(data["position"]),
            data["size"],
            data["name"]
        )
        token.visible = data.get("visible", True)
        return token


class TokenManager:
    """
    Manages game tokens that can be placed on the map.
    """
    
    def __init__(self, screen, config):
        """Initialize the token manager."""
        self.screen = screen
        self.config = config
        self.tokens_directory = config.get("tokens_directory", "assets/tokens")
        self.current_grid_size = config.get("grid_size", 50)  # Keep track of current grid size
        
        # Ensure directory exists
        os.makedirs(self.tokens_directory, exist_ok=True)
        
        # Token state
        self.tokens = []
        self.available_tokens = []
        self.selected_token = None
        self.tokens_visible = True
        self.next_token_id = 1
        
        # Load available tokens
        self.refresh_token_list()
    
    def refresh_token_list(self):
        """Refresh the list of available token images."""
        self.available_tokens = get_image_files(self.tokens_directory)
    
    def add_token(self, image_path, position, size=None, name=""):
        """Add a new token to the map."""
        token_id = f"token_{self.next_token_id}"
        self.next_token_id += 1
        
        # Use the current grid size if no specific size provided
        if size is None:
            size = self.current_grid_size
            
        token = Token(token_id, image_path, position, size, name)
        self.tokens.append(token)
        return token
    
    def remove_token(self, token):
        """Remove a token from the battlefield."""
        if token in self.tokens:
            self.tokens.remove(token)
            if self.selected_token == token:
                self.selected_token = None
            return True
        return False
    
    def get_token_at(self, position):
        """Get the topmost token at the given position."""
        # Check tokens in reverse order (top to bottom)
        for token in reversed(self.tokens):
            if token.contains_point(position):
                return token
        return None
    
    def save_tokens(self, filename):
        """Save tokens to a file."""
        token_data = [token.to_dict() for token in self.tokens]
        
        try:
            with open(filename, 'w') as f:
                json.dump(token_data, f)
            return True
        except Exception as e:
            print(f"Error saving tokens: {e}")
            return False
    
    def load_tokens(self, filename):
        """Load tokens from a file."""
        if not os.path.exists(filename):
            return False
            
        try:
            with open(filename, 'r') as f:
                token_data = json.load(f)
                
            # Clear existing tokens
            self.tokens = []
            
            # Create new tokens
            for i, data in enumerate(token_data):
                token_id = f"token_{self.next_token_id}"
                self.next_token_id += 1
                token = Token.from_dict(data, token_id)
                self.tokens.append(token)
                
            return True
        except Exception as e:
            print(f"Error loading tokens: {e}")
            return False
    
    def draw(self):
        """Draw all tokens to the screen."""
        if not self.tokens_visible:
            return
            
        for token in self.tokens:
            token.draw(self.screen)
    
    def resize_all_tokens(self, grid_size):
        """Resize all tokens to match the current grid size."""
        if grid_size <= 0:
            return
        
        # Store the current grid size for future token additions
        self.current_grid_size = grid_size
            
        for token in self.tokens:
            token.resize(grid_size)