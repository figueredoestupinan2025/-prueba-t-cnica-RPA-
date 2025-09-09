"""
Módulos principales del proceso RPA
"""

from .database_manager import DatabaseManager
from .excel_generator import ExcelReportGenerator
from .onedrive_client import OneDriveClient
from .web_automation import WebFormAutomator

__all__ = [
    'DatabaseManager',
    'ExcelReportGenerator', 
    'OneDriveClient',
    'WebFormAutomator'
]

__version__ = '1.0.0'
__author__ = 'PIX RPA Development Team'
__description__ = 'Módulos para análisis automatizado de productos'
