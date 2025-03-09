from fastapi import FastAPI, Query, Body
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated database
REF_DB = {}  # Stores referral IDs
STORY_DB = {}  # Stores story info

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
    """ Generates an HTML page with QR code and stores ref_id with timestamp """

    # ✅ Save ref_id before generating the story
    REF_DB[ref_id] = {"username": username, "verified": False}
    STORY_DB[ref_id] = {"username": username, "timestamp": datetime.now()}  # 🕒 Save timestamp

    backend_url = "https://peperefbot.onrender.com"

    html_template = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram Story</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                background-color: white;
                margin: 0;
                padding: 0;
            }}
            .story-container {{
                position: relative;
                width: 1080px;
                height: 1920px;
                background: url('https://source.unsplash.com/random/1080x1920') no-repeat center center;
                background-size: cover;
            }}
            .qr-code {{
                position: absolute;
                bottom: 20px;
                right: 20px;
                width: 80px;
                height: 80px;
                opacity: 0.2;
            }}
        </style>
    </head>
    <body>
        <div class="story-container">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=80x80&data={backend_url}/api/confirm_click?ref_id={ref_id}" class="qr-code" alt="QR Code">
        </div>
    </body>
    </html>
    """
    return html_template


@app.get("/api/check_story")
def check_story(username: str = Query(...)):
    """ Checks if the story exists AND has been up for 8 hours """
    print(f"🔍 Checking story for: {username}")  # Logging

    for ref_id, data in STORY_DB.items():
        if data["username"] == username:
            elapsed_time = datetime.now() - data["timestamp"]
            
            if elapsed_time >= timedelta(hours=8):
                print(f"✅ Story confirmed for {username}")  # Logging
                return {"success": True, "message": "Story is verified ✅"}
            else:
                remaining_time = timedelta(hours=8) - elapsed_time
                print(f"⏳ Story is too new for {username}, {remaining_time} left")  # Logging
                return {"success": False, "message": f"Story needs to stay for {remaining_time} more"}
    
    print(f"❌ Story not found for {username}")  # Logging
    return {"success": False, "message": "Story not found ❌"}
