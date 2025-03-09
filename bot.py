import telebot
import requests
import cv2
from pyzbar.pyzbar import decode
import numpy as np
import os

TOKEN = os.getenv("BOT_TOKEN")
API_URL = "https://peperefbot.onrender.com/api/confirm_click"
bot = telebot.TeleBot(TOKEN)

# ✅ Ensure temp directory exists for images
os.makedirs("temp", exist_ok=True)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """ Принимает фото и проверяет QR-код """

    chat_id = message.chat.id
    bot.send_message(chat_id, "📸 Обрабатываю фото...")

    try:
        # **1️⃣ Получаем фото**
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"

        # **2️⃣ Скачиваем фото**
        response = requests.get(file_url)
        image_path = f"temp/{chat_id}.jpg"
        with open(image_path, 'wb') as f:
            f.write(response.content)

        # **3️⃣ Открываем и сканируем QR-код**
        img = cv2.imread(image_path)
        qr_codes = decode(img)

        if not qr_codes:
            bot.send_message(chat_id, "❌ QR-код не найден на изображении!")
            return

        # **4️⃣ Декодируем QR-код**
        qr_data = qr_codes[0].data.decode("utf-8")

        # **5️⃣ Проверяем, есть ли этот QR-код в системе**
        if "story_id=" in qr_data:
            story_id = qr_data.split("story_id=")[-1]
            check_url = f"{API_URL}?story_id={story_id}"
            response = requests.get(check_url)
            data = response.json()

            if data.get("success"):
                bot.send_message(chat_id, "✅ Сторис подтверждена!")
            else:
                bot.send_message(chat_id, "⚠ Этот QR-код не найден в базе!")
        else:
            bot.send_message(chat_id, "⚠ QR-код не соответствует формату!")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при обработке фото: {str(e)}")

bot.polling()
