from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import requests
from bs4 import BeautifulSoup
import hashlib
import threading
import time

app = Flask(__name__)

# 環境変数から取得
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')
USER_ID = os.environ.get('USER_ID')
CHECK_URL = os.environ.get('CHECK_URL')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Webページのハッシュ取得
def get_page_hash():
    try:
        res = requests.get(CHECK_URL)
        soup = BeautifulSoup(res.content, "html.parser")
        content = soup.get_text()
        return hashlib.md5(content.encode("utf-8")).hexdigest()
    except Exception as e:
        print("ハッシュ取得エラー:", e)
        return None

# ページ変更監視スレッド
def monitor():
    time.sleep(5)  # 起動直後の安定待機
    while True:
        try:
            current_hash = get_page_hash()
            if current_hash is None:
                time.sleep(300)
                continue

            if not os.path.exists("last_hash.txt"):
                with open("last_hash.txt", "w") as f:
                    f.write(current_hash)

            with open("last_hash.txt", "r") as f:
                last_hash = f.read().strip()

            if current_hash != last_hash:
                line_bot_api.push_message(
                    USER_ID,
                    TextSendMessage(text=f"📢 Webページが更新されました！\n{CHECK_URL}")
                )
                with open("last_hash.txt", "w") as f:
                    f.write(current_hash)
        except Exception as e:
            print("監視エラー:", e)
        time.sleep(300)  # 5分ごとにチェック

# Webhook エンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    print("Request body:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# メッセージイベント処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    reply = f"受け取ったメッセージ: {event.message.text}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

# 動作確認用
@app.route("/")
def index():
    return "✅ Web Monitor Bot is running!"

# 監視スレッドをバックグラウンドで起動（Render + gunicorn対応）
threading.Thread(target=monitor, daemon=True).start()
