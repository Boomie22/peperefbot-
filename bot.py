import telebot
import requests
import os
import cv2
from pyzbar.pyzbar import decode  # ✅ Import decode for QR scanning

# ✅ Load environment variable for bot token
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is missing!")

# ✅ Ensure 'temp' folder exists
os.makedirs("temp", exist_ok=True)

API_URL = "https://peperefbot.onrender.com/api/check_story"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: message.forward_from is not None, content_types=['photo'])
def handle_forwarded_story(message):
    """ Handles forwarded stories and checks QR codes """
    
    # ✅ Get the forwarded user
    username = message.forward_from.username if message.forward_from else None
    if not username:
        bot.send_message(message.chat.id, "❌ Unable to detect the original poster!")
        return

    # ✅ Get file info
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Failed to retrieve file: {e}")
        return

    # ✅ Download the photo
    try:
        response = requests.get(file_url)
        response.raise_for_status()
        image_path = f"temp/{message.chat.id}.jpg"
        with open(image_path, 'wb') as f:
            f.write(response.content)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error downloading the image: {e}")
        return

    # ✅ Check for QR Code in the image
    try:
        img = cv2.imread(image_path)
        qr_codes = decode(img)
        if not qr_codes:
            bot.send_message(message.chat.id, "❌ No QR Code detected on the image!")
            return
        qr_data = qr_codes[0].data.decode("utf-8")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error decoding QR Code: {e}")
        return

    # ✅ Verify QR Code in the system
    if "story_id=" in qr_data:
        story_id = qr_data.split("story_id=")[-1]
        try:
            response = requests.get(f"https://peperefbot.onrender.com/api/confirm_click?story_id={story_id}")
            data = response.json()

            if data.get("success"):
                bot.send_message(message.chat.id, f"✅ Story by @{username} is **verified**!")
            else:
                bot.send_message(message.chat.id, "⚠ This QR Code is **not registered!**")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error verifying QR Code: {e}")
    else:
        bot.send_message(message.chat.id, "⚠ QR Code format is incorrect!")

# ✅ Start the bot
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.polling(none_stop=True)
