import telebot
import requests
from telebot import types

TOKEN = "7528900991:AAEqQ0m1AzMsChUKK5g6Qisn52DKv_9b90Q"  # Заменить на реальный токен бота
API_URL = "http://127.0.0.1:8000/api/check_story"  # URL локального API

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Отправь мне свой username, и я проверю, опубликована ли сторис.")

@bot.message_handler(func=lambda message: True)
def check_story(message):
    username = message.text.strip().replace("@", "")
    
    response = requests.get(f"{API_URL}?username={username}")

    if response.status_code == 200 and response.json().get("success"):
        bot.send_message(message.chat.id, "✅ Мы нашли твою сторис! Тебе засчитана награда 🎉")
    else:
        bot.send_message(message.chat.id, "❌ Не удалось найти твою сторис. Убедись, что ты правильно вставил ссылку!")

bot.polling()
