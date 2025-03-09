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
    """ Генерирует изображение сторис с QR-кодом и сохраняет его URL """

    # Создаем уникальный story_id
    story_id = str(uuid.uuid4())

    # Генерируем URL сторис
    media_url = f"https://peperefbot.onrender.com/static/stories/{story_id}.png"

    # Сохраняем в базе
    STORY_DB[story_id] = {"username": username, "timestamp": datetime.now(), "ref_id": ref_id, "media_url": media_url}

    # ✅ Создаем изображение с QR-кодом
    background_path = "static/templates/story_background.png"
    if not os.path.exists(background_path):
        return JSONResponse(content={"success": False, "message": "Фон не найден!"}, status_code=500)

    background = Image.open(background_path).convert("RGBA")
    draw = ImageDraw.Draw(background)

    # Генерируем QR-код
    qr_url = f"https://peperefbot.onrender.com/api/confirm_click?story_id={story_id}"
    qr = qrcode.make(qr_url).resize((150, 150))

    # Добавляем текст
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font = ImageFont.truetype(font_path, 50)
    except IOError:
        font = ImageFont.load_default()

    draw.text((50, 50), f"Ref ID: {ref_id}", fill=(255, 255, 255), font=font)

    # Размещаем QR-код
    qr_position = (background.width - 180, background.height - 180)
    background.paste(qr, qr_position, qr.convert("RGBA"))

    # Сохраняем изображение
    img_filename = f"static/stories/{story_id}.png"
    background.save(img_filename)

    return {
        "success": True,
        "image_url": media_url,  # Сохраненный URL сторис
        "story_id": story_id  # Отдаем story_id клиенту
    }




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



@app.get("/api/confirm_click")
def confirm_click(story_id: str = Query(...)):
    """ Подтверждает сканирование QR-кода именно этой сторис """

    if story_id in STORY_DB:
        STORY_DB[story_id]["verified"] = True
        return {"success": True, "message": "QR-код подтвержден! ✅"}
    
    return JSONResponse(content={"success": False, "message": "Сторис не найдена ❌"}, status_code=404)


import requests
from bs4 import BeautifulSoup

@app.get("/api/check_story_auto")
def check_story_auto(username: str = Query(...)):
    """ Автоматически проверяет, опубликована ли сторис по `mediaUrl` """

    for story_id, data in STORY_DB.items():
        if data["username"] == username:
            media_url = data.get("media_url")
            if not media_url:
                return {"success": False, "message": "URL сторис не найден"}

            # Запрос к странице пользователя в Telegram
            user_stories_url = f"https://t.me/s/{username}"
            response = requests.get(user_stories_url, headers={"User-Agent": "Mozilla/5.0"})

            if media_url in response.text:
                return {"success": True, "message": "Сторис найдена ✅"}
            else:
                return {"success": False, "message": "Сторис не найдена ❌"}
    
    return {"success": False, "message": "Сторис не найдена"}


from fastapi.staticfiles import StaticFiles

# ✅ Mount the static directory so images are accessible
app.mount("/static", StaticFiles(directory="static", check_dir=True), name="static")
