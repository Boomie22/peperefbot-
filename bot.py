import telebot
import requests
import os

TOKEN = os.getenv("BOT_TOKEN")
API_URL = "http://127.0.0.1:8000/api/story/verify"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['verify_story'])
def verify_story(message):
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ Используй: /verify_story <username>")
        return

    username = args[1]
    bot.send_message(message.chat.id, f"🔍 Проверяю сторис у @{username}...")

    try:
        response = requests.get(f"{API_URL}?username={username}")
        data = response.json()

        if data.get("success"):
            bot.send_message(message.chat.id, f"✅ Сторис найдена! 🎉\n\n{data.get('message')}")
        else:
            bot.send_message(message.chat.id, f"❌ {data.get('message')}")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠ Ошибка проверки сторис: {e}")

bot.polling()
