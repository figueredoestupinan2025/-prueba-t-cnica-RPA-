#!/usr/bin/env python3
"""
Lanzador CLI para el proceso PIX RPA
Permite ejecutar todos los pasos o una selección con --steps

Ejemplos:
  - python main_pix_rpa.py
  - python main_pix_rpa.py --steps 1,2,3
  - python main_pix_rpa.py --steps 123
"""

import sys
import argparse
from pathlib import Path

# Asegurar path del proyecto
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Importar la clase del proceso principal definida en main.py
from main import PIXRPAProcess  # noqa: E402


def parse_steps(steps_arg: str):
    """Convierte el argumento --steps en una lista ordenada de enteros únicos.
    Admite formatos "1,2,3" o "123".
    """
    if not steps_arg:
        return []
    # Normalizar
    s = steps_arg.replace(" ", "")
    parts = s.split(",") if "," in s else list(s)
    steps = []
    for p in parts:
        if not p:
            continue
        try:
            val = int(p)
            if val in range(1, 7) and val not in steps:
                steps.append(val)
        except ValueError:
            continue
    return sorted(steps)


def run_selected_steps(steps):
    """Ejecuta los pasos seleccionados en el orden indicado.
    Maneja dependencias entre pasos (productos para 2, excel_path para 4/5).
    """
    process = PIXRPAProcess()

    if not process.validate_environment():
        print("❌ Error validando entorno")
        return 1

    productos = None
    excel_path = None

    # Si no se especifican pasos, ejecutar el flujo completo
    if not steps:
        try:
            productos = process.step_1_api()
            process.step_2_database(productos)
            excel_path = process.step_3_excel()
            process.step_4_onedrive(excel_path)
            process.step_5_web(excel_path)
            process.step_6_evidences()
            process.finalize()
            print("✅ Proceso completado exitosamente")
            return 0
        except Exception as e:
            process.logger.error(f"❌ Error crítico en proceso: {e}")
            print("❌ Proceso completado con errores")
            return 1

    # Ejecutar pasos seleccionados
    try:
        for step in steps:
            if step == 1:
                productos = process.step_1_api()
            elif step == 2:
                # Si no hay productos (no se corrió 1), obtenerlos desde API
                if productos is None:
                    productos, _json_path = process.api_consumer.get_products()
                process.step_2_database(productos)
            elif step == 3:
                excel_path = process.step_3_excel()
            elif step == 4:
                if excel_path is None:
                    excel_path = process.step_3_excel()
                process.step_4_onedrive(excel_path)
            elif step == 5:
                if excel_path is None:
                    excel_path = process.step_3_excel()
                process.step_5_web(excel_path)
            elif step == 6:
                process.step_6_evidences()

        process.finalize()
        print("✅ Pasos seleccionados completados")
        return 0
    except Exception as e:
        process.logger.error(f"❌ Error ejecutando pasos {steps}: {e}")
        print("❌ Ejecución con errores")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Lanzador del proceso PIX RPA")
    parser.add_argument(
        "--steps",
        type=str,
        default="",
        help="Pasos a ejecutar. Formatos: '1,2,3' o '123'. Valores válidos 1..6"
    )
    args = parser.parse_args()

    steps = parse_steps(args.steps)
    return run_selected_steps(steps)


if __name__ == "__main__":
    sys.exit(main())
