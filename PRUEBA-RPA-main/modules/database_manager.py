"""
Gestor de base de datos para el proceso RPA
Soporta inserción sin duplicados y consultas para reportes
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.settings import DatabaseSettings
from utils.logger import setup_logger


class DatabaseManager:
    """Gestor de base de datos SQLite para Productos"""

    def __init__(self, db_path: Optional[str] = None):
        self.logger = setup_logger("DatabaseManager")
        self.db_path = Path(db_path) if db_path else Path(DatabaseSettings.get_connection_string())
        self._connect()
        self._initialize_database()

    def _connect(self):
        """Establece la conexión a la base de datos y aplica PRAGMAs"""
        try:
            self.conn = sqlite3.connect(
                str(self.db_path),
                timeout=DatabaseSettings.TIMEOUT,
                isolation_level=DatabaseSettings.ISOLATION_LEVEL,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            self.conn.row_factory = sqlite3.Row

            cur = self.conn.cursor()
            # PRAGMAs de rendimiento/consistencia
            cur.execute(f"PRAGMA journal_mode={DatabaseSettings.JOURNAL_MODE}")
            cur.execute(f"PRAGMA synchronous={DatabaseSettings.SYNCHRONOUS}")
            cur.execute(f"PRAGMA cache_size={DatabaseSettings.CACHE_SIZE}")
            cur.close()

            self.logger.info("✅ Conexión a BD establecida", {"db_path": str(self.db_path)})
        except Exception as e:
            self.logger.error(f"Error conectando a BD: {e}")
            raise

    def _initialize_database(self):
        """Crea la tabla Productos si no existe con índices optimizados"""
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS Productos (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                fecha_insercion TEXT NOT NULL
            );
            """
            with self.conn:
                self.conn.execute(create_table_sql)

                # Crear índices para optimizar consultas
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON Productos(category)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_fecha_insercion ON Productos(fecha_insercion)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_price ON Productos(price)")

            self.logger.info("🗄️  Tabla 'Productos' verificada/creada con índices optimizados")
        except Exception as e:
            self.logger.error(f"Error inicializando BD: {e}")
            raise

    def insert_products(self, products: List[Dict[str, Any]]) -> int:
        """Inserta productos evitando duplicados por clave primaria id con manejo robusto de concurrencia

        Args:
            products: Lista de productos con campos id, title, price, category, description, fecha_insercion
        Returns:
            int: cantidad insertada efectivamente (excluye ignorados por duplicado)
        """
        if not products:
            return 0

        insert_sql = (
            "INSERT OR IGNORE INTO Productos (id, title, price, category, description, fecha_insercion)"
            " VALUES (?, ?, ?, ?, ?, ?)"
        )

        inserted = 0
        try:
            # Usar bloqueo explícito para concurrencia
            with self.conn:
                # Adquirir lock exclusivo para escritura
                self.conn.execute("BEGIN EXCLUSIVE")

                for p in products:
                    try:
                        # Normalizar y validar datos mínimos
                        pid = int(p["id"])  # lanza si no convertible
                        title = str(p.get("title", "")).strip()
                        price = float(p.get("price", 0))
                        category = str(p.get("category", "")).strip()
                        description = str(p.get("description", "")).strip()
                        fecha = p.get("fecha_insercion")
                        if isinstance(fecha, datetime):
                            fecha_str = fecha.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            # Si viene como string o None, forzar a ahora si vacío
                            fecha_str = str(fecha) if fecha else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        cur = self.conn.execute(insert_sql, (pid, title, price, category, description, fecha_str))
                        # rowcount es 1 si insertó, 0 si ignorado
                        if cur.rowcount == 1:
                            inserted += 1

                    except (ValueError, TypeError) as ve:
                        self.logger.warning(f"Producto inválido omitido (id: {p.get('id', 'unknown')}): {ve}")
                        continue
                    except Exception as pe:
                        self.logger.error(f"Error procesando producto individual: {pe}")
                        # Rollback de la transacción completa en error crítico
                        self.conn.rollback()
                        raise

                # Commit explícito
                self.conn.commit()

            self.logger.log_db_operation(
                "INSERT_PRODUCTS",
                table="Productos",
                records_affected=inserted,
            )
            return inserted

        except Exception as e:
            self.logger.error(f"Error insertando productos: {e}")
            # Asegurar rollback en caso de error
            try:
                if self.conn:
                    self.conn.rollback()
            except:
                pass
            raise

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Retorna todos los productos ordenados por id"""
        try:
            sql = "SELECT id, title, price, category, description, fecha_insercion FROM Productos ORDER BY id"
            cur = self.conn.execute(sql)
            rows = cur.fetchall()
            # Convertir a dicts
            products = [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "price": row["price"],
                    "category": row["category"],
                    "description": row["description"],
                    "fecha_insercion": row["fecha_insercion"],
                }
                for row in rows
            ]
            return products
        except Exception as e:
            self.logger.error(f"Error consultando productos: {e}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """Calcula estadísticas globales y por categoría"""
        try:
            stats: Dict[str, Any] = {
                "total_products": 0,
                "avg_price": 0.0,
                "category_stats": [],
            }

            # Totales
            cur = self.conn.execute("SELECT COUNT(*) AS cnt, AVG(price) AS avg_price FROM Productos")
            row = cur.fetchone()
            if row:
                stats["total_products"] = int(row["cnt"]) if row["cnt"] is not None else 0
                stats["avg_price"] = float(row["avg_price"]) if row["avg_price"] is not None else 0.0

            # Por categoría
            cur = self.conn.execute(
                """
                SELECT category,
                       COUNT(*)           AS count,
                       AVG(price)         AS avg_price,
                       MIN(price)         AS min_price,
                       MAX(price)         AS max_price
                FROM Productos
                GROUP BY category
                ORDER BY category
                """
            )
            rows = cur.fetchall()
            stats["category_stats"] = [
                {
                    "category": r["category"],
                    "count": int(r["count"]) if r["count"] is not None else 0,
                    "avg_price": float(r["avg_price"]) if r["avg_price"] is not None else 0.0,
                    "min_price": float(r["min_price"]) if r["min_price"] is not None else 0.0,
                    "max_price": float(r["max_price"]) if r["max_price"] is not None else 0.0,
                }
                for r in rows
            ]

            return stats
        except Exception as e:
            self.logger.error(f"Error calculando estadísticas: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """Realiza verificación de integridad de la base de datos"""
        try:
            health = {
                "database_connected": False,
                "table_exists": False,
                "record_count": 0,
                "last_insert": None,
                "integrity_check": False
            }

            # Verificar conexión
            self.conn.execute("SELECT 1")
            health["database_connected"] = True

            # Verificar tabla
            cur = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Productos'")
            if cur.fetchone():
                health["table_exists"] = True

                # Contar registros
                cur = self.conn.execute("SELECT COUNT(*) as count FROM Productos")
                row = cur.fetchone()
                health["record_count"] = row["count"] if row else 0

                # Última inserción
                cur = self.conn.execute("SELECT MAX(fecha_insercion) as last FROM Productos")
                row = cur.fetchone()
                health["last_insert"] = row["last"] if row and row["last"] else None

            # Verificar integridad
            cur = self.conn.execute("PRAGMA integrity_check")
            result = cur.fetchone()
            health["integrity_check"] = result and result[0] == "ok"

            return health

        except Exception as e:
            self.logger.error(f"Error en health check: {e}")
            return {
                "database_connected": False,
                "error": str(e)
            }

    def close(self):
        try:
            if hasattr(self, "conn") and self.conn:
                self.conn.close()
                self.logger.debug("Conexión a BD cerrada")
        except Exception:
            pass

    # Soporte de context manager
    def __enter__(self) -> "DatabaseManager":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def test_database_manager() -> bool:
    """Test básico del gestor de BD"""
    try:
        with DatabaseManager() as db:
            # Leer estadísticas iniciales
            _ = db.get_statistics()
            # Insertar datos de prueba mínimos
            sample = [{
                "id": 1000001,
                "title": "Producto Test",
                "price": 9.99,
                "category": "test",
                "description": "desc",
                "fecha_insercion": datetime.now(),
            }]
            _ = db.insert_products(sample)
            # Leer lista
            _ = db.get_all_products()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    ok = test_database_manager()
    print("OK" if ok else "FAIL")
