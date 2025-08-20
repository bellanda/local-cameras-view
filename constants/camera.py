import dotenv
import polars

from utils.construct_rtsp_url import construct_rtsp_url

dotenv.load_dotenv()

cameras_df = polars.read_excel("cameras.xlsx")

# df Columns: Nome, Usuário, Senha, IP, Marca (assuming brand column exists)
# If brand column doesn't exist, default to HIKVISION format

CAMERAS_MAPPING = {}
for obj in cameras_df.to_dicts():
    camera_name = obj["Nome"]
    username = obj["Usuário"]
    password = obj["Senha"]
    ip = obj["IP"]

    # Check if brand column exists, otherwise default to HIKVISION
    brand = obj.get("Marca", "HIKVISION")

    try:
        rtsp_url = construct_rtsp_url(brand, username, password, ip)
        CAMERAS_MAPPING[camera_name] = rtsp_url
    except ValueError as e:
        print(f"Warning: {e} for camera {camera_name}. Using default HIKVISION format.")
        # Fallback to HIKVISION format
        rtsp_url = construct_rtsp_url("HIKVISION", username, password, ip)
        CAMERAS_MAPPING[camera_name] = rtsp_url

print(CAMERAS_MAPPING)
