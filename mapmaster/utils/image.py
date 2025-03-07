import os
import pygame
from PIL import Image
import numpy as np

def load_image(filepath):
    """Load an image from filesystem and convert to Pygame surface."""
    try:
        image = pygame.image.load(filepath)
        return image.convert_alpha()
    except pygame.error as e:
        print(f"Error loading image {filepath}: {e}")
        # Return a small red square as fallback
        fallback = pygame.Surface((100, 100))
        fallback.fill((255, 0, 0))
        return fallback

def get_image_files(directory):
    """Get list of image files in directory."""
    supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
    images = []
    
    if not os.path.exists(directory):
        print(f"Warning: Directory {directory} does not exist.")
        return images
        
    for file in os.listdir(directory):
        if any(file.lower().endswith(fmt) for fmt in supported_formats):
            images.append(os.path.join(directory, file))
    
    return sorted(images)

def scale_image_to_fit(image, width, height):
    """Scale image to fit within dimensions while maintaining aspect ratio."""
    img_width, img_height = image.get_size()
    
    # Calculate scale factors
    scale_width = width / img_width
    scale_height = height / img_height
    
    # Use the smaller scale factor to ensure image fits within bounds
    scale = min(scale_width, scale_height)
    
    # Calculate new dimensions
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    
    # Scale the image
    scaled_image = pygame.transform.smoothscale(image, (new_width, new_height))
    return scaled_image

def surface_to_bytes(surface):
    """Convert a pygame surface to bytes for streaming."""
    image_data = pygame.surfarray.array3d(surface)
    # Convert from (width, height, 3) to (height, width, 3)
    image_data = image_data.transpose([1, 0, 2])
    # Convert to BGR (for OpenCV compatibility)
    image_data = image_data[:, :, ::-1].copy()
    return image_data