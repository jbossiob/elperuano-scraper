from pathlib import Path
from upload_to_drive import upload_pdf_to_folder

DRIVE_FOLDER_ID = "1y7QRmbETlzL1cTBobyEdvxQBzpbZubcW"
DOWNLOADS_DIR = Path("downloads")

def upload_latest_pdf():
    pdfs = sorted(DOWNLOADS_DIR.glob("*.pdf"), key=lambda p: p.stat().st_mtime)
    if not pdfs:
        raise SystemExit("No hay PDFs en downloads/")
    latest = pdfs[-1]
    upload_pdf_to_folder(latest, DRIVE_FOLDER_ID)

if __name__ == "__main__":
    # aquí va tu lógica actual de descarga...
    # e.g. run_scraper()

    upload_latest_pdf()
