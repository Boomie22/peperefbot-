from fastapi import FastAPI, Query, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
import json
from bs4 import BeautifulSoup
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# ✅ Ensure static folders exist
os.makedirs("static", exist_ok=True)
os.makedirs("static/stories", exist_ok=True)
os.makedirs("static/templates", exist_ok=True)  # ✅ Ensure templates folder exists

# Simulated database
REF_DB = {}
STORY_DB = {}

# 🔹 Load data on startup

class StoryData(BaseModel):
    username: str
    story_id: str
    media_url: str


class RefData(BaseModel):
    ref_id: str
    username: str

REF_DB_FILE = "static/ref_db.json"  # ✅ Store directly in /static/

@app.post("/api/save_story")
def save_story(data: StoryData):
    """ Saves the story with its media URL """
    STORY_DB[data.username] = {"story_id": data.story_id, "media_url": data.media_url}
    
    # Save to a file (optional)
    with open("story_db.json", "w") as f:
        json.dump(STORY_DB, f)
    
    return {"success": True, "message": "Story saved!"}

def save_ref_db():
    """ Saves REF_DB to a file in the static directory so it's accessible """
    os.makedirs("static", exist_ok=True)  # Ensure static exists
    with open(REF_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(REF_DB, f, ensure_ascii=False, indent=4)
    print(f"✅ DEBUG: Saved REF_DB to {REF_DB_FILE}")


def load_ref_db():
    """ Loads REF_DB from a file in the static directory (if exists) """
    global REF_DB
    if os.path.exists(REF_DB_FILE):
        with open(REF_DB_FILE, "r", encoding="utf-8") as f:
            REF_DB = json.load(f)
        print(f"✅ DEBUG: Loaded REF_DB from {REF_DB_FILE}")
    else:
        REF_DB = {}
        print(f"⚠ DEBUG: {REF_DB_FILE} not found, starting fresh.")

load_ref_db()  # ✅ Load database on startup

@app.post("/api/debug/save_ref_db")
def force_save_ref_db():
    """ Manually saves REF_DB and copies it to static """
    save_ref_db()
    return {"success": True, "message": "Saved ref_db.json to static"}


@app.post("/api/save_ref")
def save_ref(data: RefData):
    """ Saves referral ID persistently """

    if data.ref_id in REF_DB:
        return JSONResponse(
            content={"success": False, "message": f"⚠ Ref ID {data.ref_id} already exists for @{data.username}"},
            media_type="application/json; charset=utf-8"
        )

    REF_DB[data.ref_id] = {"username": data.username, "verified": False}
    save_ref_db()  # 🔹 Save REF_DB to file

    return JSONResponse(
        content={"success": True, "message": f"Ref ID {data.ref_id} saved for @{data.username}"},
        media_type="application/json; charset=utf-8"
    )

@app.get("/api/stories/generate")


def generate_story(username: str, ref_id: str):
    """ Generates a story with a custom QR-coded background """

    # ✅ Ensure directories exist
    os.makedirs("static/stories", exist_ok=True)

    # ✅ Unique Story ID
    story_id = str(uuid.uuid4())

    # ✅ Story Image Path
    img_filename = f"static/stories/{story_id}.png"

    # ✅ Generate QR Code URL
    qr_url = f"https://peperefbot.onrender.com/api/confirm_click?story_id={story_id}"
    qr = qrcode.make(qr_url).resize((250, 250))

    # ✅ Load Base Template or Create White Background
    img_width, img_height = 1080, 1920
    background = Image.new("RGB", (img_width, img_height), "white")

    # ✅ Generate Chessboard QR Pattern (New Detection Method)
    square_size = 40
    draw = ImageDraw.Draw(background)
    
    for i in range(0, img_width, square_size):
        for j in range(0, img_height, square_size):
            if (i // square_size + j // square_size) % 2 == 0:
                draw.rectangle([i, j, i + square_size, j + square_size], fill=(200, 200, 200))

    # ✅ Overlay QR Code in a Fixed Position (Bottom Right)
    qr_position = (img_width - 270, img_height - 270)
    background.paste(qr, qr_position)

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




@app.get("/api/debug/get_story_db")
def get_story_db():
    """ Debugging route to check all saved stories in STORY_DB """
    return {"stories": STORY_DB}



@app.get("/api/debug/get_ref_db")
def get_ref_db():
    """ Returns the REF_DB JSON data """
    if not os.path.exists(REF_DB_FILE):
        return JSONResponse(content={"success": False, "message": "ref_db.json not found"}, status_code=404)
    
    with open(REF_DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return JSONResponse(content=data)

@app.get("/api/get_latest_story")
def get_latest_story(username: str = Query(...)):
    """ Returns the latest generated story for a user """
    for story_id, data in STORY_DB.items():
        if data["username"] == username:
            return {
                "success": True,
                "image_url": data["media_url"]
            }
    return {"success": False, "message": "No generated story found!"}

@app.get("/api/verify_story")
def verify_story(media_url: str = Query(...), user_id: str = Query(...)):
    """ Verifies if the forwarded story matches the stored story """

    print(f"🔍 Checking story for user ID {user_id}")

    for story_id, data in STORY_DB.items():
        if str(data.get("user_id")) == str(user_id):  # Ensure matching user ID
            if media_url == data["media_url"]:  # Compare story URLs
                return {"success": True, "message": "Story confirmed!"}
            else:
                return {"success": False, "message": "Story does not match."}

    return {"success": False, "message": "No story found for this user."}

@app.get("/api/check_story")
def check_story(username: str = Query(...)):
    """ Проверяет, была ли сторис отсканирована и прошло ли 8 часов """
    
    for story_id, data in STORY_DB.items():
        if data["username"] == username:
            elapsed_time = datetime.now() - data["timestamp"]

            if "verified" in data and data["verified"]:
                if elapsed_time >= timedelta(hours=8):
                    return {"success": True, "message": "Сторис подтверждена ✅"}
                else:
                    remaining_time = timedelta(hours=8) - elapsed_time
                    return {"success": False, "message": f"Сторис слишком свежая, ждем {remaining_time}"}
            else:
                return {"success": False, "message": "QR-код не был отсканирован! ❌"}
    
    return {"success": False, "message": "Сторис не найдена ❌"}

@app.get("/api/get_latest_story")
def get_latest_story(username: str = Query(...)):
    """ Fetches the latest story for a user """

    print(f"📌 DEBUG: Fetching latest story for @{username}")

    for story_id, data in STORY_DB.items():
        if data["username"] == username:
            media_url = data.get("media_url")

            # 🔹 Fix: Handle missing media_url properly
            if not media_url:
                print(f"❌ ERROR: No media_url found for @{username}")
                return {"success": False, "message": "No media URL found for this user."}

            return {
                "success": True,
                "story_id": story_id,
                "image_url": media_url
            }

    print(f"❌ ERROR: No story found for @{username}")
    return {"success": False, "message": "No generated story found!"}



@app.get("/api/confirm_click")
def confirm_click(story_id: str = Query(...)):
    """ Confirms the QR code scan and marks the story as verified """

    print(f"✅ DEBUG: Checking story_id: {story_id}")
    print(f"✅ DEBUG: Current STORY_DB Keys: {list(STORY_DB.keys())}")

    if story_id in STORY_DB:
        STORY_DB[story_id]["verified"] = True
        print(f"✅ DEBUG: Story ID {story_id} verified!")
        return {"success": True, "message": "QR scan confirmed! ✅"}

    print(f"❌ DEBUG: Story ID {story_id} NOT found in STORY_DB!")
    return JSONResponse(content={"success": False, "message": "Story ID not found ❌"}, status_code=404)


@app.get("/api/check_story_auto")
def check_story_auto(username: str = Query(...)):
    """ Automatically verifies if the posted story exists """

    if username not in STORY_DB:
        return {"success": False, "message": "No story record found!"}

    media_url = STORY_DB[username]["media_url"]
    if not media_url:
        return {"success": False, "message": "No media URL saved!"}

    # Simulate checking Telegram public profile (not perfect)
    user_stories_url = f"https://t.me/s/{username}"
    response = requests.get(user_stories_url)

    if media_url in response.text:
        return {"success": True, "message": "Story is verified! ✅"}
    
    return {"success": False, "message": "Story not found ❌"}

@app.get("/")
def serve_webapp():
    """ Serves the Telegram WebApp index.html """
    return FileResponse("index.html")

# ✅ Mount the static directory so images are accessible
app.mount("/static", StaticFiles(directory="static", check_dir=True), name="static")

