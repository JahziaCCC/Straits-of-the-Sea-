import os
import json
import requests
import feedparser

# جلب المتغيرات السرية
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# قائمة مصادر الأخبار الرسمية (RSS Feeds) - يمكنك إضافة أي رابط RSS هنا
SOURCES = [
    {"name": "وكالة الأنباء السعودية (واس)", "url": "https://www.spa.gov.sa/rss.xml"},
    {"name": "رويترز - البحر الأحمر والشحن", "url": "https://www.reutersagency.com/feed/?best-topics=maritime&post_type=best"},
    # أضف مصادر أخرى هنا بنفس الصيغة
]

HISTORY_FILE = "sent_posts.json"

def load_sent_posts():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return set(json.load(f))
            except Exception:
                return set()
    return set()

def save_sent_posts(sent_posts):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(sent_posts), f, ensure_ascii=False, indent=2)

def send_telegram_message(title, link, source_name):
    message = f"🚨 **خبر جديد من {source_name}**\n\n📌 {title}\n\n🔗 [رابط الخبر]({link})"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

def main():
    sent_posts = load_sent_posts()
    new_posts_found = False

    for source in SOURCES:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:5]:  # فحص أحدث 5 أخبار من كل مصدر
            post_id = entry.get("id", entry.get("link", entry.get("title")))
            
            if post_id not in sent_posts:
                title = entry.get("title", "بدون عنوان")
                link = entry.get("link", "")
                
                print(f"إرسال خبر جديد: {title}")
                send_telegram_message(title, link, source["name"])
                
                sent_posts.add(post_id)
                new_posts_found = True

    if new_posts_found:
        save_sent_posts(sent_posts)

if __name__ == "__main__":
    main()
