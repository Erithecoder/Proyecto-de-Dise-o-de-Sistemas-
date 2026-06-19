import psycopg2

def get_db_connection():
    try:
        # Aquí configuramos la llave de acceso a tu servidor PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            database="sgcat_db",
            user="postgres",
            password="admin",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"Error fatal conectando a la base de datos: {e}")
        return None