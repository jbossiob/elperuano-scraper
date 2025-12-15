from src import ElPeruanoScraper, Config, setup_logger

def main():
    logger = setup_logger(log_level=10)
    logger.info("Starting El Peruano Scraper")

    try:
        config = Config()

        scraper = ElPeruanoScraper(
            config,
            browser="auto"
        )

        # ✅ Solo descargar (sin subir, sin borrar)
        downloaded_file = scraper.download_bulletin(
            date=None,                 # usa fecha actual de Perú
            delete_after_upload=False, # NO borrar el PDF
            upload_callback=None       # NO subir a ningún lado
        )

        if downloaded_file:
            logger.info(f"✓ Download completed successfully: {downloaded_file}")
        else:
            logger.error("✗ Download failed")

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
