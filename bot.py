import os
import telebot
import requests
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image, ImageDraw
import qrcode

# ✅ Get bot token from environment variables
TOKEN = os.getenv("BOT_TOKEN")
API_URL = "https://peperefbot.onrender.com/api/confirm_click"
bot = telebot.TeleBot(TOKEN)

# ✅ Ensure temp directory exists
os.makedirs("temp", exist_ok=True)

def generate_centered_qr_story(username, ref_id, output_path):
    """
    ✅ Generates a **story** with a **centered QR code**
    """

    # ✅ 1. Create a blank **Instagram Story-size** white background
    img_size = (1080, 1920)
    background = Image.new("RGB", img_size, "white")
    draw = ImageDraw.Draw(background)

    # ✅ 2. Generate the QR Code
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr_data = f"https://peperefbot.onrender.com/scan?story_id={ref_id}"
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    # ✅ 3. Resize QR code for **better visibility**
    qr_size = 600  # Bigger for scanning
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

    # ✅ 4. **Center the QR code**
    pos = ((img_size[0] - qr_size) // 2, (img_size[1] - qr_size) // 2)
    background.paste(qr_img, pos, mask=qr_img)

    # ✅ 5. Add **Referral ID** text below QR code
    text_position = (img_size[0] // 2 - 200, pos[1] + qr_size + 50)
    draw.text(text_position, f"Referral ID: {ref_id}", fill="black")

    # ✅ 6. Save the final **story image**
    background.save(output_path)
    print(f"✅ Story with Centered QR Code saved at {output_path}")
    return output_path

def detect_qr_code(image_path):
    """
    ✅ Detects & extracts **QR Code data** from an image
    """
    img = cv2.imread(image_path)
    qr_codes = decode(img)
    
    if not qr_codes:
        return None
    return qr_codes[0].data.decode("utf-8")

@bot.message_handler(func=lambda message: message.forward_from is not None, content_types=['photo'])
def handle_forwarded_story(message):
    """ ✅ Handles forwarded **stories**, scans QR codes, verifies them """

    # ✅ 1. Ensure message is forwarded
    username = message.forward_from.username if message.forward_from else None
    if not username:
        bot.send_message(message.chat.id, "❌ Could not detect original poster! Ensure the story is correctly forwarded.")
        return

    # ✅ 2. Get **file URL** from Telegram servers
    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
    image_path = f"temp/{message.chat.id}.jpg"

    # ✅ 3. Download **forwarded story**
    response = requests.get(file_url)
    with open(image_path, 'wb') as f:
        f.write(response.content)

    # ✅ 4. Scan **for QR code in the story**
    qr_data = detect_qr_code(image_path)
    if not qr_data:
        bot.send_message(message.chat.id, "❌ No QR code detected in the forwarded story!")
        return

    # ✅ 5. Validate **QR code format**
    if "story_id=" in qr_data:
        story_id = qr_data.split("story_id=")[-1]
        response = requests.get(f"{API_URL}?story_id={story_id}")
        data = response.json()

        if data.get("success"):
            bot.send_message(message.chat.id, f"✅ Story by @{username} is **verified!** 🎉")
        else:
            bot.send_message(message.chat.id, "⚠ This QR Code is **not registered!** Ensure you used the correct story.")
    else:
        bot.send_message(message.chat.id, "⚠ QR Code format is incorrect!")

# ✅ Start the bot
print("🚀 Bot is running...")
bot.polling()
