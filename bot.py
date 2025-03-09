import telebot
import requests
import os
import cv2
import numpy as np
from pyzbar.pyzbar import decode

TOKEN = os.getenv("BOT_TOKEN")
API_URL = "https://peperefbot.onrender.com/api/confirm_click"
bot = telebot.TeleBot(TOKEN)

# Ensure temp directory exists
os.makedirs("temp", exist_ok=True)

@bot.message_handler(func=lambda message: message.forward_from is not None, content_types=['photo'])
def handle_forwarded_story(message):
    """ Handles forwarded stories, scans QR codes, and verifies them """

    # ✅ 1. Ensure the message is forwarded
    username = message.forward_from.username if message.forward_from else None
    if not username:
        bot.send_message(message.chat.id, "❌ Unable to detect the original poster! Please ensure the story is correctly forwarded.")
        return

    # ✅ 2. Get the file URL from Telegram servers
    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"

    # ✅ 3. Download the forwarded story
    image_path = f"temp/{message.chat.id}.jpg"
    response = requests.get(file_url)
    with open(image_path, 'wb') as f:
        f.write(response.content)

    # ✅ 4. Scan for QR code in the image
    img = cv2.imread(image_path)
    qr_codes = decode(img)

    if not qr_codes:
        bot.send_message(message.chat.id, "❌ No QR code detected in the forwarded story!")
        return

    qr_data = qr_codes[0].data.decode("utf-8")

    # ✅ 5. Validate QR code format
    if "story_id=" in qr_data:
        story_id = qr_data.split("story_id=")[-1]

        # ✅ 6. Send request to verify the QR code
        response = requests.get(f"{API_URL}?story_id={story_id}")
        data = response.json()

        if data.get("success"):
            bot.send_message(message.chat.id, f"✅ Story by @{username} is **verified!** 🎉")
        else:
            bot.send_message(message.chat.id, "⚠ This QR Code is **not registered!** Please ensure you used the correct story.")
    else:
        bot.send_message(message.chat.id, "⚠ QR Code format is incorrect!")

# ✅ Start the bot
bot.polling()
