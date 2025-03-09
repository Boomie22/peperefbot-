from fastapi import APIRouter
import qrcode
from PIL import Image, ImageDraw
import uuid
import os

router = APIRouter() 
SAVE_DIR = "static/stories"
os.makedirs(SAVE_DIR, exist_ok=True)

@router.post("/api/stories/generate")
def generate_story():
    """Генерирует изображение с QR-кодом, скрытым в углу"""
    ref_id = str(uuid.uuid4())

    qr = qrcode.QRCode(box_size=2, border=0)
    qr.add_data(ref_id)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="gray", back_color="white")
    qr_img = qr_img.resize((50, 50))

    base_image = Image.new("RGB", (800, 600), "white")
    draw = ImageDraw.Draw(base_image)
    draw.text((10, 10), f"ID: {ref_id[:6]}", fill="lightgray")

    base_image.paste(qr_img, (740, 550))
    image_path = f"{SAVE_DIR}/{ref_id}.png"
    base_image.save(image_path)

    return {"success": True, "image_url": f"/{image_path}", "ref_id": ref_id}
