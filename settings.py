# modules/settings.py
"""
Configuraciones específicas para los módulos RPA
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class APISettings:
    """Configuraciones para APIs"""
    fake_store_base_url: str = "https://fakestoreapi.com"
    timeout: int = 30
    max_retries: int = 3
    
@dataclass
class DatabaseSettings:
    """Configuraciones de base de datos"""
    db_path: str = "data/products.db"
    backup_enabled: bool = True
    backup_interval: int = 3600  # segundos
    
@dataclass
class OneDriveSettings:
    """Configuraciones de OneDrive"""
    client_id: str = os.getenv('ONEDRIVE_CLIENT_ID', '')
    client_secret: str = os.getenv('ONEDRIVE_CLIENT_SECRET', '')
    tenant_id: str = os.getenv('ONEDRIVE_TENANT_ID', '')
    upload_folder: str = "/Reports"
    
@dataclass
class WebAutomationSettings:
    """Configuraciones de automatización web"""
    browser: str = "chrome"
    headless: bool = False
    implicit_wait: int = 10
    page_load_timeout: int = 30
    
@dataclass
class ExcelSettings:
    """Configuraciones de Excel"""
    default_sheet_name: str = "Productos"
    auto_adjust_columns: bool = True
    include_charts: bool = True
    
@dataclass
class LoggingSettings:
    """Configuraciones de logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/rpa.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
@dataclass
class FileSettings:
    """Configuraciones de archivos"""
    base_path: Path = Path(__file__).parent.parent
    data_folder: str = "data"
    reports_folder: str = "reports"
    logs_folder: str = "logs"
    temp_folder: str = "temp"
    
@dataclass
class SecuritySettings:
    """Configuraciones de seguridad"""
    encrypt_sensitive_data: bool = True
    hash_algorithm: str = "sha256"
    token_expiry: int = 3600  # segundos
    
@dataclass
class PIXRPASettings:
    """Configuraciones principales del proyecto PIX RPA"""
    project_name: str = "PIX RPA - Análisis de Productos"
    version: str = "1.0.0"
    author: str = "PIX RPA Development Team"
    description: str = "Proceso completo de análisis de productos"
    
    # Configuraciones específicas
    api: APISettings = APISettings()
    database: DatabaseSettings = DatabaseSettings()
    onedrive: OneDriveSettings = OneDriveSettings()
    web: WebAutomationSettings = WebAutomationSettings()
    excel: ExcelSettings = ExcelSettings()
    logging: LoggingSettings = LoggingSettings()
    files: FileSettings = FileSettings()
    security: SecuritySettings = SecuritySettings()