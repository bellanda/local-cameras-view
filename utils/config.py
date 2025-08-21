"""
Configuration settings for camera stream optimization.
"""

# Camera stream settings
CAMERA_CONFIG = {
    "max_buffer_size": 30,  # Maximum frames to buffer
    "target_fps": 30,  # Target frames per second
    "jpeg_quality": 85,  # JPEG compression quality (0-100)
    "frame_timeout": 30.0,  # Timeout for frame delivery (seconds)
    "client_queue_size": 10,  # Maximum frames in client queue
    "keepalive_interval": 5.0,  # Keep-alive frame interval (seconds)
}

# OpenCV settings for different camera types
OPENCV_CONFIG = {
    "webcam": {
        "buffer_size": 1,
        "fps": 30,
        "width": 640,
        "height": 480,
    },
    "ip_camera": {
        "buffer_size": 1,
        "fps": 30,
        "width": 1920,
        "height": 1080,
        "rtsp_transport": "tcp",  # Use TCP for better reliability
    },
}

# PyFFMPEG settings for low-latency RTSP
FFMPEG_CONFIG = {
    "rtsp_transport": "tcp",
    "stimeout": 2000000,  # Socket timeout in microseconds (2 seconds)
    "fflags": "nobuffer",  # Reduce buffering
    "flags": "low_delay",  # Low delay flag
    "probesize": 32,  # Minimal probe size for faster startup
    "analyzeduration": 0,  # No analysis delay
}

# Performance tuning
PERFORMANCE_CONFIG = {
    "max_concurrent_streams": 10,  # Maximum concurrent camera streams
    "max_clients_per_camera": 50,  # Maximum clients per camera
    "frame_skip_threshold": 0.1,  # Skip frame if client is too slow (seconds)
    "cleanup_interval": 60.0,  # Cleanup interval for disconnected clients (seconds)
    "jpeg_cache_enabled": True,  # Enable JPEG caching to avoid re-encoding
    "frame_copy_optimization": True,  # Optimize frame copying
    "rtsp_low_latency": True,  # Enable RTSP low-latency optimizations
}
