import time
import logging
import requests
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo  

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions


class ElPeruanoScraper:
    
    SUPPORTED_BROWSERS = ['chrome', 'firefox', 'edge', 'auto']
    
    def __init__(self, config_or_path, headless: bool = True, browser: str = 'auto'):
      
        if hasattr(config_or_path, 'DOWNLOAD_DIR'):
            self.config = config_or_path
            self.download_dir = config_or_path.DOWNLOAD_DIR
            self.headless = getattr(config_or_path, 'HEADLESS', headless)
        else:
            self.config = None
            self.download_dir = Path(config_or_path)
            self.headless = headless
        
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.browser = browser.lower()
        if self.browser not in self.SUPPORTED_BROWSERS:
            raise ValueError(f"Navegador no soportado. Use: {', '.join(self.SUPPORTED_BROWSERS)}")
        
        self.logger = logging.getLogger("elperuano_scraper")
        self.driver = None
        
        mode = "HEADLESS (sin ventana)" if self.headless else "VISIBLE (con ventana)"
        self.logger.info(f"Modo de navegador: {mode}")
    
    def get_peru_date(self) -> str:
        try:
            peru_tz = ZoneInfo("America/Lima")
            peru_now = datetime.now(peru_tz)
            date_str = peru_now.strftime("%d/%m/%Y")
            
            self.logger.info(f"Fecha actual en Perú: {date_str}")
            return date_str
            
        except Exception as e:
            self.logger.warning(f"No se pudo obtener zona horaria de Perú: {e}")
            date_str = datetime.now().strftime("%d/%m/%Y")
            self.logger.info(f"Usando fecha local: {date_str}")
            return date_str
    
    def _setup_chrome(self) -> webdriver.Chrome:
        options = ChromeOptions()
        
        if self.headless:
            options.add_argument("--headless=new")
            self.logger.info("Chrome configurado en modo HEADLESS")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        
        self.logger.info("✓ Chrome configurado")
        return driver
    
    def _setup_firefox(self) -> webdriver.Firefox:
        options = FirefoxOptions()
        
        if self.headless:
            options.add_argument("--headless")
            self.logger.info("Firefox configurado en modo HEADLESS")
        
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", str(self.download_dir.absolute()))
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
        options.set_preference("pdfjs.disabled", True)
        
        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(60)
        
        self.logger.info("✓ Firefox configurado")
        return driver
    
    def _setup_edge(self) -> webdriver.Edge:
        options = EdgeOptions()
        
        if self.headless:
            options.add_argument("--headless=new")
            self.logger.info("Edge configurado en modo HEADLESS")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--log-level=3")
        
        driver = webdriver.Edge(options=options)
        driver.set_page_load_timeout(60)
        
        self.logger.info("✓ Edge configurado")
        return driver
        
    def _detect_available_browser(self):
        self.logger.info("Auto-detectando navegadores disponibles...")

        browsers_to_try = ['chrome', 'firefox', 'edge']

        for browser in browsers_to_try:
            try:
                self.logger.info(f"Probando {browser.upper()}...")

                if browser == 'chrome':
                    options = ChromeOptions()
                    options.add_argument("--headless=new")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-gpu")
                    driver = webdriver.Chrome(options=options)

                elif browser == 'firefox':
                    options = FirefoxOptions()
                    options.add_argument("--headless")
                    driver = webdriver.Firefox(options=options)

                elif browser == 'edge':
                    options = EdgeOptions()
                    options.add_argument("--headless=new")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-gpu")
                    driver = webdriver.Edge(options=options)

                driver.quit()
                self.logger.info(f"✓ {browser.upper()} disponible")
                return browser

            except Exception as e:
                self.logger.warning(f"✗ {browser.upper()} no disponible: {e}")
                continue

        raise RuntimeError(
            "❌ No se encontró ningún navegador instalado. "
            "Instala Chrome, Firefox o Edge."
        )

    def _setup_driver(self):
        """Configura el driver del navegador"""
        self.logger.info(f"Configurando navegador: {self.browser.upper()}")
        
        try:
            if self.browser == 'auto':
                self.browser = self._detect_available_browser()
            
            if self.browser == 'chrome':
                return self._setup_chrome()
            elif self.browser == 'firefox':
                return self._setup_firefox()
            elif self.browser == 'edge':
                return self._setup_edge()
                
        except Exception as e:
            self.logger.error(f"Error configurando {self.browser}: {e}")
            
            if self.browser != 'auto':
                self.logger.info("Intentando auto-detección de navegadores...")
                try:
                    self.browser = self._detect_available_browser()
                    return self._setup_driver()
                except Exception as fallback_error:
                    raise RuntimeError(
                        f"No se pudo inicializar ningún navegador. "
                        f"Error original: {e}. "
                        f"Fallback: {fallback_error}"
                    )
    
    def _fill_date_field(self, field_id: str, date: str):
        self.logger.info(f"Llenando campo {field_id} con fecha: {date}")
        
        date_input = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.ID, field_id))
        )
        
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
            date_input
        )
        time.sleep(0.5)
        
        self.driver.execute_script("arguments[0].value = '';", date_input)
        time.sleep(0.3)
        self.driver.execute_script(f"arguments[0].value = '{date}';", date_input)
        
        self.logger.info(f"✓ Campo {field_id} llenado")
    
    
    def _download_single_cuadernillo(self, date: str) -> str:
        try:
            self.logger.info("Buscando primer cuadernillo completo...")
            
            cuadernillo_btn = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-tipo='CuNl']"))
            )
            
            pdf_url = cuadernillo_btn.get_attribute("data-url")
            
            if not pdf_url:
                self.logger.error("No se encontró URL del cuadernillo")
                return None
            
            self.logger.info(f"✓ Cuadernillo encontrado: {pdf_url}")
            
            output_path = self.download_dir / f"{date}.pdf"
            
            self.logger.info(f"Descargando PDF...")
            response = requests.get(pdf_url, timeout=120)
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                file_size = output_path.stat().st_size / (1024 * 1024)
                self.logger.info(f"✓ Descarga completa: {output_path.name} ({file_size:.2f} MB)")
                return str(output_path)
            else:
                self.logger.error(f"Error HTTP: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error al descargar cuadernillo: {e}")
            return None
    
    def _cleanup_file(self, file_path: str) -> bool:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                self.logger.info(f" Archivo borrado: {path.name}")
                return True
            else:
                self.logger.warning(f"Archivo no encontrado para borrar: {file_path}")
                return False
        except PermissionError:
            self.logger.error(f"Sin permisos para borrar: {file_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error al borrar archivo: {e}")
            return False
    
    def download_bulletin(self, date: str = None, delete_after_upload: bool = False, 
                         upload_callback=None) -> str:

        try:
            if date is None:
                date = self.get_peru_date()
            
            day, month, year = date.split("/")
            date_str = f"{year}{month}{day}"
            
            self.logger.info("Iniciando navegador...")
            self.driver = self._setup_driver()
            
            url = "https://diariooficial.elperuano.pe/Normas"
            self.logger.info(f"Navegando a {url}")
            self.driver.get(url)
            time.sleep(5)
            
            
            file_path = self._download_single_cuadernillo(date_str)

            if file_path:
                self.logger.info("=" * 60)
                self.logger.info(f"✓ DESCARGA EXITOSA: {file_path}")
                self.logger.info("=" * 60)
                
                # Si se debe borrar después de subir
                if delete_after_upload and upload_callback:
                    self.logger.info("Procediendo a subir archivo...")
                    try:
                        upload_result = upload_callback(file_path)
                        
                        if upload_result is not None:
                            self.logger.info("✓ Subida exitosa, borrando archivo local...")
                            self._cleanup_file(file_path)
                        else:
                            self.logger.warning("⚠️  Subida falló, archivo conservado")
                    except Exception as e:
                        self.logger.error(f"Error durante la subida: {e}")
                        self.logger.info("Archivo conservado debido al error")

            return file_path
            
        except Exception as e:
            self.logger.error(f"Error durante el scraping: {e}")
            if self.driver:
                try:
                    self.driver.save_screenshot("error_screenshot.png")
                    self.logger.info("Screenshot guardado: error_screenshot.png")
                except:
                    pass
            return None
            
        finally:
            if self.driver:
                self.logger.info("Cerrando navegador...")
                time.sleep(2)
                self.driver.quit()
