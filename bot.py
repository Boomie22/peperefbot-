import telebot
import requests
import cv2
from pyzbar.pyzbar import decode
import numpy as np
import os
import time
import threading

TOKEN = os.getenv("BOT_TOKEN")  # Your bot token
API_URL = "https://peperefbot.onrender.com/api/confirm_click"  # API to confirm stories
bot = telebot.TeleBot(TOKEN)

# 🔹 Store active story verifications
ACTIVE_STORIES = {}  # { chat_id: { "message_id": int, "story_id": str, "expires_at": timestamp } }


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """ Handles a forwarded story and verifies its QR code. """

    # Ensure this is a forwarded message
    if not message.forward_date:
        bot.send_message(message.chat.id, "❌ Пожалуйста, перешлите историю, а не загружайте фото вручную!")
        return

    # **1️⃣ Get the photo file info**
    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"

    # **2️⃣ Download the image**
    response = requests.get(file_url)
    image_path = f"temp/{message.chat.id}.jpg"
    os.makedirs("temp", exist_ok=True)

    with open(image_path, 'wb') as f:
        f.write(response.content)

    # **3️⃣ Decode the QR code**
    img = cv2.imread(image_path)
    qr_codes = decode(img)

    if not qr_codes:
        bot.send_message(message.chat.id, "❌ QR-код не найден на изображении!")
        return

    qr_data = qr_codes[0].data.decode("utf-8")

    # **4️⃣ Extract `story_id` from QR code**
    if "story_id=" in qr_data:
        story_id = qr_data.split("story_id=")[-1]

        # **5️⃣ Check if the story exists in the database**
        response = requests.get(f"{API_URL}?story_id={story_id}")
        data = response.json()

        if data.get("success"):
            bot.send_message(message.chat.id, "✅ Сторис подтверждена! Запускаем 8-часовой таймер.")
            
            # **6️⃣ Store the verification details**
            expires_at = time.time() + 8 * 3600  # 8 hours from now
            ACTIVE_STORIES[message.chat.id] = {
                "message_id": message.message_id,
                "story_id": story_id,
                "expires_at": expires_at
            }

        else:
            bot.send_message(message.chat.id, "⚠ Этот QR-код не найден в базе!")
    else:
        bot.send_message(message.chat.id, "⚠ QR-код не соответствует формату!")


# ✅ **Step 2: Periodic Check to Ensure Story Still Exists**
def periodic_check():
    while True:
        current_time = time.time()
        for chat_id, data in list(ACTIVE_STORIES.items()):
            if current_time >= data["expires_at"]:
                bot.send_message(chat_id, "✅ Сторис была опубликована 8 часов и успешно подтверждена! 🎉")
                del ACTIVE_STORIES[chat_id]  # Remove from active tracking
            else:
                # 🔹 Try checking if the forwarded message still exists
                try:
                    bot.forward_message(chat_id, chat_id, data["message_id"])
                    print(f"✅ Story still exists for chat_id {chat_id}")
                except Exception:
                    bot.send_message(chat_id, "⚠ Ваша сторис удалена! Проверка отменена.")
                    del ACTIVE_STORIES[chat_id]  # Remove from active tracking

        time.sleep(3600)  # 🔄 Check every hour


# ✅ **Start the periodic check in the background**
threading.Thread(target=periodic_check, daemon=True).start()

bot.polling()
