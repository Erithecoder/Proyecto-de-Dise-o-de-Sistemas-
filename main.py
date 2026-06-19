from fastapi import FastAPI, HTTPException
from database import get_db_connection
from schemas import TicketCrear
from ai_model import predecir_categoria_ticket # <-- Importamos tu motor de IA

app = FastAPI(title="API SGCAT - Sistema de Tickets con NLP", version="1.0")

from fastapi import FastAPI, HTTPException
from database import get_db_connection
from schemas import TicketCrear
from ai_model import predecir_categoria_ticket
from fastapi.middleware.cors import CORSMiddleware # <-- NUEVO

app = FastAPI(title="API SGCAT - Sistema de Tickets con NLP", version="1.0")

from pydantic import BaseModel

class LoginRequest(BaseModel):
    correo: str
    contrasena: str

@app.post("/login/")
def login(req: LoginRequest):
    conexion = get_db_connection()
    if not conexion:
        raise HTTPException(status_code=500, detail="Error de conexión")
    try:
        from psycopg2.extras import RealDictCursor
        cursor = conexion.cursor(cursor_factory=RealDictCursor)
        
        # Comparamos el correo y la clave en la tabla usuarios
        sql = """
            SELECT u.id_usuario, u.nombre_completo, r.nombre_rol 
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id_rol
            WHERE u.correo = %s AND u.contrasena_hash = %s;
        """
        cursor.execute(sql, (req.correo, req.contrasena))
        usuario = cursor.fetchone()
        
        cursor.close()
        conexion.close()
        
        if not usuario:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        return usuario
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Damos permiso al navegador para consumir la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción se pone el dominio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def ruta_principal():
    conexion = get_db_connection()
    if conexion:
        conexion.close()
        return {"estado": "¡Servidor SGCAT en línea y conectado a PostgreSQL con éxito!"}
    else:
        return {"estado": "Servidor en línea, pero falló la conexión."}

@app.post("/tickets/")
def crear_ticket(ticket: TicketCrear):
    conexion = get_db_connection()
    if not conexion:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")
    
    try:
        id_categoria_predicha, sugerencia_ia = predecir_categoria_ticket(ticket.descripcion)
        
        cursor = conexion.cursor()
        sql = """
            INSERT INTO tickets (titulo, descripcion, id_usuario_creador, id_usuario_afectado, id_categoria_ia)
            VALUES (%s, %s, %s, %s, %s) RETURNING id_ticket;
        """
        valores = (ticket.titulo, ticket.descripcion, ticket.id_usuario_creador, ticket.id_usuario_afectado, id_categoria_predicha)
        
        cursor.execute(sql, valores)
        nuevo_id = cursor.fetchone()[0] 
        conexion.commit() 
        cursor.close()
        conexion.close()
        
        nombres_categorias = {1: "Hardware", 2: "Software", 3: "Redes", 4: "Revisión Manual"}
        nombre_cat = nombres_categorias.get(id_categoria_predicha, "Desconocida")
        
        # Agregamos la sugerencia a la respuesta JSON
        return {
            "mensaje": "Ticket registrado", 
            "id_ticket": nuevo_id,
            "clasificacion_ia": nombre_cat,
            "recomendacion_usuario": sugerencia_ia # <-- El mensaje para el usuario
        }
        
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=400, detail=f"Error al registrar el ticket: {str(e)}")
    
@app.get("/tickets/")
def obtener_tickets():
    conexion = get_db_connection()
    if not conexion:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")
    
    try:
        # Usamos RealDictCursor para que PostgreSQL devuelva los datos como un diccionario (JSON) automáticamente
        from psycopg2.extras import RealDictCursor
        cursor = conexion.cursor(cursor_factory=RealDictCursor)
        
        # Sentencia SQL con JOIN para cruzar las tablas y obtener nombres en lugar de IDs
        sql = """
            SELECT 
                t.id_ticket, 
                t.titulo, 
                t.descripcion, 
                t.estado,
                t.fecha_creacion,
                u_creador.nombre_completo AS creador,
                u_afectado.nombre_completo AS afectado,
                c.nombre_categoria AS clasificacion_ia
            FROM tickets t
            JOIN usuarios u_creador ON t.id_usuario_creador = u_creador.id_usuario
            JOIN usuarios u_afectado ON t.id_usuario_afectado = u_afectado.id_usuario
            LEFT JOIN categorias_ia c ON t.id_categoria_ia = c.id_categoria
            ORDER BY t.id_ticket DESC;
        """
        
        cursor.execute(sql)
        tickets_db = cursor.fetchall()
        
        cursor.close()
        conexion.close()
        
        return tickets_db
        
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=400, detail=f"Error al obtener los tickets: {str(e)}")
    
    # ENDPOINT: Obtener un solo ticket por su ID
@app.get("/tickets/{ticket_id}")
def obtener_ticket(ticket_id: int):
    conexion = get_db_connection()
    if not conexion:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")
    
    try:
        from psycopg2.extras import RealDictCursor
        cursor = conexion.cursor(cursor_factory=RealDictCursor)
        
        # Buscamos el ticket exacto usando el ID de la URL
        sql = """
        SELECT 
        t.id_ticket, 
        t.titulo, 
        t.descripcion, 
        t.estado,
        t.fecha_creacion,
        u_creador.nombre_completo AS creador,
        COALESCE(u_afectado.nombre_completo, u_creador.nombre_completo) AS afectado, -- Si es nulo, el afectado es el mismo creador
        c.nombre_categoria AS clasificacion_ia
    FROM tickets t
    JOIN usuarios u_creador ON t.id_usuario_creador = u_creador.id_usuario
    LEFT JOIN usuarios u_afectado ON t.id_usuario_afectado = u_afectado.id_usuario
    LEFT JOIN categorias_ia c ON t.id_categoria_ia = c.id_categoria
    ORDER BY t.id_ticket DESC;
    """
        cursor.execute(sql, (ticket_id,))
        ticket_db = cursor.fetchone() # fetchone() trae solo uno, no una lista
        
        cursor.close()
        conexion.close()
        
        if ticket_db is None:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
            
        return ticket_db
        
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=400, detail=f"Error al obtener el ticket: {str(e)}")
    
    # ENDPOINT: Obtener los tickets creados por un usuario específico
@app.get("/tickets/usuario/{usuario_id}")
def obtener_tickets_por_usuario(usuario_id: int):
    conexion = get_db_connection()
    if not conexion:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")
    
    try:
        from psycopg2.extras import RealDictCursor
        cursor = conexion.cursor(cursor_factory=RealDictCursor)
        
        sql = """
            SELECT 
        t.id_ticket, 
        t.titulo, 
        t.descripcion, 
        t.estado,
        t.fecha_creacion,
        u_creador.nombre_completo AS creador,
        COALESCE(u_afectado.nombre_completo, u_creador.nombre_completo) AS afectado, -- Si es nulo, el afectado es el mismo creador
        c.nombre_categoria AS clasificacion_ia
    FROM tickets t
    JOIN usuarios u_creador ON t.id_usuario_creador = u_creador.id_usuario
    LEFT JOIN usuarios u_afectado ON t.id_usuario_afectado = u_afectado.id_usuario -- <-- LEFT JOIN para proteger registros antiguos
    LEFT JOIN categorias_ia c ON t.id_categoria_ia = c.id_categoria
    ORDER BY t.id_ticket DESC;
        """
        
        cursor.execute(sql, (usuario_id,))
        tickets_user = cursor.fetchall()
        
        cursor.close()
        conexion.close()
        
        return tickets_user
        
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=400, detail=f"Error al obtener tickets del usuario: {str(e)}")
    
@app.delete("/tickets/{ticket_id}")
def eliminar_ticket(ticket_id: int):
    conexion = get_db_connection()
    if not conexion:
        raise HTTPException(status_code=500, detail="Error de conexión")
    try:
        cursor = conexion.cursor()
        sql = "DELETE FROM tickets WHERE id_ticket = %s;"
        cursor.execute(sql, (ticket_id,))
        conexion.commit()
        cursor.close()
        conexion.close()
        return {"mensaje": "Ticket eliminado"}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
    # ENDPOINT: Obtener la lista de usuarios para el formulario
@app.get("/usuarios/")
def obtener_usuarios():
    conexion = get_db_connection()
    if not conexion:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")
    
    try:
        from psycopg2.extras import RealDictCursor
        cursor = conexion.cursor(cursor_factory=RealDictCursor)
        
        # Solo traemos el ID y el nombre para llenar el menú desplegable
        sql = "SELECT id_usuario, nombre_completo FROM usuarios ORDER BY nombre_completo;"
        cursor.execute(sql)
        usuarios_db = cursor.fetchall()
        
        cursor.close()
        conexion.close()
        
        return usuarios_db
        
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=400, detail=f"Error al obtener los usuarios: {str(e)}")
    
    # ENDPOINT: Cambiar el estado del ticket a "Resuelto"
@app.put("/tickets/{ticket_id}/resolver")
def resolver_ticket(ticket_id: int):
    conexion = get_db_connection()
    if not conexion:
        raise HTTPException(status_code=500, detail="Error de conexión")
    try:
        cursor = conexion.cursor()
        sql = "UPDATE tickets SET estado = 'Resuelto' WHERE id_ticket = %s;"
        cursor.execute(sql, (ticket_id,))
        conexion.commit()
        
        cursor.close()
        conexion.close()
        return {"mensaje": f"Ticket #{ticket_id} marcado como resuelto"}
    except Exception as e:
        conexion.rollback()
        raise HTTPException(status_code=400, detail=str(e))