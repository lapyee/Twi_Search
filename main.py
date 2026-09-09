import os
import requests
from ntscraper import Nitter

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
KEYWORD = "김찬종 임태현 양도-is:retweet"  # 可以改為你想監控的關鍵字


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)


def main():
    scraper = Nitter(log_level=0)
    try:
        results = scraper.get_tweets(KEYWORD, mode="term", number=3)
        tweets = results.get("tweets", [])
        for tweet in reversed(tweets):
            link = tweet.get("link", "")
            text = tweet.get("text", "").replace("*", "\\*")
            user = tweet.get("user", {}).get("username", "")

            msg = (
                f"🚨 *X (Twitter) 新動態！*\n\n"
                f"👤 @{user}\n"
                f"📝 {text}\n\n"
                f"🔗 [查看推文]({link})"
            )
            send_telegram(msg)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
