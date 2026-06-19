from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import numpy as np

# Datos de entrenamiento ampliados
textos_entrenamiento = [
    # Hardware (1)
    "La PC no da video, el monitor no enciende",
    "El teclado mecánico dejó de funcionar",
    "La pantalla tiene líneas de colores",
    "El mouse no responde o la computadora no prende",
    # Software (2)
    "Windows me tira un pantallazo azul de error",
    "Word se cierra solo al intentar guardar",
    "El sistema operativo está muy lento",
    "Mi programa no guarda, se congela o da error", # <-- Añadimos tu caso real
    # Redes (3)
    "No hay conexión a internet en la oficina",
    "El cable de red está desconectado",
    "No puedo acceder a la intranet corporativa",
    "El Wi-Fi está muy lento y se desconecta a cada rato"
]

etiquetas = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]

modelo_nlp = make_pipeline(TfidfVectorizer(), MultinomialNB())
modelo_nlp.fit(textos_entrenamiento, etiquetas)

# Base de conocimiento para las recomendaciones automáticas
RECOMENDACIONES = {
    1: "Autodiagnóstico de Hardware: Por favor, verifique que todos los cables de alimentación y conexión estén firmemente conectados antes de que llegue el técnico.",
    2: "Autodiagnóstico de Software: Intente guardar su trabajo (si es posible) y reinicie el equipo. Si el problema persiste, no abra más programas.",
    3: "Autodiagnóstico de Redes: Verifique si el cable Ethernet está bien conectado a su equipo o si el icono de Wi-Fi muestra alguna alerta.",
    4: "Su ticket ha sido registrado. Un técnico evaluará la descripción manualmente para asignarle la prioridad correcta."
}

def predecir_categoria_ticket(descripcion: str):
    """Devuelve una tupla: (id_categoria, sugerencia_para_el_usuario)"""
    # Calculamos la probabilidad de cada categoría
    probabilidades = modelo_nlp.predict_proba([descripcion])[0]
    confianza_maxima = np.max(probabilidades)
    
    # Si la IA tiene menos del 35% de confianza (ej. texto sin sentido "ajshdaksjdh")
    if confianza_maxima < 0.35:
        id_predicho = 4 # ID de "Otros / Revisión Manual"
    else:
        # Obtenemos el ID de la categoría ganadora
        indice_ganador = np.argmax(probabilidades)
        id_predicho = int(modelo_nlp.classes_[indice_ganador])
        
    sugerencia = RECOMENDACIONES.get(id_predicho, "")
    
    return id_predicho, sugerencia