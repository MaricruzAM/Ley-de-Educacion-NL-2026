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

# Guarda estado por usuario
estados = {}

def limpiar_html(texto):
    reemplazos = {
        "<p>": "",
        "</p>": "\n\n",
        "<br>": "\n",
        "<br/>": "\n",
        "<br />": "\n",
        "<ul>": "",
        "</ul>": "",
        "<li>": "• ",
        "</li>": "\n",
    }

    for k, v in reemplazos.items():
        texto = texto.replace(k, v)

    return texto

def enviar_largo(chat_id, texto):
    if not texto:
        bot.send_message(chat_id, "No pude generar una respuesta.")
        return

    texto = limpiar_html(texto)

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
        "Hazme una pregunta sobre la ley."
    )

@bot.message_handler(func=lambda message: True)
def responder(message):
    try:
        chat_id = message.chat.id
        texto_usuario = message.text.strip()

        # Nueva pregunta
        if chat_id not in estados:
            estados[chat_id] = {
                "fase": "tipo",
                "pregunta": texto_usuario,
                "respuesta": ""
            }

            bot.reply_to(
                message,
                "¿Cómo deseas la respuesta?\n\n"
                "<b>1. Resumen claro</b>\n"
                "<b>2. Análisis completo con artículos</b>",
                parse_mode="HTML"
            )
            return

        fase = estados[chat_id]["fase"]

        # Elegir tipo de respuesta
        if fase == "tipo":
            if texto_usuario not in ["1", "2"]:
                bot.reply_to(message, "Responde 1 o 2")
                return

            tipo = "resumen claro" if texto_usuario == "1" else "análisis completo"

            pregunta = estados[chat_id]["pregunta"]

            bot.send_message(chat_id, "Estoy analizando la ley...")
            bot.send_chat_action(chat_id, "typing")

            prompt = f"""
Eres experto en la Ley de Educación de Nuevo León 2026.

Tipo: {tipo}

Reglas:
- Usa HTML simple (<b>)
- No inventes artículos
- Explica claro

Ley:
{texto_ley}

Pregunta:
{pregunta}
"""

            respuesta = client.generate_content(prompt)
            texto = respuesta.text if respuesta.text else "No pude responder."

            estados[chat_id]["respuesta"] = texto
            estados[chat_id]["fase"] = "aplica"

            enviar_largo(chat_id, texto)

            bot.send_message(chat_id, "¿Deseas aplicación práctica? (si/no)")
            return

        # Preguntar aplicación
        if fase == "aplica":
            if texto_usuario.lower() not in ["si", "sí", "no"]:
                bot.reply_to(message, "Responde si o no")
                return

            if texto_usuario.lower() == "no":
                estados.pop(chat_id)
                bot.send_message(chat_id, "Puedes hacer otra pregunta.")
                return

            estados[chat_id]["fase"] = "rol"

            bot.send_message(
                chat_id,
                "¿Para qué rol?\n\n"
                "1 Docente\n"
                "2 UDEI\n"
                "3 Directivo\n"
                "4 Supervisor\n"
                "5 Familia\n"
                "6 Todos"
            )
            return

        # Elegir rol
        if fase == "rol":
            roles = {
                "1": "docente",
                "2": "UDEI",
                "3": "directivo",
                "4": "supervisor",
                "5": "familia",
                "6": "todos"
            }

            if texto_usuario not in roles:
                bot.reply_to(message, "Elige del 1 al 6")
                return

            rol = roles[texto_usuario]

            bot.send_message(chat_id, "Generando aplicación práctica...")
            bot.send_chat_action(chat_id, "typing")

            prompt = f"""
Con base en esta respuesta legal:

{estados[chat_id]["respuesta"]}

Genera aplicación práctica para: {rol}

Reglas:
- No inventes ley
- Diferencia legal vs sugerencia
- Usa negritas
- Agrega advertencia de revisión
"""

            respuesta = client.generate_content(prompt)
            texto = respuesta.text if respuesta.text else "No pude generar aplicación."

            enviar_largo(chat_id, texto)

            bot.send_message(chat_id, "Puedes hacer otra pregunta.")

            estados.pop(chat_id)

    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

print("Bot corriendo...")
bot.infinity_polling()
