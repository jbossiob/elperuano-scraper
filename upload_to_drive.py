import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_drive_service():
    sa_json = os.environ.get("GDRIVE_SA_KEY")
    if not sa_json:
        raise RuntimeError("Falta la variable de entorno GDRIVE_SA_KEY")

    creds_info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

def upload_pdf_to_folder(pdf_path: Path, folder_id: str) -> str:
    service = get_drive_service()

    file_metadata = {
        "name": pdf_path.name,
        "parents": [folder_id],
    }

    media = MediaFileUpload(
        str(pdf_path),
        mimetype="application/pdf",
        resumable=True,
    )

    created = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, name")
        .execute()
    )

    print(f"✅ Uploaded to Drive: {created['name']} (id={created['id']})")
    return created["id"]
