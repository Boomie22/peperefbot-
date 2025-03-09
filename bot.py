import telebot
import requests
import os

TOKEN = os.getenv("BOT_TOKEN")
API_URL = "https://peperefbot.onrender.com/api/check_story"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """ Handles forwarded photos (stories) and verifies them """

    # **1️⃣ Check if the message is forwarded**
    if not message.forward_from and not message.forward_from_chat:
        bot.send_message(message.chat.id, "❌ Please **forward** your story from Telegram.")
        return

    # **2️⃣ Get the file ID of the forwarded photo**
    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"

    bot.send_message(message.chat.id, "🔍 Checking your story... Please wait.")

    # **3️⃣ Send request to backend to check if this story is valid**
    response = requests.get(f"https://peperefbot.onrender.com/api/verify_story", params={"media_url": file_url, "user_id": message.from_user.id})
    data = response.json()

    # **4️⃣ Respond based on verification result**
    if data.get("success"):
        bot.send_message(message.chat.id, "✅ **Story confirmed!**\nYour verification has started.")
    else:
        bot.send_message(message.chat.id, "❌ **Invalid story!**\nPlease make sure you are forwarding the correct story.")

# Start the bot
bot.polling()
