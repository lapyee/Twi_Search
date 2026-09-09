import os
import requests
from ntscraper import Nitter

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 設定你想搜尋的韓文關鍵字與過濾語法
KEYWORD = "김찬종 임태현 양도 -is:retweet"


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    res = requests.post(url, json=payload)
    print("Telegram API 回應:", res.json())


def main():
    try:
        # 爬取最新推文
        scraper = Nitter(log_level=1)
        results = scraper.get_tweets(KEYWORD, mode="term", number=3)
        tweets = results.get("tweets", [])

        if not tweets:
            print("目前沒有搜尋到相關的新推文。")
            return

        for tweet in reversed(tweets):
            link = tweet.get("link", "")
            text = tweet.get("text", "")

            # 雙重保險：程式層面再次過濾轉推 (RT)
            if text.startswith("RT @"):
                continue

            # 清除 Markdown 符號，避免 Telegram 解析失敗
            clean_text = (
                text.replace("*", "")
                .replace("_", "")
                .replace("`", "")
                .replace("[", "")
                .replace("]", "")
            )
            user = tweet.get("user", {}).get("username", "未知用戶")

            msg = (
                f"🚨 *X (Twitter) 發現新 양도 (轉讓) 推文！*\n\n"
                f"👤 @{user}\n"
                f"📝 {clean_text}\n\n"
                f"🔗 [點擊開啟原推文]({link})"
            )
            send_telegram(msg)

    except Exception as e:
        print(f"執行出錯: {e}")


if __name__ == "__main__":
    main()
