# upload_latest.py
from pathlib import Path
import os
from upload_to_drive import upload_pdf_to_folder

IN_DIR = Path("downloads")

def main():
    folder_id = os.environ.get("GDRIVE_FOLDER_ID")
    if not folder_id:
        raise RuntimeError("Falta la variable de entorno GDRIVE_FOLDER_ID")

    pdfs = sorted(IN_DIR.glob("*.pdf"))
    if not pdfs:
        raise SystemExit("No PDFs found in downloads/")

    latest = pdfs[-1]
    upload_pdf_to_folder(str(latest), folder_id)

if __name__ == "__main__":
    main()
