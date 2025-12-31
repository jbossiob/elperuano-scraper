from src import ElPeruanoScraper, Config, setup_logger, upload_pdf_to_drive

def main():
    logger = setup_logger(log_level=10)
    logger.info("Starting El Peruano Scraper")

    try:
        config = Config()

        scraper = ElPeruanoScraper(
            config,
            browser="auto"
        )

        downloaded_file = scraper.download_bulletin(
            date=None,
            delete_after_upload=True,
            upload_callback=upload_pdf_to_drive
        )

        if downloaded_file:
            logger.info(f"Pipeline completed successfully: {downloaded_file}")
        else:
            logger.error("Pipeline failed")

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
