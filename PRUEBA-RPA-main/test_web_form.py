import os
from modules.web_form_manager import upload_to_web_form
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)

def test_web_form():
    """Probar subida de archivo al formulario"""
    
    # Buscar el archivo Excel más reciente (robusto a cwd)
    base_dir = Path(__file__).resolve().parent
    reports_dir = base_dir / "reports"
    if not reports_dir.exists():
        print(f"❌ Directorio {reports_dir} no existe")
        return False
    
    excel_files = sorted([p.name for p in reports_dir.glob('*.xlsx')])
    
    if not excel_files:
        print(f"❌ No se encontraron archivos Excel en {reports_dir}")
        return False
    
    # Usar el archivo más reciente
    latest_file = str((reports_dir / excel_files[-1]).resolve())
    
    print(f"🚀 Probando subida de archivo: {latest_file}")
    
    # Intentar subir
    result = upload_to_web_form(latest_file)
    
    if result:
        print("✅ Prueba exitosa!")
    else:
        print("❌ Prueba falló")
    
    return result

if __name__ == "__main__":
    test_web_form()
