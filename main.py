import html
import os
import re
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 你的搜尋關鍵字
KEYWORD = "김찬종 임태현 양도 -is:retweet"


def send_telegram(text):
    """發送訊息給 Telegram Bot"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print("Telegram 發送結果:", res.status_code, res.json())
    except Exception as e:
        print("Telegram 發送失敗:", e)


def clean_html(raw_html):
    """清除 HTML 標籤並轉義文字"""
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, "", raw_html)
    return html.unescape(cleantext)


def main():
    print(f"開始搜尋 X 關鍵字: {KEYWORD}")

    # 使用免費穩定的 RSSHub 公開節點
    encoded_query = quote(KEYWORD)
    rss_url = f"https://rsshub.app/twitter/keyword/{encoded_query}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
        response = requests.get(rss_url, headers=headers, timeout=15)

        if response.status_code != 200:
            print(f"RSS 源回應異常: HTTP {response.status_code}")
            # 如果 RSS 暫時拿不到資料，發送測試訊息確認 Telegram 是否正常 Working
            send_telegram(
                f"🤖 *監控系統運作中*\n目前 X 搜尋暫無新動態（HTTP {response.status_code}）。"
            )
            return

        # 解析 RSS XML
        root = ET.fromstring(response.text)
        items = root.findall("./channel/item")

        if not items:
            print("目前沒有搜尋到相關的新推文。")
            send_telegram(
                f"🤖 *監控系統運作中*\n搜尋關鍵字：`{KEYWORD}`\n目前暫無最新轉讓推文。"
            )
            return

        # 只取最新的 3 則推文
        for item in items[:3]:
            title = (
                item.find("title").text
                if item.find("title") is not None
                else ""
            )
            link = (
                item.find("link").text if item.find("link") is not None else ""
            )
            description = (
                item.find("description").text
                if item.find("description") is not None
                else ""
            )

            # 清理文字內容
            clean_text = clean_html(description)
            clean_text = (
                clean_text.replace("*", "")
                .replace("_", "")
                .replace("`", "")
                .replace("[", "")
                .replace("]", "")
            )

            msg = (
                f"🚨 *發現 X (Twitter) 新 양도 (轉讓) 推文！*\n\n"
                f"📝 {clean_text[:200]}...\n\n"
                f"🔗 [點擊開啟原推文]({link})"
            )
            send_telegram(msg)

    except Exception as e:
        print(f"發生錯誤: {e}")
        send_telegram(f"⚠️ 監控程式執行時出錯: {e}")


if __name__ == "__main__":
    main()
