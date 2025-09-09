import sqlite3

conn = sqlite3.connect('PRUEBA-RPA-main/data/database/productos.db')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) as total_products, AVG(price) as avg_price FROM Productos;")
result = cur.fetchone()
print(f"Total products: {result[0]}, Average price: {result[1]}")
conn.close()
