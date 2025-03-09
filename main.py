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
def generate_story(ref_id: str = Query(...), username: str = Query(...)):
    """ Generates a story image with a QR code and saves it as a PNG """

    print(f"✅ DEBUG: Generating story for ref_id: {ref_id} (username: {username})")

    # ✅ Generate unique story ID
    story_id = str(uuid.uuid4())  # Unique for each story
    img_filename = f"static/stories/{story_id}.png"

    # ✅ Ensure ref_id is stored in REF_DB
    if ref_id not in REF_DB:
        REF_DB[ref_id] = {"username": username, "verified": False}
        print(f"✅ DEBUG: Stored ref_id {ref_id} in REF_DB!")  

    # ✅ Store story details in STORY_DB
    STORY_DB[story_id] = {"username": username, "timestamp": datetime.now(), "media_url": f"https://peperefbot.onrender.com/{img_filename}"}
    
    # ✅ Ensure directory exists
    os.makedirs("static/stories", exist_ok=True)

    # **1️⃣ Load Background Image**
    background_path = "static/templates/story_background.png"
    if not os.path.exists(background_path):
        print("❌ DEBUG: Background image NOT found!")
        return JSONResponse(content={"success": False, "message": "Background image not found!"}, status_code=500)

    background = Image.open(background_path).convert("RGBA")
    img_width, img_height = background.size  

    # **2️⃣ Generate QR Code (now includes story_id)**
    qr_size = 150
    qr_url = f"https://peperefbot.onrender.com/api/confirm_click?ref_id={ref_id}&story_id={story_id}"  # ✅ FIXED!
    qr = qrcode.make(qr_url)
    qr = qr.resize((qr_size, qr_size))

    # **3️⃣ Add Text**
    draw = ImageDraw.Draw(background)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  

    try:
        font = ImageFont.truetype(font_path, 50)
    except IOError:
        print("❌ DEBUG: Font file not found! Using default font.")
        font = ImageFont.load_default()

    text_position = (50, 50)  
    text_color = (255, 255, 255)
    shadow_color = (0, 0, 0, 128)  

    # **Draw shadow for readability**
    shadow_offset = 4
    draw.text((text_position[0] + shadow_offset, text_position[1] + shadow_offset), f"Ref ID: {ref_id}", fill=shadow_color, font=font)
    draw.text(text_position, f"Ref ID: {ref_id}", fill=text_color, font=font)

    # **4️⃣ Paste QR Code**
    qr_position = (img_width - qr_size - 30, img_height - qr_size - 30)
    print(f"✅ DEBUG: Pasting QR code at {qr_position}")
    background.paste(qr, qr_position, qr.convert("RGBA"))

    # **5️⃣ Save Image**
    try:
        background = background.convert("RGB")  
        background.save(img_filename)
        print(f"✅ DEBUG: Image successfully saved at {img_filename}")  

        return {"success": True, "image_url": f"https://peperefbot.onrender.com/{img_filename}"}
    except Exception as e:
        print(f"❌ DEBUG: Error saving image: {e}")
        return JSONResponse(content={"success": False, "message": "Error saving image"}, status_code=500)



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
    """ Returns the latest generated story URL for a user """
    for story_id, data in reversed(STORY_DB.items()):  # Get latest story
        if data["username"] == username:
            return {"success": True, "image_url": data["media_url"]}

    return {"success": False, "message": "No story found for this user."}


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

