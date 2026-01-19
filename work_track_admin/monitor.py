import os
import time
import base64
import requests
import pyautogui
from io import BytesIO
from datetime import datetime

# ==========================
# CONFIG
# ==========================

SCREENSHOT_INTERVAL_SEC = 60   # 1 minute
DJANGO_BASE_URL = "http://127.0.0.1:8000"
UPLOAD_URL = f"{DJANGO_BASE_URL}/api/upload-screenshot/"
TASK_STATUS_URL = f"{DJANGO_BASE_URL}/tasks/running/"

ACCESS_TOKEN = "PASTE_USER_JWT_ACCESS_TOKEN_HERE"
USERNAME = os.getlogin()

# ==========================
# SCREENSHOT UPLOAD
# ==========================

def send_screenshot_to_server(reason):
    try:
        screenshot = pyautogui.screenshot()
        buffer = BytesIO()
        screenshot.save(buffer, format="PNG")

        encoded_image = base64.b64encode(buffer.getvalue()).decode()

        payload = {
            "image": encoded_image,
            "reason": reason,
            "username": USERNAME,
        }

        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }

        requests.post(UPLOAD_URL, data=payload, headers=headers, timeout=5)
        print("📸 Screenshot uploaded")

    except Exception as e:
        print("❌ Screenshot failed:", e)

# ==========================
# TASK CHECK
# ==========================

def get_running_task():
    try:
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }

        res = requests.get(
            TASK_STATUS_URL,
            headers=headers,
            timeout=3
        )

        return res.json()

    except Exception as e:
        print("❌ Task check failed:", e)
        return {"running": False}

# ==========================
# MAIN LOOP
# ==========================

def screenshot_loop():
    print("🟢 Screenshot agent started")

    while True:
        task = get_running_task()

        if task.get("running"):
            print("✅ Task running → taking screenshot")
            send_screenshot_to_server("interval")
            time.sleep(SCREENSHOT_INTERVAL_SEC)
        else:
            print("⏸ No active task")
            time.sleep(5)

# ==========================
# ENTRY POINT
# ==========================

if __name__ == "__main__":
    screenshot_loop()

