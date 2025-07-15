from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
from dotenv import load_dotenv
from preference import save_user_preference, get_user_preference

load_dotenv()

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Error:", e)
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_msg = event.message.text

    # 讀取使用者偏好
    past_pref = get_user_preference(user_id)

    # 組合 GPT Prompt
    prompt = f"""
你是一位專業的精品代購顧問，客戶目前說：「{user_msg}」。
請根據訊息推薦合適的品牌與商品類型，推薦理由簡單明確。
如果你已知該客戶偏好是：{past_pref}，請一併考慮。
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    reply_text = response.choices[0].message['content'].strip()

    # 儲存此次對話內容（作為偏好依據）
    save_user_preference(user_id, user_msg)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(port=5000)
