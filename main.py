from fastapi import FastAPI, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
import json
import shutil

app = FastAPI()

# ✅ Ensure static folders exist
os.makedirs("static", exist_ok=True)
os.makedirs("static/stories", exist_ok=True)
os.makedirs("static/templates", exist_ok=True)  # ✅ Ensure templates folder exists

# Simulated database
REF_DB = {}
STORY_DB = {}

# 🔹 Load data on startup


class RefData(BaseModel):
    ref_id: str
    username: str

REF_DB_FILE = "static/ref_db.json"  # ✅ Store directly in /static/

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

    # ✅ Ensure `ref_id` is stored in `REF_DB`
    if ref_id not in REF_DB:
        REF_DB[ref_id] = {"username": username, "verified": False}
        print(f"✅ DEBUG: Stored ref_id {ref_id} in REF_DB!")  # Log stored ref_id

    # ✅ Store in STORY_DB
    STORY_DB[ref_id] = {"username": username, "timestamp": datetime.now()}
    
    # ✅ Generate and save the story image
    img_id = str(uuid.uuid4())
    img_filename = f"static/stories/{img_id}.png"

    # ✅ Ensure the directory exists
    os.makedirs("static/stories", exist_ok=True)

    # **1️⃣ Load Background Image**
    background_path = "static/templates/story_background.png"
    if not os.path.exists(background_path):
        print("❌ DEBUG: Background image NOT found!")
        return JSONResponse(content={"success": False, "message": "Background image not found!"}, status_code=500)

    background = Image.open(background_path).convert("RGBA")
    img_width, img_height = background.size  

    # **2️⃣ Generate QR Code**
    qr_size = 150
    qr_url = f"https://peperefbot.onrender.com/api/confirm_click?ref_id={ref_id}"
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

    # **Draw shadow**
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
    """ Checks if the story exists AND has been up for 8 hours AND QR is verified """
    print(f"🔍 Checking story for: {username}")

    for ref_id, data in STORY_DB.items():
        if data["username"] == username:
            elapsed_time = datetime.now() - data["timestamp"]
            
            if ref_id in REF_DB and REF_DB[ref_id].get("verified", False):
                if elapsed_time >= timedelta(hours=8):
                    print(f"✅ Story confirmed for {username}")
                    return {"success": True, "message": "Story is verified ✅"}
                else:
                    remaining_time = timedelta(hours=8) - elapsed_time
                    print(f"⏳ Story is too new for {username}, {remaining_time} left")
                    return {"success": False, "message": f"Story needs to stay for {remaining_time} more"}
            else:
                print(f"⚠ QR code scan is missing for ref_id {ref_id}!")
                return {"success": False, "message": "QR code scan not confirmed! ❌"}

    print(f"❌ Story not found for {username}")
    return {"success": False, "message": "Story not found ❌"}


@app.get("/api/confirm_click")
def confirm_click(ref_id: str = Query(...)):
    """ Confirms the QR code scan and marks the story as verified """

    print(f"✅ DEBUG: Checking ref_id: {ref_id}")  
    print(f"✅ DEBUG: Current REF_DB Keys: {list(REF_DB.keys())}")  

    # ✅ Ensure ref_id exists
    if ref_id in REF_DB:
        REF_DB[ref_id]["verified"] = True  # ✅ Mark it as verified
        print(f"✅ DEBUG: Ref ID {ref_id} verified!")  
        return {"success": True, "message": "QR scan confirmed! ✅"}

    print(f"❌ DEBUG: Ref ID {ref_id} NOT found in REF_DB!")  
    return JSONResponse(content={"success": False, "message": "Ref ID not found ❌"}, status_code=404)



from fastapi.staticfiles import StaticFiles

# ✅ Mount the static directory so images are accessible
app.mount("/static", StaticFiles(directory="static", check_dir=True), name="static")
