"""
Módulo para consumir la Fake Store API
Obtiene productos, guarda JSON de respaldo y procesa los datos
"""

import requests
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from pathlib import Path

from config.settings import APISettings, FileSettings, DATA_DIR
from utils.logger import setup_logger


class FakeStoreAPIConsumer:
    """Cliente para consumir la Fake Store API"""
    
    def __init__(self):
        self.logger = setup_logger("APIConsumer")
        self.api_url = "https://fakestoreapi.com/products"
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0"
        }
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_products(self) -> Tuple[List[Dict], str]:
        """
        Obtiene productos de la API y guarda respaldo JSON
        
        Returns:
            Tuple[List[Dict], str]: Lista de productos y path del archivo JSON
        """
        start_time = time.time()
        
        try:
            self.logger.log_step(1, "Consumo de API", "INICIADO")
            
            # Realizar petición
            self.logger.info(f"Consultando API: {APISettings.PRODUCTS_ENDPOINT}")
            response = self.session.get(
                APISettings.PRODUCTS_ENDPOINT,
                headers=self.headers,
                timeout=APISettings.TIMEOUT
            )
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # Validar respuesta
            response.raise_for_status()
            
            # Log de la llamada exitosa
            self.logger.log_api_call(
                APISettings.PRODUCTS_ENDPOINT,
                "GET",
                response.status_code,
                response_time
            )
            
            # Obtener datos JSON
            products_data = response.json()
            
            if not isinstance(products_data, list):
                raise ValueError("La respuesta de la API no es una lista válida")
            
            self.logger.info(f"✅ API respondió con {len(products_data)} productos")
            
            # Guardar respaldo JSON
            json_filepath = self._save_json_backup(products_data)
            
            # Procesar productos
            processed_products = self._process_products(products_data)
            
            self.logger.log_step(
                1, "Consumo de API", "COMPLETADO",
                {"productos_obtenidos": len(processed_products), "archivo_json": json_filepath}
            )
            
            return processed_products, json_filepath
            
        except requests.exceptions.Timeout:
            self.logger.error("Timeout al consultar la API")
            raise
        except requests.exceptions.ConnectionError:
            self.logger.error("Error de conexión con la API")
            raise
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Error HTTP: {e.response.status_code}")
            raise
        except json.JSONDecodeError:
            self.logger.error("Error al decodificar respuesta JSON")
            raise
        except Exception as e:
            self.logger.error(f"Error inesperado en consumo de API: {str(e)}")
            raise
    
    def _save_json_backup(self, data: List[Dict]) -> str:
        """
        Guarda respaldo JSON con timestamp
        
        Args:
            data: Datos de productos de la API
            
        Returns:
            str: Ruta del archivo JSON guardado
        """
        try:
            # Generar nombre de archivo con fecha
            today = datetime.now().strftime(FileSettings.DATE_FORMAT)
            filename = f"{FileSettings.JSON_PREFIX}{today}{FileSettings.JSON_EXTENSION}"
            
            # Ruta completa
            raw_dir = DATA_DIR / "raw"
            raw_dir.mkdir(exist_ok=True)
            filepath = raw_dir / filename
            
            # Agregar metadata
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "source_api": APISettings.PRODUCTS_ENDPOINT,
                "total_products": len(data),
                "products": data
            }
            
            # Guardar archivo
            with open(filepath, 'w', encoding=FileSettings.DEFAULT_ENCODING) as f:
                json.dump(
                    backup_data,
                    f,
                    ensure_ascii=FileSettings.JSON_ENSURE_ASCII,
                    indent=FileSettings.JSON_INDENT
                )
            
            file_size = filepath.stat().st_size
            
            self.logger.log_file_operation(
                "JSON_BACKUP",
                str(filepath),
                file_size,
                True
            )
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error al guardar respaldo JSON: {str(e)}")
            raise
    
    def _process_products(self, raw_products: List[Dict]) -> List[Dict]:
        """
        Procesa y valida los productos obtenidos de la API
        
        Args:
            raw_products: Lista de productos sin procesar
            
        Returns:
            List[Dict]: Lista de productos procesados
        """
        processed_products = []
        
        for i, product in enumerate(raw_products, 1):
            try:
                # Validar campos requeridos
                required_fields = ['id', 'title', 'price', 'category', 'description']
                
                if not all(field in product for field in required_fields):
                    self.logger.warning(f"Producto {i} omitido por campos faltantes")
                    continue
                
                # Procesar producto
                processed_product = {
                    'id': int(product['id']),
                    'title': str(product['title']).strip(),
                    'price': float(product['price']),
                    'category': str(product['category']).strip(),
                    'description': str(product['description']).strip(),
                    'fecha_insercion': datetime.now()
                }
                
                # Validaciones adicionales
                if processed_product['price'] <= 0:
                    self.logger.warning(f"Producto {processed_product['id']} tiene precio inválido")
                    continue
                
                if len(processed_product['title']) < 3:
                    self.logger.warning(f"Producto {processed_product['id']} tiene título muy corto")
                    continue
                
                processed_products.append(processed_product)
                
            except (ValueError, KeyError, TypeError) as e:
                self.logger.warning(f"Error procesando producto {i}: {str(e)}")
                continue
        
        self.logger.info(f"Procesados {len(processed_products)} de {len(raw_products)} productos")
        return processed_products
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """
        Obtiene un producto específico por ID
        
        Args:
            product_id: ID del producto
            
        Returns:
            Dict: Datos del producto o None si no existe
        """
        try:
            url = f"{APISettings.PRODUCTS_ENDPOINT}/{product_id}"
            response = self.session.get(url, timeout=APISettings.TIMEOUT)
            
            response.raise_for_status()
            product_data = response.json()
            
            self.logger.log_api_call(url, "GET", response.status_code)
            
            return self._process_products([product_data])[0] if product_data else None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo producto {product_id}: {str(e)}")
            return None
    
    def get_categories(self) -> List[str]:
        """
        Obtiene las categorías disponibles
        
        Returns:
            List[str]: Lista de categorías
        """
        try:
            url = f"{APISettings.PRODUCTS_ENDPOINT}/categories"
            response = self.session.get(url, timeout=APISettings.TIMEOUT)
            
            response.raise_for_status()
            categories = response.json()
            
            self.logger.log_api_call(url, "GET", response.status_code)
            self.logger.info(f"Obtenidas {len(categories)} categorías")
            
            return categories
            
        except Exception as e:
            self.logger.error(f"Error obteniendo categorías: {str(e)}")
            return []
    
    def validate_api_connection(self) -> bool:
        """
        Valida que la API esté disponible
        
        Returns:
            bool: True si la API está disponible
        """
        try:
            response = self.session.get(
                self.api_url,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("✅ API está disponible")
                return True
            else:
                self.logger.warning(f"⚠️ API respondió con código: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ API no está disponible: {str(e)}")
            return False
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cerrar sesión"""
        if hasattr(self, 'session'):
            self.session.close()


def test_api_consumer():
    """Función de prueba para el consumidor de API"""
    logger = setup_logger("APITest")
    
    try:
        with FakeStoreAPIConsumer() as api_client:
            # Validar conexión
            if not api_client.validate_api_connection():
                raise ConnectionError("API no disponible")
            
            # Obtener productos
            products, json_path = api_client.get_products()
            
            logger.info(f"✅ Test exitoso: {len(products)} productos obtenidos")
            logger.info(f"📄 JSON guardado en: {json_path}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Test fallido: {str(e)}")
        return False


if __name__ == "__main__":
    # Ejecutar test si se corre directamente
    test_api_consumer()
