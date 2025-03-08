from fastapi import FastAPI, Query, Body

app = FastAPI()

# Фейковая база данных
REF_DB = {}  # Здесь храним ID, по которым надо проверять сторис

@app.post("/api/save_ref")
def save_ref(ref_id: str = Body(...), username: str = Body(...)):
    """ Сохраняет реферальный ID для проверки. """
    REF_DB[ref_id] = {"username": username, "verified": False}
    return {"success": True, "message": "Реф ID сохранен"}

@app.get("/api/check_story")
def check_story(username: str = Query(...)):
    """ Проверяет, были ли переходы по реф ID этого юзера. """
    for ref_id, data in REF_DB.items():
        if data["username"] == username and data["verified"]:
            return {"success": True, "message": "Сторис найдена ✅"}
    return {"success": False, "message": "Сторис не найдена ❌"}

@app.post("/api/confirm_click")
def confirm_click(ref_id: str = Body(...)):
    """ Отмечает, что по реф ссылке перешли. """
    if ref_id in REF_DB:
        REF_DB[ref_id]["verified"] = True
        return {"success": True, "message": "Переход зафиксирован"}
    return {"success": False, "message": "Реф ID не найден"}
