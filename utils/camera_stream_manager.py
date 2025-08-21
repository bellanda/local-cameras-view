"""
Camera Stream Manager for handling multiple clients with single camera connections.
Uses PyFFMPEG and OpenCV for optimal performance.
"""

import asyncio
import threading
import time
from collections import deque
from typing import Dict, List, Optional

import cv2

from utils.config import CAMERA_CONFIG, FFMPEG_CONFIG, OPENCV_CONFIG


class CameraStream:
    """Manages a single camera stream with multiple clients."""

    def __init__(self, camera_name: str, rtsp_url: str, max_buffer_size: int = None):
        self.camera_name = camera_name
        self.rtsp_url = rtsp_url
        self.max_buffer_size = max_buffer_size or CAMERA_CONFIG["max_buffer_size"]
        self.frame_buffer = deque(maxlen=self.max_buffer_size)
        self.clients: List[asyncio.Queue] = []
        self.is_running = False
        self.last_frame = None
        self.last_frame_time = 0
        self.last_frame_jpeg = None  # Cache JPEG to avoid re-encoding
        self.frame_interval = 1.0 / CAMERA_CONFIG["target_fps"]
        self.lock = threading.Lock()
        self.stream_thread = None
        self.jpeg_params = [cv2.IMWRITE_JPEG_QUALITY, CAMERA_CONFIG["jpeg_quality"]]

    def start(self):
        """Start the camera stream thread."""
        if not self.is_running:
            self.is_running = True
            self.stream_thread = threading.Thread(target=self._stream_worker, daemon=True)
            self.stream_thread.start()
            print(f"Started stream for camera: {self.camera_name}")

    def stop(self):
        """Stop the camera stream thread."""
        self.is_running = False
        if self.stream_thread:
            self.stream_thread.join(timeout=1.0)
        print(f"Stopped stream for camera: {self.camera_name}")

    def _stream_worker(self):
        """Worker thread that continuously reads from camera."""
        cap = None
        try:
            if self.rtsp_url == "0":
                # Webcam
                cap = cv2.VideoCapture(0)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            else:
                # IP Camera - try PyFFMPEG first, fallback to OpenCV
                try:
                    cap = self._create_ffmpeg_capture()
                except Exception as e:
                    print(f"PyFFMPEG failed for {self.camera_name}, falling back to OpenCV: {e}")
                    cap = cv2.VideoCapture(self.rtsp_url)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not cap.isOpened():
                print(f"Failed to open camera: {self.camera_name}")
                return

            print(f"Successfully connected to camera: {self.camera_name}")

            while self.is_running:
                ret, frame = cap.read()
                if ret:
                    current_time = time.time()

                    # Only update if enough time has passed (rate limiting)
                    if current_time - self.last_frame_time >= self.frame_interval:
                        # Encode ONCE outside the lock
                        ok, buf = cv2.imencode(".jpg", frame, self.jpeg_params)
                        if not ok:
                            time.sleep(0.001)
                            continue
                        frame_bytes = buf.tobytes()

                        with self.lock:
                            # Store frame and JPEG data
                            self.last_frame = frame  # No .copy() needed
                            self.last_frame_time = current_time
                            self.last_frame_jpeg = frame_bytes

                            # Add to buffer if needed
                            if len(self.frame_buffer) < self.max_buffer_size:
                                self.frame_buffer.append(frame)  # No .copy() needed

                        # Notify all clients with the same JPEG bytes
                        self._notify_clients(frame_bytes)

                        # Pace using remaining time instead of fixed sleep
                        remaining = self.frame_interval - (time.time() - current_time)
                        if remaining > 0:
                            time.sleep(remaining)
                    else:
                        time.sleep(0.001)
                else:
                    time.sleep(0.1)

        except Exception as e:
            print(f"Error in stream worker for {self.camera_name}: {e}")
        finally:
            if cap:
                cap.release()

    def _create_ffmpeg_capture(self):
        """Create OpenCV capture using FFmpeg backend for better RTSP performance."""
        # Add RTSP optimization parameters to URL
        url = self.rtsp_url
        sep = "&" if "?" in url else "?"
        url += f"{sep}rtsp_transport=tcp&fflags=nobuffer&flags=low_delay&stimeout={FFMPEG_CONFIG['stimeout']}"

        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, OPENCV_CONFIG["ip_camera"]["buffer_size"])
        cap.set(cv2.CAP_PROP_FPS, OPENCV_CONFIG["ip_camera"]["fps"])
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, OPENCV_CONFIG["ip_camera"]["width"])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, OPENCV_CONFIG["ip_camera"]["height"])
        return cap

    def _notify_clients(self, frame_bytes: bytes):
        """Notify all connected clients with the new frame."""
        if not self.clients:
            return

        # Keep all clients, even slow ones (they just lose this frame)
        alive = []
        for client_queue in self.clients:
            try:
                if not client_queue.full():
                    client_queue.put_nowait(frame_bytes)
                # Even if queue is full, keep the client (they just lose this frame)
                alive.append(client_queue)
            except Exception:
                # Real error: remove client
                pass

        self.clients = alive

    def add_client(self, client_queue: asyncio.Queue):
        """Add a new client to receive frames."""
        with self.lock:
            self.clients.append(client_queue)
            # Send the last frame immediately if available (using cached JPEG)
            if self.last_frame_jpeg is not None:
                try:
                    client_queue.put_nowait(self.last_frame_jpeg)
                except asyncio.QueueFull:
                    pass

    def remove_client(self, client_queue: asyncio.Queue):
        """Remove a client from the stream."""
        with self.lock:
            if client_queue in self.clients:
                self.clients.remove(client_queue)

    def get_frame_count(self) -> int:
        """Get the number of active clients."""
        return len(self.clients)

    def get_buffer_size(self) -> int:
        """Get the current buffer size."""
        return len(self.frame_buffer)


class CameraStreamManager:
    """Manages multiple camera streams and their clients."""

    def __init__(self):
        self.cameras: Dict[str, CameraStream] = {}
        self.lock = threading.Lock()

    def add_camera(self, camera_name: str, rtsp_url: str) -> CameraStream:
        """Add a new camera to the manager."""
        with self.lock:
            if camera_name not in self.cameras:
                camera_stream = CameraStream(camera_name, rtsp_url)
                self.cameras[camera_name] = camera_stream
                camera_stream.start()
                print(f"Added camera: {camera_name}")
            return self.cameras[camera_name]

    def get_camera(self, camera_name: str) -> Optional[CameraStream]:
        """Get a camera stream by name."""
        return self.cameras.get(camera_name)

    def remove_camera(self, camera_name: str):
        """Remove a camera from the manager."""
        with self.lock:
            if camera_name in self.cameras:
                self.cameras[camera_name].stop()
                del self.cameras[camera_name]
                print(f"Removed camera: {camera_name}")

    def get_camera_status(self) -> Dict[str, Dict]:
        """Get status of all cameras."""
        status = {}
        with self.lock:
            for name, camera in self.cameras.items():
                status[name] = {
                    "clients": camera.get_frame_count(),
                    "buffer_size": camera.get_buffer_size(),
                    "is_running": camera.is_running,
                    "last_frame_time": camera.last_frame_time,
                }
        return status

    def stop_all(self):
        """Stop all camera streams."""
        with self.lock:
            for camera in self.cameras.values():
                camera.stop()
            self.cameras.clear()
        print("Stopped all camera streams")


# Global instance
stream_manager = CameraStreamManager()
