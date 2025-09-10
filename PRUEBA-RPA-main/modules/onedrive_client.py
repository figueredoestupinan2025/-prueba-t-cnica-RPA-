"""
Cliente para Microsoft OneDrive usando Graph API
Sube archivos JSON y Excel automáticamente
"""

import os
import requests
import json
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import quote
from msal import ConfidentialClientApplication

from config.settings import OneDriveSettings
from utils.logger import setup_logger


class OneDriveClient:
    """Cliente para subir archivos a OneDrive"""
    
    def __init__(self):
        self.logger = setup_logger("OneDriveClient")
        self.access_token = None
        self.is_app_only = False
        
        if not OneDriveSettings.is_configured():
            self.logger.warning("⚠️ OneDrive no está configurado completamente")
    
    def authenticate(self) -> bool:
        """Autentica con Microsoft Graph API"""
        try:
            if not OneDriveSettings.is_configured():
                return False
            
            self.logger.info("Autenticando con Microsoft Graph...")
            
            # Crear aplicación MSAL
            app = ConfidentialClientApplication(
                OneDriveSettings.CLIENT_ID,
                authority=f"https://login.microsoftonline.com/{OneDriveSettings.TENANT_ID}",
                client_credential=OneDriveSettings.CLIENT_SECRET,
            )
            
            # Obtener token
            result = app.acquire_token_silent(OneDriveSettings.SCOPE, account=None)
            
            if not result:
                result = app.acquire_token_for_client(scopes=OneDriveSettings.SCOPE)
            
            # Detectar si el token es de aplicación (app-only) o delegado
            # Tokens delegados suelen incluir id_token; app-only no.
            self.is_app_only = 'id_token' not in result
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                
                # En flujo app-only es obligatorio especificar un usuario o drive destino
                if self.is_app_only and not (OneDriveSettings.TARGET_USER_ID or OneDriveSettings.TARGET_USER_EMAIL):
                    self.logger.error(
                        "Token de aplicación (app-only) obtenido, pero no se configuró usuario objetivo. "
                        "Define ONEDRIVE_USER_EMAIL o ONEDRIVE_USER_ID en .env para evitar usar /me/drive, "
                        "que no es válido con app-only."
                    )
                    return False
                
                self.logger.info("✅ Autenticación exitosa")
                return True
            else:
                self.logger.error(f"Error de autenticación: {result.get('error_description', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en autenticación: {str(e)}")
            return False
    
    def upload_file(self, local_path: str, remote_path: str, file_type: str = "json") -> bool:
        """
        Sube archivo a OneDrive
        
        Args:
            local_path: Ruta local del archivo
            remote_path: Ruta en OneDrive
            file_type: Tipo de archivo (json, excel, evidence)
            
        Returns:
            bool: True si la subida fue exitosa
        """
        try:
            if not self.access_token:
                if not self.authenticate():
                    return False
            
            local_file = Path(local_path)
            if not local_file.exists():
                self.logger.error(f"Archivo no encontrado: {local_path}")
                return False
            
            self.logger.info(f"Subiendo {file_type}: {local_file.name}")
            
            # Determinar ruta base según tipo
            base_paths = {
                "json": OneDriveSettings.JSON_PATH,
                "excel": OneDriveSettings.REPORTS_PATH,
                "evidence": OneDriveSettings.EVIDENCES_PATH
            }
            
            base_path = base_paths.get(file_type, OneDriveSettings.JSON_PATH)
            full_remote_path = f"{base_path}/{remote_path}"
            
            # Crear directorio si no existe
            self._ensure_directory_exists(base_path)
            
            # Subir archivo
            file_size = local_file.stat().st_size
            
            if file_size > OneDriveSettings.MAX_FILE_SIZE:
                self.logger.error(f"Archivo muy grande: {file_size} bytes")
                return False
            
            # Subida simple para archivos pequeños
            if file_size < OneDriveSettings.CHUNK_SIZE:
                return self._upload_small_file(local_file, full_remote_path)
            else:
                return self._upload_large_file(local_file, full_remote_path)
                
        except Exception as e:
            self.logger.error(f"Error subiendo archivo: {str(e)}")
            return False
    
    def _upload_small_file(self, local_file: Path, remote_path: str) -> bool:
        """Sube archivo pequeño en una sola petición"""
        try:
            encoded_path = quote(remote_path.strip('/'), safe="/")
            url = f"{OneDriveSettings.get_drive_base_url()}/root:/{encoded_path}:/content"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/octet-stream'
            }
            
            size = local_file.stat().st_size
            with open(local_file, 'rb') as f:
                response = requests.put(url, headers=headers, data=f)
            
            if response.status_code in [200, 201]:
                self.logger.log_file_operation("ONEDRIVE_UPLOAD", remote_path, size, True)
                self.logger.info(f"✅ Archivo subido: {remote_path}")
                return True
            else:
                self.logger.log_file_operation("ONEDRIVE_UPLOAD", remote_path, size, False)
                self.logger.error(f"Error subiendo archivo: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en subida simple: {str(e)}")
            return False
    
    def _upload_large_file(self, local_file: Path, remote_path: str) -> bool:
        """Sube archivo grande por chunks"""
        try:
            # Crear sesión de subida
            encoded_path = quote(remote_path.strip('/'), safe="/")
            url = f"{OneDriveSettings.get_drive_base_url()}/root:/{encoded_path}:/createUploadSession"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "item": {
                    "@microsoft.graph.conflictBehavior": OneDriveSettings.CONFLICT_BEHAVIOR
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                self.logger.error(f"Error creando sesión: {response.status_code} - {response.text}")
                self.logger.log_file_operation("ONEDRIVE_UPLOAD", remote_path, local_file.stat().st_size, False)
                return False
            
            upload_url = response.json()['uploadUrl']
            file_size = local_file.stat().st_size
            
            # Subir por chunks
            with open(local_file, 'rb') as f:
                chunk_size = OneDriveSettings.CHUNK_SIZE
                bytes_uploaded = 0
                
                while bytes_uploaded < file_size:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    chunk_start = bytes_uploaded
                    chunk_end = min(bytes_uploaded + len(chunk) - 1, file_size - 1)
                    
                    headers = {
                        'Content-Range': f'bytes {chunk_start}-{chunk_end}/{file_size}',
                        'Content-Length': str(len(chunk)),
                        'Content-Type': 'application/octet-stream'
                    }
                    
                    response = requests.put(upload_url, headers=headers, data=chunk)
                    
                    if response.status_code not in [202, 200, 201]:
                        self.logger.error(f"Error en chunk: {response.status_code}")
                        self.logger.log_file_operation("ONEDRIVE_UPLOAD", remote_path, file_size, False)
                        return False
                    
                    bytes_uploaded += len(chunk)
                    
                    # Log progreso
                    progress = (bytes_uploaded / file_size) * 100
                    self.logger.debug(f"Progreso: {progress:.1f}%")
            
            self.logger.log_file_operation("ONEDRIVE_UPLOAD", remote_path, file_size, True)
            self.logger.info(f"✅ Archivo grande subido: {remote_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en subida por chunks: {str(e)}")
            return False
    
    def _ensure_directory_exists(self, directory_path: str):
        """Asegura que el directorio existe en OneDrive (creación recursiva)"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            # Normalizar ruta y partirla en segmentos
            clean_path = directory_path.strip('/').replace('\\', '/')
            if not clean_path:
                return

            segments = clean_path.split('/')
            current_path = ''

            for segment in segments:
                # Avanzar un nivel
                current_path = f"{current_path}/{segment}" if current_path else segment

                # Verificar existencia del nivel actual
                encoded_current = quote(current_path.strip('/'), safe="/")
                check_url = f"{OneDriveSettings.get_drive_base_url()}/root:/{encoded_current}"
                resp = requests.get(check_url, headers=headers)

                if resp.status_code == 200:
                    continue  # Existe, avanzar al siguiente nivel
                elif resp.status_code == 404:
                    # Crear este nivel dentro del padre
                    parent = "/".join(current_path.split('/')[:-1])
                    if parent:
                        encoded_parent = quote(parent.strip('/'), safe="/")
                        create_url = f"{OneDriveSettings.get_drive_base_url()}/root:/{encoded_parent}:/children"
                    else:
                        # Crear directamente en root
                        create_url = f"{OneDriveSettings.get_drive_base_url()}/root/children"

                    data = {
                        "name": segment,
                        "folder": {},
                        "@microsoft.graph.conflictBehavior": "replace"
                    }
                    create_resp = requests.post(create_url, headers=headers, json=data)
                    if create_resp.status_code in (200, 201):
                        self.logger.info(f"📁 Directorio creado: {current_path}")
                    elif create_resp.status_code == 409:
                        # Condición de carrera: el folder fue creado en paralelo
                        self.logger.warning(f"⚠️ Directorio ya existía (409): {current_path}")
                    else:
                        self.logger.warning(
                            f"No se pudo crear directorio: {current_path} | status={create_resp.status_code}"
                        )
                        # No abortar, intentar continuar por si es transitorio
                else:
                    self.logger.warning(
                        f"No se pudo verificar directorio: {current_path} | status={resp.status_code}"
                    )
        except Exception as e:
            self.logger.warning(f"Error verificando/creando ruta en OneDrive: {str(e)}")
    
    def upload_json_backup(self, json_path: str) -> bool:
        """Sube respaldo JSON a OneDrive"""
        filename = Path(json_path).name
        return self.upload_file(json_path, filename, "json")
    
    def upload_excel_report(self, excel_path: str) -> bool:
        """Sube reporte Excel a OneDrive"""
        filename = Path(excel_path).name
        return self.upload_file(excel_path, filename, "excel")
    
    def upload_evidence(self, evidence_path: str) -> bool:
        """Sube evidencia (screenshot) a OneDrive"""
        filename = Path(evidence_path).name
        return self.upload_file(evidence_path, filename, "evidence")


def test_onedrive_client():
    """Función de prueba para el cliente OneDrive"""
    logger = setup_logger("OneDriveTest")
    
    try:
        if not OneDriveSettings.is_configured():
            logger.warning("⚠️ OneDrive no configurado, omitiendo test")
            return True
        
        client = OneDriveClient()
        
        # Test de autenticación
        if client.authenticate():
            logger.info("✅ Test autenticación exitoso")
            return True
        else:
            logger.error("❌ Test autenticación fallido")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test OneDrive fallido: {str(e)}")
        return False


if __name__ == "__main__":
    test_onedrive_client()
