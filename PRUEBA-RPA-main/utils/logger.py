"""
Sistema de logging avanzado para RPA
Soporta múltiples niveles, archivos rotatorios y colores
"""

import os
import logging
import colorlog
from datetime import datetime
from pathvalidate import sanitize_filename
import json


class RPALogger:
    """Logger personalizado para el proceso RPA"""
    
    def __init__(self, name="RPA_Main", log_level="INFO"):
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.setup_logger()
    
    def setup_logger(self):
        """Configura el logger con handlers de archivo y consola"""
        
        # Crear logger principal
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.log_level)
        # Evitar propagación al logger raíz para no duplicar mensajes
        self.logger.propagate = False
        
        # Evitar duplicados de handlers
        if self.logger.handlers:
            return self.logger
        
        # Crear directorio de logs
        logs_dir = os.getenv('LOGS_PATH', 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Handler para archivo
        log_filename = f"rpa_{datetime.now().strftime('%Y-%m-%d')}.log"
        log_filepath = os.path.join(logs_dir, log_filename)
        
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        file_handler.setLevel(self.log_level)
        
        # Handler para consola con colores
        console_handler = colorlog.StreamHandler()
        console_handler.setLevel(self.log_level)
        
        # Formatters
        file_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_format = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s | %(name)s | %(levelname)s | %(message)s%(reset)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green', 
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )
        
        file_handler.setFormatter(file_format)
        console_handler.setFormatter(console_format)
        
        # Agregar handlers
        self.logger.addHandler(file_handler)
        
        # Solo agregar consola si está habilitado
        if os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true':
            self.logger.addHandler(console_handler)
    
    def info(self, message, extra_data=None):
        """Log nivel INFO"""
        formatted_msg = self._format_message(message, extra_data)
        self.logger.info(formatted_msg)
    
    def error(self, message, extra_data=None):
        """Log nivel ERROR"""
        formatted_msg = self._format_message(message, extra_data)
        self.logger.error(formatted_msg)
    
    def warning(self, message, extra_data=None):
        """Log nivel WARNING"""
        formatted_msg = self._format_message(message, extra_data)
        self.logger.warning(formatted_msg)
    
    def debug(self, message, extra_data=None):
        """Log nivel DEBUG"""
        formatted_msg = self._format_message(message, extra_data)
        self.logger.debug(formatted_msg)
    
    def critical(self, message, extra_data=None):
        """Log nivel CRITICAL"""
        formatted_msg = self._format_message(message, extra_data)
        self.logger.critical(formatted_msg)
    
    def _format_message(self, message, extra_data=None):
        """Formatea el mensaje con datos adicionales"""
        if extra_data:
            if isinstance(extra_data, dict):
                extra_str = " | ".join([f"{k}={v}" for k, v in extra_data.items()])
                return f"{message} | {extra_str}"
            else:
                return f"{message} | {extra_data}"
        return message
    
    def log_step(self, step_number, step_name, status="INICIADO", details=None):
        """Log especializado para pasos del proceso RPA"""
        step_msg = f"PASO {step_number}: {step_name} - {status}"
        
        if status.upper() in ["INICIADO", "STARTED", "BEGIN"]:
            self.info(f"🚀 {step_msg}", details)
        elif status.upper() in ["COMPLETADO", "COMPLETED", "SUCCESS"]:
            self.info(f"✅ {step_msg}", details)
        elif status.upper() in ["ERROR", "FAILED", "FALLIDO"]:
            self.error(f"❌ {step_msg}", details)
        elif status.upper() in ["WARNING", "ADVERTENCIA"]:
            self.warning(f"⚠️ {step_msg}", details)
        else:
            self.info(step_msg, details)
    
    def log_api_call(self, url, method="GET", status_code=None, response_time=None):
        """Log especializado para llamadas API"""
        details = {
            "url": url,
            "method": method,
            "status_code": status_code,
            "response_time_ms": response_time
        }
        
        if status_code and 200 <= status_code < 300:
            self.info(f"API CALL SUCCESS: {method} {url}", details)
        elif status_code:
            self.error(f"API CALL ERROR: {method} {url}", details)
        else:
            self.info(f"API CALL: {method} {url}", details)
    
    def log_db_operation(self, operation, table=None, records_affected=None, execution_time=None):
        """Log especializado para operaciones de base de datos"""
        details = {
            "operation": operation,
            "table": table,
            "records_affected": records_affected,
            "execution_time_ms": execution_time
        }
        
        self.info(f"DB OPERATION: {operation}", details)
    
    def log_file_operation(self, operation, filepath, file_size=None, success=True):
        """Log especializado para operaciones de archivos"""
        details = {
            "operation": operation,
            "filepath": filepath,
            "file_size_bytes": file_size,
            "success": success
        }
        
        if success:
            self.info(f"FILE OPERATION SUCCESS: {operation}", details)
        else:
            self.error(f"FILE OPERATION FAILED: {operation}", details)
    
    def log_process_summary(self, start_time, end_time, total_records=None, files_created=None):
        """Log resumen del proceso completo"""
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": round(duration, 2),
            "total_records": total_records,
            "files_created": files_created
        }
        
        self.info("=== PROCESO RPA COMPLETADO ===", summary)


def setup_logger(name="RPA", level="INFO"):
    """Factory function para crear loggers"""
    return RPALogger(name, level)


def mask_sensitive_data(data, sensitive_keys=None):
    """Enmascara datos sensibles en logs"""
    if sensitive_keys is None:
        sensitive_keys = [
            'password', 'secret', 'token', 'key', 'credential',
            'client_secret', 'api_key', 'auth', 'authorization'
        ]
    
    if isinstance(data, dict):
        masked_data = {}
        for key, value in data.items():
            if any(sensitive_key.lower() in key.lower() for sensitive_key in sensitive_keys):
                masked_data[key] = "***MASKED***"
            else:
                masked_data[key] = value
        return masked_data
    
    return data


# Configurar logger por defecto
default_logger = setup_logger()

# Funciones de conveniencia
def log_info(message, extra_data=None):
    default_logger.info(message, extra_data)

def log_error(message, extra_data=None):
    default_logger.error(message, extra_data)

def log_warning(message, extra_data=None):
    default_logger.warning(message, extra_data)

def log_step(step_number, step_name, status="INICIADO", details=None):
    default_logger.log_step(step_number, step_name, status, details)
