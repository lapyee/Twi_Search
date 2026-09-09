import html
import os
import re
import requests
from urllib.parse import quote

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
KEYWORD = "김찬종 임태현 양도 -is:retweet"

# X 官方 Web App 的公共 Bearer Token（公開固定值）
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"


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


def get_guest_token():
    """動態向 X 獲取 Guest Token"""
    url = "https://api.x.com/1.1/guest/activate.json"
    headers = {"authorization": f"Bearer {BEARER_TOKEN}"}
    try:
        res = requests.post(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json().get("guest_token")
    except Exception as e:
        print(f"獲取 Guest Token 失敗: {e}")
    return None


def main():
    print(f"🔍 開始請求 X 搜尋: {KEYWORD}")

    guest_token = get_guest_token()
    if not guest_token:
        print("🔴 無法取得 Guest Token，暫時無法請求 X API。")
        return

    print("🔑 成功取得 Guest Token，發起搜尋請求...")

    search_url = f"https://api.x.com/1.1/search/tweets.json?q={quote(KEYWORD)}&count=10&result_type=recent"
    headers = {
        "authorization": f"Bearer {BEARER_TOKEN}",
        "x-guest-token": guest_token,
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ),
    }

    try:
        res = requests.get(search_url, headers=headers, timeout=10)
        print(f"📡 伺服器回應 HTTP 狀態碼: {res.status_code}")

        if res.status_code == 200:
            statuses = res.json().get("statuses", [])
            print(f"📊 成功抓取到 {len(statuses)} 條推文項目")

            if statuses:
                print("✅ 發現符合條件的推文，準備發送 Telegram...")
                for tweet in statuses[:3]:
                    text = tweet.get("text", "")
                    user = tweet.get("user", {}).get("screen_name", "twitter")
                    tweet_id = tweet.get("id_str", "")
                    link = f"https://x.com/{user}/status/{tweet_id}"

                    clean_text = clean_html(text)
                    clean_text = (
                        clean_text.replace("*", "")
                        .replace("_", "")
                        .replace("`", "")
                        .replace("[", "")
                        .replace("]", "")
                    )

                    msg = (
                        f"🚨 *發現 X (Twitter) 新 양도 (轉讓) 推文！*\n\n"
                        f"👤 @{user}\n"
                        f"📝 {clean_text[:200]}...\n\n"
                        f"🔗 [點擊開啟原推文]({link})"
                    )
                    send_telegram(msg)
            else:
                print(
                    "🟢 連線完全正常，HTTP 200 OK！但目前 X 上確實沒有符合條件的新推文。"
                )
        else:
            print(f"🔴 請求失敗，HTTP 狀態碼: {res.status_code}")

    except Exception as e:
        print(f"❌ 執行發生例外異常: {e}")


if __name__ == "__main__":
    main()
