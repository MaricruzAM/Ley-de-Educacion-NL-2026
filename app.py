import os
import telebot
from google import genai

TOKEN = os.getenv("TOKEN_TELEGRAM")
CLAVE_GEMINI = os.getenv("CLAVE_GEMINI")

bot = telebot.TeleBot(TOKEN)
client = genai.Client(api_key=CLAVE_GEMINI)

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Hola, soy tu asistente de la Ley de Educación de NL. Pregúntame lo que quieras.")

@bot.message_handler(func=lambda message: True)
def responder(message):
    try:
        pregunta = message.text

        respuesta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=pregunta
        )

        texto = respuesta.text if respuesta.text else "No pude responder."
        bot.reply_to(message, texto[:4000])

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

print("Bot corriendo...")
bot.infinity_polling()


