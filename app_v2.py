import os
import telebot
import google.generativeai as genai

with open("ley_limpia.txt", "r", encoding="utf-8") as f:
    texto_ley = f.read()

MODELO_GEMINI = "gemini-2.5-flash"

TOKEN = os.getenv("TOKEN_TELEGRAM")
CLAVE_GEMINI = os.getenv("CLAVE_GEMINI")

bot = telebot.TeleBot(TOKEN)

genai.configure(api_key=CLAVE_GEMINI)
client = genai.GenerativeModel(MODELO_GEMINI)

# Guarda el estado temporal de cada usuario/chat
estados = {}


def enviar_largo(chat_id, texto):
    """
    Telegram tiene límite de caracteres.
    Esta función divide respuestas largas en partes.
    """
    if not texto:
        bot.send_message(chat_id, "No pude generar una respuesta.")
        return

    limite = 3500
    partes = [texto[i:i + limite] for i in range(0, len(texto), limite)]

    for i, parte in enumerate(partes, start=1):
        if len(partes) > 1:
            encabezado = f"<b>Parte {i} de {len(partes)}</b>\n\n"
            bot.send_message(chat_id, encabezado + parte, parse_mode="HTML")
        else:
            bot.send_message(chat_id, parte, parse_mode="HTML")


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Hola, soy tu asistente de la Ley de Educación de Nuevo León 2026.\n\n"
        "Hazme una pregunta sobre la ley y te ayudaré a revisarla."
    )


@bot.message_handler(func=lambda message: True)
def responder(message):
    try:
        chat_id = message.chat.id
        texto_usuario = message.text.strip()

        # Si el usuario no tiene estado, su mensaje se toma como nueva pregunta
        if chat_id not in estados:
            estados[chat_id] = {
                "fase": "elegir_tipo",
                "pregunta": texto_usuario,
                "respuesta_legal": ""
            }

            bot.reply_to(
                message,
                "Recibí tu pregunta.\n\n"
                "¿Cómo deseas la respuesta?\n\n"
                "<b>1. Resumen claro</b>\n"
                "<b>2. Análisis completo con artículos</b>",
                parse_mode="HTML"
            )
            return

        fase = estados[chat_id]["fase"]

        # FASE 1: Elegir resumen o análisis completo
        if fase == "elegir_tipo":
            pregunta = estados[chat_id]["pregunta"]

            if texto_usuario not in ["1", "2"]:
                bot.reply_to(
                    message,
                    "Por favor responde con:\n\n"
                    "<b>1</b> para Resumen claro\n"
                    "<b>2</b> para Análisis completo con artículos",
                    parse_mode="HTML"
                )
                return

            tipo_respuesta = "resumen claro" if texto_usuario == "1" else "análisis completo con artículos"

            bot.send_message(
                chat_id,
                "Estoy revisando la Ley de Educación de Nuevo León 2026 para darte una respuesta fundamentada..."
            )
            bot.send_chat_action(chat_id, "typing")

            prompt = f"""
Eres un asistente experto en la Ley de Educación de Nuevo León 2026.

Responde SIEMPRE en español.

Tipo de respuesta solicitada:
{tipo_respuesta}

Reglas obligatorias:
1. Usa formato HTML compatible con Telegram.
2. Usa <b>negritas</b> para encabezados y secciones.
3. Fundamenta con artículos cuando el texto de la ley lo permita.
4. No inventes artículos.
5. Si no encuentras fundamento textual suficiente, dilo claramente.
6. Diferencia entre:
   - lo que dice la ley
   - interpretación práctica
   - posibles implicaciones escolares
7. Mantén tono claro, institucional y útil.
8. No uses Markdown. Usa HTML simple.

Texto completo de la ley:
{texto_ley}

Pregunta del usuario:
{pregunta}
"""

            respuesta = client.generate_content(prompt)
            texto_respuesta = respuesta.text if respuesta.text else "No pude responder."

            estados[chat_id]["respuesta_legal"] = texto_respuesta
            estados[chat_id]["fase"] = "preguntar_aplicacion"

            enviar_largo(chat_id, texto_respuesta)

            bot.send_message(
                chat_id,
                "¿Deseas opciones de <b>aplicación práctica</b> de este segmento de la ley?\n\n"
                "Responde:\n"
                "<b>Sí</b> o <b>No</b>",
                parse_mode="HTML"
            )
            return

        # FASE 2: Preguntar si desea aplicación práctica
        if fase == "preguntar_aplicacion":
            if texto_usuario.lower() in ["no", "n"]:
                bot.reply_to(
                    message,
                    "De acuerdo. Puedes hacerme otra pregunta sobre la Ley de Educación de Nuevo León 2026."
                )
                estados.pop(chat_id, None)
                return

            if texto_usuario.lower() not in ["sí", "si", "s"]:
                bot.reply_to(
                    message,
                    "Por favor responde <b>Sí</b> o <b>No</b>.",
                    parse_mode="HTML"
                )
                return

            estados[chat_id]["fase"] = "elegir_rol"

            bot.reply_to(
                message,
                "¿Para qué rol deseas la aplicación práctica?\n\n"
                "<b>1. Docente regular</b>\n"
                "<b>2. Docente UDEI / educación especial</b>\n"
                "<b>3. Directivo escolar</b>\n"
                "<b>4. Supervisor / inspector</b>\n"
                "<b>5. Familia</b>\n"
                "<b>6. Todos los roles</b>",
                parse_mode="HTML"
            )
            return

        # FASE 3: Elegir rol y generar aplicación práctica
        if fase == "elegir_rol":
            roles = {
                "1": "docente regular",
                "2": "docente UDEI o educación especial",
                "3": "directivo escolar",
                "4": "supervisor o inspector",
                "5": "familia",
                "6": "todos los roles"
            }

            if texto_usuario not in roles:
                bot.reply_to(
                    message,
                    "Por favor elige una opción del <b>1</b> al <b>6</b>.",
                    parse_mode="HTML"
                )
                return

            rol = roles[texto_usuario]
            pregunta = estados[chat_id]["pregunta"]
            respuesta_legal = estados[chat_id]["respuesta_legal"]

            bot.send_message(
                chat_id,
                f"Estoy preparando opciones de aplicación práctica para: <b>{rol}</b>...",
                parse_mode="HTML"
            )
            bot.send_chat_action(chat_id, "typing")

            prompt_aplicacion = f"""
Eres un asistente experto en educación inclusiva y en la Ley de Educación de Nuevo León 2026.

Con base en la respuesta legal anterior, genera aplicación práctica para el rol de:
{rol}

Pregunta original:
{pregunta}

Respuesta legal previa:
{respuesta_legal}

Reglas obligatorias:
1. Responde en español.
2. Usa HTML compatible con Telegram.
3. Usa <b>negritas</b> para encabezados.
4. No inventes obligaciones.
5. Si algo no está expresamente en la ley, preséntalo como sugerencia práctica, no como mandato legal.
6. Diferencia claramente:
   - obligación o fundamento legal
   - acción práctica sugerida
   - ejemplo escolar
   - evidencia observable
7. Agrega una advertencia breve indicando que la IA puede equivocarse y que se debe revisar el texto oficial de la ley.
8. No uses Markdown. Usa HTML simple.
"""

            respuesta = client.generate_content(prompt_aplicacion)
            texto_aplicacion = respuesta.text if respuesta.text else "No pude generar aplicación práctica."

            enviar_largo(chat_id, texto_aplicacion)

            bot.send_message(
                chat_id,
                "Puedes hacerme otra pregunta sobre la Ley de Educación de Nuevo León 2026."
            )

            estados.pop(chat_id, None)
            return

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")


print("Bot corriendo...")
bot.infinity_polling()
