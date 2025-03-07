"""
Map management module for MapMaster.
Handles loading, displaying, and switching between battlemaps.
"""

import os
import pygame
import json
from ..utils.image import load_image, scale_image_to_fit, get_image_files

class MapManager:
    """
    Manages battlemap images and their display properties.
    """
    
    def __init__(self, screen, config):
        """Initialize the map manager."""
        self.screen = screen
        self.config = config
        self.maps_directory = config.get("maps_directory", "assets/maps")
        self.annotations_directory = config.get("annotations_directory", "annotations")
        
        # Ensure directories exist
        os.makedirs(self.maps_directory, exist_ok=True)
        os.makedirs(self.annotations_directory, exist_ok=True)
        
        # Map loading and tracking
        self.map_files = []
        self.current_map_index = 0
        self.current_map = None
        self.current_map_surface = None
        self.map_position = (0, 0)
        
        # Annotations
        self.annotations_surface = None
        self.annotation_points = []
        
        # State tracking
        self.drawing_enabled = True
        self.grid_enabled = config.get("grid_enabled", False)
        self.grid_size = config.get("grid_size", 50)
        self.grid_color = tuple(config.get("grid_color", [100, 100, 100, 128]))
        self.grid_offset = (0, 0)
        
        # Load map files
        self.refresh_map_list()
    
    def refresh_map_list(self):
        """Refresh the list of available map files."""
        self.map_files = get_image_files(self.maps_directory)
        
        # Reset to first map if no current map or out of bounds
        if not self.map_files:
            self.current_map_index = 0
            self.current_map = None
        elif self.current_map not in self.map_files:
            self.current_map_index = 0
            self.load_map(self.map_files[0] if self.map_files else None)
    
    def load_map(self, map_path):
        """Load a specific map by path."""
        if not map_path or not os.path.exists(map_path):
            self.current_map = None
            self.current_map_surface = None
            return False
            
        # Load the map image
        surface = load_image(map_path)
        if not surface:
            return False
            
        # Update state
        self.current_map = map_path
        if self.map_files and map_path in self.map_files:
            self.current_map_index = self.map_files.index(map_path)
        
        # Scale the map to fit the screen if needed
        screen_rect = self.screen.get_rect()
        self.current_map_surface = scale_image_to_fit(surface, screen_rect.width, screen_rect.height)
        
        # Center the map on screen
        map_rect = self.current_map_surface.get_rect()
        self.map_position = ((screen_rect.width - map_rect.width) // 2, 
                            (screen_rect.height - map_rect.height) // 2)
        
        # Create a new annotations surface
        self.annotations_surface = pygame.Surface(self.current_map_surface.get_size(), pygame.SRCALPHA)
        self.annotations_surface.fill((0, 0, 0, 0))  # Transparent
        
        # Reset annotation points
        self.annotation_points = []
        
        # Try to load saved annotations
        self.load_annotations()
        
        return True
    
    def next_map(self):
        """Switch to the next map in the list."""
        if not self.map_files:
            return False
            
        self.current_map_index = (self.current_map_index + 1) % len(self.map_files)
        return self.load_map(self.map_files[self.current_map_index])
    
    def previous_map(self):
        """Switch to the previous map in the list."""
        if not self.map_files:
            return False
            
        self.current_map_index = (self.current_map_index - 1) % len(self.map_files)
        return self.load_map(self.map_files[self.current_map_index])
    
    def get_annotation_filename(self):
        """Get the filename for the current map's annotations."""
        if not self.current_map:
            return None
            
        # Get map filename without path or extension
        map_name = os.path.splitext(os.path.basename(self.current_map))[0]
        return os.path.join(self.annotations_directory, f"{map_name}_annotations.json")
    
    def save_annotations(self):
        """Save the current annotations to file."""
        if not self.current_map:
            return False
            
        annotation_file = self.get_annotation_filename()
        if not annotation_file:
            return False
            
        try:
            # Save annotation points (color, size, points)
            with open(annotation_file, 'w') as f:
                json.dump(self.annotation_points, f)
            return True
        except Exception as e:
            print(f"Error saving annotations: {e}")
            return False
    
    def load_annotations(self):
        """Load annotations for the current map."""
        if not self.current_map:
            return False
            
        annotation_file = self.get_annotation_filename()
        if not annotation_file or not os.path.exists(annotation_file):
            return False
            
        try:
            with open(annotation_file, 'r') as f:
                self.annotation_points = json.load(f)
                
            # Redraw the annotations
            self.redraw_annotations()
            return True
        except Exception as e:
            print(f"Error loading annotations: {e}")
            return False
    
    def clear_annotations(self):
        """Clear all annotations for the current map."""
        if self.annotations_surface:
            self.annotations_surface.fill((0, 0, 0, 0))  # Transparent
            self.annotation_points = []
            return True
        return False
    
    def add_annotation_point(self, point, color, size):
        """Add a point to the current annotation stroke."""
        if not self.drawing_enabled or not self.current_map:
            return False
            
        # Add the point to the list
        if not self.annotation_points or self.annotation_points[-1][0] != color or self.annotation_points[-1][1] != size:
            # Start new stroke
            self.annotation_points.append([color, size, [point]])
        else:
            # Add to existing stroke
            self.annotation_points[-1][2].append(point)
            
        # Draw the point
        rel_point = (point[0] - self.map_position[0], point[1] - self.map_position[1])
        pygame.draw.circle(self.annotations_surface, color, rel_point, size // 2)
        
        # If continuing a stroke, draw a line from the previous point
        points = self.annotation_points[-1][2]
        if len(points) > 1:
            prev_point = points[-2]
            prev_rel_point = (prev_point[0] - self.map_position[0], prev_point[1] - self.map_position[1])
            pygame.draw.line(self.annotations_surface, color, prev_rel_point, rel_point, size)
        
        return True
    
    def redraw_annotations(self):
        """Redraw all annotations from saved points."""
        if not self.annotations_surface:
            return
            
        # Clear the surface
        self.annotations_surface.fill((0, 0, 0, 0))
        
        # Redraw each stroke
        for color_str, size, points in self.annotation_points:
            # Convert color from list/string to tuple if needed
            color = tuple(color_str) if isinstance(color_str, list) else color_str
            
            # Draw each point in the stroke
            for i, point in enumerate(points):
                # Adjust point position relative to map
                rel_point = (point[0] - self.map_position[0], point[1] - self.map_position[1])
                
                # Draw the point
                pygame.draw.circle(self.annotations_surface, color, rel_point, size // 2)
                
                # Draw a line to the previous point
                if i > 0:
                    prev_point = points[i-1]
                    prev_rel_point = (prev_point[0] - self.map_position[0], prev_point[1] - self.map_position[1])
                    pygame.draw.line(self.annotations_surface, color, prev_rel_point, rel_point, size)
    
    def toggle_grid(self):
        """Toggle the grid overlay."""
        self.grid_enabled = not self.grid_enabled
        return self.grid_enabled
    
    def set_grid_size(self, size):
        """Set the grid size."""
        self.grid_size = max(10, min(200, size))  # Clamp between 10 and 200
        return self.grid_size
    
    def set_grid_offset(self, offset):
        """Set the grid offset."""
        self.grid_offset = offset
    
    def draw_grid(self):
        """Draw the grid overlay."""
        if not self.grid_enabled or not self.current_map_surface:
            return
            
        map_rect = self.current_map_surface.get_rect()
        map_rect.topleft = self.map_position
        
        # Create a grid overlay surface
        grid_surface = pygame.Surface(map_rect.size, pygame.SRCALPHA)
        
        # Draw horizontal lines
        y = self.grid_offset[1] % self.grid_size
        while y < map_rect.height:
            pygame.draw.line(grid_surface, self.grid_color, (0, y), (map_rect.width, y))
            y += self.grid_size
            
        # Draw vertical lines
        x = self.grid_offset[0] % self.grid_size
        while x < map_rect.width:
            pygame.draw.line(grid_surface, self.grid_color, (x, 0), (x, map_rect.height))
            x += self.grid_size
            
        # Blit the grid onto the screen at map position
        self.screen.blit(grid_surface, map_rect.topleft)
    
    def draw(self):
        """Draw the current map to the screen."""
        if not self.current_map_surface:
            # Draw a black background if no map is loaded
            self.screen.fill((0, 0, 0))
            return False
            
        # Draw the map
        self.screen.blit(self.current_map_surface, self.map_position)
        
        # Draw the grid if enabled (handled separately in main.py)
        # if self.grid_enabled:
        #     self.draw_grid()
            
        return True
    
    def draw_map_only(self):
        """Draw just the current map to the screen without annotations."""
        if not self.current_map_surface:
            # Draw a black background if no map is loaded
            self.screen.fill((0, 0, 0))
            return False
            
        # Draw the map
        self.screen.blit(self.current_map_surface, self.map_position)
        return True
    
    def get_current_filename(self):
        """Get the current map filename."""
        if not self.current_map:
            return None
        return self.current_map