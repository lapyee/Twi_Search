import os
import requests
import xml.etree.ElementTree as ET
import html
import re
from urllib.parse import quote

# 讀取 GitHub Secrets 機密資料
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 你的韓文關鍵字搜尋（過濾轉推）
KEYWORD = "김찬종 임태현 양도 -is:retweet"

def send_telegram(text):
    """發送 Telegram 訊息"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print("Telegram 發送結果:", res.status_code, res.json())
    except Exception as e:
        print("Telegram 發送失敗:", e)

def clean_html(raw_html):
    """清除內文的 HTML 標籤"""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return html.unescape(cleantext)

def main():
    print(f"=== 開始執行關鍵字監控: {KEYWORD} ===")
    
    # 先發送一條測試訊息，確保 Telegram Bot 運作正常
    send_telegram(f"🤖 *X 關鍵字監控運行中*\n搜尋關鍵字：`{KEYWORD}`")

    encoded_query = quote(KEYWORD)
    # 使用公共 RSS 節點抓取 X 資料
    rss_url = f"https://rsshub.app/twitter/keyword/{encoded_query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(rss_url, headers=headers, timeout=15)
        print("RSS 伺服器回應狀態碼:", response.status_code)

        if response.status_code != 200:
            print("無法從 RSS 取得資料")
            return

        root = ET.fromstring(response.text)
        items = root.findall('./channel/item')

        if not items:
            print("目前沒有搜尋到相關推文。")
            return

        # 抓取最新的 3 條推文發送
        for item in items[:3]:
            link = item.find('link').text if item.find('link') is not None else ''
            description = item.find('description').text if item.find('description') is not None else ''

            clean_text = clean_html(description)
            # 清除可能導致 Telegram Markdown 語法錯亂的特殊符號
            clean_text = clean_text.replace('*', '').replace('_', '').replace('`', '').replace('[', '').replace(']', '')

            msg = (
                f"🚨 *發現 X (Twitter) 新 양도 (轉讓) 推文！*\n\n"
                f"📝 {clean_text[:200]}...\n\n"
                f"🔗 [點擊開啟原推文]({link})"
            )
            send_telegram(msg)

    except Exception as e:
        print(f"執行時發生錯誤: {e}")

if __name__ == "__main__":
    main()
