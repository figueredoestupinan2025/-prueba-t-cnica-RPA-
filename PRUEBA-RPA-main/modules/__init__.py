# modules/__init__.py
""" 
Módulos principales del proceso RPA 
"""

# Importar módulos principales
try:
    from .api_consumer import FakeStoreAPIConsumer
    from .database_manager import DatabaseManager
    from .excel_generator import ExcelReportGenerator
except ImportError as e:
    print(f"Warning: No se pudieron importar módulos principales: {e}")

# Importar módulos opcionales
try:
    from .onedrive_client import OneDriveClient
except ImportError:
    print("Warning: OneDrive client no disponible")

try:
    from .web_automation import WebFormAutomator
except ImportError:
    print("Warning: Web automation no disponible")

try:
    from .web_form_manager import upload_to_web_form
except ImportError:
    print("Warning: Web form manager no disponible")

try:
    from .evidence_manager import EvidenceManager, initialize_evidence_manager
except ImportError:
    print("Warning: Evidence manager no disponible")

# Importar configuraciones desde el archivo local settings.py
try:
    from .settings import (
        APISettings,
        DatabaseSettings,
        OneDriveSettings,
        WebAutomationSettings,
        ExcelSettings,
        LoggingSettings,
        FileSettings,
        SecuritySettings,
        PIXRPASettings
    )
except ImportError as e:
    print(f"Warning: No se pudieron importar configuraciones locales: {e}")
    # Crear configuraciones básicas como fallback
    
    class APISettings:
        fake_store_base_url = "https://fakestoreapi.com"
        timeout = 30
        max_retries = 3
    
    class DatabaseSettings:
        db_path = "data/products.db"
        backup_enabled = True
    
    class OneDriveSettings:
        upload_folder = "/Reports"
    
    class WebAutomationSettings:
        browser = "chrome"
        headless = False
        implicit_wait = 10
        
        @staticmethod
        def is_configured():
            return False
    
    class ExcelSettings:
        default_sheet_name = "Productos"
        auto_adjust_columns = True
    
    class LoggingSettings:
        level = "INFO"
        file_path = "logs/rpa.log"
    
    class FileSettings:
        data_folder = "data"
        reports_folder = "reports"
    
    class SecuritySettings:
        encrypt_sensitive_data = True
    
    class PIXRPASettings:
        project_name = "PIX RPA - Análisis de Productos"
        version = "1.0.0"
        author = "PIX RPA Development Team"

# Definir qué se exporta cuando se hace "from modules import *"
__all__ = [
    # Módulos principales
    'FakeStoreAPIConsumer',
    'DatabaseManager', 
    'ExcelReportGenerator',
    # Módulos opcionales (si están disponibles)
    'OneDriveClient',
    'WebFormAutomator',
    'upload_to_web_form',
    'EvidenceManager',
    'initialize_evidence_manager',
    # Configuraciones
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

# Metadatos del paquete
__version__ = '1.0.0'
__author__ = 'PIX RPA Development Team'
__description__ = 'Módulos para análisis automatizado de productos'

# Función de inicialización opcional
def initialize_modules():
    """Inicializa y verifica todos los módulos disponibles"""
    available_modules = []
    
    # Verificar módulos principales
    try:
        from .api_consumer import FakeStoreAPIConsumer
        available_modules.append('api_consumer')
    except ImportError:
        pass
        
    try:
        from .database_manager import DatabaseManager
        available_modules.append('database_manager')
    except ImportError:
        pass
        
    try:
        from .excel_generator import ExcelReportGenerator
        available_modules.append('excel_generator')
    except ImportError:
        pass
    
    # Verificar módulos opcionales
    optional_modules = [
        'onedrive_client', 'web_automation', 
        'web_form_manager', 'evidence_manager'
    ]
    
    for module_name in optional_modules:
        try:
            __import__(f'.{module_name}', package=__name__)
            available_modules.append(module_name)
        except ImportError:
            pass
    
    return available_modules

# Auto-inicialización si se desea
if __name__ == '__main__':
    available = initialize_modules()
    print(f"Módulos disponibles: {available}")