import requests
import time
import json
import re
import os
import threading
from flask import Flask

# =========================
# 🌐 FLASK SERVER (keep alive)
# =========================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Running ✅"

def run_server():
    app.run(host="0.0.0.0", port=10000)

# =========================
# 🔐 API SETTINGS
# =========================
API_URL = "http://51.77.216.195/crapi/lamix/viewstats"
TOKEN = "YOUR_API_TOKEN"

# =========================
# 🤖 TELEGRAM SETTINGS
# =========================
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = -1001234567890

# =========================
# 📁 STORAGE
# =========================
FILE = "sent.txt"

if os.path.exists(FILE):
    with open(FILE, "r") as f:
        sent_messages = set(f.read().splitlines())
else:
    sent_messages = set()

def save_message(uid):
    with open(FILE, "a") as f:
        f.write(uid + "\n")

# =========================
# 📱 MASK NUMBER
# =========================
def mask_number(num):
    if num and len(num) >= 8:
        return num[:4] + "XXXX" + num[-4:]
    return num

# =========================
# 📤 SEND
# =========================
def send(msg, number):
    try:
        otp = re.findall(r"\d{4,6}", msg)
        otp_text = otp[0] if otp else "N/A"

        masked = mask_number(number)

        text = f"""
📩 <b>NEW OTP</b>

📱 Number: <b>{masked}</b>

🔐 OTP:
<code>{otp_text}</code>
"""

        buttons = {
            "inline_keyboard": [
                [{"text": "📋 Copy OTP", "callback_data": f"copy_{otp_text}"}],
                [
                    {"text": "📢 CHANNEL", "url": "https://t.me/yourchannel"},
                    {"text": "🌐 PANEL", "url": "https://yourpanel.com"}
                ]
            ]
        }

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(buttons)
            },
            timeout=10
        )

    except Exception as e:
        print("Send Error:", e)

# =========================
# 🔘 CALLBACK
# =========================
last_update_id = 0

def handle_callbacks():
    global last_update_id

    try:
        res = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
            params={"offset": last_update_id + 1},
            timeout=10
        ).json()

        for update in res.get("result", []):
            last_update_id = update["update_id"]

            if "callback_query" in update:
                data = update["callback_query"]["data"]
                chat_id = update["callback_query"]["message"]["chat"]["id"]

                if data.startswith("copy_"):
                    otp = data.replace("copy_", "")

                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        data={"chat_id": chat_id, "text": otp},
                        timeout=10
                    )

    except Exception as e:
        print("Callback Error:", e)

# =========================
# 🔄 BOT LOOP
# =========================
def bot_loop():
    while True:
        try:
            res = requests.get(API_URL, params={"token": TOKEN, "records": 10}, timeout=10)
            result = res.json()

            if result.get("status") == "success":
                for sms in result["data"]:
                    msg = sms.get("msg")
                    number = sms.get("num")
                    dt = sms.get("dt")

                    unique_id = f"{dt}_{msg}_{number}"

                    if unique_id not in sent_messages:
                        send(msg, number)
                        sent_messages.add(unique_id)
                        save_message(unique_id)

            handle_callbacks()

        except Exception as e:
            print("Main Error:", e)

        time.sleep(5)

# =========================
# 🚀 START BOTH
# =========================
if __name__ == "__main__":
    threading.Thread(target=bot_loop).start()
    run_server()
