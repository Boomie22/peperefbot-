from fastapi import FastAPI, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

app = FastAPI()

# ✅ Ensure static folders exist
os.makedirs("static", exist_ok=True)
os.makedirs("static/stories", exist_ok=True)
os.makedirs("static/templates", exist_ok=True)  # ✅ Ensure templates folder exists

# Simulated database
REF_DB = {}
STORY_DB = {}

class RefData(BaseModel):
    ref_id: str
    username: str

@app.post("/api/save_ref")
def save_ref(data: RefData):
    """ Saves referral ID with UTF-8 encoding """
    if data.ref_id in REF_DB:
        return JSONResponse(
            content={"success": False, "message": f"⚠ Ref ID {data.ref_id} already exists for @{data.username}"},
            media_type="application/json; charset=utf-8"
        )

    REF_DB[data.ref_id] = {"username": data.username, "verified": False}
    return JSONResponse(
        content={"success": True, "message": f"Ref ID {data.ref_id} saved for @{data.username}"},
        media_type="application/json; charset=utf-8"
    )

@app.get("/api/stories/generate")
def generate_story(ref_id: str = Query(...), username: str = Query(...)):
    """ Generates a story image with a QR code and saves it as a PNG """

    STORY_DB[ref_id] = {"username": username, "timestamp": datetime.now()}

    # Paths
    img_id = str(uuid.uuid4())
    img_filename = f"static/stories/{img_id}.png"

    # ✅ Debugging: Print file path
    print(f"Saving image to: {img_filename}")

    # ✅ Ensure the directory exists
    os.makedirs("static/stories", exist_ok=True)

    # **1️⃣ Load Background Image**
    background_path = "static/templates/story_background.png"
    if not os.path.exists(background_path):
        print("❌ Background image NOT found!")
        return JSONResponse(content={"success": False, "message": "Background image not found!"}, status_code=500)

    background = Image.open(background_path).convert("RGBA")  # Convert to RGBA for transparency
    img_width, img_height = background.size  # Use actual background size

    # **2️⃣ Generate QR Code**
    qr_size = 150
    qr_url = f"https://peperefbot.onrender.com/api/confirm_click?ref_id={ref_id}"
    qr = qrcode.make(qr_url)
    qr = qr.resize((qr_size, qr_size))

    # **3️⃣ Add Text with Shadow Effect**
    draw = ImageDraw.Draw(background)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Change if needed

    try:
        font = ImageFont.truetype(font_path, 50)  # Slightly larger font
    except IOError:
        print("❌ Font file not found! Using default font.")
        font = ImageFont.load_default()

    text_position = (50, 50)  # Move text down slightly for visibility
    text_color = (255, 255, 255)  # White text
    shadow_color = (0, 0, 0, 128)  # Semi-transparent black shadow

    # **Draw shadow effect (slightly offset)**
    shadow_offset = 4
    draw.text((text_position[0] + shadow_offset, text_position[1] + shadow_offset), f"Ref ID: {ref_id}", fill=shadow_color, font=font)

    # **Draw main white text on top**
    draw.text(text_position, f"Ref ID: {ref_id}", fill=text_color, font=font)

    # **4️⃣ Paste QR Code**
    qr_position = (img_width - qr_size - 30, img_height - qr_size - 30)
    print(f"✅ Pasting QR code at {qr_position}")
    background.paste(qr, qr_position, qr.convert("RGBA"))

    # **5️⃣ Save Image**
    try:
        background = background.convert("RGB")  # Convert back to RGB before saving
        background.save(img_filename)
        print(f"✅ Image successfully saved at {img_filename}")  # Log success
        return {"success": True, "image_url": f"http://127.0.0.1:8000/{img_filename}"}
    except Exception as e:
        print(f"❌ Error saving image: {e}")
        return JSONResponse(content={"success": False, "message": "Error saving image"}, status_code=500)



@app.get("/api/check_story")
def check_story(username: str = Query(...)):
    """ Checks if the story exists AND has been up for 8 hours """
    print(f"🔍 Checking story for: {username}")

    for ref_id, data in STORY_DB.items():
        if data["username"] == username:
            elapsed_time = datetime.now() - data["timestamp"]
            
            if elapsed_time >= timedelta(hours=8):
                print(f"✅ Story confirmed for {username}")
                return {"success": True, "message": "Story is verified ✅"}
            else:
                remaining_time = timedelta(hours=8) - elapsed_time
                print(f"⏳ Story is too new for {username}, {remaining_time} left")
                return {"success": False, "message": f"Story needs to stay for {remaining_time} more"}
    
    print(f"❌ Story not found for {username}")
    return {"success": False, "message": "Story not found ❌"}

@app.get("/api/confirm_click")
def confirm_click(ref_id: str = Query(...)):
    """ Confirms the QR code scan and marks the story as verified """
    if ref_id in REF_DB:
        REF_DB[ref_id]["verified"] = True
        return {"success": True, "message": "QR scan confirmed! ✅"}
    
    return JSONResponse(content={"success": False, "message": "Ref ID not found ❌"}, status_code=404)


from fastapi.staticfiles import StaticFiles

# ✅ Mount the static directory so images are accessible
app.mount("/static", StaticFiles(directory="static", check_dir=True), name="static")
