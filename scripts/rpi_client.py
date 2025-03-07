#!/usr/bin/env python3
"""
MapMaster Raspberry Pi Client
A lightweight MJPEG stream viewer optimized for Raspberry Pi devices.

Usage:
    python3 rpi_client.py http://server_ip:port/stream
"""

import pygame
import requests
import io
import argparse
import re
import threading
from PIL import Image

# Function to validate the URL format
def is_valid_url(url):
    regex = re.compile(
        r'^(http://|https://)'  # protocol
        r'(([0-9]{1,3}\.){3}[0-9]{1,3}|'  # IPv4
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})'  # domain name
        r'(:[0-9]+)?'  # optional port
        r'(/.*)?$'  # optional path
    )
    return re.match(regex, url) is not None

# Set up argument parsing to get the IP address from the command line
parser = argparse.ArgumentParser(description='MJPEG Stream Viewer')
parser.add_argument('ip_address', help='Full URL of the MJPEG stream (e.g., http://192.168.1.127:5000/stream)')
args = parser.parse_args()

# URL of the MJPEG stream from the command-line argument
stream_url = args.ip_address

# Validate the provided URL
if not is_valid_url(stream_url):
    print(f"Invalid URL: {stream_url}. Please provide a valid MJPEG stream URL.")
    exit(1)

# Initialize Pygame
pygame.init()

# Set up fullscreen mode with double buffering
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
pygame.display.set_caption("MJPEG Stream Viewer")

# Hide the mouse cursor
pygame.mouse.set_visible(False)

# Create a clock to control the frame rate
clock = pygame.time.Clock()

# Shared variable for the latest image surface
latest_surface = None
buffer = b''

def fetch_stream():
    global latest_surface, buffer

    try:
        with requests.get(stream_url, stream=True) as r:
            for chunk in r.iter_content(chunk_size=1024):
                buffer += chunk

                # Look for the JPEG start and end markers
                start_idx = buffer.find(b'\xff\xd8')  # Start of JPEG
                end_idx = buffer.find(b'\xff\xd9')    # End of JPEG

                if start_idx != -1 and end_idx != -1:
                    jpg_data = buffer[start_idx:end_idx + 2]
                    buffer = buffer[end_idx + 2:]

                    # Convert JPEG data to a Pygame surface
                    image = Image.open(io.BytesIO(jpg_data))
                    mode = image.mode
                    size = image.size
                    data = image.tobytes()

                    # Create a Pygame surface from the image
                    latest_surface = pygame.image.fromstring(data, size, mode)

    except Exception as e:
        print(f"Error fetching the stream: {e}")

# Start the stream fetching in a separate thread
stream_thread = threading.Thread(target=fetch_stream, daemon=True)
stream_thread.start()

# Function to display the stream
def display_stream():
    global latest_surface

    if latest_surface is not None:
        # Get screen dimensions
        screen_width, screen_height = screen.get_size()

        # Get original image dimensions
        img_width, img_height = latest_surface.get_size()

        # Calculate new dimensions to fill the screen while maintaining aspect ratio
        aspect_ratio = img_width / img_height
        screen_aspect_ratio = screen_width / screen_height

        if aspect_ratio > screen_aspect_ratio:
            new_width = screen_width
            new_height = int(screen_width / aspect_ratio)
        else:
            new_height = screen_height
            new_width = int(screen_height * aspect_ratio)

        # Scale the image using bilinear interpolation
        surface = pygame.transform.smoothscale(latest_surface, (new_width, new_height))

        # Create a back buffer surface
        back_buffer = pygame.Surface((screen_width, screen_height))

        # Fill the back buffer with black
        back_buffer.fill((0, 0, 0))

        # Calculate position to center the image
        x = (screen_width - new_width) // 2
        y = (screen_height - new_height) // 2

        # Blit the image to the back buffer at the calculated position
        back_buffer.blit(surface, (x, y))

        # Blit the back buffer to the screen
        screen.blit(back_buffer, (0, 0))

        # Update the display
        pygame.display.flip()

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  # Exit on ESC key
                running = False

    display_stream()  # Continuously update the stream

    # Control the frame rate (e.g., 30 FPS)
    clock.tick(30)

# Clean up
pygame.quit()