# config/__init__.py
"""
Configuraciones centralizadas del proyecto RPA
"""

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

# modules/__init__.py
"""
Módulos principales del proceso RPA
"""

from .api_consumer import FakeStoreAPIConsumer
from .database_manager import DatabaseManager
from .excel_generator import ExcelReportGenerator
from .onedrive_client import OneDriveClient
from .web_automation import WebFormAutomator

__all__ = [
    'FakeStoreAPIConsumer',
    'DatabaseManager',
    'ExcelReportGenerator', 
    'OneDriveClient',
    'WebFormAutomator'
]

__version__ = '1.0.0'
__author__ = 'PIX RPA Development Team'
__description__ = 'Módulos para análisis automatizado de productos'

# utils/__init__.py
"""
Utilidades y funciones auxiliares
"""

from .logger import setup_logger, RPALogger, log_info, log_error, log_warning, log_step
from .helpers import (
    validate_file_path,
    calculate_file_hash,
    format_file_size,
    format_duration,
    sanitize_filename,
    safe_json_loads,
    safe_json_dumps,
    create_backup_copy,
    cleanup_temp_files,
    compress_files,
    extract_zip,
    get_directory_size,
    ensure_directory_exists,
    is_file_locked,
    wait_for_file_unlock,
    generate_unique_filename,
    copy_file_with_retry,
    get_file_info,
    validate_json_structure,
    merge_dictionaries,
    flatten_dictionary,
    create_temp_file,
    parse_date_flexible
)

__all__ = [
    # Logger
    'setup_logger', 'RPALogger', 'log_info', 'log_error', 'log_warning', 'log_step',
    
    # File utilities
    'validate_file_path', 'calculate_file_hash', 'format_file_size', 'format_duration',
    'sanitize_filename', 'create_backup_copy', 'cleanup_temp_files', 'compress_files',
    'extract_zip', 'get_directory_size', 'ensure_directory_exists', 'is_file_locked',
    'wait_for_file_unlock', 'generate_unique_filename', 'copy_file_with_retry',
    'get_file_info', 'create_temp_file',
    
    # Data utilities
    'safe_json_loads', 'safe_json_dumps', 'validate_json_structure', 
    'merge_dictionaries', 'flatten_dictionary', 'parse_date_flexible'
]
