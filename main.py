from fastapi import FastAPI, Query, Body
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta

app = FastAPI()

# Имитация базы данных (заменим на Postgres позже)
REF_DB = {}  # Храним реферальные ID
STORY_DB = {}  # Храним сторис с их ID и временем публикации

class RefData(BaseModel):
    ref_id: str
    username: str

@app.post("/api/save_ref")
def save_ref(data: RefData):
    """ Сохраняет реферальный ID """
    REF_DB[data.ref_id] = {"username": data.username, "verified": False}
    return {"success": True, "message": f"Реф ID {data.ref_id} сохранен для @{data.username}"}

@app.get("/api/stories/generate")
def generate_story(ref_id: str = Query(...), username: str = Query(...)):
    """ Генерирует HTML-страницу с QR-кодом и сохраняет ref_id в базе """
    
    # ✅ Сохраняем реф ID перед генерацией, чтобы он не терялся
    REF_DB[ref_id] = {"username": username, "verified": False}
    STORY_DB[ref_id] = {"username": username, "timestamp": datetime.now()}

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
    """ Проверяет, была ли сторис опубликована """
    print(f"🔍 Запрос на проверку сторис для: {username}")  # Логируем
    for ref_id, data in STORY_DB.items():
        if data["username"] == username:
            print(f"✅ Найдена сторис для {username}")  # Логируем
            return {"success": True, "message": "Сторис найдена ✅"}
    print(f"❌ Сторис не найдена для {username}")  # Логируем
    return {"success": False, "message": "Сторис не найдена ❌"}
