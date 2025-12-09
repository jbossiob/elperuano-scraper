from datetime import datetime
from pathlib import Path
from src import ElPeruanoScraper, Config, setup_logger
from src.upload_drive import upload_to_drive
import shutil
import os

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
        
        # ✅ DESCARGA SIN BORRAR EL ARCHIVO LOCAL
        downloaded_file = scraper.download_bulletin(
            date=None,  # Usa fecha actual de Perú
            delete_after_upload=False,  # ✅ MUY IMPORTANTE
            upload_callback=upload_to_drive
        )
        
        if not downloaded_file:
            logger.error("✗ Download failed")
            return
        
        logger.info("✓ Download completed successfully!")
        logger.info("✓ Upload completed successfully!")

        # ✅ ASEGURAR QUE EXISTA /downloads
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)

        # ✅ COPIAR EL ARCHIVO FINAL A /downloads PARA ANALYZE.TS
        source_path = Path(downloaded_file)
        target_path = downloads_dir / source_path.name

        shutil.copy(source_path, target_path)

        logger.info(f"✓ Copia local creada para análisis: {target_path}")

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return

if __name__ == "__main__":
    main()
