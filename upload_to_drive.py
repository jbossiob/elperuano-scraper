# upload_to_drive.py
import io
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def get_drive_service(token_path: str = "token.json"):
    if not os.path.exists(token_path):
        raise RuntimeError(f"No existe {token_path}. Debes crearlo desde el secret en GitHub Actions.")

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # Si está expirado pero tiene refresh_token, se refresca solo
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("drive", "v3", credentials=creds)


def upload_pdf_to_folder(pdf_path: str, folder_id: str):
    service = get_drive_service()

    filename = os.path.basename(pdf_path)

    file_metadata = {
        "name": filename,
        "parents": [folder_id],
    }

    with open(pdf_path, "rb") as f:
        media = MediaIoBaseUpload(io.BytesIO(f.read()), mimetype="application/pdf", resumable=True)

    created = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id,name,webViewLink",
        supportsAllDrives=True
    ).execute()

    print(f"Uploaded: {created['name']} -> {created['webViewLink']}")
    return created
