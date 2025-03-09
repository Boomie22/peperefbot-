import telebot
import requests
import os
import time
import threading

TOKEN = os.getenv("BOT_TOKEN")
API_URL = "http://127.0.0.1:8000/api/check_story"
bot = telebot.TeleBot(TOKEN)

# 🔹 Store user chat IDs who need verification
USER_CHAT_IDS = set()

@bot.message_handler(commands=['start'])
def start(message):
    """ Greets the user and saves their chat_id """
    USER_CHAT_IDS.add(message.chat.id)
    bot.send_message(message.chat.id, "👋 Hello! Send /verify_story <username> to check a story.")

@bot.message_handler(commands=['verify_story'])
def verify_story(message):
    """ Manually checks the story for a given username """
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ Use: /verify_story <username>")
        return

    username = args[1]
    bot.send_message(message.chat.id, f"🔍 Checking story for @{username}...")

    try:
        response = requests.get(f"{API_URL}?username={username}")
        data = response.json()

        if data.get("success"):
            bot.send_message(message.chat.id, f"✅ Story verified! 🎉\n\n{data.get('message')}")
        else:
            bot.send_message(message.chat.id, f"⚠ {data.get('message')}")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠ Error checking story: {e}")

# ✅ **Periodic Background Check for Story Validity**
def periodic_check():
    while True:
        if USER_CHAT_IDS:
            for chat_id in USER_CHAT_IDS:
                username = "test_user"  # 🔹 Replace with dynamic usernames from DB
                response = requests.get(f"{API_URL}?username={username}")
                data = response.json()

                if data.get("success"):
                    bot.send_message(chat_id, f"✅ Story for @{username} is verified! 🎉")
                else:
                    bot.send_message(chat_id, f"⚠ @{username}, your story is not valid yet.")

        time.sleep(3600)  # Check every hour

# ✅ Start periodic checking in a background thread
threading.Thread(target=periodic_check, daemon=True).start()

bot.polling()
