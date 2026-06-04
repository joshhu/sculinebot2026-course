"""
東吳大學資料系 LINEBOT — 文生圖範例

使用者在 LINE 輸入任何文字 → 呼叫 Gemini 圖片生成模型 → 把生成的圖片回傳到 LINE。
不做多輪對話、不解釋圖片、不接收圖片，純粹「一句話 → 一張圖」。
"""

import logging
import os
import tempfile
import uuid
from io import BytesIO

from flask import Flask, abort, request, send_from_directory
from PIL import Image

from google import genai
from google.genai import types

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    ImageMessage,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent


# === Google Gemini 初始化 ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
IMAGE_MODEL = "gemini-3.1-flash-image-preview"

# === 圖片暫存 + 對外 URL ===
# SPACE_HOST 是 Hugging Face Spaces 自動注入的環境變數（例如 "joshhu-sculinebot.hf.space"），
# 本機開發要靠 ngrok 等 tunneling 工具自己模擬一個對外可達的主機名。
static_tmp_path = tempfile.gettempdir()
base_url = os.getenv("SPACE_HOST")

# === Flask 與 LINE SDK 初始化 ===
app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

line_channel_secret = os.getenv("LINE_CHANNEL_SECRET")
line_channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
configuration = Configuration(access_token=line_channel_access_token)
handler = WebhookHandler(line_channel_secret)


def generate_image(prompt: str) -> str | None:
    """呼叫 Gemini 文生圖，存成 PNG 到暫存目錄並回傳檔名；沒拿到圖片回傳 None。"""
    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        ),
    )
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image = Image.open(BytesIO(part.inline_data.data))
            filename = f"{uuid.uuid4().hex}.png"
            image.save(os.path.join(static_tmp_path, filename))
            return filename
    return None


# === 靜態圖檔路由（給 LINE 抓取生成的圖片）===
@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(static_tmp_path, filename)


# === LINE Webhook 端點 ===
@app.route("/", methods=["GET"])
def home():
    return {"message": "Line Webhook Server"}


@app.route("/", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    app.logger.info("Request body: %s", body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning("Invalid signature. Check channel credentials.")
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    prompt = event.message.text.strip()
    app.logger.info("Image prompt: %s", prompt)

    try:
        filename = generate_image(prompt)
    except Exception as e:
        app.logger.error("Gemini image generation failed: %s", e)
        filename = None

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        if filename:
            image_url = f"https://{base_url}/images/{filename}"
            app.logger.info("Image URL: %s", image_url)
            messages = [
                ImageMessage(
                    original_content_url=image_url,
                    preview_image_url=image_url,
                )
            ]
        else:
            messages = [
                TextMessage(text="抱歉，這次沒生出圖，請換個說法再試一次。")
            ]

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=messages,
            )
        )
