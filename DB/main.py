from fastapi import FastAPI
from database import get_db_connection

# Inicializamos el servidor
app = FastAPI(title="API SGCAT - Sistema de Tickets", version="1.0")

# Creamos nuestro primer "Endpoint" (Ruta)
@app.get("/")
def ruta_principal():
    # Probamos si la base de datos responde
    conexion = get_db_connection()
    
    if conexion:
        conexion.close() # Siempre debemos cerrar la puerta después de usarla
        return {"estado": "Servidor SGCAT en línea y conectado a PostgreSQL con éxito"}
    else:
        return {"estado": "Servidor en línea, pero falló la conexión a la base de datos."}