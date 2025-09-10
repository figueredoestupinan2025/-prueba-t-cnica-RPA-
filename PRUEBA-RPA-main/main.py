#!/usr/bin/env python3
"""
PIX RPA - Proceso completo de análisis de productos
Incluye: API, Base de datos, Excel, OneDrive, Web Automation y Evidencias

Autor: PIX RPA Development Team
Fecha: 2024-2025
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Añadir directorios al path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / 'modules'))
sys.path.insert(0, str(current_dir / 'config'))

# Importar módulos principales
try:
    from modules.api_consumer import FakeStoreAPIConsumer as APIConsumer
    from modules.database_manager import DatabaseManager
    from modules.excel_generator import ExcelReportGenerator as ExcelGenerator
    print("✓ Módulos principales importados correctamente")
except ImportError as e:
    print(f"❌ Error importando módulos principales: {e}")
    print("Intentando importación directa...")
    try:
        from api_consumer import FakeStoreAPIConsumer as APIConsumer
        from database_manager import DatabaseManager
        from excel_generator import ExcelReportGenerator as ExcelGenerator
        print("✓ Módulos principales importados (método alternativo)")
    except ImportError as e2:
        print(f"❌ Error crítico importando módulos: {e2}")
        sys.exit(1)

# Importar módulos extendidos
try:
    from modules.onedrive_client import OneDriveClient as OneDriveManager
    from modules.web_automation import WebFormAutomator as WebFormAutomation
    from modules.web_form_manager import upload_to_web_form
    from modules.evidence_manager import EvidenceManager, initialize_evidence_manager
    print("✓ Módulos extendidos importados correctamente")
except ImportError as e:
    print(f"⚠️ Algunos módulos extendidos no disponibles: {e}")
    print("Continuando con módulos básicos...")
    # Crear clases mock para módulos opcionales
    class OneDriveManager:
        def authenticate(self): return False
        def upload_excel_report(self, path): return None
    
    class WebFormAutomation:
        def submit_form(self, path): return False
    
    class EvidenceManager:
        def capture_process_evidence(self, *args, **kwargs): pass
        def capture_file_operation(self, *args, **kwargs): pass
        def save_evidence_log(self, *args, **kwargs): return None
    
    def upload_to_web_form(path): return False
    def initialize_evidence_manager(): return EvidenceManager()

# Importar configuraciones
try:
    from config.settings import WebAutomationSettings
    print("✓ Configuraciones importadas desde config")
except ImportError:
    print("⚠️ Configuraciones no disponibles, usando valores por defecto")
    class WebAutomationSettings:
        @staticmethod
        def is_configured(): return False


class PIXRPAProcess:
    """Proceso principal PIX RPA"""

    def __init__(self):
        self._setup_logging()
        self.logger = logging.getLogger("PIX_RPA_MAIN")
        self.logger.info("🚀 Inicializando PIX RPA Process")

        # Inicializar gestores principales
        try:
            self.api_consumer = APIConsumer()
            self.db_manager = DatabaseManager()
            self.excel_generator = ExcelGenerator()
            self.logger.info("✓ Gestores principales inicializados")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando gestores principales: {e}")
            raise

        # Inicializar gestores opcionales
        try:
            self.onedrive_manager = OneDriveManager()
            self.web_automation = WebFormAutomation()
            self.evidence_manager = initialize_evidence_manager()
            self.logger.info("✓ Gestores opcionales inicializados")
        except Exception as e:
            self.logger.warning(f"⚠️ Algunos gestores opcionales no disponibles: {e}")

        self.start_time = datetime.now()
        self.process_stats = {
            "productos_procesados": 0,
            "pasos_completados": 0,
            "archivos_generados": [],
            "evidencias_capturadas": 0,
            "inicio": self.start_time.isoformat(),
        }

    def _setup_logging(self):
        """Configura el logging centralizado"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_filename = f"pix_rpa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_filepath = log_dir / log_filename

        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%H:%M:%S",
            handlers=[
                logging.FileHandler(log_filepath, encoding="utf-8"),
                logging.StreamHandler()
            ],
            force=True  # Forzar reconfiguración
        )

    def validate_environment(self) -> bool:
        """Valida entorno y dependencias"""
        self.logger.info("🔍 Validando entorno PIX RPA...")

        # Crear directorios requeridos
        required_dirs = ["data", "reports", "logs", "evidencias", "config"]
        for directory in required_dirs:
            Path(directory).mkdir(exist_ok=True)
            self.logger.info(f"  ✓ Directorio verificado: {directory}/")

        # Verificar dependencias críticas
        try:
            import requests
            import pandas
            import openpyxl
            import sqlite3
            self.logger.info("  ✓ Dependencias críticas verificadas")
        except ImportError as e:
            self.logger.error(f"  ✗ Dependencia faltante: {e}")
            return False

        # Verificar estructura de archivos
        required_files = [
            "modules/api_consumer.py",
            "modules/database_manager.py", 
            "modules/excel_generator.py"
        ]
        
        missing_files = []
        base_path = Path(__file__).parent.resolve()
        for file_path in required_files:
            full_path = base_path / file_path
            if not full_path.exists():
                missing_files.append(str(full_path))
        
        if missing_files:
            self.logger.error(f"  ✗ Archivos faltantes: {missing_files}")
            return False

        self.logger.info("✅ Validación de entorno completada")
        return True

    def step_1_api(self):
        """Paso 1: Consumo API pública"""
        self.logger.info("🚀 PASO 1: Consumo de API pública")
        try:
            productos, json_file = self.api_consumer.get_products()
            self.process_stats["productos_procesados"] = len(productos)
            self.process_stats["archivos_generados"].append(json_file)
            self.process_stats["pasos_completados"] += 1
            
            # Evidencias si está disponible
            if hasattr(self, 'evidence_manager'):
                self.evidence_manager.capture_process_evidence(
                    "API_CONSUMPTION", True, {"count": len(productos)}
                )
                self.evidence_manager.capture_file_operation(
                    "JSON_BACKUP", json_file, True
                )
            
            self.logger.info(f"✅ Productos obtenidos: {len(productos)}")

            # Subir JSON a OneDrive
            if hasattr(self, 'onedrive_manager') and os.getenv("ONEDRIVE_ENABLED", "false").lower() == "true":
                self.logger.info("☁️ Intentando subir JSON de respaldo a OneDrive...")
                if self.onedrive_manager.authenticate():
                    onedrive_upload_success = self.onedrive_manager.upload_json_backup(json_file)
                    if onedrive_upload_success:
                        self.logger.info("✅ JSON de respaldo subido a OneDrive.")
                        if hasattr(self, 'evidence_manager'):
                            self.evidence_manager.capture_file_operation(
                                "ONEDRIVE_JSON_UPLOAD", json_file, True
                            )
                    else:
                        self.logger.warning("⚠️ Fallo al subir JSON de respaldo a OneDrive.")
                        if hasattr(self, 'evidence_manager'):
                            self.evidence_manager.capture_file_operation(
                                "ONEDRIVE_JSON_UPLOAD", json_file, False
                            )
                else:
                    self.logger.warning("⚠️ OneDrive: fallo de autenticación para subir JSON.")
                    if hasattr(self, 'evidence_manager'):
                        self.evidence_manager.capture_file_operation(
                            "ONEDRIVE_JSON_UPLOAD", json_file, False, {"reason": "auth_failed"}
                        )
            else:
                self.logger.info("☁️ Subida de JSON a OneDrive deshabilitada o no configurada.")
            
            return productos
            
        except Exception as e:
            self.logger.error(f"❌ Error en paso 1 (API): {e}")
            raise

    def step_2_database(self, productos):
        """Paso 2: Almacenamiento en BD"""
        self.logger.info("🚀 PASO 2: Almacenamiento en base de datos")
        try:
            inserted = self.db_manager.insert_products(productos)
            self.process_stats["pasos_completados"] += 1
            
            # Evidencias si está disponible
            if hasattr(self, 'evidence_manager'):
                self.evidence_manager.capture_process_evidence(
                    "DATABASE_INSERT", True, {"inserted": inserted}
                )
            
            self.logger.info(f"✅ Productos insertados en BD: {inserted}")
            return inserted
            
        except Exception as e:
            self.logger.error(f"❌ Error en paso 2 (Database): {e}")
            raise

    def step_3_excel(self):
        """Paso 3: Generación reporte Excel"""
        self.logger.info("🚀 PASO 3: Generación de reporte Excel")
        try:
            products = self.db_manager.get_all_products()
            statistics = self.db_manager.get_statistics()
            excel_path = self.excel_generator.generate_report(products, statistics)
            
            self.process_stats["archivos_generados"].append(excel_path)
            self.process_stats["pasos_completados"] += 1
            
            # Evidencias si está disponible
            if hasattr(self, 'evidence_manager'):
                self.evidence_manager.capture_file_operation(
                    "EXCEL_REPORT", excel_path, True
                )
            
            self.logger.info(f"✅ Reporte Excel generado: {excel_path}")
            return excel_path
            
        except Exception as e:
            self.logger.error(f"❌ Error en paso 3 (Excel): {e}")
            raise

    def step_4_onedrive(self, excel_path):
        """Paso 4: Subida a OneDrive"""
        self.logger.info("🚀 PASO 4: Subida a OneDrive")

        # Verificar si OneDrive está habilitado
        if os.getenv("ONEDRIVE_ENABLED", "false").lower() != "true":
            self.logger.info("☁️ OneDrive deshabilitado por configuración")
            if hasattr(self, 'evidence_manager'):
                self.evidence_manager.capture_process_evidence(
                    "ONEDRIVE_UPLOAD", False, {"reason": "disabled"}
                )
            return

        try:
            if not self.onedrive_manager.authenticate():
                self.logger.warning("⚠️ OneDrive: fallo de autenticación")
                if hasattr(self, 'evidence_manager'):
                    self.evidence_manager.capture_process_evidence(
                        "ONEDRIVE_UPLOAD", False, {"reason": "auth_failed"}
                    )
                return

            result = self.onedrive_manager.upload_excel_report(excel_path)
            success = bool(result)
            
            if hasattr(self, 'evidence_manager'):
                self.evidence_manager.capture_process_evidence(
                    "ONEDRIVE_UPLOAD", success, {"file": excel_path}
                )
            
            if success:
                self.logger.info("✅ Archivo subido a OneDrive correctamente")
                self.process_stats["pasos_completados"] += 1
            else:
                self.logger.warning("⚠️ No se pudo subir el archivo a OneDrive")
                
        except Exception as e:
            self.logger.error(f"❌ Error en paso 4 (OneDrive): {e}")

    def step_5_web(self, excel_path):
        """Paso 5: Automatización web"""
        self.logger.info("🚀 PASO 5: Automatización web (formulario)")

        try:
            # Verificar evidencia existente para evitar duplicados
            evidencia_path = Path("evidencias") / "formulario_confirmacion.png"
            if evidencia_path.exists():
                mod_time = datetime.fromtimestamp(evidencia_path.stat().st_mtime)
                if mod_time.date() == datetime.now().date():
                    self.logger.info("⚠️ Formulario ya procesado hoy, omitiendo")
                    if hasattr(self, 'evidence_manager'):
                        self.evidence_manager.capture_process_evidence(
                            "WEB_FORM", True, {"file": excel_path, "mode": "skipped_duplicate"}
                        )
                    return

            # Intentar envío con configuración nativa
            if hasattr(WebAutomationSettings, 'is_configured') and WebAutomationSettings.is_configured():
                success = self.web_automation.submit_form(excel_path)
                mode = "settings"
            # Intentar envío con configuración de entorno
            elif os.getenv("WEB_FORM_ENABLED", "false").lower() == "true" and os.getenv("WEB_FORM_URL"):
                self.logger.info("Usando configuración de entorno para formulario web")
                success = upload_to_web_form(excel_path)
                mode = "env"
            else:
                self.logger.warning("⚠️ Formulario web no configurado")
                success = False
                mode = "not_configured"

            if hasattr(self, 'evidence_manager'):
                self.evidence_manager.capture_process_evidence(
                    "WEB_FORM", success, {"file": excel_path, "mode": mode}
                )

            if success:
                self.logger.info("✅ Formulario web enviado correctamente")
                self.process_stats["pasos_completados"] += 1
            else:
                self.logger.warning("⚠️ No se pudo enviar el formulario web")

        except Exception as e:
            self.logger.error(f"❌ Error en paso 5 (Web): {e}")

    def step_6_evidences(self):
        """Paso 6: Evidencias finales"""
        self.logger.info("🚀 PASO 6: Registro de evidencias")
        try:
            if hasattr(self, 'evidence_manager'):
                path = self.evidence_manager.save_evidence_log(self.process_stats)
                if path:
                    self.logger.info(f"✅ Evidencias registradas en: {path}")
                    self.process_stats["pasos_completados"] += 1
                else:
                    self.logger.warning("⚠️ No fue posible guardar el log de evidencias")
            else:
                self.logger.info("ℹ️ Evidence manager no disponible")
        except Exception as e:
            self.logger.error(f"❌ Error en paso 6 (Evidencias): {e}")

    def run(self):
        """Ejecuta el proceso completo"""
        self.logger.info("🚀 Iniciando proceso PIX RPA")
        
        if not self.validate_environment():
            self.logger.error("❌ Error validando entorno")
            return False

        try:
            productos = self.step_1_api()
            self.step_2_database(productos)
            excel_path = self.step_3_excel()
            self.step_4_onedrive(excel_path)
            self.step_5_web(excel_path)
            self.step_6_evidences()
            self.finalize()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error crítico en proceso: {str(e)}")
            self.logger.exception("Detalles del error:")
            return False

    def finalize(self):
        """Finaliza con resumen"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.logger.info("=" * 80)
        self.logger.info("🎉 PROCESO PIX RPA FINALIZADO")
        self.logger.info(f"⏱️  Tiempo total: {duration:.2f} segundos")
        self.logger.info(f"📊 Productos procesados: {self.process_stats['productos_procesados']}")
        self.logger.info(f"📁 Archivos generados: {len(self.process_stats['archivos_generados'])}")
        self.logger.info(f"✅ Pasos completados: {self.process_stats['pasos_completados']}/6")
        
        if self.process_stats['archivos_generados']:
            self.logger.info("📂 Archivos creados:")
            for archivo in self.process_stats['archivos_generados']:
                self.logger.info(f"   • {archivo}")
        
        self.logger.info("=" * 80)


def main():
    """Función principal"""
    print("🚀 PIX RPA - Iniciando proceso de análisis de productos")
    print("=" * 60)
    
    try:
        process = PIXRPAProcess()
        success = process.run()
        
        if success:
            print("\n✅ Proceso completado exitosamente")
            return 0
        else:
            print("\n❌ Proceso completado con errores")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Proceso interrumpido por el usuario")
        return 2
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
