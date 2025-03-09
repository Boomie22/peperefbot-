from fastapi import FastAPI, Query, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta
import qrcode
from PIL import Image, ImageDraw
import os
import json
import requests

app = FastAPI()

# ✅ Ensure necessary directories exist
os.makedirs("static", exist_ok=True)
os.makedirs("static/stories", exist_ok=True)

# Simulated database
REF_DB = {}
STORY_DB = {}

# ✅ Load stored referral database
REF_DB_FILE = "static/ref_db.json"

def save_ref_db():
    """ Saves REF_DB to a file """
    with open(REF_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(REF_DB, f, ensure_ascii=False, indent=4)

def load_ref_db():
    """ Loads REF_DB from file if exists """
    global REF_DB
    if os.path.exists(REF_DB_FILE):
        with open(REF_DB_FILE, "r", encoding="utf-8") as f:
            REF_DB = json.load(f)

load_ref_db()  # Load on startup

@app.get("/api/stories/generate")
def generate_story(username: str, ref_id: str):
    """ Generates a story with a **CENTERED QR CODE** """

    # ✅ Ensure directories exist
    os.makedirs("static/stories", exist_ok=True)

    # ✅ Generate Unique Story ID
    story_id = str(uuid.uuid4())

    # ✅ Story Image Path
    img_filename = f"static/stories/{story_id}.png"

    # ✅ Generate QR Code URL
    qr_url = f"https://peperefbot.onrender.com/api/confirm_click?story_id={story_id}"
    qr = qrcode.make(qr_url).resize((600, 600))  # Bigger QR for easy detection

    # ✅ Create Background (White Image)
    img_width, img_height = 1080, 1920
    background = Image.new("RGB", (img_width, img_height), "white")

    # ✅ Chessboard QR Pattern
    square_size = 50  # Adjust pattern size
    draw = ImageDraw.Draw(background)

    for i in range(0, img_width, square_size):
        for j in range(0, img_height, square_size):
            if (i // square_size + j // square_size) % 2 == 0:
                draw.rectangle([i, j, i + square_size, j + square_size], fill=(220, 220, 220))

    # ✅ Overlay QR Code **CENTERED**
    center_x = (img_width - qr.size[0]) // 2
    center_y = (img_height - qr.size[1]) // 2
    background.paste(qr, (center_x, center_y))

    # ✅ Save Story
    background.save(img_filename)

    # ✅ Store Story in Database
    STORY_DB[story_id] = {
        "username": username,
        "story_id": story_id,
        "image_url": f"https://peperefbot.onrender.com/{img_filename}",
        "timestamp": datetime.now(),
        "verified": False,
        "ref_id": ref_id
    }

    return {
        "success": True,
        "image_url": f"https://peperefbot.onrender.com/{img_filename}"
    }

@app.get("/api/get_latest_story")
def get_latest_story(username: str = Query(...)):
    """ Fetches the latest generated story for a user """
    for story_id, data in STORY_DB.items():
        if data["username"] == username:
            media_url = data.get("image_url")

            # 🔹 Fix: Handle missing media_url properly
            if not media_url:
                return {"success": False, "message": "No media URL found for this user."}

            return {
                "success": True,
                "story_id": story_id,
                "image_url": media_url
            }

    return {"success": False, "message": "No generated story found!"}

@app.get("/api/confirm_click")
def confirm_click(story_id: str = Query(...)):
    """ Confirms the QR code scan and marks the story as verified """

    if story_id in STORY_DB:
        STORY_DB[story_id]["verified"] = True
        return {"success": True, "message": "QR scan confirmed! ✅"}

    return JSONResponse(content={"success": False, "message": "Story ID not found ❌"}, status_code=404)

@app.get("/")
def serve_webapp():
    """ Serves the Telegram WebApp index.html """
    return FileResponse("index.html")

# ✅ Mount the static directory so images are accessible
app.mount("/static", StaticFiles(directory="static", check_dir=True), name="static")
