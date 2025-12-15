# src/upload_drive.py
import os
import json
from pathlib import Path
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_drive_service():
    sa_json = os.environ.get("GDRIVE_SA_JSON")
    if not sa_json:
        raise RuntimeError("Falta la variable de entorno GDRIVE_SA_JSON (GitHub Secret).")

    try:
        sa_info = json.loads(sa_json)
    except json.JSONDecodeError as e:
        raise RuntimeError("GDRIVE_SA_JSON no es JSON válido. Revisa el Secret en GitHub.") from e

    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def upload_to_drive(file_path: str | Path, folder_id: Optional[str] = None) -> str:
    """
    Sube un archivo a Google Drive usando Service Account.
    Retorna el fileId de Drive.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    folder_id = folder_id or os.environ.get("DRIVE_FOLDER_ID")
    if not folder_id:
        raise RuntimeError("Falta DRIVE_FOLDER_ID (GitHub Secret) o folder_id como argumento.")

    drive = _get_drive_service()

    file_metadata = {
        "name": path.name,
        "parents": [folder_id],
    }

    media = MediaFileUpload(
        str(path),
        mimetype="application/pdf",
        resumable=True
    )

    created = drive.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, parents"
    ).execute()

    return created["id"]
