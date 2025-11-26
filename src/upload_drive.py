import json
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_ID = '1DZVh2uxV6sgbzJMTDRHBTMDtt29iTSZI'

def get_drive_service():
    # Cargar token desde GitHub Secrets
    token_data = os.getenv("GOOGLE_TOKEN")
    
    if not token_data:
        raise Exception("GOOGLE_TOKEN no está configurado como secret en GitHub.")

    creds_dict = json.loads(token_data)
    creds = Credentials.from_authorized_user_info(creds_dict, SCOPES)

    # Refrescar token automáticamente
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build('drive', 'v3', credentials=creds)


def upload_to_drive(file_path):
    if not os.path.exists(file_path):
        print(f"✗ El archivo no existe: {file_path}")
        return None
    
    service = get_drive_service()
    file_name = os.path.basename(file_path)

    file_metadata = {
        'name': file_name,
        'parents': [FOLDER_ID]
    }

    media = MediaFileUpload(file_path, resumable=True)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    print(f"✓ Subido: {file_name}")
    print(f"🔗 Link: {file.get('webViewLink')}")

    return file.get("id")
