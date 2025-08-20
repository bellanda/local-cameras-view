import asyncio
import signal
import socket
import sys

import cv2
import numpy as np
import qrcode
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

from constants.camera import CAMERAS_MAPPING
from utils.camera_stream_manager import stream_manager
from utils.config import CAMERA_CONFIG
from utils.construct_rtsp_url import is_webcam
from utils.status_endpoint import create_status_router

app = FastAPI(title="Local Camera Viewer", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add status router
app.include_router(create_status_router())


# Initialize camera streams on startup
@app.on_event("startup")
async def startup_event():
    """Initialize all camera streams on startup."""
    print("🚀 Initializing camera streams...")
    for camera_name, rtsp_url in CAMERAS_MAPPING.items():
        stream_manager.add_camera(camera_name, rtsp_url)
    print(f"✅ Initialized {len(CAMERAS_MAPPING)} camera streams")


# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup camera streams on shutdown."""
    print("🛑 Shutting down camera streams...")
    stream_manager.stop_all()


# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    stream_manager.stop_all()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def render_tabs(selected=None):
    """Generate navigation tabs for all cameras."""
    tabs = ""
    for name in CAMERAS_MAPPING.keys():
        active = "active-tab" if name == selected else ""
        tabs += f"<a href='/camera/{name}' class='tab {active}'>{name}</a>"
    return tabs


@app.get("/", response_class=HTMLResponse)
def index():
    """Main page with camera selection - redirects to first camera."""
    # Redirect to first camera if available
    if CAMERAS_MAPPING:
        first_camera = list(CAMERAS_MAPPING.keys())[0]
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url=f"/camera/{first_camera}")

    # Fallback to camera selection if no cameras
    tabs = render_tabs()
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Visualização de Câmeras v2.0</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; }}
            .header {{ text-align: center; padding: 1rem 0.5rem; background: #222; color: #fff; }}
            .header h1 {{ font-size: 1.5rem; margin: 0 0 0.5rem 0; }}
            .header p {{ font-size: 0.9rem; margin: 0; opacity: 0.9; }}
            .tabs {{ display: flex; justify-content: center; background: #333; padding: 0.5rem; flex-wrap: wrap; gap: 0.3rem; }}
            .tab {{ color: #fff; text-decoration: none; padding: 0.8rem 1.2rem; border-radius: 8px; background: #444; transition: background 0.2s; font-size: 0.9rem; white-space: nowrap; }}
            .tab:hover {{ background: #666; }}
            .active-tab {{ background: #fff; color: #222; font-weight: bold; }}
            .main-content {{ display: flex; flex-direction: column; align-items: center; margin-top: 2rem; padding: 0 1rem; }}
            .info {{ margin-top: 1.5rem; color: #555; text-align: center; }}
            .status-bar {{ background: #fff; padding: 1rem; border-radius: 8px; margin-top: 1.5rem; box-shadow: 0 2px 8px #0001; width: 100%; max-width: 500px; }}
            .status-item {{ margin: 0.5rem 0; }}
            .status-item a {{ color: #007bff; text-decoration: none; }}
            .status-item a:hover {{ text-decoration: underline; }}
            
            .features-info {{ background: #fff; padding: 1.5rem; border-radius: 8px; margin-top: 1.5rem; box-shadow: 0 2px 8px #0001; width: 100%; max-width: 600px; }}
            .features-info h3 {{ margin: 0 0 1rem 0; color: #333; text-align: center; }}
            .feature-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem; }}
            .feature-item {{ display: flex; flex-direction: column; align-items: center; text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px; }}
            .feature-icon {{ font-size: 2rem; margin-bottom: 0.5rem; }}
            .feature-text {{ font-size: 0.9rem; color: #555; font-weight: 500; }}
            
            /* Mobile optimizations */
            @media (max-width: 768px) {{
                .header {{ padding: 1rem 0.3rem; }}
                .header h1 {{ font-size: 1.3rem; }}
                .header p {{ font-size: 0.8rem; }}
                .tabs {{ padding: 0.3rem; gap: 0.2rem; }}
                .tab {{ padding: 0.6rem 1rem; font-size: 0.8rem; }}
                .main-content {{ margin-top: 1.5rem; padding: 0 0.5rem; }}
                .status-bar {{ margin-top: 1rem; padding: 0.8rem; }}
            }}
            
            @media (max-width: 480px) {{
                .header h1 {{ font-size: 1.2rem; }}
                .header p {{ font-size: 0.75rem; }}
                .tabs {{ flex-direction: column; align-items: center; }}
                .tab {{ width: 100%; text-align: center; max-width: 200px; }}
                .main-content {{ margin-top: 1rem; }}
                .status-bar {{ padding: 0.6rem; }}
            }}
        </style>
    </head>
    <body>
        <div class='header'>
            <h1>Visualização de Câmeras v2.0</h1>
            <p>Servidor Intermediário com Suporte a Múltiplos Clientes</p>
        </div>
        <div class='tabs'>
            {tabs}
        </div>
        <div class='main-content'>
            <div class='info'>Selecione uma câmera acima para visualizar.</div>
            <div class='status-bar'>
                <h3>Status do Sistema</h3>
                <div class='status-item'>📊 <a href='/api/status' target='_blank'>Ver Status Completo</a></div>
                <div class='status-item'>🔧 <a href='/docs' target='_blank'>API Documentation</a></div>
                <div class='status-item'>📱 <a href='/mobile-test' target='_blank'>Teste Mobile</a></div>
            </div>
            <div class='features-info'>
                <h3>✨ Funcionalidades</h3>
                <div class='feature-grid'>
                    <div class='feature-item'>
                        <div class='feature-icon'>🔀</div>
                        <div class='feature-text'>Múltiplos Clientes</div>
                    </div>
                    <div class='feature-item'>
                        <div class='feature-icon'>⚡</div>
                        <div class='feature-text'>Alta Performance</div>
                    </div>
                    <div class='feature-item'>
                        <div class='feature-icon'>📱</div>
                        <div class='feature-text'>Mobile Responsivo</div>
                    </div>
                    <div class='feature-item'>
                        <div class='feature-icon'>🔄</div>
                        <div class='feature-text'>Stream Otimizado</div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/camera/{camera_name}", response_class=HTMLResponse)
def camera_page(camera_name: str):
    """Individual camera page."""
    if camera_name not in CAMERAS_MAPPING:
        raise HTTPException(status_code=404, detail="Câmera não encontrada")

    tabs = render_tabs(selected=camera_name)
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Câmera: {camera_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; }}
            .header {{ text-align: center; padding: 1rem 0.5rem; background: #222; color: #fff; }}
            .header h1 {{ font-size: 1.5rem; margin: 0 0 0.5rem 0; }}
            .tabs {{ display: flex; justify-content: center; background: #333; padding: 0.5rem; flex-wrap: wrap; gap: 0.3rem; }}
            .tab {{ color: #fff; text-decoration: none; padding: 0.8rem 1.2rem; border-radius: 8px; background: #444; transition: background 0.2s; font-size: 0.9rem; white-space: nowrap; }}
            .tab:hover {{ background: #666; }}
            .active-tab {{ background: #fff; color: #222; font-weight: bold; }}
            .main-content {{ display: flex; flex-direction: column; align-items: center; margin-top: 1.5rem; padding: 0 1rem; }}
            .camera-title {{ font-size: 1.8rem; margin-bottom: 1.2rem; color: #222; text-align: center; }}
            .camera-img-wrapper {{ background: #fff; padding: 1rem; border-radius: 16px; box-shadow: 0 2px 16px #0001; display: flex; flex-direction: column; align-items: center; width: 100%; max-width: 95vw; }}
            .camera-img {{ width: 100%; height: auto; max-height: 60vh; border-radius: 8px; box-shadow: 0 1px 8px #0002; object-fit: contain; }}
            .camera-controls {{ display: flex; flex-direction: column; gap: 1rem; align-items: center; margin-top: 1.5rem; width: 100%; }}
            .back-link, .status-link {{ color: #333; text-decoration: none; font-size: 1rem; padding: 0.8rem 1.5rem; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #0001; text-align: center; min-width: 200px; }}
            .back-link:hover, .status-link:hover {{ text-decoration: underline; background: #f8f8f8; }}
            .status-link {{ background: #007bff; color: #fff; }}
            .status-link:hover {{ background: #0056b3; }}
            .status-info {{ background: #e8f5e8; padding: 1rem; border-radius: 8px; margin-top: 1rem; border-left: 4px solid #4caf50; width: 100%; text-align: center; font-size: 0.9rem; line-height: 1.4; }}
            
            /* Mobile optimizations */
            @media (max-width: 768px) {{
                .header {{ padding: 1rem 0.3rem; }}
                .header h1 {{ font-size: 1.3rem; }}
                .tabs {{ padding: 0.3rem; gap: 0.2rem; }}
                .tab {{ padding: 0.6rem 1rem; font-size: 0.8rem; }}
                .main-content {{ margin-top: 1rem; padding: 0 0.5rem; }}
                .camera-title {{ font-size: 1.5rem; margin-bottom: 1rem; }}
                .camera-img-wrapper {{ padding: 0.8rem; }}
                .camera-img {{ max-height: 50vh; }}
                .status-info {{ font-size: 0.8rem; padding: 0.8rem; }}
                .camera-controls {{ margin-top: 1.2rem; }}
                .back-link, .status-link {{ padding: 0.6rem 1.2rem; font-size: 0.9rem; min-width: 180px; }}
            }}
            
            @media (max-width: 480px) {{
                .header h1 {{ font-size: 1.2rem; }}
                .tabs {{ flex-direction: column; align-items: center; }}
                .tab {{ width: 100%; text-align: center; max-width: 200px; }}
                .main-content {{ margin-top: 0.8rem; }}
                .camera-title {{ font-size: 1.3rem; }}
                .camera-img-wrapper {{ padding: 0.6rem; }}
                .camera-img {{ max-height: 45vh; }}
                .status-info {{ font-size: 0.75rem; padding: 0.6rem; }}
                .camera-controls {{ margin-top: 1rem; }}
                .back-link, .status-link {{ padding: 0.5rem 1rem; font-size: 0.85rem; min-width: 160px; }}
            }}
            
            /* Landscape orientation for mobile */
            @media (max-width: 768px) and (orientation: landscape) {{
                .camera-img {{ max-height: 70vh; }}
                .header h1 {{ font-size: 1.2rem; }}
                .camera-title {{ font-size: 1.4rem; }}
            }}
        </style>
    </head>
    <body>
        <div class='header'>
            <h1>Visualização de Câmeras v2.0</h1>
        </div>
        <div class='tabs'>
            {tabs}
        </div>
        <div class='main-content'>
            <div class='camera-title'>Câmera: {camera_name}</div>
            <div class='camera-img-wrapper'>
                <img src='/video_feed/{camera_name}' class='camera-img' alt='Stream da câmera {camera_name}' />
            </div>
            <div class='camera-controls' style="margin-bottom: 1.5rem;">
                <a href='/' class='back-link'>&larr; Voltar para lista de câmeras</a>
            </div>
        </div>
    </body>
    </html>
    """


async def gen_frames_async(camera_name: str):
    """Generate frames asynchronously for a specific camera."""
    camera = stream_manager.get_camera(camera_name)
    if not camera:
        raise HTTPException(status_code=404, detail="Câmera não encontrada")

    # Create a queue for this client
    client_queue = asyncio.Queue(maxsize=CAMERA_CONFIG["client_queue_size"])

    try:
        # Add client to camera stream
        camera.add_client(client_queue)
        print(f"Client connected to {camera_name}. Total clients: {camera.get_frame_count()}")

        while True:
            try:
                # Wait for frame with timeout
                frame_data = await asyncio.wait_for(client_queue.get(), timeout=CAMERA_CONFIG["frame_timeout"])
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_data + b"\r\n")
            except asyncio.TimeoutError:
                # Send a keep-alive frame if no new data
                if camera.last_frame is not None:
                    _, buffer = cv2.imencode(
                        ".jpg", camera.last_frame, [cv2.IMWRITE_JPEG_QUALITY, CAMERA_CONFIG["jpeg_quality"]]
                    )
                    frame_data = buffer.tobytes()
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_data + b"\r\n")
                else:
                    # Send a black frame if no camera data
                    black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    _, buffer = cv2.imencode(".jpg", black_frame)
                    frame_data = buffer.tobytes()
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_data + b"\r\n")

    except asyncio.CancelledError:
        print(f"Client disconnected from {camera_name}")
    finally:
        # Remove client from camera stream
        camera.remove_client(client_queue)
        print(f"Client disconnected from {camera_name}. Total clients: {camera.get_frame_count()}")


@app.get("/video_feed/{camera_name}")
def video_feed(camera_name: str):
    """Video feed endpoint for a specific camera."""
    if camera_name not in CAMERAS_MAPPING:
        raise HTTPException(status_code=404, detail="Câmera não encontrada")

    rtsp_url = CAMERAS_MAPPING[camera_name]
    camera_type = "Webcam" if is_webcam(rtsp_url) else "IP Camera"
    print(f"Streaming {camera_name} ({camera_type}): {rtsp_url}")

    return StreamingResponse(gen_frames_async(camera_name), media_type="multipart/x-mixed-replace; boundary=frame")


def get_local_ip():
    """Get local IP address for QR code generation."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


def generate_qr_code():
    """Generate and display QR code in terminal and save as JPG file."""
    from pathlib import Path

    local_ip = get_local_ip()
    app_url = f"http://{local_ip}:8000"

    print("\n" + "=" * 70)
    print("🚀 CAMERA VIEWER APPLICATION v2.0 - MULTI-CLIENT SUPPORT")
    print("=" * 70)
    print(f"📱 Scan QR Code or visit: {app_url}")
    print("=" * 70)

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=20,
        border=2,
    )
    qr.add_data(app_url)
    qr.make(fit=True)

    # Create QR code as ASCII art for terminal
    qr_matrix = qr.get_matrix()

    # Print QR code in terminal
    for row in qr_matrix:
        line = ""
        for cell in row:
            line += "██" if cell else "  "
        print(line)

    # Save QR code as JPG file in home directory
    try:
        home_dir = Path.home() / "Desktop"
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_file_path = home_dir / "camera_viewer_qr.jpg"
        qr_img.save(qr_file_path, "JPEG", quality=95)
        print(f"📱 QR Code salvo em: {qr_file_path}")
    except Exception as e:
        print(f"⚠️  Não foi possível salvar o QR Code: {e}")

    print("=" * 70)
    print("🌐 Local: http://localhost:8000")
    print(f"🌍 Network: {app_url}")
    print("📊 Status: /api/status")
    print("📚 API Docs: /docs")
    print("=" * 70)
    print("✨ NEW FEATURES:")
    print("   • Suporte a múltiplos clientes simultâneos")
    print("   • Servidor intermediário com PyFFMPEG/OpenCV")
    print("   • Gerenciamento inteligente de streams")
    print("   • Endpoints de status e monitoramento")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    generate_qr_code()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
