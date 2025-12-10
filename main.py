from datetime import datetime
from pathlib import Path
from src import ElPeruanoScraper, Config, setup_logger
from src.upload_drive import upload_to_drive

def main():
    logger = setup_logger(log_level=10)
    logger.info("Starting El Peruano Scraper")
    
    downloaded_file = None
    
    try:
        config = Config()
        
        scraper = ElPeruanoScraper(
            config,
            browser='auto'
        )
        
        # Descargar y SUBIR a Drive
        downloaded_file = scraper.download_bulletin(
            date=None,  # Usa fecha actual de Perú
            delete_after_upload=True,  # ← el PDF se borra localmente luego de subir
            upload_callback=upload_to_drive  # ← función que sube a tu Drive
        )
        
        if downloaded_file:
            logger.info("✓ Download completed successfully!")
            logger.info("✓ Upload and cleanup completed!")
        else:
            logger.error("✗ Download failed")
            return
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return

if __name__ == "__main__":
    main()
