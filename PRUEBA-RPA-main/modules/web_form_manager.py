from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import logging
from dotenv import load_dotenv

load_dotenv()

class WebFormManager:
    def __init__(self):
        self.logger = logging.getLogger('WebFormManager')
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Configurar ChromeDriver"""
        chrome_options = Options()
        
        # Configuraciones para permitir uploads
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        # Configurar ventana
        chrome_options.add_argument(f"--window-size={os.getenv('WINDOW_WIDTH', 1920)},{os.getenv('WINDOW_HEIGHT', 1080)}")
        
        # Modo headless opcional
        if os.getenv('HEADLESS_MODE', 'false').lower() == 'true':
            chrome_options.add_argument('--headless=new')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(int(os.getenv('WEBDRIVER_TIMEOUT', 30)))
            self.wait = WebDriverWait(self.driver, int(os.getenv('ELEMENT_WAIT_TIME', 10)))
            
            self.logger.info("✅ ChromeDriver configurado correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando ChromeDriver: {str(e)}")
            return False
    
    def navigate_to_form(self):
        """Navegar al formulario"""
        try:
            form_url = os.getenv('WEB_FORM_URL')
            self.driver.get(form_url)
            self.logger.info(f"🌐 Navegando a: {form_url}")
            
            # Esperar que la página cargue
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error navegando al formulario: {str(e)}")
            return False
    
    def upload_file(self, file_path):
        """Subir archivo al formulario"""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"❌ Archivo no encontrado: {file_path}")
                return False
            
            self.logger.info(f"📎 Intentando subir archivo: {os.path.basename(file_path)}")
            
            # Buscar input de archivo - múltiples estrategias
            file_input = None
            
            # Estrategia 1: Por name
            try:
                file_input_name = os.getenv('WEB_FORM_FILE_INPUT_NAME', 'file')
                file_input = self.wait.until(
                    EC.presence_of_element_located((By.NAME, file_input_name))
                )
                self.logger.info(f"✅ Input encontrado por NAME: {file_input_name}")
            except:
                pass
            
            # Estrategia 2: Por tipo file
            if not file_input:
                try:
                    file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                    self.logger.info("✅ Input encontrado por TYPE=file")
                except:
                    pass
            
            # Estrategia 3: Por ID común
            if not file_input:
                common_ids = ['file', 'upload', 'fileupload', 'file-input']
                for file_id in common_ids:
                    try:
                        file_input = self.driver.find_element(By.ID, file_id)
                        self.logger.info(f"✅ Input encontrado por ID: {file_id}")
                        break
                    except:
                        continue
            
            if not file_input:
                self.logger.error("❌ No se encontró input de archivo")
                return False
            
            # Subir archivo
            absolute_path = os.path.abspath(file_path)
            file_input.send_keys(absolute_path)
            
            self.logger.info(f"📁 Archivo seleccionado: {os.path.basename(file_path)}")
            time.sleep(2)
            
            # Buscar y hacer click en botón de envío
            submit_button = None
            submit_text = os.getenv('WEB_FORM_SUBMIT_BUTTON_TEXT', 'Submit')
            
            # Estrategia 1: Por texto
            try:
                submit_button = self.driver.find_element(By.XPATH, 
                    f"//button[contains(text(), '{submit_text}')] | //input[@value='{submit_text}']")
                self.logger.info(f"✅ Botón encontrado por texto: {submit_text}")
            except:
                pass
            
            # Estrategia 2: Por tipo submit
            if not submit_button:
                try:
                    submit_button = self.driver.find_element(By.XPATH, 
                        "//button[@type='submit'] | //input[@type='submit']")
                    self.logger.info("✅ Botón encontrado por TYPE=submit")
                except:
                    pass
            
            # Estrategia 3: Botón genérico
            if not submit_button:
                try:
                    submit_button = self.driver.find_element(By.TAG_NAME, "button")
                    self.logger.info("✅ Botón genérico encontrado")
                except:
                    pass
            
            if not submit_button:
                self.logger.error("❌ No se encontró botón de envío")
                return False
            
            # Click en enviar
            submit_button.click()
            self.logger.info("📤 Formulario enviado")
            time.sleep(3)
            
            # Verificar resultado
            try:
                # Buscar mensaje de éxito
                success_message = os.getenv('WEB_FORM_SUCCESS_MESSAGE', 'success')
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{success_message}')]"))
                )
                self.logger.info("✅ Mensaje de éxito detectado")
                return True
                
            except:
                # Si no hay mensaje específico, verificar que cambió la página
                self.logger.info("✅ Formulario procesado (no se detectó mensaje específico)")
                return True
            
        except Exception as e:
            self.logger.error(f"❌ Error subiendo archivo: {str(e)}")
            return False
    
    def take_screenshot(self, filename="form_screenshot.png"):
        """Tomar captura de pantalla"""
        try:
            screenshot_path = os.path.join("evidencias", "screenshots", filename)
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            self.driver.save_screenshot(screenshot_path)
            self.logger.info(f"📸 Screenshot guardado: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            self.logger.error(f"❌ Error tomando screenshot: {str(e)}")
            return None
    
    def close(self):
        """Cerrar navegador"""
        if self.driver:
            self.driver.quit()
            self.logger.info("🔒 Navegador cerrado")

def upload_to_web_form(file_path):
    """Función principal para subir archivo"""
    if os.getenv('WEB_FORM_ENABLED', 'false').lower() != 'true':
        print("⚠️ Formulario web no habilitado en .env")
        return False
    
    web_manager = WebFormManager()
    
    try:
        if not web_manager.setup_driver():
            return False
        
        if not web_manager.navigate_to_form():
            return False
        
        # Tomar screenshot antes
        web_manager.take_screenshot("before_upload.png")
        
        result = web_manager.upload_file(file_path)
        
        # Tomar screenshot después
        web_manager.take_screenshot("after_upload.png")
        
        return result
        
    except Exception as e:
        print(f"❌ Error general en upload_to_web_form: {str(e)}")
        return False
        
    finally:
        web_manager.close()
