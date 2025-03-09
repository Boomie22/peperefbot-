import telebot
import requests
import os
import time
import threading
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import requests
from io import BytesIO

TOKEN = os.getenv("BOT_TOKEN")
API_URL = "http://127.0.0.1:8000/api/check_story"
bot = telebot.TeleBot(TOKEN)

# 🔹 Store user chat IDs who need verification
USER_CHAT_IDS = set()


def extract_qr_code(image_url):
    """Downloads an image and extracts the QR code."""
    response = requests.get(image_url)
    if response.status_code != 200:
        return None

    image = np.asarray(bytearray(response.content), dtype=np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    detected_qrs = decode(image)
    if detected_qrs:
        return detected_qrs[0].data.decode("utf-8")  # Extracted QR link

    return None


@bot.message_handler(commands=['start'])
def start(message):
    """ Greets the user and saves their chat_id """
    USER_CHAT_IDS.add(message.chat.id)
    bot.send_message(message.chat.id, "👋 Hello! Send /verify_story <username> to check a story.")

@bot.message_handler(commands=['verify_story'])
def verify_story(message):
    """ Verifies if the user posted the correct story. """
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ Use: /verify_story <username>")
        return

    username = args[1]
    bot.send_message(message.chat.id, f"🔍 Checking story for @{username}...")

    # ✅ Fetch latest story from Telegram API
    user_story_url = f"https://api.telegram.org/bot{TOKEN}/getUserStories?user_id={username}"
    
    try:
        response = requests.get(user_story_url)
        data = response.json()

        if not data.get("ok"):
            bot.send_message(message.chat.id, "⚠ No story found for this user.")
            return

        # ✅ Get the first story's media (Image URL)
        story_url = data["result"][0]["photo"]["sizes"][-1]["file_path"]
        print(f"✅ Found story: {story_url}")

        # ✅ Extract QR Code from Story Image
        extracted_qr = extract_qr_code(story_url)
        if not extracted_qr:
            bot.send_message(message.chat.id, "⚠ No QR code detected in the story.")
            return

        # ✅ Validate QR Code
        if "peperefbot.onrender.com/api/confirm_click?ref_id=" in extracted_qr:
            bot.send_message(message.chat.id, f"✅ Story verified! 🎉\nQR Code: {extracted_qr}")
        else:
            bot.send_message(message.chat.id, "⚠ Incorrect QR code. Make sure you posted the right story.")

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
