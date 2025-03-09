import os
import telebot
import requests
import time

TOKEN = os.getenv("BOT_TOKEN")  # Make sure this is set in Render!
API_URL = "https://peperefbot.onrender.com/api/stories/generate"
bot = telebot.TeleBot(TOKEN)

# Store generated story info
USER_STORIES = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 Welcome! Use /generate_story to create a story and then forward it to me for verification.")

@bot.message_handler(commands=['generate_story'])
def generate_story(message):
    """ Generates a story and sends it to the user. """
    username = message.from_user.username
    if not username:
        bot.send_message(message.chat.id, "❌ You must have a Telegram username to use this feature!")
        return

    bot.send_message(message.chat.id, "⏳ Generating your story... Please wait.")

    # Request to generate a story
    try:
        response = requests.get(f"{API_URL}?username={username}")
        data = response.json()

        if data.get("success"):
            story_url = data["image_url"]
            USER_STORIES[username] = None  # Will store file_id once they upload

            bot.send_photo(message.chat.id, photo=story_url, caption="📸 Here is your story! Post it and then forward it back to me.")
        else:
            bot.send_message(message.chat.id, "❌ Failed to generate story. Please try again later.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error generating story: {str(e)}")
        print(f"Error in /generate_story: {e}")

@bot.message_handler(content_types=['photo'])
def handle_uploaded_story(message):
    """ Handles when a user uploads the generated story. """
    username = message.from_user.username
    if not username:
        bot.send_message(message.chat.id, "❌ You must have a Telegram username!")
        return

    file_id = message.photo[-1].file_id
    USER_STORIES[username] = file_id  # Store the uploaded file_id

    bot.send_message(message.chat.id, "✅ Story uploaded! Now post it and forward it to me.")

@bot.message_handler(func=lambda message: message.forward_from is not None or message.forward_from_chat is not None, content_types=['photo'])
def handle_forwarded_story(message):
    """ Handles forwarded stories and verifies if they match the original """
    username = message.forward_from.username if message.forward_from else message.forward_from_chat.title
    if not username:
        bot.send_message(message.chat.id, "❌ Unable to detect the original poster!")
        return

    if username not in USER_STORIES or not USER_STORIES[username]:
        bot.send_message(message.chat.id, "⚠ No record of this user generating a story. Please use /generate_story first.")
        return

    # Check if the forwarded photo matches the saved file_id
    forwarded_file_id = message.photo[-1].file_id
    if forwarded_file_id == USER_STORIES[username]:
        bot.send_message(message.chat.id, f"✅ Story by @{username} is **verified!** 🎉")
    else:
        bot.send_message(message.chat.id, "❌ This story does not match our records. Please generate and post a new one.")

# Start the bot
print("🚀 Bot is running...")
bot.polling()
