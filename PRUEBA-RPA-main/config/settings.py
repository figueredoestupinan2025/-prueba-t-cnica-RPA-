"""
Configuraciones centralizadas para el proyecto RPA
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

# Paths base del proyecto
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"
EVIDENCES_DIR = BASE_DIR / "evidencias"

# Crear directorios si no existen
for directory in [DATA_DIR, REPORTS_DIR, LOGS_DIR, EVIDENCES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
    
# Subdirectorios de data
(DATA_DIR / "raw").mkdir(exist_ok=True)
(DATA_DIR / "database").mkdir(exist_ok=True)
(DATA_DIR / "temp").mkdir(exist_ok=True)


class APISettings:
    """Configuraciones para el consumo de APIs"""
    
    FAKE_STORE_URL = os.getenv('FAKE_STORE_API_URL', 'https://fakestoreapi.com')
    PRODUCTS_ENDPOINT = f"{FAKE_STORE_URL}/products"
    TIMEOUT = int(os.getenv('API_TIMEOUT', 30))
    RETRY_ATTEMPTS = int(os.getenv('API_RETRY_ATTEMPTS', 3))
    BACKOFF_FACTOR = float(os.getenv('RETRY_BACKOFF_FACTOR', 0.3))
    
    # Headers para las peticiones
    HEADERS = {
        'User-Agent': 'RPA-Productos/1.0',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }


class DatabaseSettings:
    """Configuraciones para la base de datos"""
    
    DATABASE_PATH = DATA_DIR / "database" / "productos.db"
    BACKUP_ENABLED = os.getenv('DATABASE_BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_INTERVAL_HOURS = int(os.getenv('DATABASE_BACKUP_INTERVAL', 24))
    
    # Configuraciones de conexión
    TIMEOUT = 30
    ISOLATION_LEVEL = None  # Autocommit
    
    # Configuraciones de rendimiento
    JOURNAL_MODE = 'WAL'
    SYNCHRONOUS = 'NORMAL'
    CACHE_SIZE = 2000
    
    @classmethod
    def get_connection_string(cls):
        """Retorna la cadena de conexión"""
        return str(cls.DATABASE_PATH.absolute())


class OneDriveSettings:
    """Configuraciones para Microsoft OneDrive"""
    
    CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
    CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
    TENANT_ID = os.getenv('AZURE_TENANT_ID')
    
    # Rutas en OneDrive
    JSON_PATH = os.getenv('ONEDRIVE_JSON_PATH', 'RPA/Logs')
    REPORTS_PATH = os.getenv('ONEDRIVE_REPORTS_PATH', 'RPA/Reportes')
    EVIDENCES_PATH = os.getenv('ONEDRIVE_EVIDENCES_PATH', 'RPA/Evidencias')
    
    # Comportamiento ante conflicto de nombre de archivo: 'replace' (default) o 'rename'
    CONFLICT_BEHAVIOR = os.getenv('ONEDRIVE_CONFLICT_BEHAVIOR', 'replace')
    
    # Configuraciones de Graph API
    GRAPH_URL = 'https://graph.microsoft.com/v1.0'
    SCOPE = ['https://graph.microsoft.com/.default']
    
    # Target user for app-only (optional)
    TARGET_USER_ID = os.getenv('ONEDRIVE_USER_ID')  # e.g. GUID
    TARGET_USER_EMAIL = os.getenv('ONEDRIVE_USER_EMAIL')  # e.g. user@domain.com
    
    # Configuraciones de subida
    CHUNK_SIZE = 1024 * 1024 * 4  # 4MB chunks para archivos grandes
    MAX_FILE_SIZE = 1024 * 1024 * 250  # 250MB máximo
    
    @classmethod
    def get_drive_base_url(cls):
        """Devuelve la URL base del drive para Graph API, compatible con app-only o delegada"""
        if cls.TARGET_USER_ID or cls.TARGET_USER_EMAIL:
            user = cls.TARGET_USER_ID or cls.TARGET_USER_EMAIL
            return f"{cls.GRAPH_URL}/users/{user}/drive"
        # Nota: /me requiere flujo delegado (token de usuario). Para app-only se recomienda 'users/{id|email}'.
        return f"{cls.GRAPH_URL}/me/drive"

    @classmethod
    def is_configured(cls):
        """Verifica si OneDrive está configurado"""
        return all([cls.CLIENT_ID, cls.CLIENT_SECRET, cls.TENANT_ID])


class WebAutomationSettings:
    """Configuraciones para automatización web"""
    
    FORM_URL = os.getenv('FORM_URL', 'https://docs.google.com/forms/d/e/1FAIpQLSdVQEHNQsSIBN3Tl1bEBJaABs_3Mg4Wv_Wbg1oXnFM7wsrjUA/viewform?usp=dialog')
    FORM_TYPE = os.getenv('FORM_TYPE', 'google_forms')
    
    # Configuraciones de Selenium
    HEADLESS = os.getenv('WEBDRIVER_HEADLESS', 'false').lower() == 'true'
    TIMEOUT = int(os.getenv('WEBDRIVER_TIMEOUT', 30))
    IMPLICIT_WAIT = 10
    PAGE_LOAD_TIMEOUT = 30
    
    # Configuraciones de Chrome
    CHROME_OPTIONS = [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-extensions',
        '--disable-plugins',
        '--window-size=1920,1080'
    ]
    
    if HEADLESS:
        CHROME_OPTIONS.append('--headless')
    
    # Configuraciones de screenshots
    SCREENSHOT_QUALITY = int(os.getenv('SCREENSHOT_QUALITY', 95))
    SCREENSHOT_FORMAT = 'PNG'
    
    # Datos del formulario
    FORM_DATA = {
        'collaborator_name': 'Robot RPA Automatizado',
        'comments': 'Reporte generado automáticamente por proceso RPA'
    }
    
    @classmethod
    def is_configured(cls):
        """Verifica si la automatización web está configurada"""
        return bool(cls.FORM_URL)


class ExcelSettings:
    """Configuraciones para generación de reportes Excel"""
    
    ENGINE = os.getenv('EXCEL_ENGINE', 'openpyxl')
    INCLUDE_CHARTS = os.getenv('INCLUDE_CHARTS', 'true').lower() == 'true'
    LANGUAGE = os.getenv('REPORT_LANGUAGE', 'es')
    
    # Configuraciones de formato
    HEADER_STYLE = {
        'font': {'bold': True, 'color': '000000'},
        'fill': {'fgColor': 'CCCCCC', 'patternType': 'solid'},
        'alignment': {'horizontal': 'center'}
    }
    
    DATA_STYLE = {
        'alignment': {'horizontal': 'left'},
        'number_format': '#,##0.00'  # Para números
    }
    
    # Nombres de hojas según idioma
    SHEET_NAMES = {
        'es': {
            'products': 'Productos',
            'summary': 'Resumen'
        },
        'en': {
            'products': 'Products', 
            'summary': 'Summary'
        }
    }
    
    # Configuraciones de columnas
    COLUMN_WIDTHS = {
        'id': 10,
        'title': 40,
        'price': 15,
        'category': 20,
        'description': 50,
        'fecha_insercion': 20
    }


class LoggingSettings:
    """Configuraciones para el sistema de logging"""
    
    LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    TO_FILE = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'
    TO_CONSOLE = os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true'
    MAX_FILES = int(os.getenv('LOG_MAX_FILES', 7))
    
    # Configuraciones de archivos
    LOG_FORMAT = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Configuraciones de seguridad
    MASK_CREDENTIALS = os.getenv('MASK_CREDENTIALS_IN_LOGS', 'true').lower() == 'true'
    ENCRYPT_LOGS = os.getenv('ENCRYPT_SENSITIVE_LOGS', 'false').lower() == 'true'


class FileSettings:
    """Configuraciones para manejo de archivos"""
    
    # Formatos de fecha para nombres de archivo
    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
    
    # Prefijos para diferentes tipos de archivo
    JSON_PREFIX = 'Productos_'
    EXCEL_PREFIX = 'Reporte_'
    EVIDENCE_PREFIX = 'evidencia_'
    
    # Extensiones
    JSON_EXTENSION = '.json'
    EXCEL_EXTENSION = '.xlsx'
    IMAGE_EXTENSION = '.png'
    LOG_EXTENSION = '.log'
    
    # Configuraciones de encoding
    DEFAULT_ENCODING = 'utf-8'
    JSON_ENSURE_ASCII = False
    JSON_INDENT = 2


class SecuritySettings:
    """Configuraciones de seguridad"""
    
    # Campos sensibles que deben enmascararse en logs
    SENSITIVE_FIELDS = [
        'password', 'secret', 'token', 'key', 'credential',
        'client_secret', 'api_key', 'auth', 'authorization',
        'bearer', 'access_token', 'refresh_token'
    ]
    
    # Configuraciones de validación
    MAX_FILE_SIZE_MB = 100
    ALLOWED_EXTENSIONS = ['.json', '.xlsx', '.png', '.pdf']
    
    # Timeout de operaciones
    DEFAULT_TIMEOUT = 30
    LONG_OPERATION_TIMEOUT = 300


class PIXRPASettings:
    """Configuraciones específicas para PIX RPA"""
    
    VERSION = os.getenv('PIX_STUDIO_VERSION', 'latest')
    PROJECT_NAME = os.getenv('PIX_PROJECT_NAME', 'RPA_Productos_Analysis')
    
    # Configuraciones de integración
    USE_PIX_LOGGING = True
    PIX_LOG_FORMAT = '[{timestamp}] {level}: {message}'
    
    # Configuraciones de rendimiento
    PARALLEL_PROCESSING = False
    MAX_WORKERS = 1  # PIX RPA funciona mejor con un solo hilo


# Validar configuraciones críticas al importar
def validate_settings():
    """Valida que las configuraciones críticas estén presentes"""
    errors = []
    
    # Validar base de datos
    if not DatabaseSettings.DATABASE_PATH.parent.exists():
        try:
            DatabaseSettings.DATABASE_PATH.parent.mkdir(parents=True)
        except Exception as e:
            errors.append(f"No se puede crear directorio de BD: {e}")
    
    # Validar OneDrive (opcional)
    if not OneDriveSettings.is_configured():
        print("⚠️ WARNING: OneDrive no está configurado completamente")
    
    # Validar automatización web (opcional)
    if not WebAutomationSettings.is_configured():
        print("⚠️ WARNING: Automatización web no está configurada")
    
    if errors:
        raise ValueError(f"Errores de configuración: {', '.join(errors)}")
    
    return True


def validate_configuration():
    """
    Verifica que los componentes críticos y opcionales estén configurados.
    Devuelve un diccionario con el estado de cada componente.
    """
    status = {
        'api': True,  # Suponiendo que la API siempre está configurada
        'database': True,  # Suponiendo que la BD siempre está configurada
        'directories': True,  # Suponiendo que los directorios existen
        'onedrive': False,  # Cambia a True si tienes credenciales en .env
        'web_automation': False  # Cambia a True si tienes configurado el formulario web
    }
    # Aquí puedes agregar lógica real para verificar cada componente
    return status

def print_configuration_status():
    """
    Imprime el estado actual de la configuración.
    """
    status = validate_configuration()
    print("Estado de configuración:")
    for key, value in status.items():
        print(f"  {key}: {'OK' if value else 'NO CONFIGURADO'}")


# Validar al importar
try:
    validate_settings()
    print("✅ Configuraciones validadas correctamente")
except Exception as e:
    print(f"❌ Error en configuraciones: {e}")


# Exportar configuraciones principales
__all__ = [
    'APISettings',
    'DatabaseSettings', 
    'OneDriveSettings',
    'WebAutomationSettings',
    'ExcelSettings',
    'LoggingSettings',
    'FileSettings',
    'SecuritySettings',
    'PIXRPASettings'
]
