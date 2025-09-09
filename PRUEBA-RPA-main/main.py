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

# Añadir carpeta modules al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Importar módulos principales
try:
    from api_consumer import FakeStoreAPIConsumer as APIConsumer
    from database_manager import DatabaseManager
    from excel_generator import ExcelReportGenerator as ExcelGenerator
except ImportError as e:
    print(f"❌ Error importando módulos principales: {e}")
    sys.exit(1)

# Importar módulos extendidos
try:
    from onedrive_client import OneDriveClient as OneDriveManager
    from web_automation import WebFormAutomator as WebFormAutomation
    from web_form_manager import upload_to_web_form
    from config.settings import WebAutomationSettings
    from evidence_manager import EvidenceManager, initialize_evidence_manager
except ImportError as e:
    print(f"❌ Error importando módulos extendidos: {e}")
    sys.exit(1)


class PIXRPAProcess:
    """Proceso principal PIX RPA"""

    def __init__(self):
        self._setup_logging()
        self.logger = logging.getLogger("PIX_RPA_MAIN")

        # Inicializar gestores
        self.api_consumer = APIConsumer()
        self.db_manager = DatabaseManager()
        self.excel_generator = ExcelGenerator()
        self.onedrive_manager = OneDriveManager()
        self.web_automation = WebFormAutomation()
        self.evidence_manager = initialize_evidence_manager()

        self.start_time = datetime.now()
        self.process_stats = {
            "productos_procesados": 0,
            "pasos_completados": 0,
            "archivos_generados": [],
            "evidencias_capturadas": 0,
        }

    def _setup_logging(self):
        """Configura el logging centralizado"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        log_filename = f"pix_rpa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_filepath = os.path.join(log_dir, log_filename)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%H:%M:%S",
            handlers=[logging.FileHandler(log_filepath, encoding="utf-8"), logging.StreamHandler()],
        )

    def validate_environment(self) -> bool:
        """Valida entorno y dependencias"""
        self.logger.info("🔍 Validando entorno PIX RPA...")

        # Crear templates de configuración si no existen
                
        # Verificar directorios
        required_dirs = ["data", "reports", "logs", "evidencias", "config"]
        for directory in required_dirs:
            os.makedirs(directory, exist_ok=True)
            self.logger.info(f"  ✓ Directorio verificado: {directory}/")

        # Verificar dependencias críticas
        try:
            import requests, pandas, openpyxl, sqlite3
            self.logger.info("  ✓ Dependencias críticas verificadas")
        except ImportError as e:
            self.logger.error(f"  ✗ Dependencia faltante: {e}")
            return False

        return True

    def step_1_api(self):
        """Paso 1: Consumo API pública"""
        self.logger.info("🚀 PASO 1: Consumo de API pública")
        productos, json_file = self.api_consumer.get_products()
        self.process_stats["productos_procesados"] = len(productos)
        self.process_stats["archivos_generados"].append(json_file)
        # Evidencias
        self.evidence_manager.capture_process_evidence("API_CONSUMPTION", True, {"count": len(productos)})
        self.evidence_manager.capture_file_operation("JSON_BACKUP", json_file, True)
        return productos

    def step_2_database(self, productos):
        """Paso 2: Almacenamiento en BD"""
        self.logger.info("🚀 PASO 2: Almacenamiento en base de datos")
        inserted = self.db_manager.insert_products(productos)
        self.logger.info(f"Productos insertados en BD: {inserted}")
        # Evidencias
        self.evidence_manager.capture_process_evidence("DATABASE_INSERT", True, {"inserted": inserted})
        return inserted

    def step_3_excel(self):
        """Paso 3: Generación reporte Excel"""
        self.logger.info("🚀 PASO 3: Generación de reporte Excel")
        products = self.db_manager.get_all_products()
        statistics = self.db_manager.get_statistics()
        excel_path = self.excel_generator.generate_report(products, statistics)
        self.process_stats["archivos_generados"].append(excel_path)
        # Evidencias
        self.evidence_manager.capture_file_operation("EXCEL_REPORT", excel_path, True)
        return excel_path

    def step_4_onedrive(self, excel_path):
        """Paso 4: Subida a OneDrive"""
        self.logger.info("🚀 PASO 4: Subida a OneDrive")

        # Respetar flag de configuración
        if os.getenv("ONEDRIVE_ENABLED", "false").lower() != "true":
            self.logger.info("☁️ OneDrive deshabilitado por configuración, se omite")
            self.evidence_manager.capture_process_evidence("ONEDRIVE_UPLOAD", False, {"reason": "disabled"})
            return

        if not self.onedrive_manager.authenticate():
            self.logger.warning("⚠️ OneDrive no configurado o fallo de autenticación, se omite")
            # Evidencias
            self.evidence_manager.capture_process_evidence("ONEDRIVE_UPLOAD", False, {"reason": "auth_failed"})
            return

        result = self.onedrive_manager.upload_excel_report(excel_path)
        self.evidence_manager.capture_process_evidence("ONEDRIVE_UPLOAD", bool(result), {"file": excel_path})

    def step_5_web(self, excel_path):
        """Paso 5: Automatización web"""
        self.logger.info("🚀 PASO 5: Automatización web (formulario)")

        # Verificar si ya existe evidencia de formulario enviado hoy para evitar reenvío
        from datetime import datetime
        import os
        evidencia_confirmacion = os.path.join("evidencias", "formulario_confirmacion.png")
        if os.path.exists(evidencia_confirmacion):
            mod_time = os.path.getmtime(evidencia_confirmacion)
            mod_date = datetime.fromtimestamp(mod_time).date()
            today = datetime.now().date()
            if mod_date == today:
                self.logger.info("⚠️ Evidencia de formulario ya existe para hoy, se omite reenvío automático")
                self.evidence_manager.capture_process_evidence("WEB_FORM", True, {"file": excel_path, "mode": "skipped_duplicate"})
                return

        # Ruta A: configuración nativa (WebAutomationSettings)
        if WebAutomationSettings.is_configured():
            success = self.web_automation.submit_form(excel_path)
            self.evidence_manager.capture_process_evidence("WEB_FORM", bool(success), {"file": excel_path, "mode": "settings"})
            if not success:
                raise Exception("Error enviando formulario web")
            return

        # Ruta B: configuración por .env (WEB_FORM_ENABLED/WEB_FORM_URL)
        env_enabled = os.getenv("WEB_FORM_ENABLED", "false").lower() == "true"
        env_url = os.getenv("WEB_FORM_URL")
        if env_enabled and env_url:
            self.logger.info("Usando WebFormManager basado en .env para envío de formulario")
            success = upload_to_web_form(excel_path)
            self.evidence_manager.capture_process_evidence("WEB_FORM", bool(success), {"file": excel_path, "mode": "env"})
            if not success:
                self.logger.warning("Formulario web (env) no pudo enviarse")
            return

        # Si no hay ninguna configuración válida, omitir
        self.logger.warning("⚠️ Formulario no configurado, se omite")
        self.evidence_manager.capture_process_evidence("WEB_FORM", False, {"reason": "not_configured"})
        return

    def step_6_evidences(self):
        """Paso 6: Evidencias finales"""
        self.logger.info("🚀 PASO 6: Registro de evidencias")
        path = self.evidence_manager.save_evidence_log(self.process_stats)
        if path:
            self.logger.info(f"✅ Evidencias registradas en: {path}")
        else:
            self.logger.warning("⚠️ No fue posible guardar el log de evidencias")

    def run(self):
        """Ejecuta el proceso completo"""
        if not self.validate_environment():
            print("❌ Error validando entorno")
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
            return False

    def finalize(self):
        """Finaliza con resumen"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        self.logger.info("=" * 80)
        self.logger.info("PROCESO PIX RPA FINALIZADO")
        self.logger.info(f"Tiempo total: {duration:.2f} seg")
        self.logger.info(f"Productos procesados: {self.process_stats['productos_procesados']}")
        self.logger.info(f"Archivos generados: {self.process_stats['archivos_generados']}")
        self.logger.info("=" * 80)


def main():
    process = PIXRPAProcess()
    success = process.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
