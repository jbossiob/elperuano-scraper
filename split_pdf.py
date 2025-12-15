from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter

IN_DIR = Path("downloads")
OUT_DIR = Path("downloads/chunks")
PAGES_PER_CHUNK = 25  # ajusta: 20/25 suele ir bien

def split_pdf(pdf_path: Path):
    reader = PdfReader(str(pdf_path))
    total = len(reader.pages)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    base = pdf_path.stem
    for start in range(0, total, PAGES_PER_CHUNK):
        writer = PdfWriter()
        end = min(start + PAGES_PER_CHUNK, total)
        for i in range(start, end):
            writer.add_page(reader.pages[i])

        out = OUT_DIR / f"{base}_p{start+1:03d}-{end:03d}.pdf"
        with open(out, "wb") as f:
            writer.write(f)
        print(f"Created: {out}")

def main():
    pdfs = sorted(IN_DIR.glob("*.pdf"))
    if not pdfs:
        raise SystemExit("No PDFs found in downloads/")
    split_pdf(pdfs[-1])

if __name__ == "__main__":
    main()
