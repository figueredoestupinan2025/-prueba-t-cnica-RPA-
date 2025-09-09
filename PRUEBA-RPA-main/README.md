# Proceso RPA PIX - Análisis de Productos

## Descripción del Proyecto

Proceso RPA desarrollado con la **plantilla universal de PIX RPA** para automatizar el análisis diario de productos de una tienda online. El robot realiza las siguientes tareas de forma completamente automática:

1. **Consumo de API Pública** - Obtiene productos desde Fake Store API
2. **Almacenamiento en Base de Datos** - SQLite con validación de duplicados
3. **Generación de Reportes Excel** - Con estadísticas y gráficos
4. **Integración OneDrive** - Subida automática vía Microsoft Graph API
5. **Automatización Web** - Envío de formularios con Selenium
6. **Registro de Evidencias** - Screenshots del proceso completo

## Tecnologías Utilizadas

- **PIX RPA Studio** - Plataforma principal de desarrollo
- **Python 3.8+** - Lenguaje de programación
- **SQLite** - Base de datos embebida
- **Microsoft Graph API** - Integración con OneDrive
- **Selenium WebDriver** - Automatización web
- **OpenPyXL** - Generación de archivos Excel
- **Requests** - Consumo de APIs REST

## Estructura del Proyecto

\`\`\`
RPA_Productos_Analysis/
├── config/                    # Configuraciones centralizadas
│   ├── __init__.py
│   └── settings.py           # Variables y configuraciones
├── modules/                   # Módulos principales del RPA
│   ├── __init__.py
│   ├── api_consumer.py       # Consumo de Fake Store API
│   ├── database_manager.py   # Gestión de base de datos SQLite
│   ├── excel_generator.py    # Generación de reportes Excel
│   ├── onedrive_client.py    # Cliente Microsoft Graph API
│   └── web_automation.py     # Automatización web con Selenium
├── utils/                     # Utilidades y funciones auxiliares
│   ├── __init__.py
│   └── logger.py             # Sistema de logging avanzado
├── data/                      # Directorio de datos
│   ├── raw/                  # JSON de respaldo de API
│   ├── database/             # Base de datos SQLite
│   └── temp/                 # Archivos temporales
├── reports/                   # Reportes Excel generados
├── logs/                      # Archivos de log del proceso
├── evidencias/               # Screenshots y evidencias
├── scripts/                   # Scripts auxiliares
│   └── create_database.sql   # Script de creación de BD
├── main_pix_rpa.py           # Script principal del proceso
├── setup_pix_studio.py       # Configuración PIX Studio
├── test_rpa.py               # Pruebas del sistema
├── requirements.txt          # Dependencias de Python
├── .env                      # Variables de entorno
└── README.md                 # Esta documentación
\`\`\`

## Instalación y Configuración

### Prerrequisitos

1. **PIX Studio** instalado y conectado al Master
2. **Python 3.8+** con pip
3. **Google Chrome** (para automatización web)
4. **Conexión a Internet** (para APIs)

### Paso 1: Configurar PIX Studio

\`\`\`bash
# Ejecutar configurador de PIX Studio
python setup_pix_studio.py
\`\`\`

Seguir las instrucciones en `PIX_STUDIO_SETUP.md` para:
- Conectar PIX Studio al Master PIX
- Usar credenciales: `Prueba_tecnica2025`
- Ampliar licencia a 42 pasos

### Paso 2: Instalar Dependencias

\`\`\`bash
# Instalar dependencias de Python
pip install -r requirements.txt
\`\`\`

### Paso 3: Configurar Variables de Entorno

Editar el archivo `.env` con sus credenciales:

\`\`\`env
# API de productos
FAKE_STORE_API_URL=https://fakestoreapi.com

# OneDrive (opcional)
AZURE_CLIENT_ID=su_client_id
AZURE_CLIENT_SECRET=su_client_secret  
AZURE_TENANT_ID=su_tenant_id

# Formulario web (opcional)
FORM_URL=https://forms.google.com/d/su-formulario-id/viewform
FORM_TYPE=google_forms

# Logging
LOG_LEVEL=INFO
\`\`\`

### Paso 4: Crear Formulario Web (Opcional)

1. Ir a [Google Forms](https://forms.google.com)
2. Crear formulario con campos:
   - **Nombre del colaborador** (texto corto, obligatorio)
   - **Fecha de generación** (texto corto, obligatorio) 
   - **Comentarios** (párrafo, opcional)
   - **Subida de archivo** (archivo, obligatorio, .xlsx)
3. Copiar URL al archivo `.env`

### Paso 5: Configurar OneDrive (Opcional)

1. Ir a [Azure Portal](https://portal.azure.com)
2. Registrar nueva aplicación
3. Obtener: Client ID, Client Secret, Tenant ID
4. Configurar permisos para Microsoft Graph API
5. Agregar credenciales al archivo `.env`

## Ejecución del Proceso

### Prueba Rápida del Sistema

\`\`\`bash
# Verificar que todo esté configurado correctamente
python test_rpa.py
\`\`\`

### Ejecución Completa

\`\`\`bash
# Ejecutar proceso RPA completo
python main_pix_rpa.py
\`\`\`

### Ejecución por Pasos

\`\`\`bash
# Solo consumo de API y base de datos (pasos críticos)
python main_pix_rpa.py --steps 1,2,3
\`\`\`

### Ejecución con Variables de Entorno

\`\`\`bash
# Configurar variables de entorno antes de ejecutar
export ALLOW_MANUAL_LOGIN=true
export MANUAL_LOGIN_WAIT_SECONDS=60
export WEB_FORM_ENABLED=true
export FORM_URL="https://forms.google.com/d/tu-formulario-id/viewform"

# Ejecutar proceso
python main_pix_rpa.py
\`\`\`

### Ejecución en Modo Debug

\`\`\`bash
# Ejecutar con logging detallado
export LOG_LEVEL=DEBUG
python main_pix_rpa.py
\`\`\`

### Ejecución Programada (Cron)

\`\`\`bash
# Agregar al crontab para ejecución diaria a las 8:00 AM
0 8 * * * cd /ruta/al/proyecto && python main_pix_rpa.py
\`\`\`

## Archivos Generados

El proceso genera automáticamente:

- **`data/raw/Productos_YYYY-MM-DD.json`** - Respaldo de datos de API
- **`reports/Reporte_YYYY-MM-DD.xlsx`** - Reporte Excel con estadísticas
- **`evidencias/formulario_confirmacion.png`** - Screenshot de confirmación
- **`logs/rpa_YYYY-MM-DD.log`** - Log detallado del proceso

## Especificaciones Técnicas

### API Consumida

- **Endpoint:** `https://fakestoreapi.com/products`
- **Método:** GET
- **Campos extraídos:** id, title, price, category, description
- **Formato respaldo:** JSON con timestamp

### Base de Datos

- **Tecnología:** SQLite
- **Tabla:** Productos
- **Campos:** 
  - `id` (INTEGER, PRIMARY KEY)
  - `title` (TEXT, NOT NULL)
  - `price` (REAL, NOT NULL)
  - `category` (TEXT, NOT NULL) 
  - `description` (TEXT, NOT NULL)
  - `fecha_insercion` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
- **Validación:** Prevención de duplicados por ID

### Reporte Excel

- **Formato:** .xlsx (Excel 2007+)
- **Nombre:** `Reporte_YYYY-MM-DD.xlsx`
- **Hojas:**
  - **Hoja 1 - Productos:** Lista completa con formato
  - **Hoja 2 - Resumen:** Estadísticas y gráficos
    - Total de productos
    - Precio promedio general  
    - Precio promedio por categoría
    - Cantidad de productos por categoría

### Integración OneDrive

- **API:** Microsoft Graph API v1.0
- **Autenticación:** Client Credentials (no interactiva)
- **Rutas:**
  - JSON: `/RPA/Logs/Productos_YYYY-MM-DD.json`
  - Excel: `/RPA/Reportes/Reporte_YYYY-MM-DD.xlsx`
- **Funciones:** Creación automática de directorios, control de versiones

### Automatización Web

- **Tecnología:** Selenium WebDriver
- **Navegador:** Chrome (ChromeDriver automático)
- **Formularios soportados:** Google Forms, JotForm, Typeform
- **Evidencias:** Screenshots automáticos en PNG

## Criterios de Evaluación Cumplidos

- ✅ **Uso de plantilla PIX:** Estructura y nomenclatura PIX RPA
- ✅ **API y JSON:** Consumo correcto y respaldo completo
- ✅ **Base de Datos:** Inserción limpia con validación de duplicados
- ✅ **Reporte Excel:** Datos organizados y estadísticas precisas
- ✅ **Automatización Web:** Llenado preciso de formularios
- ✅ **OneDrive API:** Subida funcional con control de errores
- ✅ **Logs y Errores:** Sistema de logging estructurado
- ✅ **Documentación:** README completo con instrucciones
- ✅ **Evidencias:** Screenshots de confirmación automáticos

## Solución de Problemas

### Error: Módulos no encontrados

\`\`\`bash
# Verificar estructura de proyecto
python -c "from modules import api_consumer; print('✓ Módulos OK')"
\`\`\`

### Error: ChromeDriver no encontrado

\`\`\`bash
# ChromeDriver se instala automáticamente
# Si falla, verificar conexión a Internet
\`\`\`

### Error: Base de datos bloqueada

\`\`\`bash
# Verificar permisos en directorio data/
mkdir -p data/database
chmod 755 data/database
\`\`\`

### Error: API no responde

\`\`\`bash
# Verificar conectividad
curl -I https://fakestoreapi.com/products
\`\`\`

## Configuración PIX Studio

### Credenciales PIX Master

- **Servidor:** `https://students.pixrobotics.org/`
- **Usuario:** `Prueba_tecnica2025`
- **Contraseña:** `Prueba_tecnica2025`
- **Conexión automática:** Habilitada

### Pasos de Conexión

1. Abrir PIX Studio
2. Hacer clic en "Master no conectado"
3. Introducir credenciales proporcionadas
4. Marcar "Conectar automáticamente"
5. Verificar conexión exitosa (icono verde)

## Logs y Monitoreo

El sistema genera logs detallados en `logs/rpa_YYYY-MM-DD.log` con:

- Inicio y fin de cada paso
- Errores y advertencias
- Estadísticas de performance
- Archivos generados
- Evidencias capturadas

Ejemplo de log:
\`\`\`
2024-12-08 10:30:15 | PIX_RPA_MAIN | INFO | PASO 1: CONSUMO DE API PÚBLICA - INICIADO
2024-12-08 10:30:16 | APIConsumer | INFO | ✅ API respondió con 20 productos
2024-12-08 10:30:17 | PIX_RPA_MAIN | INFO | PASO 1: CONSUMO DE API PÚBLICA - COMPLETADO
\`\`\`

## Enlaces de Referencia

- **PIX RPA Academy:** https://academy.es.pixrobotics.com/course/index.php
- **Fake Store API:** https://fakestoreapi.com/docs
- **Microsoft Graph API:** https://docs.microsoft.com/en-us/graph/
- **Google Forms:** https://forms.google.com
- **PIX Studio Download:** https://es.pixrobotics.com/download/

## Autor

**PIX RPA Development Team**  
Prueba Técnica - Desarrollo RPA con PIX RPA  
Fecha límite: 18/08/2025

## Licencia

Este proyecto está desarrollado como prueba técnica para PIX RPA y utiliza la licencia del Master PIX para estudiantes.

---

**Formulario utilizado:** https://forms.google.com/d/1J7XQnJ7fGhIkLmNoPqRsTuVwXyZ/viewform  
**Repositorio:** https://github.com/usuario/rpa-productos-pix
