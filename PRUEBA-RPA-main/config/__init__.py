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
    PIXRPASettings,
    BASE_DIR,
    DATA_DIR,
    REPORTS_DIR,
    LOGS_DIR,
    EVIDENCES_DIR
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
    'PIXRPASettings',
    'BASE_DIR',
    'DATA_DIR',
    'REPORTS_DIR',
    'LOGS_DIR',
    'EVIDENCES_DIR'
]

__version__ = '1.0.0'
__author__ = 'PIX RPA Development Team'
