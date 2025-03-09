from fastapi import FastAPI, Query, Body
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta

app = FastAPI()

# База данных (заменим на Postgres позже)
REF_DB = {}  # Для хранения реферальных ID
STORY_DB = {}  # Для хранения данных о сторис

class RefData(BaseModel):
    ref_id: str
    username: str

class StoryData(BaseModel):
    ref_id: str
    username: str

@app.post("/api/story/save")
def save_story(data: StoryData):
    """ Сохраняет данные о сторис, которую запостил пользователь. """
    STORY_DB[data.ref_id] = {
        "username": data.username,
        "verified": False,
        "timestamp": datetime.now()  # Фиксируем время публикации
    }
    return {"success": True, "message": "Сторис сохранена"}

@app.post("/api/save_ref")
def save_ref(data: RefData):
    """ Сохраняет реферальный ID перед генерацией истории """
    REF_DB[data.ref_id] = {
        "username": data.username,
        "verified": False
    }
    return {"success": True, "message": f"Реф ID {data.ref_id} сохранен для @{data.username}"}

@app.get("/api/stories/generate")
def generate_story(ref_id: str = Query(...), username: str = Query(...)):
    """ Генерирует HTML-страницу со скрытым QR-кодом """
    if ref_id not in REF_DB:
        return {"success": False, "message": "Реф ID не найден"}

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

@app.get("/api/story/verify")
def verify_story(username: str = Query(...)):
    """ Проверяет, опубликована ли сторис и прошло ли 8 часов """
    for ref_id, data in STORY_DB.items():
        if data["username"] == username:
            elapsed_time = datetime.now() - data["timestamp"]
            if elapsed_time > timedelta(hours=8):
                return {"success": True, "message": "Сторис подтверждена ✅"}
            return {"success": False, "message": "Сторис опубликована, но не прошло 8 часов ❌"}
    
    return {"success": False, "message": "Сторис не найдена ❌"}
