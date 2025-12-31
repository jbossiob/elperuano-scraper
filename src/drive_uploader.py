import os
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def get_drive_service():
    """
    Crea un cliente de Google Drive usando OAuth de usuario (refresh token).
    Variables requeridas:
    - GOOGLE_CLIENT_ID
    - GOOGLE_CLIENT_SECRET
    - GOOGLE_REFRESH_TOKEN
    """
    creds = Credentials(
        token=None,
        refresh_token=os.environ.get("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES,
    )

    if not creds.refresh_token:
        raise RuntimeError("Falta GOOGLE_REFRESH_TOKEN")

    creds.refresh(Request())
    return build("drive", "v3", credentials=creds)


def upload_pdf_to_drive(
    file_path: str | Path,
    folder_id: Optional[str] = None
) -> dict:
    """
    Sube un PDF a Google Drive usando OAuth usuario.
    Retorna metadata del archivo creado.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    folder_id = folder_id or os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    if not folder_id:
        raise RuntimeError("Falta GOOGLE_DRIVE_FOLDER_ID")

    service = get_drive_service()

    file_metadata = {
        "name": path.name,
        "parents": [folder_id],
    }

    media = MediaFileUpload(
        str(path),
        mimetype="application/pdf",
        resumable=True
    )

    created = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id,name,webViewLink"
    ).execute()

    return created
