from pydantic import BaseModel

class TicketCrear(BaseModel):
    titulo: str
    descripcion: str
    id_usuario_creador: int
    id_usuario_afectado: int