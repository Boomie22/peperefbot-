from fastapi import FastAPI, Query, Body
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os


app = FastAPI()
os.makedirs("static/stories", exist_ok=True)

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

    # ✅ Store the story reference in the database
    STORY_DB[ref_id] = {"username": username, "timestamp": datetime.now()}

    # Image settings
    img_width, img_height = 1080, 1920
    qr_size = 150
    text_color = (255, 255, 255)  # White text

    # Create a blank image
    background = Image.new("RGB", (img_width, img_height), (30, 30, 30))

    # Generate QR code
    qr_url = f"https://peperefbot.onrender.com/api/confirm_click?ref_id={ref_id}"
    qr = qrcode.make(qr_url)
    qr = qr.resize((qr_size, qr_size))

    # Draw text on image
    draw = ImageDraw.Draw(background)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Change this if needed
    font = ImageFont.truetype(font_path, 40)

    draw.text((50, 50), f"Ref ID: {ref_id}", fill=text_color, font=font)

    # Paste QR code onto image
    background.paste(qr, (img_width - qr_size - 30, img_height - qr_size - 30))

    # Save image
    img_filename = f"static/stories/{uuid.uuid4()}.png"
    background.save(img_filename)

    print(f"✅ Image saved at: {img_filename}")  # log

    # ✅ Return a JSON response with the image URL
    return {"success": True, "image_url": f"https://peperefbot.onrender.com/{img_filename}"}


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

from fastapi.staticfiles import StaticFiles

# ✅ Mount the static directory so images are accessible
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
