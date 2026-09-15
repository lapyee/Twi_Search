import html
import os
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 🔍 在此處定義你想監控的多組關鍵字列表 (符合任意一組就會通知)
KEYWORDS = [
    "김종구 정민 양도 20",
    "김찬종 임태현 양도 4",
    "김찬종 박정혁 양도 17"
]

def send_telegram(html_text):
    """發送 Telegram 訊息 (HTML 模式)"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": html_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"Telegram 發送狀態碼: {res.status_code}")
    except Exception as e:
        print(f"Telegram 發送失敗: {e}")

def clean_text_for_html(raw_text):
    """清除 HTML 標籤並轉義文字"""
    cleanr = re.compile("<.*?>")
    text_without_html = re.sub(cleanr, "", raw_text)
    unescaped_text = html.unescape(text_without_html)
    return html.escape(unescaped_text)

def parse_date(date_str):
    """安全解析 RSS 的 pubDate"""
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        return None

def fetch_tweets_for_keyword(keyword):
    """針對單一關鍵字抓取推文"""
    encoded_query = quote(keyword)
    sources = [
        f"https://rsshub.app/twitter/keyword/{encoded_query}",
        f"https://nitter.net/search/rss?f=tweets&q={encoded_query}",
        f"https://nitter.cz/search/rss?f=tweets&q={encoded_query}",
    ]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    now = datetime.now(timezone.utc)
    time_window = timedelta(minutes=25)  # 25 分鐘的時間窗口

    for url in sources:
        domain = url.split("/")[2]
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                root = ET.fromstring(res.text)
                items = root.findall("./channel/item")

                if not items:
                    return []

                valid_tweets = []
                for item in items:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    pub_date_str = item.find("pubDate").text if item.find("pubDate") is not None else ""

                    raw_content = desc if desc else title
                    content = clean_text_for_html(raw_content)

                    pub_dt = parse_date(pub_date_str)
                    if pub_dt:
                        if pub_dt.tzinfo is None:
                            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                        if now - pub_dt <= time_window:
                            valid_tweets.append({"text": content, "link": link, "keyword": keyword})
                    else:
                        valid_tweets.append({"text": content, "link": link, "keyword": keyword})

                return valid_tweets
        except Exception as e:
            continue

    return []

def main():
    print(f"🔍 [系統啟動] 開始多關鍵字監控: {KEYWORDS}")
    all_matched_tweets = []

    # 輪流檢查清單中的每一個關鍵字
    for kw in KEYWORDS:
        print(f"👉 檢查關鍵字: '{kw}'")
        tweets = fetch_tweets_for_keyword(kw)
        if tweets:
            all_matched_tweets.extend(tweets)

    if all_matched_tweets:
        print(f"✅ 成功監測到 {len(all_matched_tweets)} 條相關推文，準備發送 Telegram...")
        for tweet in all_matched_tweets[:5]:  # 最多發送前 5 條
            msg = (
                f"🚨 <b>發現 X (Twitter) 新 양도 (轉讓) 推文！</b>\n"
                f"🏷 匹配關鍵字：<code>{tweet['keyword']}</code>\n\n"
                f"📝 {tweet['text'][:250]}...\n\n"
                f"🔗 <a href='{tweet['link']}'>點擊開啟原推文</a>"
            )
            send_telegram(msg)
    else:
        print("🟢 所有關鍵字目前皆無 25 分鐘內的最新推文，維持完全靜音。")

if __name__ == "__main__":
    main()
