from __future__ import annotations

import os
from pathlib import Path
from flask import Flask, request, render_template_string, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

# Configuración
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"xlsx", "xls"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)
app.secret_key = "dev-secret"

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Formulario REAL - Subida de archivo</title>
  <style>
    :root { color-scheme: light dark; }
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Arial; margin: 0; padding: 0; }
    .container { max-width: 760px; margin: 40px auto; padding: 24px; border: 1px solid #ccc; border-radius: 12px; }
    h1 { margin-top: 0; font-size: 22px; }
    form { display: grid; gap: 12px; }
    label { font-weight: 600; }
    input[type="text"], input[type="password"], input[type="file"] { padding: 8px; }
    button { padding: 10px 16px; border: 0; border-radius: 8px; background: #2563eb; color: #fff; font-weight: 600; cursor: pointer; }
    button:hover { background: #1d4ed8; }
    .note { color: #6b7280; }
    .msg { margin-top: 16px; padding: 12px; border-radius: 8px; }
    .ok { background: #064e3b; color: #d1fae5; }
    .err { background: #7f1d1d; color: #fee2e2; }
    .meta { font-size: 12px; margin-top: 6px; color: #6b7280; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Formulario REAL - Subida de archivo</h1>
    <p class="note">Este formulario escucha por HTTP en localhost y recibe archivos Excel. Compatible con tu robot (name="file", botón "Submit", mensaje con "success").</p>

    {% if message %}
      <div class="msg {{ 'ok' if success else 'err' }}">{{ message }}</div>
      {% if saved_name %}
        <div class="meta">Guardado como: {{ saved_name }}</div>
        <div class="meta">Directorio: {{ upload_dir }}</div>
      {% endif %}
    {% endif %}

    <form method="post" action="{{ url_for('upload') }}" enctype="multipart/form-data">
      <div>
        <label for="username">Usuario (opcional):</label><br />
        <input type="text" id="username" name="username" placeholder="test_user" />
      </div>
      <div>
        <label for="password">Contraseña (opcional):</label><br />
        <input type="password" id="password" name="password" placeholder="test_pass" />
      </div>
      <div>
        <label for="file">Selecciona un archivo Excel (.xlsx)</label><br />
        <!-- Importante: name="file" para Selenium -->
        <input type="file" id="file" name="file" accept=".xlsx,.xls" required />
        <div class="note">Campo requerido (name="file").</div>
      </div>
      <!-- El botón debe contener el texto "Submit" para coincidir con la configuración del robot -->
      <button type="submit">Submit</button>
    </form>
  </div>
</body>
</html>
"""

SUCCESS_TEMPLATE = """<!DOCTYPE html>
<html lang=\"es\">
<meta charset=\"utf-8\" />
<title>Resultado</title>
<body>
  <div class=\"msg ok\">Archivo subido exitosamente: {{ saved_name }} - success</div>
  <div><a href=\"{{ url_for('index') }}\">Volver</a></div>
</body>
</html>
"""


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.get("/")
def index():
    return render_template_string(PAGE_TEMPLATE, message=None)


@app.post("/upload")
def upload():
    if "file" not in request.files:
        return render_template_string(
            PAGE_TEMPLATE,
            message="No se envió el campo de archivo 'file'",
            success=False,
            saved_name=None,
            upload_dir=str(UPLOAD_DIR),
        ), 400

    file = request.files["file"]

    if file.filename == "":
        return render_template_string(
            PAGE_TEMPLATE,
            message="No se seleccionó archivo",
            success=False,
            saved_name=None,
            upload_dir=str(UPLOAD_DIR),
        ), 400

    if not allowed_file(file.filename):
        return render_template_string(
            PAGE_TEMPLATE,
            message="Extensión no permitida. Solo .xlsx/.xls",
            success=False,
            saved_name=None,
            upload_dir=str(UPLOAD_DIR),
        ), 400

    # Guardar con nombre seguro
    filename = secure_filename(file.filename)
    save_path = UPLOAD_DIR / filename
    file.save(save_path)

    # Página de éxito; contiene la palabra "success" para que el robot la detecte
    return render_template_string(SUCCESS_TEMPLATE, saved_name=filename)


@app.get("/uploads/<path:filename>")
def serve_uploaded(filename: str):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=False)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # Ejecutar: python web/form_server.py
    # Luego usar la URL: http://127.0.0.1:5000/
    app.run(host="127.0.0.1", port=5000, debug=False)
