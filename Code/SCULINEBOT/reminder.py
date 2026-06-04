"""
東吳大學資料系 2026 LINEBOT —— 定時提醒範例

示範 LINE Bot「主動、定時」發訊息（push message）的能力，而不只是被動回覆。

互動方式：在 LINE 傳「提醒 HH:MM 內容」，bot 會立刻回覆已設定，
並在每天該時間（Asia/Taipei）用 push_message 主動把提醒推給你。

注意：排程與使用者 id 都存在記憶體，Space 重啟（含 rebuild、休眠喚醒）後會清空，
需重新設定。這對課堂現場 demo 已足夠；若要長期可靠提醒需另外設計（外部 cron 等）。
"""

import os
import re
import atexit
import uuid

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from flask import Flask, abort, request

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent


# Initialize Flask app
app = Flask(__name__)
line_channel_secret = os.getenv("LINE_CHANNEL_SECRET")
line_channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
configuration = Configuration(access_token=line_channel_access_token)
handler = WebhookHandler(line_channel_secret)

# 程式內排程器（記憶體保存，Space 重啟後清空 —— demo 用途足夠）
TZ = "Asia/Taipei"
scheduler = BackgroundScheduler(timezone=TZ)
scheduler.start()
atexit.register(lambda: scheduler.shutdown(wait=False))

# 指令格式： 提醒 HH:MM 內容
REMINDER_PATTERN = re.compile(r"^提醒\s+(\d{1,2}):(\d{2})\s+(.+)$")
USAGE = (
    "用法：提醒 HH:MM 要提醒的內容\n"
    "例如：提醒 17:00 記得交作業\n"
    "（想馬上看到效果，把時間設成下一分鐘即可）"
)


def send_reminder(user_id: str, text: str) -> None:
    """到指定時間時，主動 push 訊息給使用者（不需 reply token）。"""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=f"⏰ 提醒：{text}")],
            ),
            x_line_retry_key=str(uuid.uuid4()),
        )


@app.route("/", methods=["GET"])
def home():
    """Health check endpoint."""
    return {"message": "Line Webhook Server"}


@app.route("/", methods=["POST"])
def callback():
    """Handle incoming webhook from LINE."""
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    app.logger.info("Request body: %s", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning(
            "Invalid signature. Please check channel credentials."
        )
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """解析提醒指令、排程，並回覆確認訊息。"""
    user_id = getattr(event.source, "user_id", None)
    text = event.message.text.strip()
    match = REMINDER_PATTERN.match(text)

    if not match or not user_id:
        reply = USAGE
    else:
        hour, minute = int(match.group(1)), int(match.group(2))
        content = match.group(3).strip()
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            reply = "時間格式怪怪的，請用 24 小時制 HH:MM。\n" + USAGE
        else:
            # 每天 HH:MM 觸發一次；同一人同一時間重設會覆蓋舊的
            scheduler.add_job(
                send_reminder,
                trigger=CronTrigger(hour=hour, minute=minute, timezone=TZ),
                args=[user_id, content],
                id=f"{user_id}-{hour:02d}{minute:02d}",
                replace_existing=True,
            )
            reply = f"好的，我會在每天 {hour:02d}:{minute:02d} 提醒你：{content}"

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)],
            )
        )
