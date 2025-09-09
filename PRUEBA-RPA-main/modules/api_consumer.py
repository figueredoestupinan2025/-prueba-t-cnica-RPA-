"""
Wrapper para exponer FakeStoreAPIConsumer dentro del paquete 'modules'.
Reexporta la implementación real ubicada en el archivo raíz 'api_consumer.py'.
"""

import sys
from pathlib import Path

# Agregar el directorio padre (raíz del proyecto) al sys.path para permitir importar api_consumer.py
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.append(str(_PROJECT_ROOT))

# Reexportar la clase desde el módulo real
from api_consumer import FakeStoreAPIConsumer  # noqa: E402,F401

__all__ = ["FakeStoreAPIConsumer"]
