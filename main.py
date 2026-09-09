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


def main():
    encoded_query = quote(KEYWORD)
    url = f"https://syndication.twitter.com/srv/timeline-profile/x/search?q={encoded_query}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    print(f"🔍 開始請求 X 搜尋: {KEYWORD}")

    try:
        res = requests.get(url, headers=headers, timeout=10)
        print(f"📡 伺服器回應 HTTP 狀態碼: {res.status_code}")

        if res.status_code == 200:
            try:
                data = res.json()
                entries = (
                    data.get("props", {})
                    .get("pageProps", {})
                    .get("timeline", {})
                    .get("entries", [])
                )
                print(f"📊 成功解析 API，共抓取到 {len(entries)} 條原始項目")

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
                    if text.startswith("RT @"):
                        continue

                    user = (
                        tweet_data.get("user", {}).get("screen_name", "twitter")
                    )
                    tweet_id = tweet_data.get("id_str", "")
                    link = f"https://x.com/{user}/status/{tweet_id}"
                    tweets.append({"text": text, "link": link, "user": user})

                if tweets:
                    print(f"✅ 篩選後共有 {len(tweets)} 條有效推文，準備發送 Telegram...")
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
                    print("🟢 連線完全正常，但目前 X 上確實沒有符合條件的新推文。")

            except Exception as json_err:
                print(f"⚠️ 資料解析失敗 (可能回傳內容非 JSON): {json_err}")
        else:
            print(
                f"🔴 請求被 X 限制或阻擋，狀態碼: {res.status_code} (內容長度: {len(res.text)})"
            )

    except Exception as e:
        print(f"❌ 連線發生例外異常: {e}")


if __name__ == "__main__":
    main()
