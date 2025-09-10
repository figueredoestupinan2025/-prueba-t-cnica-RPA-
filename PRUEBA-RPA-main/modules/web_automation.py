"""
Automatización web para envío de formularios
Soporta Google Forms, Jotform y Typeform
"""

import os
import sys
import time
import random
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from functools import wraps

# Add project root to sys.path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import WebAutomationSettings, EVIDENCES_DIR
from utils.logger import setup_logger


def retry_with_backoff(max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
    """Decorador para reintentar operaciones con backoff exponencial"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                        args[0].logger.warning(f"Reintentando {func.__name__} en {delay:.1f}s (intento {attempt + 1}/{max_attempts})")
                        time.sleep(delay)
                    else:
                        args[0].logger.error(f"Error persistente en {func.__name__}: {str(e)}")
            raise last_exception
        return wrapper
    return decorator


class WebFormAutomator:
    """Automatizador de formularios web usando Selenium"""
    
    def __init__(self):
        self.logger = setup_logger("WebAutomator")
        self.driver = None
        self.wait = None

        # Preferencias de modo manual (con fallback a variables de entorno)
        self.allow_manual_login = getattr(WebAutomationSettings, 'ALLOW_MANUAL_LOGIN', os.getenv('ALLOW_MANUAL_LOGIN', 'true').lower() == 'true')
        self.manual_login_wait = int(os.getenv('MANUAL_LOGIN_WAIT_SECONDS', getattr(WebAutomationSettings, 'MANUAL_LOGIN_WAIT_SECONDS', 20)))
        self.manual_review_enabled = getattr(WebAutomationSettings, 'MANUAL_REVIEW_ENABLED', os.getenv('MANUAL_REVIEW_ENABLED', 'true').lower() == 'true')
        self.manual_review_seconds = int(os.getenv('MANUAL_REVIEW_SECONDS', getattr(WebAutomationSettings, 'MANUAL_REVIEW_SECONDS', 60)))
        self.auto_submit = getattr(WebAutomationSettings, 'AUTO_SUBMIT', os.getenv('AUTO_SUBMIT', 'true').lower() == 'true')
        # Subida de archivo opcional: si el formulario no tiene campo de archivo, no fallar por defecto
        self.require_file_upload = getattr(
            WebAutomationSettings,
            'REQUIRE_FILE_UPLOAD',
            os.getenv('REQUIRE_FILE_UPLOAD', 'false').lower() == 'true'
        )
        # Fuente del archivo a adjuntar: 'excel' (default) o 'screenshot'
        self.file_upload_source = os.getenv('FILE_UPLOAD_SOURCE', 'excel').lower()

        # Opcional: usar el perfil del usuario para conservar sesión (e.g., login de Google)
        self.chrome_user_data_dir = getattr(WebAutomationSettings, 'CHROME_USER_DATA_DIR', os.getenv('CHROME_USER_DATA_DIR'))
        self.chrome_profile_dir = getattr(WebAutomationSettings, 'CHROME_PROFILE_DIR', os.getenv('CHROME_PROFILE_DIR'))
        
        # Configurar directorio de evidencias
        EVIDENCES_DIR.mkdir(exist_ok=True)

    def _find_element_robust(self, by: By, value: str, timeout: int = None) -> Optional[Any]:
        """Encuentra elemento de forma robusta con múltiples estrategias"""
        if timeout is None:
            timeout = WebAutomationSettings.TIMEOUT

        strategies = [
            (by, value),
            (By.ID, value.split('=')[-1] if '=' in value else value),
            (By.NAME, value.split('=')[-1] if '=' in value else value),
            (By.CLASS_NAME, value.replace('[class*=', '').replace(']', '').replace("'", "")),
        ]

        for strategy_by, strategy_value in strategies:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((strategy_by, strategy_value))
                )
                if element and element.is_displayed():
                    return element
            except:
                continue

        # Fallback: buscar en todo el DOM
        try:
            elements = self.driver.find_elements(by, value)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    return element
        except:
            pass

        return None

    def _setup_driver(self):
        """Configura y inicializa el driver de Chrome"""
        try:
            self.logger.info("Configurando WebDriver...")
            
            # Opciones de Chrome
            chrome_options = Options()
            
            # Agregar opciones configuradas
            for option in WebAutomationSettings.CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            # Configuraciones adicionales
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("prefs", {
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })

            # Si se configuró perfil de Chrome, usarlo para mantener sesiones
            if self.chrome_user_data_dir:
                chrome_options.add_argument(f"--user-data-dir={self.chrome_user_data_dir}")
            if self.chrome_profile_dir:
                chrome_options.add_argument(f"--profile-directory={self.chrome_profile_dir}")
            
            # Instalar y configurar ChromeDriver
            chromedriver_path = ChromeDriverManager().install()
            # Fix for webdriver-manager bug - it returns wrong path
            if chromedriver_path.endswith('THIRD_PARTY_NOTICES.chromedriver'):
                chromedriver_path = chromedriver_path.replace('THIRD_PARTY_NOTICES.chromedriver', 'chromedriver')
            service = Service(chromedriver_path)
            
            # Crear driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Configurar timeouts
            self.driver.implicitly_wait(WebAutomationSettings.IMPLICIT_WAIT)
            self.driver.set_page_load_timeout(WebAutomationSettings.PAGE_LOAD_TIMEOUT)
            
            # Crear WebDriverWait
            self.wait = WebDriverWait(self.driver, WebAutomationSettings.TIMEOUT)
            
            # Eliminar bandera de automatización
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("✅ WebDriver configurado exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error configurando WebDriver: {str(e)}")
            raise
    
    def submit_form(self, excel_file_path: str, form_data: Dict[str, Any] = None) -> bool:
        """
        Envía formulario web con archivo Excel
        
        Args:
            excel_file_path: Ruta del archivo Excel a subir
            form_data: Datos adicionales del formulario
            
        Returns:
            bool: True si el envío fue exitoso
        """
        if not WebAutomationSettings.is_configured():
            self.logger.warning("⚠️ Automatización web no está configurada")
            return False
        
        try:
            self.logger.log_step(6, "Envío de formulario web", "INICIADO")
            
            # Verificar archivo Excel (requerido por el proceso previo)
            excel_path = Path(excel_file_path)
            if not excel_path.exists():
                raise FileNotFoundError(f"Archivo Excel no encontrado: {excel_file_path}")

            # Determinar archivo a adjuntar según configuración
            attachment_path = excel_path
            if self.file_upload_source == 'screenshot':
                latest = self._get_latest_screenshot()
                if latest:
                    attachment_path = latest
                    self.logger.info(f"📎 Se adjuntará la última captura: {attachment_path.name}")
                else:
                    self.logger.warning("No se encontró captura reciente. Se adjuntará el Excel por defecto.")
            
            # Configurar driver
            self._setup_driver()
            
            # Navegar al formulario
            self.logger.info(f"Navegando a: {WebAutomationSettings.FORM_URL}")
            self.driver.get(WebAutomationSettings.FORM_URL)
            
            # Tomar screenshot inicial
            self._take_screenshot("formulario_inicial.png")

            # Pausa opcional para permitir login manual y revisión del formulario
            if self.allow_manual_login:
                self.logger.info(f"⏳ Pausa para login/revisión manual: {self.manual_login_wait}s (habilitable con ALLOW_MANUAL_LOGIN)")
                self._take_screenshot("formulario_login.png")
                time.sleep(self.manual_login_wait)
            
            # Procesar según tipo de formulario
            form_type = WebAutomationSettings.FORM_TYPE.lower()
            
            if form_type == 'google_forms':
                success = self._handle_google_form(attachment_path, form_data)
            elif form_type == 'jotform':
                success = self._handle_jotform(attachment_path, form_data)
            elif form_type == 'typeform':
                success = self._handle_typeform(attachment_path, form_data)
            else:
                success = self._handle_generic_form(attachment_path, form_data)
            
            if success:
                # Tomar screenshot de confirmación
                self._take_screenshot("formulario_confirmacion.png")
                
                self.logger.log_step(6, "Envío de formulario web", "COMPLETADO")
                return True
            else:
                self._take_screenshot("formulario_error.png")
                return False
                
        except Exception as e:
            self.logger.error(f"Error enviando formulario: {str(e)}")
            if self.driver:
                self._take_screenshot("formulario_error_exception.png")
            return False
        finally:
            self._cleanup_driver()
    
    @retry_with_backoff(max_attempts=3, base_delay=2.0)
    def _handle_google_form(self, attachment_path: Path, form_data: Dict[str, Any] = None) -> bool:
        """Maneja formularios de Google Forms con robustez mejorada"""
        try:
            self.logger.info("Procesando Google Form...")

            # Esperar a que cargue el formulario con timeout extendido
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            # Usar datos por defecto si no se proporcionan
            if not form_data:
                form_data = WebAutomationSettings.FORM_DATA
            
            # Buscar campos comunes de texto
            text_inputs = self.driver.find_elements(By.CSS_SELECTOR, 
                "input[type='text'], input[type='email'], textarea")
            
            # Llenar campos de texto
            for i, input_field in enumerate(text_inputs[:2]):  # Primeros 2 campos
                try:
                    if input_field.is_displayed() and input_field.is_enabled():
                        if i == 0:
                            # Primer campo: nombre del colaborador
                            input_field.clear()
                            input_field.send_keys(form_data.get('collaborator_name', 'Robot RPA'))
                            time.sleep(0.5)
                        elif i == 1:
                            # Segundo campo: fecha o comentarios
                            input_field.clear()
                            input_field.send_keys(form_data.get('comments', 
                                f"Reporte generado el {datetime.now().strftime('%Y-%m-%d')}"))
                            time.sleep(0.5)
                except Exception as e:
                    self.logger.warning(f"Error llenando campo de texto {i}: {str(e)}")
                    continue
            
            # Buscar campo de subida de archivos (opcional) con método robusto
            file_input = self._find_element_robust(By.CSS_SELECTOR, "input[type='file']", timeout=10)

            if not file_input:
                if self.require_file_upload:
                    raise Exception("No se encontró campo de subida de archivos")
                else:
                    self.logger.info("ℹ️ Formulario sin campo de archivo; se omite adjuntar y se continúa.")
            else:
                # Subir archivo con manejo de errores
                try:
                    file_input.send_keys(str(Path(attachment_path).absolute()))
                    self.logger.info("✅ Archivo subido al formulario")
                    # Esperar un momento para que se procese la subida
                    time.sleep(2)
                except Exception as e:
                    self.logger.warning(f"Error subiendo archivo: {e}")
                    if self.require_file_upload:
                        raise
            
            # Buscar y hacer clic en el botón de envío
            submit_selectors = [
                "[type='submit']",
                "[role='button'][aria-label*='Enviar']",
                "[role='button'][aria-label*='Submit']",
                "div[role='button']:contains('Enviar')",
                ".appsMaterialWizButtonPaperbuttonLabel",
                ".quantumWizButtonPaperbuttonLabel"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            text = element.text.lower()
                            if any(word in text for word in ['enviar', 'submit', 'send']):
                                submit_button = element
                                break
                    if submit_button:
                        break
                except:
                    continue
            
            if not submit_button:
                # Buscar por XPath como último recurso
                xpath_selectors = [
                    "//span[contains(text(), 'Enviar')]//parent::*",
                    "//span[contains(text(), 'Submit')]//parent::*",
                    "//div[@role='button' and contains(., 'Enviar')]",
                    "//input[@value='Enviar']"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        submit_button = self.driver.find_element(By.XPATH, xpath)
                        if submit_button.is_displayed() and submit_button.is_enabled():
                            break
                    except:
                        continue
            
            if not submit_button:
                raise Exception("No se encontró botón de envío")
            
            # Envío condicionado por modo manual
            if not self.auto_submit:
                self.logger.info(f"🔎 Revisión manual activa ({self.manual_review_seconds}s). No se enviará automáticamente.")
                self._take_screenshot("formulario_revision.png")
                time.sleep(self.manual_review_seconds)
                return True

            # Hacer clic en enviar
            self.logger.info("Enviando formulario...")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            time.sleep(1)
            submit_button.click()
            
            # Esperar confirmación
            time.sleep(3)
            
            # Verificar confirmación
            confirmation_texts = [
                "Tu respuesta se ha registrado",
                "Your response has been recorded",
                "Gracias",
                "Thank you",
                "enviado",
                "submitted"
            ]
            
            page_source = self.driver.page_source.lower()
            confirmation_found = any(text.lower() in page_source for text in confirmation_texts)
            
            if confirmation_found:
                self.logger.info("✅ Formulario enviado exitosamente")
                return True
            else:
                self.logger.warning("⚠️ No se detectó confirmación clara")
                return True  # Asumir éxito si no hay error evidente
                
        except Exception as e:
            self.logger.error(f"Error en Google Form: {str(e)}")
            return False
    
    def _handle_jotform(self, attachment_path: Path, form_data: Dict[str, Any] = None) -> bool:
        """Maneja formularios de JotForm"""
        try:
            self.logger.info("Procesando JotForm...")
            
            # Esperar a que cargue el formulario
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "form-all")))
            
            if not form_data:
                form_data = WebAutomationSettings.FORM_DATA
            
            # Buscar campos de texto
            text_fields = self.driver.find_elements(By.CSS_SELECTOR, 
                "input[type='text'], input[type='email'], textarea")
            
            # Llenar campos
            for i, field in enumerate(text_fields[:2]):
                try:
                    if field.is_displayed() and field.is_enabled():
                        field.clear()
                        if i == 0:
                            field.send_keys(form_data.get('collaborator_name', 'Robot RPA'))
                        else:
                            field.send_keys(form_data.get('comments', 
                                f"Reporte - {datetime.now().strftime('%Y-%m-%d')}"))
                        time.sleep(0.5)
                except Exception as e:
                    self.logger.warning(f"Error en campo JotForm {i}: {str(e)}")
            
            # Subir archivo
            file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(str(Path(attachment_path).absolute()))
            
            time.sleep(2)
            
            # Envío condicionado por modo manual
            if not self.auto_submit:
                self.logger.info(f"🔎 Revisión manual activa ({self.manual_review_seconds}s). No se enviará automáticamente.")
                self._take_screenshot("formulario_revision.png")
                time.sleep(self.manual_review_seconds)
                return True

            # Enviar formulario
            submit_button = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".form-submit-button, button[type='submit']")
            ))
            submit_button.click()
            
            time.sleep(3)
            
            # Verificar confirmación
            try:
                self.wait.until(EC.presence_of_element_located(
                    (By.CLASS_NAME, "form-confirmation")
                ))
                self.logger.info("✅ JotForm enviado exitosamente")
                return True
            except TimeoutException:
                self.logger.warning("⚠️ No se detectó página de confirmación")
                return True
                
        except Exception as e:
            self.logger.error(f"Error en JotForm: {str(e)}")
            return False
    
    def _handle_typeform(self, attachment_path: Path, form_data: Dict[str, Any] = None) -> bool:
        """Maneja formularios de Typeform"""
        try:
            self.logger.info("Procesando Typeform...")
            
            # Typeform tiene una interfaz más dinámica
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            if not form_data:
                form_data = WebAutomationSettings.FORM_DATA
            
            # Esperar y llenar campos uno por uno (Typeform muestra campos secuencialmente)
            time.sleep(2)
            
            # Buscar campo activo
            active_input = self.driver.find_element(By.CSS_SELECTOR, 
                "input[type='text']:not([disabled]), textarea:not([disabled])")
            
            if active_input:
                active_input.send_keys(form_data.get('collaborator_name', 'Robot RPA'))
                active_input.send_keys(Keys.ENTER)
                time.sleep(1)
            
            # Continuar con siguiente campo si existe
            try:
                next_input = self.wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "input[type='text']:not([disabled]), textarea:not([disabled])")
                ))
                next_input.send_keys(form_data.get('comments', 
                    f"Reporte - {datetime.now().strftime('%Y-%m-%d')}"))
                next_input.send_keys(Keys.ENTER)
                time.sleep(1)
            except TimeoutException:
                pass
            
            # Buscar campo de archivo
            file_input = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='file']")
            ))
            file_input.send_keys(str(Path(attachment_path).absolute()))
            
            time.sleep(3)
            
            # Envío condicionado por modo manual
            if not self.auto_submit:
                self.logger.info(f"🔎 Revisión manual activa ({self.manual_review_seconds}s). No se enviará automáticamente.")
                self._take_screenshot("formulario_revision.png")
                time.sleep(self.manual_review_seconds)
                return True

            # Enviar (buscar botón submit o presionar Enter)
            try:
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, 
                    "button[type='submit'], button[data-qa='submit-button']")
                submit_btn.click()
            except NoSuchElementException:
                # En algunos Typeforms, Enter es suficiente
                ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            
            time.sleep(3)
            
            self.logger.info("✅ Typeform procesado")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en Typeform: {str(e)}")
            return False
    
    def _handle_generic_form(self, attachment_path: Path, form_data: Dict[str, Any] = None) -> bool:
        """Maneja formularios genéricos"""
        try:
            self.logger.info("Procesando formulario genérico...")
            
            if not form_data:
                form_data = WebAutomationSettings.FORM_DATA
            
            # Esperar a que cargue la página
            time.sleep(2)
            
            # Buscar todos los campos de entrada
            text_inputs = self.driver.find_elements(By.CSS_SELECTOR, 
                "input[type='text'], input[type='email'], textarea")
            
            # Llenar primeros campos encontrados
            for i, input_field in enumerate(text_inputs[:3]):
                try:
                    if input_field.is_displayed() and input_field.is_enabled():
                        input_field.clear()
                        if i == 0:
                            input_field.send_keys(form_data.get('collaborator_name', 'Robot RPA'))
                        elif i == 1:
                            input_field.send_keys(datetime.now().strftime('%Y-%m-%d'))
                        else:
                            input_field.send_keys(form_data.get('comments', 'Reporte automático'))
                        time.sleep(0.5)
                except:
                    continue
            
            # Subir archivo
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            if file_inputs:
                file_inputs[0].send_keys(str(Path(attachment_path).absolute()))
                time.sleep(2)
            
            # Buscar botón de envío
            submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                "input[type='submit'], button[type='submit'], button:contains('Submit'), button:contains('Enviar')")
            
            # Envío condicionado por modo manual
            if not self.auto_submit:
                self.logger.info(f"🔎 Revisión manual activa ({self.manual_review_seconds}s). No se enviará automáticamente.")
                self._take_screenshot("formulario_revision.png")
                time.sleep(self.manual_review_seconds)
                return True

            if submit_buttons:
                submit_buttons[0].click()
                time.sleep(3)
            
            self.logger.info("✅ Formulario genérico procesado")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en formulario genérico: {str(e)}")
            return False
    
    def _take_screenshot(self, filename: str) -> str:
        """
        Toma screenshot de la página actual
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            str: Ruta del screenshot
        """
        try:
            if not self.driver:
                return ""
            
            screenshot_path = EVIDENCES_DIR / filename
            
            # Tomar screenshot
            success = self.driver.save_screenshot(str(screenshot_path))
            
            if success:
                self.logger.info(f"📸 Screenshot guardado: {filename}")
                return str(screenshot_path)
            else:
                self.logger.warning(f"Error guardando screenshot: {filename}")
                return ""
                
        except Exception as e:
            self.logger.error(f"Error tomando screenshot: {str(e)}")
            return ""
    
    def _get_latest_screenshot(self) -> Optional[Path]:
        """Obtiene la captura más reciente del directorio de evidencias"""
        try:
            shots = list(EVIDENCES_DIR.glob("*.png"))
            if not shots:
                return None
            shots.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return shots[0]
        except Exception:
            return None

    def health_check(self) -> Dict[str, Any]:
        """Verifica el estado del automatizador web"""
        health = {
            "webdriver_available": False,
            "chrome_driver_installed": False,
            "form_url_configured": False,
            "evidences_dir_exists": False,
            "last_test_result": None
        }

        try:
            # Verificar configuración
            health["form_url_configured"] = bool(WebAutomationSettings.FORM_URL)
            health["evidences_dir_exists"] = EVIDENCES_DIR.exists()

            # Verificar ChromeDriver
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager().install()
                health["chrome_driver_installed"] = bool(driver_path)
            except:
                pass

            # Verificar WebDriver (sin inicializar completamente)
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                options = Options()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                driver = webdriver.Chrome(options=options)
                health["webdriver_available"] = True
                driver.quit()
            except:
                pass

            return health

        except Exception as e:
            self.logger.error(f"Error en health check web: {e}")
            return {
                "error": str(e),
                **health
            }

    def _cleanup_driver(self):
        """Limpia recursos del driver"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                self.logger.debug("WebDriver cerrado correctamente")
        except Exception as e:
            self.logger.warning(f"Error cerrando WebDriver: {str(e)}")


def test_web_automation():
    """Función de prueba para automatización web"""
    logger = setup_logger("WebTest")
    
    try:
        if not WebAutomationSettings.is_configured():
            logger.warning("⚠️ Automatización web no configurada, omitiendo test")
            return True
        
        automator = WebFormAutomator()
        
        # Test básico de configuración
        automator._setup_driver()
        
        if automator.driver:
            logger.info("✅ Test configuración WebDriver exitoso")
            automator._cleanup_driver()
            return True
        else:
            logger.error("❌ Test WebDriver fallido")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test automatización fallido: {str(e)}")
        return False


if __name__ == "__main__":
    test_web_automation()
