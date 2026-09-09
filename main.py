import html
import os
import re
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
KEYWORD = "김찬종 임태현 양도"


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


def try_rsshub_sources(encoded_query):
    """嘗試透過公開 RSS/RSSHub 鏡像源獲取推文"""
    sources = [
        f"https://rsshub.app/twitter/keyword/{encoded_query}",
        f"https://nitter.privacydev.net/search/rss?f=tweets&q={encoded_query}",
        f"https://nitter.poast.org/search/rss?f=tweets&q={encoded_query}",
    ]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    for url in sources:
        try:
            print(f"🔄 嘗試備用 RSS 管道: {url.split('/')[2]}")
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                root = ET.fromstring(res.text)
                items = root.findall("./channel/item")
                if items:
                    tweets = []
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
                        tweets.append({"text": desc, "link": link, "user": "X"})
                    return tweets
        except Exception as e:
            print(f"⚠️ 該 RSS 源失敗: {e}")
            continue
    return None


def main():
    encoded_query = quote(KEYWORD)
    print(f"🔍 開始請求 X 搜尋: {KEYWORD}")

    tweets = try_rsshub_sources(encoded_query)

    if tweets:
        print(f"✅ 成功抓取到 {len(tweets)} 條推文，準備發送 Telegram...")
        for tweet in tweets:
            clean_text = clean_html(tweet["text"])
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
                f"🔗 [點擊開啟原推文]({tweet['link']})"
            )
            send_telegram(msg)
    else:
        print(
            "🟢 目前所有免登入管道暫無新推文（或節點冷卻中），系統維持靜音等待下一次輪詢。"
        )


if __name__ == "__main__":
    main()
