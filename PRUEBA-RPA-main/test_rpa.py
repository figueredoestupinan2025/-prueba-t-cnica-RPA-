#!/usr/bin/env python3
"""
Sistema de Pruebas para RPA PIX
Verifica que todos los componentes funcionen correctamente antes de la ejecución
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Configurar path para importaciones
sys.path.append(str(Path(__file__).parent))

from config.settings import validate_configuration, print_configuration_status
from utils.logger import setup_logger


class RPATestSuite:
    """Suite de pruebas para el sistema RPA"""
    
    def __init__(self):
        self.logger = setup_logger("RPATest")
        self.test_results = {}
        self.start_time = datetime.now()
    
    def run_all_tests(self) -> bool:
        """Ejecuta todas las pruebas del sistema"""
        print("\n" + "="*60)
        print("🧪 INICIANDO SUITE DE PRUEBAS PIX RPA")
        print("="*60)
        
        tests = [
            ("Configuración del Sistema", self.test_configuration),
            ("Estructura de Directorios", self.test_directories),
            ("Importación de Módulos", self.test_module_imports),
            ("Conectividad API", self.test_api_connectivity),
            ("Base de Datos", self.test_database),
            ("Generación Excel", self.test_excel_generation),
            ("OneDrive (Opcional)", self.test_onedrive),
            ("Automatización Web (Opcional)", self.test_web_automation)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_function in tests:
            print(f"\n🔍 Ejecutando: {test_name}")
            try:
                result = test_function()
                self.test_results[test_name] = result
                
                if result:
                    print(f"   ✅ {test_name}: PASÓ")
                    passed_tests += 1
                else:
                    print(f"   ❌ {test_name}: FALLÓ")
                    
            except Exception as e:
                print(f"   💥 {test_name}: ERROR - {str(e)}")
                self.test_results[test_name] = False
        
        # Resumen final
        self._print_final_results(passed_tests, total_tests)
        
        # Determinar si el sistema está listo
        critical_tests = [
            "Configuración del Sistema",
            "Estructura de Directorios", 
            "Importación de Módulos",
            "Conectividad API",
            "Base de Datos"
        ]
        
        critical_passed = all(self.test_results.get(test, False) for test in critical_tests)
        
        return critical_passed
    
    def test_configuration(self) -> bool:
        """Prueba la configuración del sistema"""
        try:
            config_status = validate_configuration()
            
            # Verificar componentes críticos
            critical_components = ['api', 'database', 'directories']
            critical_ok = all(config_status.get(comp, False) for comp in critical_components)
            
            if critical_ok:
                print("   📋 Configuración crítica: OK")
                
                # Verificar componentes opcionales
                optional_ok = []
                if config_status.get('onedrive', False):
                    print("   ☁️  OneDrive: Configurado")
                    optional_ok.append(True)
                else:
                    print("   ⚠️  OneDrive: No configurado (opcional)")
                
                if config_status.get('web_automation', False):
                    print("   🌐 Formulario Web: Configurado")
                    optional_ok.append(True)
                else:
                    print("   ⚠️  Formulario Web: No configurado (opcional)")
                
                return True
            else:
                print("   ❌ Configuración crítica incompleta")
                return False
                
        except Exception as e:
            print(f"   💥 Error en configuración: {e}")
            return False
    
    def test_directories(self) -> bool:
        """Prueba la estructura de directorios"""
        try:
            from config.settings import DATA_DIR, LOGS_DIR, REPORTS_DIR, EVIDENCES_DIR
            
            directories = {
                'data': DATA_DIR,
                'logs': LOGS_DIR,
                'reports': REPORTS_DIR,
                'evidences': EVIDENCES_DIR
            }
            
            all_exist = True
            for name, path in directories.items():
                if path.exists():
                    print(f"   📁 {name}: {path}")
                else:
                    print(f"   ❌ {name}: {path} - NO EXISTE")
                    all_exist = False
            
            return all_exist
            
        except Exception as e:
            print(f"   💥 Error verificando directorios: {e}")
            return False
    
    def test_module_imports(self) -> bool:
        """Prueba que todos los módulos se importen correctamente"""
        modules_to_test = [
            ('config.settings', 'Configuraciones'),
            ('modules.api_consumer', 'Consumidor API'),
            ('modules.database_manager', 'Gestor BD'),
            ('modules.excel_generator', 'Generador Excel'),
            ('modules.onedrive_client', 'Cliente OneDrive'),
            ('modules.web_automation', 'Automatización Web'),
            ('utils.logger', 'Sistema Logging')
        ]
        
        failed_imports = []
        
        for module_name, description in modules_to_test:
            try:
                __import__(module_name)
                print(f"   ✅ {description}: Importado")
            except ImportError as e:
                print(f"   ❌ {description}: {e}")
                failed_imports.append(module_name)
            except Exception as e:
                print(f"   ⚠️  {description}: {e}")
        
        return len(failed_imports) == 0
    
    def test_api_connectivity(self) -> bool:
        """Prueba conectividad con Fake Store API"""
        try:
            from modules.api_consumer import FakeStoreAPIConsumer
            
            with FakeStoreAPIConsumer() as api_client:
                if api_client.validate_api_connection():
                    print("   🌐 Fake Store API: Accesible")
                    
                    # Obtener una pequeña muestra
                    try:
                        categories = api_client.get_categories()
                        if categories:
                            print(f"   📊 Categorías disponibles: {len(categories)}")
                            print(f"      {', '.join(categories[:3])}{'...' if len(categories) > 3 else ''}")
                        return True
                    except:
                        print("   ⚠️  API accesible pero sin datos de categorías")
                        return True
                else:
                    print("   ❌ Fake Store API: No accesible")
                    return False
                    
        except Exception as e:
            print(f"   💥 Error probando API: {e}")
            return False
    
    def test_database(self) -> bool:
        """Prueba operaciones básicas de base de datos"""
        try:
            from modules.database_manager import DatabaseManager
            
            db = DatabaseManager()
            print("   💾 Base de datos: Inicializada")
            
            # Obtener estadísticas actuales
            stats = db.get_statistics()
            if stats:
                print(f"   📈 Productos existentes: {stats.get('total_products', 0)}")
                print(f"   🏷️  Categorías: {len(stats.get('category_stats', []))}")
                return True
            else:
                print("   ⚠️  BD inicializada pero sin datos")
                return True
                
        except Exception as e:
            print(f"   💥 Error en base de datos: {e}")
            return False
    
    def test_excel_generation(self) -> bool:
        """Prueba la generación de archivos Excel"""
        try:
            from modules.excel_generator import ExcelReportGenerator
            
            # Usar datos de prueba mínimos
            test_products = [{
                'id': 999,
                'title': 'Producto Test',
                'price': 19.99,
                'category': 'test',
                'description': 'Producto de prueba',
                'fecha_insercion': datetime.now()
            }]
            
            test_stats = {
                'total_products': 1,
                'avg_price': 19.99,
                'category_stats': [{
                    'category': 'test',
                    'count': 1,
                    'avg_price': 19.99,
                    'min_price': 19.99,
                    'max_price': 19.99
                }]
            }
            
            generator = ExcelReportGenerator()
            excel_path = generator.generate_report(test_products, test_stats)
            
            if Path(excel_path).exists():
                print(f"   📊 Excel generado: {Path(excel_path).name}")
                # Limpiar archivo de prueba
                Path(excel_path).unlink()
                return True
            else:
                print("   ❌ Excel no se generó correctamente")
                return False
                
        except Exception as e:
            print(f"   💥 Error generando Excel: {e}")
            return False
    
    def test_onedrive(self) -> bool:
        """Prueba configuración OneDrive (opcional)"""
        try:
            from modules.onedrive_client import OneDriveClient
            from config.settings import OneDriveSettings
            
            if not OneDriveSettings.is_configured():
                print("   ⚠️  OneDrive no configurado - OPCIONAL")
                return True  # No es error crítico
            
            client = OneDriveClient()
            if client.authenticate():
                print("   ☁️  OneDrive: Autenticación exitosa")
                return True
            else:
                print("   ❌ OneDrive: Error de autenticación")
                return False
                
        except Exception as e:
            print(f"   ⚠️  OneDrive error: {e} - OPCIONAL")
            return True  # No crítico
    
    def test_web_automation(self) -> bool:
        """Prueba configuración de automatización web (opcional)"""
        try:
            from modules.web_automation import WebFormAutomator, test_web_automation
            from config.settings import WebAutomationSettings
            
            if not WebAutomationSettings.is_configured():
                print("   ⚠️  Formulario web no configurado - OPCIONAL")
                return True  # No es error crítico
            
            # Ejecutar test básico de WebDriver
            if test_web_automation():
                print("   🌐 WebDriver: Configuración OK")
                return True
            else:
                print("   ❌ WebDriver: Error de configuración")
                return False
                
        except Exception as e:
            print(f"   ⚠️  Web automation error: {e} - OPCIONAL")
            return True  # No crítico
    
    def _print_final_results(self, passed: int, total: int):
        """Imprime resumen final de las pruebas"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "="*60)
        print("📋 RESUMEN DE PRUEBAS")
        print("="*60)
        print(f"⏱️  Duración: {duration:.2f} segundos")
        print(f"✅ Pruebas pasadas: {passed}/{total}")
        print(f"❌ Pruebas fallidas: {total - passed}/{total}")
        print(f"📊 Tasa de éxito: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 TODAS LAS PRUEBAS PASARON - Sistema listo para ejecución")
        elif passed >= 5:  # Pruebas críticas
            print("\n✅ PRUEBAS CRÍTICAS PASARON - Sistema funcional")
            print("⚠️  Algunas funciones opcionales no están configuradas")
        else:
            print("\n❌ PRUEBAS CRÍTICAS FALLARON - Revisar configuración")
        
        print("="*60)


def main():
    """Función principal de testing"""
    try:
        # Banner inicial
        print("PIX RPA - SISTEMA DE PRUEBAS")
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Mostrar configuración actual
        print("\n📋 CONFIGURACIÓN ACTUAL:")
        print_configuration_status()
        
        # Ejecutar pruebas
        test_suite = RPATestSuite()
        system_ready = test_suite.run_all_tests()
        
        # Recommendations
        print("\n🚀 PRÓXIMOS PASOS:")
        
        if system_ready:
            print("1. ✅ Sistema listo - ejecutar: python main_pix_rpa.py")
            print("2. 📊 Para solo pasos críticos: python main_pix_rpa.py --steps 1,2,3")
            
            # Configuraciones opcionales
            from config.settings import OneDriveSettings, WebAutomationSettings
            
            if not OneDriveSettings.is_configured():
                print("3. ☁️  (Opcional) Configurar OneDrive en .env para paso 4")
            
            if not WebAutomationSettings.is_configured():
                print("4. 🌐 (Opcional) Crear formulario web y configurar en .env para paso 5")
                
            return 0
        else:
            print("1. ❌ Revisar errores arriba")
            print("2. 📖 Consultar README.md para instrucciones")
            print("3. 🔧 Instalar dependencias: pip install -r requirements.txt")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Pruebas interrumpidas")
        return 2
    except Exception as e:
        print(f"\n💥 Error crítico en pruebas: {e}")
        return 3


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
