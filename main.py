from flask import Flask
from linebot import LineBotApi
from linebot.models import TextSendMessage
import os
import requests
from bs4 import BeautifulSoup
import hashlib
import threading
import time

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# 環境変数
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
USER_ID = os.environ.get('USER_ID')
CHECK_URL = os.environ.get('CHECK_URL')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

def get_page_hash():
    try:
        res = requests.get(CHECK_URL)
        soup = BeautifulSoup(res.content, "html.parser")
        content = soup.get_text()
        return hashlib.md5(content.encode("utf-8")).hexdigest()
    except:
        return None

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
                # 通知送信
                line_bot_api.push_message(
                    USER_ID,
                    TextSendMessage(text="📢 Webページが更新されました！\n" + CHECK_URL)
                )
                with open("last_hash.txt", "w") as f:
                    f.write(current_hash)
        except Exception as e:
            print("エラー:", e)
        time.sleep(300)  # 5分ごとにチェック

@app.route("/")
def index():
    return "Web Monitor Bot is running!"

if __name__ == "__main__":
    threading.Thread(target=monitor).start()
    app.run(host="0.0.0.0", port=3000)
