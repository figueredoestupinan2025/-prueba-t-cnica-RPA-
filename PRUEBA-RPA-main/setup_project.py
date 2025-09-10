#!/usr/bin/env python3
"""
Script de configuración completa para el proyecto RPA PIX
Crea estructura, instala dependencias y configura el proyecto
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def create_directory_structure():
    """Crea la estructura completa de directorios"""
    print("Creando estructura de directorios...")
    
    directories = [
        'config',
        'modules',
        'utils',
        'data/raw',
        'data/database', 
        'data/temp',
        'reports',
        'logs',
        'evidencias',
        'tests',
        'scripts'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}/")
    
    # Crear archivos __init__.py
    init_files = [
        'config/__init__.py',
        'modules/__init__.py',
        'utils/__init__.py', 
        'tests/__init__.py'
    ]
    
    for init_file in init_files:
        if not Path(init_file).exists():
            Path(init_file).touch()
            print(f"  ✓ {init_file}")


def organize_existing_files():
    """Organiza los archivos existentes en la estructura correcta"""
    print("Organizando archivos existentes...")
    
    file_movements = {
        # Archivos de configuración
        'settings.py': 'config/',
        
        # Módulos principales
        'api_consumer.py': 'modules/',
        'database_manager.py': 'modules/',
        'excel_generator.py': 'modules/',
        'onedrive_client.py': 'modules/', 
        'web_automation.py': 'modules/',
        
        # Utilidades
        'logger.py': 'utils/',
        
        # Scripts
        'create_database.sql': 'scripts/'
    }
    
    for source, destination_dir in file_movements.items():
        source_path = Path(source)
        if source_path.exists():
            destination_path = Path(destination_dir) / source_path.name
            
            # Crear copia de seguridad si ya existe
            if destination_path.exists():
                backup_path = destination_path.with_suffix('.backup')
                shutil.move(str(destination_path), str(backup_path))
                print(f"  ⚠ Backup: {destination_path} -> {backup_path}")
            
            shutil.move(str(source_path), str(destination_path))
            print(f"  ✓ Movido: {source} -> {destination_dir}")
        else:
            print(f"  ⚠ No encontrado: {source}")


def create_init_files():
    """Crea archivos __init__.py con contenido"""
    print("Creando archivos de inicialización...")
    
    # config/__init__.py
    config_init = '''"""
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
'''
    
    # modules/__init__.py
    modules_init = '''"""
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
'''
    
    # utils/__init__.py
    utils_init = '''"""
Utilidades y funciones auxiliares
"""

from .logger import setup_logger, RPALogger

__all__ = [
    'setup_logger',
    'RPALogger'
]
'''
    
    # Escribir archivos
    init_contents = {
        'config/__init__.py': config_init,
        'modules/__init__.py': modules_init,
        'utils/__init__.py': utils_init
    }
    
    for filepath, content in init_contents.items():
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        print(f"  ✓ Creado: {filepath}")


def create_env_file():
    """Crea archivo .env si no existe"""
    print("Configurando variables de entorno...")
    
    if Path('.env').exists():
        print("  ✓ Archivo .env ya existe")
        return
    
    env_content = '''# Configuración RPA PIX
# API
FAKE_STORE_API_URL=https://fakestoreapi.com

# Base de datos  
DATABASE_PATH=data/database/productos.db

# OneDrive (opcional - configurar con tus credenciales)
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=

# Formulario web (opcional - crear en Google Forms)
FORM_URL=
FORM_TYPE=google_forms

# Logging
LOG_LEVEL=INFO
LOG_TO_CONSOLE=true
LOG_TO_FILE=true

# Selenium
WEBDRIVER_HEADLESS=false
'''
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("  ✓ Archivo .env creado")
    print("  ⚠ IMPORTANTE: Configura las credenciales en .env")


def install_dependencies():
    """Instala dependencias de requirements.txt"""
    print("Instalando dependencias...")
    
    if not Path('requirements.txt').exists():
        print("  ❌ requirements.txt no encontrado")
        return False
    
    try:
        # Actualizar pip primero
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
        ])
        
        # Instalar dependencias
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        
        print("  ✓ Dependencias instaladas")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error instalando dependencias: {e}")
        return False


def create_readme():
    """Crea README.md básico"""
    print("Creando documentación...")
    
    readme_content = '''# Proyecto RPA PIX - Análisis de Productos

## Descripción
Proceso RPA automatizado que:
1. Obtiene productos de Fake Store API
2. Los almacena en base de datos SQLite
3. Genera reporte Excel con estadísticas
4. Opcionalmente sube archivos a OneDrive
5. Opcionalmente envía reporte por formulario web

## Instalación

1. Instalar dependencias:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. Configurar variables de entorno:
- Copia `env.example` a `.env`
- Configura tus credenciales de OneDrive y URL del formulario

3. Ejecutar proceso:
\`\`\`bash
python main.py
\`\`\`

## Estructura del Proyecto
\`\`\`
├── config/          # Configuraciones
├── modules/
