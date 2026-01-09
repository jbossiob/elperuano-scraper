from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from src import ElPeruanoScraper, Config, setup_logger, upload_pdf_to_drive
from split_pdf import split_pdf
from src.index_scraper import scrape_normas_index


def main():
    logger = setup_logger(log_level=10)
    logger.info("Starting El Peruano Scraper")

    try:
        config = Config()

        scraper = ElPeruanoScraper(
            config,
            browser="auto"
        )

        pdf_path = scraper.download_bulletin(
            date=None,
            delete_after_upload=False,  # NO borrar aún
            upload_callback=None
        )

        if not pdf_path:
            logger.error("Download failed")
            return

        index_file = scrape_normas_index()
        logger.info(f"Uploading index file {index_file.name} to Drive...")
        upload_pdf_to_drive(index_file)

        logger.info("Splitting PDF into chunks...")
        chunks = split_pdf(Path(pdf_path))

        logger.info(f"{len(chunks)} chunks created")

        for chunk in chunks:
            logger.info(f"Uploading {chunk.name} to Drive...")
            upload_pdf_to_drive(chunk)


        logger.info("✓ All chunks uploaded successfully")

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
