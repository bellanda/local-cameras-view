"""
Status endpoint utilities for monitoring camera streams.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from utils.camera_stream_manager import stream_manager


def create_status_router() -> APIRouter:
    """Create a router for status endpoints."""
    router = APIRouter(prefix="/api", tags=["status"])

    @router.get("/status")
    async def get_status():
        """Get overall system status."""
        camera_status = stream_manager.get_camera_status()
        total_cameras = len(camera_status)
        total_clients = sum(status["clients"] for status in camera_status.values())

        return JSONResponse(
            {
                "system": "Camera Stream Manager",
                "status": "running",
                "total_cameras": total_cameras,
                "total_clients": total_clients,
                "cameras": camera_status,
            }
        )

    @router.get("/cameras/{camera_name}/status")
    async def get_camera_status(camera_name: str):
        """Get status for a specific camera."""
        camera = stream_manager.get_camera(camera_name)
        if not camera:
            return JSONResponse({"error": f"Camera {camera_name} not found"}, status_code=404)

        return JSONResponse(
            {
                "camera_name": camera_name,
                "rtsp_url": camera.rtsp_url,
                "is_running": camera.is_running,
                "clients": camera.get_frame_count(),
                "buffer_size": camera.get_buffer_size(),
                "last_frame_time": camera.last_frame_time,
            }
        )

    @router.post("/cameras/{camera_name}/restart")
    async def restart_camera(camera_name: str):
        """Restart a camera stream."""
        camera = stream_manager.get_camera(camera_name)
        if not camera:
            return JSONResponse({"error": f"Camera {camera_name} not found"}, status_code=404)

        # Restart the camera
        camera.stop()
        camera.start()

        return JSONResponse({"message": f"Camera {camera_name} restarted successfully", "status": "restarting"})

    return router
