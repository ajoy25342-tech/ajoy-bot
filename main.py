import requests
import time
import os
import re

# ==================================================
# CONFIG (এখানে টোকেন বসাবেন না, Render.com এ বসাবেন)
# ==================================================

TELEGRAM_TOKEN = "YOUR_TELEGRAM_TOKEN_HERE"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

GEMINI_MODEL = "gemini-2.5-flash"

TELEGRAM_API = (
    "https://api.telegram.org/bot"
    + TELEGRAM_TOKEN
)

GEMINI_API = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + GEMINI_MODEL
    + ":generateContent"
)

TELEGRAM_LIMIT = 4000

# ==================================================
# TELEGRAM API
# ==================================================

def telegram_request(method, data=None, files=None):
    try:
        url = TELEGRAM_API + "/" + method
        response = requests.post(
            url,
            data=data,
            files=files,
            timeout=60
        )
        return response.json()
    except Exception as e:
        print("Telegram Error:", e)
        return {
            "ok": False,
            "error": str(e)
        }

# ==================================================
# SEND MESSAGE
# ==================================================

def send_message(chat_id, text):
    if not text:
        return
    for i in range(0, len(text), TELEGRAM_LIMIT):
        part = text[i:i + TELEGRAM_LIMIT]
        telegram_request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": part
            }
        )
        time.sleep(0.3)

# ==================================================
# TYPING
# ==================================================

def send_typing(chat_id):
    telegram_request(
        "sendChatAction",
        {
            "chat_id": chat_id,
            "action": "typing"
        }
    )

# ==================================================
# SEND FILE
# ==================================================

def send_document(chat_id, filepath, caption=""):
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, "rb") as file:
            telegram_request(
                "sendDocument",
                {
                    "chat_id": chat_id,
                    "caption": caption
                },
                {
                    "document": file
                }
            )
    except Exception as e:
        print("File Send Error:", e)

# ==================================================
# GEMINI
# ==================================================

def ask_gemini(user_request):
    prompt = """
You are Ajoy App Builder.

Create working app and website code from the user's request.

Rules:

1. Understand the user's request.
2. For web apps create a complete index.html.
3. Put HTML, CSS and JavaScript in one file whenever possible.
4. Make the design modern and mobile friendly.
5. Make buttons and interactions work.
6. Do not claim that an app has been deployed.
7. Never expose API keys or private credentials.
8. Keep the explanation short.
9. Return complete HTML inside a ```html code block.
10. Code must be ready to copy and run.
11. Use Bengali when useful.
12. Games must be demo-only and must not use real money.

USER REQUEST:
""" + "\n" + user_request

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 12000
        }
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    try:
        response = requests.post(
            GEMINI_API,
            headers=headers,
            json=payload,
            timeout=120
        )
        print("Gemini Status:", response.status_code)
        data = response.json()

        if response.status_code != 200:
            print(data)
            return (
                "❌ Gemini API Error\n\n"
                + str(data)
            )

        candidates = data.get("candidates", [])

        if not candidates:
            return "❌ Gemini কোনো উত্তর দেয়নি।"

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        result = ""

        for part in parts:
            if "text" in part:
                result += part["text"]

        if not result:
            return "❌ কোনো উত্তর পাওয়া যায়নি।"

        return result

    except Exception as e:
        print("Gemini Error:", e)
        return (
            "❌ Gemini connection error\n\n"
            + str(e)
        )

# ==================================================
# EXTRACT HTML
# ==================================================

def extract_html_code(text):
    match = re.search(
        r"```html\s*(.*?)```",
        text,
        re.IGNORECASE | re.DOTALL
    )
    if match:
        return match.group(1).strip()

    match = re.search(
        r"```\s*(.*?)```",
        text,
        re.DOTALL
    )
    if match:
        code = match.group(1).strip()
        if (
            "<!DOCTYPE html" in code.upper()
            or "<html" in code.lower()
        ):
            return code

    if (
        "<!DOCTYPE html" in text.upper()
        or "<html" in text.lower()
    ):
        return text.strip()

    return None

# ==================================================
# SAVE HTML
# ==================================================

def save_html(code):
    filename = "index.html"
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(code)
        return filename
    except Exception as e:
        print("Save Error:", e)
        return None

# ==================================================
# START COMMAND
# ==================================================

def start_command(chat_id):
    message = """
👋 Ajoy App Builder-এ স্বাগতম!

আমি Gemini ব্যবহার করে তোমার App/Website-এর code তৈরি করতে পারি।

উদাহরণ:

📅 একটা Calendar App বানাও
🧮 একটা Calculator App বানাও
📝 একটা Notes App বানাও
🎨 একটা Profile Website বানাও
🏍️ একটা Bike Game Home Page বানাও
💬 একটা Chat App UI বানাও

তুমি শুধু তোমার idea লিখে পাঠাও।
"""
    send_message(chat_id, message)

# ==================================================
# HELP COMMAND
# ==================================================

def help_command(chat_id):
    message = """
🤖 Ajoy App Builder Help

/start
Bot শুরু করবে।

/help
Help দেখাবে।

তারপর সরাসরি লিখো:

একটা সুন্দর Calculator App বানাও
অথবা:
একটা Calendar App বানাও
অথবা:
একটা Bike Game Home Page বানাও

আমি Gemini দিয়ে code তৈরি করে পাঠাব।
"""
    send_message(chat_id, message)

# ==================================================
# HANDLE MESSAGE
# ==================================================

def handle_message(message):
    if "chat" not in message:
        return

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if not text:
        return

    text = text.strip()
    print()
    print("User:", text)

    if text == "/start":
        start_command(chat_id)
        return

    if text == "/help":
        help_command(chat_id)
        return

    send_typing(chat_id)
    send_message(chat_id, "⏳ তোমার App-এর code তৈরি করছি...")

    result = ask_gemini(text)
    html_code = extract_html_code(result)

    if html_code:
        filepath = save_html(html_code)
        if filepath:
            send_message(chat_id, "✅ App-এর code তৈরি হয়েছে!")
            send_document(
                chat_id,
                filepath,
                "📦 Ajoy App Builder - index.html"
            )
        else:
            send_message(chat_id, result)
    else:
        send_message(chat_id, result)

# ==================================================
# GET UPDATEপS
# ==================================================

def get_updates(offset=None):
    params = {"timeout": 30}
    if offset is not None:
        params["offset"] = offset
    try:
        response = requests.get(
            TELEGRAM_API + "/getUpdates",
            params=params,
            timeout=40
        )
        return response.json()
    except Exception as e:
        print("Update Error:", e)
        return {"ok": False, "result": []}

# ==================================================
# MAIN
# ==================================================

def main():
    print("=" * 50)
    print("🤖 AJOY APP BUILDER BOT")
    print("=" * 50)

    if (
        TELEGRAM_TOKEN == "YOUR_TELEGRAM_TOKEN_HERE"
        or
        GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE"
    ):
        print()
        print("❌ আগে Token এবং API Key বসাও।")
        print()
        return

    print()
    print("✅ Bot Starting...")
    print("📱 Telegram-এ /start পাঠাও।")
    print()

    offset = None
    while True:
        try:
            data = get_updates(offset)
            if not data.get("ok"):
                print("❌ Telegram API problem.")
                time.sleep(5)
                continue

            updates = data.get("result", [])

            for update in updates:
                update_id = update.get("update_id")
                if update_id is not None:
                    offset = update_id + 1
                message = update.get("message")
                if message:
                    handle_message(message)

        except KeyboardInterrupt:
            print()
            print("🛑 Bot stopped.")
            break
        except Exception as e:
            print("Main Error:", e)
            time.sleep(5)

# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    main()
