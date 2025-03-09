from fastapi import APIRouter
import qrcode
import io
import base64
from fastapi.responses import HTMLResponse

router = APIRouter()

backend_url = "https://peperefbot.onrender.com"  


def generate_qr_code(data: str):
    """Создает QR-код и возвращает его в base64."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=2
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

@router.get("/api/stories/generate", response_class=HTMLResponse)
def generate_story(ref_id: str):
    """Генерирует HTML-страницу с QR-кодом для сторис."""
    qr_base64 = generate_qr_code(ref_id)
    
    html_content = f"""
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
                width: 100px;
                height: 100px;
            }}
        </style>
    </head>
    <body>
        <div class="story-container">
            <img src="data:image/png;base64,{qr_base64}" class="qr-code" alt="QR Code">
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
