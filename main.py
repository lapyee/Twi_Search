import html
import os
import re
import requests
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


def fetch_from_twitter_syndication():
    """使用 X 官方 Widget 前端 API（最穩定，無須 API Key）"""
    encoded_query = quote(KEYWORD)
    url = f"https://syndication.twitter.com/srv/timeline-profile/x/search?q={encoded_query}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            # 解析 JSON 回應
            data = res.json()
            entries = (
                data.get("props", {})
                .get("pageProps", {})
                .get("timeline", {})
                .get("entries", [])
            )

            tweets = []
            for entry in entries:
                tweet_data = (
                    entry.get("content", {}).get("tweet", {})
                    if "content" in entry
                    else {}
                )
                if not tweet_data:
                    continue

                text = tweet_data.get("text", "")
                # 過濾轉推
                if text.startswith("RT @"):
                    continue

                user = (
                    tweet_data.get("user", {}).get("screen_name", "twitter")
                )
                tweet_id = tweet_data.get("id_str", "")
                link = f"https://x.com/{user}/status/{tweet_id}"

                tweets.append({"text": text, "link": link, "user": user})

            return tweets
    except Exception as e:
        print("Syndication 抓取失敗:", e)
    return None


def main():
    print("開始抓取推文...")
    tweets = fetch_from_twitter_syndication()

    if tweets:
        for tweet in tweets[:3]:
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
                f"👤 @{tweet['user']}\n"
                f"📝 {clean_text[:200]}...\n\n"
                f"🔗 [點擊開啟原推文]({tweet['link']})"
            )
            send_telegram(msg)
    else:
        print("目前沒有搜尋到新推文或連線被限制，等待下次自動執行。")


if __name__ == "__main__":
    main()
