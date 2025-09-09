#!/usr/bin/env python3
"""
Configuración para PIX Studio Connection
Conecta automáticamente PIX Studio al PIX Master según las instrucciones de la prueba

Credenciales PIX Master:
- Servidor: https://students.pixrobotics.org/
- Usuario: Prueba_tecnica2025
- Contraseña: Prueba_tecnica2025
"""

import os
import json
import requests
from pathlib import Path


class PIXStudioConfigurator:
    """Configurador para PIX Studio Master Connection"""
    
    def __init__(self):
        self.pix_master_config = {
            'server_url': 'https://students.pixrobotics.org/',
            'username': 'Prueba_tecnica2025', 
            'password': 'Prueba_tecnica2025',
            'auto_connect': True
        }
        
        self.pix_studio_paths = [
            Path.home() / "AppData" / "Local" / "PIX Studio",
            Path.home() / "Documents" / "PIX Studio",
            Path("/opt/pix-studio/"),
            Path("/usr/local/pix-studio/"),
            Path("C:/Program Files/PIX Studio/"),
            Path("C:/Program Files (x86)/PIX Studio/")
        ]
    
    def find_pix_studio_installation(self):
        """Busca la instalación de PIX Studio en el sistema"""
        print("Buscando instalación de PIX Studio...")
        
        for path in self.pix_studio_paths:
            if path.exists():
                print(f"  ✓ PIX Studio encontrado: {path}")
                return path
        
        print("  ⚠ PIX Studio no encontrado en rutas comunes")
        return None
    
    def create_master_connection_config(self, pix_path: Path = None):
        """Crea archivo de configuración para conexión al Master"""
        print("Creando configuración de conexión PIX Master...")
        
        config_data = {
            "master_connection": {
                "enabled": True,
                "server_url": self.pix_master_config['server_url'],
                "username": self.pix_master_config['username'],
                "password_encrypted": False,  # Para pruebas técnicas
                "password": self.pix_master_config['password'],
                "auto_connect": self.pix_master_config['auto_connect'],
                "connection_timeout": 30,
                "retry_attempts": 3,
                "last_connected": None
            },
            "rpa_project": {
                "name": "RPA_Productos_Analysis",
                "version": "1.0.0",
                "description": "Proceso RPA para análisis de productos - Prueba Técnica PIX",
                "author": "PIX RPA Development Team",
                "created_date": "2024-2025"
            },
            "license_info": {
                "type": "PIX_MASTER_STUDENT",
                "max_steps": 42,
                "features_enabled": [
                    "web_automation",
                    "api_consumption", 
                    "database_operations",
                    "file_operations",
                    "excel_generation",
                    "cloud_integration"
                ]
            }
        }
        
        # Crear archivo de configuración
        config_file = Path("pix_master_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Configuración creada: {config_file}")
        return config_file
    
    def test_master_connection(self):
        """Prueba la conexión con PIX Master"""
        print("Probando conexión con PIX Master...")
        
        try:
            # Probar conectividad básica
            response = requests.head(
                self.pix_master_config['server_url'],
                timeout=10
            )
            
            if response.status_code in [200, 404, 403]:  # Server responde
                print("  ✓ PIX Master servidor accesible")
                return True
            else:
                print(f"  ⚠ PIX Master respuesta: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error conectando PIX Master: {e}")
            return False
    
    def generate_pix_studio_instructions(self):
        """Genera instrucciones detalladas para configurar PIX Studio"""
        instructions = """
PIX STUDIO - INSTRUCCIONES DE CONFIGURACIÓN
==========================================

1. DESCARGAR PIX STUDIO:
   - Ve a: https://es.pixrobotics.com/download/
   - Descarga la versión más reciente
   - Instala siguiendo el asistente

2. CONFIGURAR CONEXIÓN AL MASTER:
   - Abre PIX Studio
   - Busca el icono "Master no conectado" (lado izquierdo)
   - Haz clic en el icono
   
3. INTRODUCIR CREDENCIALES:
   En la ventana "Conectar con el Master":
   - Dirección del servidor: https://students.pixrobotics.org/
   - Usuario: Prueba_tecnica2025
   - Contraseña: Prueba_tecnica2025
   - ✓ Marcar "Conectar automáticamente"

4. CONECTAR:
   - Haz clic en "Conectar"
   - Esperar confirmación de conexión exitosa
   - Verificar que el icono cambie a "Master conectado" (verde)

5. VERIFICAR LICENCIA AMPLIADA:
   - La versión demo se amplia a 42 pasos
   - Acceso completo a funcionalidades PIX Studio
   - Listo para desarrollar el proceso RPA

CREDENCIALES PIX MASTER (Para referencia):
- Servidor: https://students.pixrobotics.org/
- Usuario: Prueba_tecnica2025  
- Contraseña: Prueba_tecnica2025

SOPORTE ADICIONAL:
- Academia PIX: https://academy.es.pixrobotics.com/course/index.php
- Documentación: Incluida en PIX Studio
"""
        
        with open("PIX_STUDIO_SETUP.md", 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        print("  ✓ Instrucciones creadas: PIX_STUDIO_SETUP.md")
    
    def setup_pix_rpa_project_template(self):
        """Crea template del proyecto RPA para PIX Studio"""
        project_template = {
            "project_info": {
                "name": "RPA_Productos_Analysis",
                "description": "Análisis automatizado de productos usando Fake Store API",
                "version": "1.0.0",
                "author": "PIX RPA Team",
                "target_platform": "PIX_Studio"
            },
            "process_steps": [
                {
                    "step": 1,
                    "name": "Consumo API",
                    "type": "HTTP_REQUEST",
                    "url": "https://fakestoreapi.com/products",
                    "method": "GET",
                    "output_file": "productos_{date}.json"
                },
                {
                    "step": 2,
                    "name": "Almacenamiento BD",
                    "type": "DATABASE",
                    "database": "SQLite",
                    "table": "Productos",
                    "operation": "INSERT_UNIQUE"
                },
                {
                    "step": 3,
                    "name": "Reporte Excel",
                    "type": "EXCEL_GENERATION",
                    "template": "productos_template.xlsx",
                    "output": "Reporte_{date}.xlsx"
                },
                {
                    "step": 4,
                    "name": "OneDrive Upload",
                    "type": "CLOUD_UPLOAD",
                    "service": "Microsoft_Graph",
                    "destination": "/RPA/Reportes/"
                },
                {
                    "step": 5,
                    "name": "Web Form",
                    "type": "WEB_AUTOMATION",
                    "browser": "Chrome",
                    "form_type": "Google_Forms"
                }
            ],
            "configuration": {
                "retry_attempts": 3,
                "timeout_seconds": 30,
                "log_level": "INFO",
                "screenshot_on_error": True,
                "backup_enabled": True
            }
        }
        
        with open("pix_project_template.json", 'w', encoding='utf-8') as f:
            json.dump(project_template, f, indent=2, ensure_ascii=False)
        
        print("  ✓ Template del proyecto PIX creado: pix_project_template.json")


def main():
    """Función principal de configuración PIX Studio"""
    print("CONFIGURACIÓN PIX STUDIO PARA PRUEBA TÉCNICA")
    print("=" * 50)
    
    configurator = PIXStudioConfigurator()
    
    # 1. Buscar instalación PIX Studio
    pix_path = configurator.find_pix_studio_installation()
    
    # 2. Crear configuración de conexión
    config_file = configurator.create_master_connection_config(pix_path)
    
    # 3. Probar conexión con Master
    configurator.test_master_connection()
    
    # 4. Generar instrucciones detalladas
    configurator.generate_pix_studio_instructions()
    
    # 5. Crear template del proyecto
    configurator.setup_pix_rpa_project_template()
    
    print("\n" + "=" * 50)
    print("CONFIGURACIÓN PIX STUDIO COMPLETADA")
    print("=" * 50)
    print("\nArchivos creados:")
    print("- pix_master_config.json (configuración de conexión)")
    print("- PIX_STUDIO_SETUP.md (instrucciones detalladas)")
    print("- pix_project_template.json (template del proyecto)")
    
    print("\nPRÓXIMOS PASOS:")
    print("1. Instalar PIX Studio desde: https://es.pixrobotics.com/download/")
    print("2. Seguir instrucciones en PIX_STUDIO_SETUP.md")
    print("3. Conectar al Master con credenciales proporcionadas")
    print("4. Importar template del proyecto RPA")
    
    return 0


if __name__ == "__main__":
    main()
