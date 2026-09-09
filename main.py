import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 你的搜尋關鍵字
SEARCH_QUERY = "김찬종 임태현 양도 -is:retweet"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    requests.post(url, json=payload)

def main():
    # 測試連線 (如果收到這條訊息代表 Telegram 設定完全正確)
    send_telegram(f"🤖 *監控系統運作中...*\n正在追蹤：`{SEARCH_QUERY}`")

    # 將關鍵字轉為 URL 編碼
    encoded_query = quote(SEARCH_QUERY)
    
    # 使用開放的 RSSHub 鏡像源抓取 X 搜尋結果
    rss_url = f"https://rsshub.app/twitter/keyword/{encoded_query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(rss_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            items = root.findall('./channel/item')
            
            if not items:
                send_telegram("⚠️ 目前未搜尋到相關的最新推文。")
                return

            # 取最新的 3 條推文
            for item in items[:3]:
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                description = item.find('description').text if item.find('description') is not None else ''
                
                # 過濾內容
                clean_text = description.replace('*', '').replace('_', '').replace('`', '')
                
                msg = (
                    f"🚨 *發現 X (Twitter) 新動態！*\n\n"
                    f"📝 {clean_text[:200]}...\n\n"
                    f"🔗 [點擊開啟原推文]({link})"
                )
                send_telegram(msg)
        else:
            send_telegram(f"⚠️ RSS 源回應異常 (HTTP {response.status_code})，正在嘗試備用方案...")

    except Exception as e:
        print(f"Error: {e}")
        send_telegram(f"❌ 抓取時發生錯誤: {e}")

if __name__ == "__main__":
    main()
