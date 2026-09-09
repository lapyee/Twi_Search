import html
import os
import re
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

KEYWORD = "김찬종 임태현 양도 -is:retweet"


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print("Telegram 發送結果:", res.status_code)
    except Exception as e:
        print("Telegram 發送失敗:", e)


def clean_html(raw_html):
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, "", raw_html)
    return html.unescape(cleantext)


def main():
    encoded_query = quote(KEYWORD)

    # 備用免費公共 RSS 節點列表（若第一個 404，會自動試第二個）
    rss_sources = [
        f"https://nitter.net/search/rss?f=tweets&q={encoded_query}",
        f"https://nitter.cz/search/rss?f=tweets&q={encoded_query}",
        f"https://nitter.privacydev.net/search/rss?f=tweets&q={encoded_query}",
    ]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    success = False
    for rss_url in rss_sources:
        try:
            print(f"嘗試抓取 RSS: {rss_url}")
            response = requests.get(rss_url, headers=headers, timeout=10)

            if response.status_code == 200:
                root = ET.fromstring(response.text)
                items = root.findall("./channel/item")

                if items:
                    for item in items[:3]:
                        link = (
                            item.find("link").text
                            if item.find("link") is not None
                            else ""
                        )
                        description = (
                            item.find("description").text
                            if item.find("description") is not None
                            else ""
                        )

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
                    success = True
                    break
        except Exception as e:
            print(f"該源抓取失敗: {e}")
            continue

    if not success:
        # 如果所有公共 RSS 源都被 X 限制，不會一直跳 404 報警，只印出 Log 保持靜默
        print(
            "公共 RSS 節點暫時無回應或沒有最新推文，等待下一次 15 分鐘自動重試。"
        )


if __name__ == "__main__":
    main()
