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
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram 發送失敗:", e)


def clean_html(raw_html):
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, "", raw_html)
    return html.unescape(cleantext)


def main():
    encoded_query = quote(KEYWORD)

    # 彙整目前可用的免費 RSS 來源 (包含 RSSHub 鏡像與 Nitter 活躍節點)
    rss_sources = [
        f"https://rsshub.app/twitter/keyword/{encoded_query}",
        f"https://rss.feed43.com/twitter/{encoded_query}",
        f"https://nitter.net/search/rss?f=tweets&q={encoded_query}",
        f"https://nitter.x86.men/search/rss?f=tweets&q={encoded_query}",
    ]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    for rss_url in rss_sources:
        try:
            print(f"嘗試抓取: {rss_url}")
            res = requests.get(rss_url, headers=headers, timeout=10)
            if res.status_code == 200:
                root = ET.fromstring(res.text)
                items = root.findall("./channel/item")

                if items:
                    for item in items[:3]:
                        link = (
                            item.find("link").text
                            if item.find("link") is not None
                            else ""
                        )
                        desc = (
                            item.find("description").text
                            if item.find("description") is not None
                            else ""
                        )

                        clean_text = clean_html(desc)
                        clean_text = (
                            clean_text.replace("*", "")
                            .replace("_", "")
                            .replace("`", "")
                        )

                        msg = (
                            f"🚨 *發現 X (Twitter) 新 양도 (轉讓) 推文！*\n\n"
                            f"📝 {clean_text[:200]}...\n\n"
                            f"🔗 [點擊開啟原推文]({link})"
                        )
                        send_telegram(msg)
                    # 成功抓到資料後跳出迴圈
                    break
        except Exception as e:
            print("該源連線失敗:", e)
            continue


if __name__ == "__main__":
    main()
