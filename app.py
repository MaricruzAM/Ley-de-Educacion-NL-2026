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


def enviar_respuesta_larga(message, texto, limite=3500):
    partes = [texto[i:i+limite] for i in range(0, len(texto), limite)]

    if len(partes) == 1:
        bot.reply_to(message, partes[0])
    else:
        total = len(partes)
        for i, parte in enumerate(partes, start=1):
            encabezado = f"Parte {i} de {total}:\n\n"
            bot.send_message(message.chat.id, encabezado + parte)


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Hola, soy tu asistente de la Ley de Educación de Nuevo León. Pregúntame lo que quieras."
    )


@bot.message_handler(func=lambda message: True)
def responder(message):
    try:
        pregunta = message.text

        bot.reply_to(message, "Estoy trabajando en tu respuesta...")

        prompt = f"""
Eres un asistente experto en la Ley de Educación de Nuevo León 2026.

Responde SIEMPRE en español.

Explica de forma clara y fundamenta tus respuestas mencionando artículos cuando sea posible.

Texto de la ley:
{texto_ley}

Pregunta del usuario:
{pregunta}
"""

        respuesta = client.generate_content(prompt)

        texto = respuesta.text if respuesta.text else "No pude responder."

        enviar_respuesta_larga(message, texto)

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")


print("Bot corriendo...")
bot.infinity_polling()
