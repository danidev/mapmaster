"""
Flask server for MapMaster.
Provides a web interface for players to connect to.
"""

import cv2
import numpy as np
from flask import Flask, Response, render_template, send_from_directory
import pygame
from ..utils.image import surface_to_bytes

def create_app(app_instance):
    """Create the Flask application."""
    flask_app = Flask(__name__, 
                     static_folder="../../static",
                     template_folder="../../templates")
    
    # Store a reference to the main application
    flask_app.app_instance = app_instance
    
    # Define routes
    @flask_app.route('/')
    def index():
        """Render the main page."""
        return render_template('index.html')
    
    @flask_app.route('/master')
    def master():
        """Render the game master page."""
        return render_template('master.html')
    
    @flask_app.route('/stream')
    def stream():
        """Stream the current screen."""
        return Response(generate_frames(flask_app.app_instance),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @flask_app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files."""
        return send_from_directory(flask_app.static_folder, filename)
    
    return flask_app

def generate_frames(app_instance):
    """Generate video frames for streaming."""
    while True:
        # Get the current screen from the application
        screen = app_instance.get_screen_image()
        if screen is None:
            continue
            
        # Convert Pygame surface to bytes
        frame = surface_to_bytes(screen)
        
        # Convert to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_bytes = buffer.tobytes()
        
        # Yield the frame in the MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

def start_server(app, host, port):
    """Start the Flask server."""
    app.run(host=host, port=port, threaded=True)