from fastapi import FastAPI, Query, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta
import qrcode
from PIL import Image, ImageDraw
import os
import json
import requests
import cv2
from skimage.metrics import structural_similarity as ssim
from io import BytesIO

app = FastAPI()

# ✅ Ensure necessary directories exist
os.makedirs("static", exist_ok=True)
os.makedirs("static/stories", exist_ok=True)

# Simulated database
REF_DB = {}
STORY_DB = {}

# ✅ Load stored referral database
REF_DB_FILE = "static/ref_db.json"
REFERENCE_IMAGE_PATH = "center_image.png"
def download_image(url):
    """Downloads an image from a URL and returns a PIL image object"""
    try:
        print(f"🔍 DEBUG: Downloading image from {url}")
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"❌ ERROR: HTTP {response.status_code} - {response.text}")
            return None

        return Image.open(BytesIO(response.content))

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to download image - {e}")
        return None

def compare_images(img1, img2, threshold=0.6):
    """Compares two images and checks if at least 60% of pixels match"""
    
    # Convert images to same mode & size
    img1 = img1.convert("RGB").resize((500, 500))
    img2 = img2.convert("RGB").resize((500, 500))
    
    # Convert to numpy arrays for pixel-wise comparison
    img1_array = np.array(img1)
    img2_array = np.array(img2)
    
    # Compute difference
    diff = np.abs(img1_array - img2_array)
    
    # Count matching pixels
    total_pixels = img1_array.size / 3  # Since RGB has 3 channels
    matching_pixels = np.sum(diff < 30) / 3  # Pixels within a small color difference

    similarity = matching_pixels / total_pixels
    print(f"🔍 DEBUG: Image similarity = {similarity:.2%}")

    return similarity >= threshold


if not os.path.exists(REFERENCE_IMAGE_PATH):
    raise FileNotFoundError(f"Reference image {REFERENCE_IMAGE_PATH} not found!")

def load_reference_image():
    """ Load reference image as a grayscale OpenCV array """
    reference_img = cv2.imread(REFERENCE_IMAGE_PATH, cv2.IMREAD_GRAYSCALE)
    if reference_img is None:
        raise ValueError("Failed to load reference image!")
    return reference_img

REFERENCE_IMAGE = load_reference_image()

def calculate_similarity(img1, img2):
    """ Calculates structural similarity (SSIM) between two images """
    img1_resized = cv2.resize(img1, (img2.shape[1], img2.shape[0]))  # Resize to match dimensions
    similarity_index = ssim(img1_resized, img2)
    return similarity_index

@app.get("/api/verify_story")
def verify_story(username: str, story_url: str):
    """ Verifies if the posted story contains the expected image """

    print(f"🔍 DEBUG: Verifying story for @{username}")
    
    # ✅ Download the posted story image
    story_img = download_image(story_url)
    if story_img is None:
        return {"success": False, "message": "Failed to download story image"}
    
    # ✅ Load the reference center image (original template)
    expected_img_path = "center_image.png"  # ✅ Make sure this exists in the root directory
    if not os.path.exists(expected_img_path):
        return {"success": False, "message": "Reference image not found"}

    expected_img = Image.open(expected_img_path)

    # ✅ Compare images (at least 60% match)
    if compare_images(story_img, expected_img, threshold=0.6):
        return {"success": True, "message": "Story verified successfully!"}
    else:
        return {"success": False, "message": "Story does not match expected content!"}

@app.get("/api/verify_story")
def api_verify_story(username: str = Query(...), story_url: str = Query(...)):
    """ API to verify the story """
    return verify_story(username, story_url)
def save_ref_db():
    """ Saves REF_DB to a file """
    with open(REF_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(REF_DB, f, ensure_ascii=False, indent=4)

def load_ref_db():
    """ Loads REF_DB from file if exists """
    global REF_DB
    if os.path.exists(REF_DB_FILE):
        with open(REF_DB_FILE, "r", encoding="utf-8") as f:
            REF_DB = json.load(f)

load_ref_db()  # Load on startup

@app.get("/api/stories/generate")
def generate_story(username: str, ref_id: str):
    """ Generates a story with a **CENTERED QR CODE** """

    # ✅ Ensure directories exist
    os.makedirs("static/stories", exist_ok=True)

    # ✅ Generate Unique Story ID
    story_id = str(uuid.uuid4())

    # ✅ Story Image Path
    img_filename = f"static/stories/{story_id}.png"

    # ✅ Generate QR Code URL
    qr_url = f"https://peperefbot.onrender.com/api/confirm_click?story_id={story_id}"
    qr = qrcode.make(qr_url).resize((600, 600))  # Bigger QR for easy detection

    # ✅ Create Background (White Image)
    img_width, img_height = 1080, 1920
    background = Image.new("RGB", (img_width, img_height), "white")

    # ✅ Chessboard QR Pattern
    square_size = 50  # Adjust pattern size
    draw = ImageDraw.Draw(background)

    for i in range(0, img_width, square_size):
        for j in range(0, img_height, square_size):
            if (i // square_size + j // square_size) % 2 == 0:
                draw.rectangle([i, j, i + square_size, j + square_size], fill=(220, 220, 220))

    # ✅ Overlay QR Code **CENTERED**
    center_x = (img_width - qr.size[0]) // 2
    center_y = (img_height - qr.size[1]) // 2
    background.paste(qr, (center_x, center_y))

    # ✅ Save Story
    background.save(img_filename)

    # ✅ Store Story in Database
    STORY_DB[story_id] = {
        "username": username,
        "story_id": story_id,
        "image_url": f"https://peperefbot.onrender.com/{img_filename}",
        "timestamp": datetime.now(),
        "verified": False,
        "ref_id": ref_id
    }

    return {
        "success": True,
        "image_url": f"https://peperefbot.onrender.com/{img_filename}"
    }

@app.get("/api/get_latest_story")
def get_latest_story(username: str = Query(...)):
    """ Fetches the latest generated story for a user """
    for story_id, data in STORY_DB.items():
        if data["username"] == username:
            media_url = data.get("image_url")

            # 🔹 Fix: Handle missing media_url properly
            if not media_url:
                return {"success": False, "message": "No media URL found for this user."}

            return {
                "success": True,
                "story_id": story_id,
                "image_url": media_url
            }

    return {"success": False, "message": "No generated story found!"}

@app.get("/api/confirm_click")
def confirm_click(story_id: str = Query(...)):
    """ Confirms the QR code scan and marks the story as verified """

    if story_id in STORY_DB:
        STORY_DB[story_id]["verified"] = True
        return {"success": True, "message": "QR scan confirmed! ✅"}

    return JSONResponse(content={"success": False, "message": "Story ID not found ❌"}, status_code=404)

@app.get("/")
def serve_webapp():
    """ Serves the Telegram WebApp index.html """
    return FileResponse("index.html")

# ✅ Mount the static directory so images are accessible
app.mount("/static", StaticFiles(directory="static", check_dir=True), name="static")
