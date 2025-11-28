import os
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
from pymongo import MongoClient

# Cargar variables de entorno desde .env
load_dotenv()

# --------- CONFIG GEMINI --------- #

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Falta GEMINI_API_KEY en el archivo .env dentro de backend")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# --------- CONFIG MONGODB --------- #

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DBNAME = os.getenv("MONGODB_DBNAME", "trabajo_titulo")

if not MONGODB_URI:
    raise RuntimeError("Falta MONGODB_URI en el archivo .env dentro de backend")

mongo_client = MongoClient(MONGODB_URI)
mongo_db = mongo_client[MONGODB_DBNAME]
interacciones_col = mongo_db["interacciones"]

# --------- FLASK --------- #

app = Flask(__name__)
CORS(app)


# --------- FUNCIONES AUXILIARES (GEMINI) --------- #

def clasificar_mensaje(mensaje_usuario: str) -> int:
    """
    Usa Gemini para clasificar el mensaje en una categoría 1..5.
    """

    prompt = f"""
Eres un clasificador de intención para un bot de la empresa Active Research,
dedicada a estudios de mercado y opinión pública.

Debes clasificar el mensaje del usuario en UNA sola de las siguientes categorías:

1. Preguntar sobre Active Research.
2. Preguntas de investigación (técnicas, estadísticas, encuestas, metodologías como CATI, etc.).
3. Cotizar proyectos de estudios de mercado u opinión pública.
4. Preguntas sobre el pulso ciudadano (opinión pública, encuestas recientes, resultados, análisis de opinión).
5. Otro (cualquier cosa que no tenga relación con los puntos anteriores).

Mensaje del usuario: \"\"\"{mensaje_usuario}\"\"\"

Responde SOLO con el número de categoría (1, 2, 3, 4 o 5), sin texto adicional.
"""

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    texto = (response.text or "").strip()

    try:
        categoria = int(texto)
    except ValueError:
        categoria = 5  # por seguridad, caemos en "No aplica"

    if categoria not in (1, 2, 3, 4, 5):
        categoria = 5

    return categoria


def generar_respuesta(mensaje_usuario: str, categoria: int) -> str:
    """
    Usa Gemini para generar una respuesta amigable según la categoría detectada.
    """

    prompt = f"""
Eres un asistente de chat de la empresa Activa Research.
Respondes de forma clara y amigable a potenciales clientes
sobre temas de estudios de mercado y opinión pública.

Categorías de intención:
1. Preguntar sobre Activa Research.
2. Preguntas de investigación (técnicas, estadísticas, encuestas, metodologías como CATI, etc.).
3. Cotizar proyectos de estudios de mercado u opinión pública.
4. Preguntas sobre el pulso ciudadano (opinión pública, encuestas recientes, resultados, análisis de opinión).
5. No aplica.

Da una respuesta breve y útil en español para el usuario,
en base a la categoría detectada y su mensaje.

Categoría detectada: {categoria}
Mensaje del usuario: \"\"\"{mensaje_usuario}\"\"\"
"""

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return (response.text or "").strip()


# --------- FUNCION AUXILIAR: GUARDAR EN MONGODB --------- #

def guardar_interaccion(mensaje_usuario: str, categoria: int, respuesta_bot: str, modo: str):
    """
    Guarda una interacción en la colección 'interacciones'.
    """
    doc = {
        "mensaje_usuario": mensaje_usuario,
        "categoria": categoria,
        "respuesta_bot": respuesta_bot,
        "modo": modo,  # 'gemini' o 'fallback'
        "timestamp": datetime.utcnow(),
    }

    try:
        interacciones_col.insert_one(doc)
    except Exception as e:
        # No queremos que un error de BD bote la respuesta al usuario
        print("Error guardando en MongoDB:", repr(e))


# --------- ENDPOINT PRINCIPAL --------- #

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensaje_usuario = (data.get("message") or "").strip()

    if not mensaje_usuario:
        return jsonify({"error": "Mensaje vacío"}), 400

    try:
        # 1) Clasificar el mensaje con Gemini
        categoria = clasificar_mensaje(mensaje_usuario)

        # 2) Decidir la respuesta según la categoría
        if categoria == 5:
            respuesta_bot = (
                "Tu pregunta no aplica al contexto del sitio. "
                "Puedes preguntarme sobre Activa Research, sobre investigación "
                "(técnicas, estadísticas, encuestas), cotización de proyectos "
                "o sobre el pulso ciudadano."
            )
        else:
            respuesta_bot = generar_respuesta(mensaje_usuario, categoria)

        modo = "gemini"

    except Exception as e:
        # Si algo falla con Gemini (sin cuota, error de red, etc.),
        # usamos un plan B con lógica simple local.
        print("Error llamando a Gemini:", repr(e))

        mensaje_lower = mensaje_usuario.lower()

        if "active research" in mensaje_lower:
            categoria = 1
            respuesta_bot = "Parece que quieres saber algo sobre Active Research. (modo sin IA)"
        elif "cotizar" in mensaje_lower:
            categoria = 3
            respuesta_bot = "Parece que quieres cotizar un proyecto. (modo sin IA)"
        elif "cati" in mensaje_lower or "encuesta" in mensaje_lower:
            categoria = 2
            respuesta_bot = "Parece que preguntas por temas de investigación/encuestas. (modo sin IA)"
        elif "pulso" in mensaje_lower or "opinión" in mensaje_lower:
            categoria = 4
            respuesta_bot = "Parece que preguntas por el pulso ciudadano. (modo sin IA)"
        else:
            categoria = 5
            respuesta_bot = (
                "Por ahora no puedo conectar con el modelo de IA de Gemini. "
                "Solo puedo filtrar preguntas básicas: Active Research, investigación, "
                "cotización de proyectos o pulso ciudadano."
            )

        modo = "fallback"

    # 3) Guardar interacción en MongoDB
    guardar_interaccion(mensaje_usuario, categoria, respuesta_bot, modo)

    # 4) Devolver la respuesta al frontend
    return jsonify({
        "categoria": categoria,
        "respuesta": respuesta_bot,
        "modo": modo,
    })


if __name__ == "__main__":
    app.run(port=5000, debug=True)
