import os
import telebot
import google.generativeai as genai

with open("ley_limpia.txt.txt", "r", encoding="utf-8") as f:
    texto_ley = f.read()

MODELO_GEMINI = "gemini-2.5-flash"

TOKEN = os.getenv("TOKEN_TELEGRAM")
CLAVE_GEMINI = os.getenv("CLAVE_GEMINI")

bot = telebot.TeleBot(TOKEN)

genai.configure(api_key=CLAVE_GEMINI)
client = genai.GenerativeModel(MODELO_GEMINI)

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

        prompt = f"""
Eres un asistente experto en la Ley de Educación de Nuevo León 2026.

Responde SIEMPRE en español.

Explica de forma clara y fundamenta tus respuestas mencionando artículos cuando sea posible.

Texto de la ley:
{texto_ley[:30000]}

Pregunta del usuario:
{pregunta}
"""

        respuesta = client.generate_content(prompt)

        texto = respuesta.text if respuesta.text else "No pude responder."
        bot.reply_to(message, texto[:4000])

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

print("Bot corriendo...")
bot.infinity_polling()
