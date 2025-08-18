import cv2
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

from constants.camera import CAMERAS_MAPPING

app = FastAPI()

# Gera as abas de navegação para todas as câmeras


def render_tabs(selected=None):
    tabs = ""
    for name in CAMERAS_MAPPING.keys():
        active = "active-tab" if name == selected else ""
        tabs += f"<a href='/camera/{name}' class='tab {active}'>{name}</a>"
    return tabs


@app.get("/", response_class=HTMLResponse)
def index():
    tabs = render_tabs()
    return f"""
    <html>
    <head>
        <title>Visualização de Câmeras</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; }}
            .header {{ text-align: center; padding: 2rem 0 1rem 0; background: #222; color: #fff; }}
            .tabs {{ display: flex; justify-content: center; background: #333; padding: 0.5rem 0; }}
            .tab {{ color: #fff; text-decoration: none; padding: 0.7rem 2rem; margin: 0 0.2rem; border-radius: 8px 8px 0 0; background: #444; transition: background 0.2s; }}
            .tab:hover {{ background: #666; }}
            .active-tab {{ background: #fff; color: #222; font-weight: bold; }}
            .main-content {{ display: flex; flex-direction: column; align-items: center; margin-top: 3rem; }}
            .info {{ margin-top: 2rem; color: #555; }}
        </style>
    </head>
    <body>
        <div class='header'>
            <h1>Visualização de Câmeras</h1>
        </div>
        <div class='tabs'>
            {tabs}
        </div>
        <div class='main-content'>
            <div class='info'>Selecione uma câmera acima para visualizar.</div>
        </div>
    </body>
    </html>
    """


@app.get("/camera/{camera_name}", response_class=HTMLResponse)
def camera_page(camera_name: str):
    if camera_name not in CAMERAS_MAPPING:
        raise HTTPException(status_code=404, detail="Câmera não encontrada")
    tabs = render_tabs(selected=camera_name)
    return f"""
    <html>
    <head>
        <title>Câmera: {camera_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; }}
            .header {{ text-align: center; padding: 2rem 0 1rem 0; background: #222; color: #fff; }}
            .tabs {{ display: flex; justify-content: center; background: #333; padding: 0.5rem 0; }}
            .tab {{ color: #fff; text-decoration: none; padding: 0.7rem 2rem; margin: 0 0.2rem; border-radius: 8px 8px 0 0; background: #444; transition: background 0.2s; }}
            .tab:hover {{ background: #666; }}
            .active-tab {{ background: #fff; color: #222; font-weight: bold; }}
            .main-content {{ display: flex; flex-direction: column; align-items: center; margin-top: 2rem; }}
            .camera-title {{ font-size: 2rem; margin-bottom: 1.5rem; color: #222; }}
            .camera-img-wrapper {{ background: #fff; padding: 1.5rem; border-radius: 16px; box-shadow: 0 2px 16px #0001; display: flex; flex-direction: column; align-items: center; }}
            .camera-img {{ max-width: 90vw; max-height: 70vh; border-radius: 8px; box-shadow: 0 1px 8px #0002; }}
            .back-link {{ margin-top: 2rem; color: #333; text-decoration: none; font-size: 1rem; }}
            .back-link:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class='header'>
            <h1>Visualização de Câmeras</h1>
        </div>
        <div class='tabs'>
            {tabs}
        </div>
        <div class='main-content'>
            <div class='camera-title'>Câmera: {camera_name}</div>
            <div class='camera-img-wrapper'>
                <img src='/video_feed/{camera_name}' class='camera-img' />
            </div>
            <a href='/' class='back-link'>&larr; Voltar para lista de câmeras</a>
        </div>
    </body>
    </html>
    """


def gen_frames(rtsp_url):
    cap = cv2.VideoCapture(rtsp_url)
    while True:
        success, frame = cap.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
    cap.release()


@app.get("/video_feed/{camera_name}")
def video_feed(camera_name: str):
    if camera_name not in CAMERAS_MAPPING:
        raise HTTPException(status_code=404, detail="Câmera não encontrada")
    rtsp_url = CAMERAS_MAPPING[camera_name]
    return StreamingResponse(gen_frames(rtsp_url), media_type="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
