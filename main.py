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
KEYWORD = "김찬종 임태현 양도"


def send_telegram(html_text):
    """發送 Telegram 訊息 (採用 HTML 模式，徹底避免 Markdown 語法錯亂)"""
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
    """清除 HTML 標籤並轉換 Telegram HTML 轉義字元"""
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


def fetch_tweets():
    encoded_query = quote(KEYWORD)

    # 全球多個免費備援節點 (自動依序切換)
    sources = [
        f"https://rsshub.app/twitter/keyword/{encoded_query}",
        f"https://rsshub.rss3.io/twitter/keyword/{encoded_query}",
        f"https://nitter.net/search/rss?f=tweets&q={encoded_query}",
        f"https://nitter.cz/search/rss?f=tweets&q={encoded_query}",
        f"https://nitter.privacydev.net/search/rss?f=tweets&q={encoded_query}",
        f"https://nitter.x86.men/search/rss?f=tweets&q={encoded_query}",
    ]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    now = datetime.now(timezone.utc)
    time_window = timedelta(minutes=25)  # 配合 15 分鐘 Cron，只發送 25 分鐘內的新推文

    for url in sources:
        domain = url.split("/")[2]
        try:
            print(f"🔄 [嘗試連線] {domain}")
            res = requests.get(url, headers=headers, timeout=10)

            if res.status_code == 200:
                root = ET.fromstring(res.text)
                items = root.findall("./channel/item")

                if not items:
                    print(f"🟢 [{domain}] 連線成功，目前沒有搜尋到任何推文。")
                    return []

                valid_tweets = []
                for item in items:
                    title = (
                        item.find("title").text
                        if item.find("title") is not None
                        else ""
                    )
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
                    pub_date_str = (
                        item.find("pubDate").text
                        if item.find("pubDate") is not None
                        else ""
                    )

                    raw_content = desc if desc else title
                    content = clean_text_for_html(raw_content)

                    # 時間篩選邏輯
                    pub_dt = parse_date(pub_date_str)
                    if pub_dt:
                        if pub_dt.tzinfo is None:
                            pub_dt = pub_dt.replace(tzinfo=timezone.utc)

                        # 只留下 25 分鐘內發布的新推文
                        if now - pub_dt <= time_window:
                            valid_tweets.append({"text": content, "link": link})
                    else:
                        valid_tweets.append({"text": content, "link": link})

                print(
                    f"✅ [{domain}] 成功擷取！篩選出 {len(valid_tweets)} 條最新推文。"
                )
                return valid_tweets

        except Exception as e:
            print(f"⚠️ [{domain}] 暫時無法連線: {e}")
            continue

    print("🔴 所有備援節點本輪皆無回應，保持靜音等待下次輪詢。")
    return []


def main():
    print(f"🔍 [系統啟動] 開始檢測 X 搜尋關鍵字: {KEYWORD}")
    tweets = fetch_tweets()

    if tweets:
        for tweet in tweets[:3]:
            msg = (
                f"🚨 <b>發現 X (Twitter) 新 양도 (轉讓) 推文！</b>\n\n"
                f"📝 {tweet['text'][:250]}...\n\n"
                f"🔗 <a href='{tweet['link']}'>點擊開啟原推文</a>"
            )
            send_telegram(msg)
    else:
        print("🟢 系統維持完全靜音，未發送 Telegram 通知。")


if __name__ == "__main__":
    main()
