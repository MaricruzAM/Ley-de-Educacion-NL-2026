import os
import telebot
import google.generativeai as genai

TOKEN = os.getenv("TOKEN_TELEGRAM")
CLAVE_GEMINI = os.getenv("CLAVE_GEMINI")

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=CLAVE_GEMINI)
client = genai.GenerativeModel(MODELO_GEMINI)

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Hola, soy tu asistente de la Ley de Educación de NL. Pregúntame lo que quieras.")

@bot.message_handler(func=lambda message: True)
def responder(message):
    try:
        pregunta = message.text

        respuesta = client.generate_content(prompt)

        texto = respuesta.text if respuesta.text else "No pude responder."
        bot.reply_to(message, texto[:4000])

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

print("Bot corriendo...")
bot.infinity_polling()


