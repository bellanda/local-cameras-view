import dotenv
import polars

dotenv.load_dotenv()

cameras_df = polars.read_excel("cameras.xlsx")

# df Columns:  Nome, Usuário, Senha, IP

CAMERAS_MAPPING = {
    obj["Nome"]: f"rtsp://{obj['Usuário']}:{obj['Senha']}@{obj['IP']}:554/Streaming/Channels/101"
    for obj in cameras_df.to_dicts()
}

print(CAMERAS_MAPPING)
