import os
import json
import requests
import feedparser

# جلب المتغيرات السرية من GitHub Secrets
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# قائمة الكلمات المفتاحية للرصد حصراً للمضائق والممرات البحرية
KEYWORDS = [
    "هرمز", "باب المندب", "قناة السويس", "البحر الأحمر", 
    "خليج عدن", "بحر العرب", "مضيق", "سفينة", "ناقلة", 
    "ملاحة", "حوادث بحرية", "شحن بحري", "Hormuz", "Bab el-Mandeb", "Suez"
]

# المصادر الرسمية
SOURCES = [
    {"name": "الحسابات الرسمية", "url": "https://rss.app/feeds/TulBq0pPDHsPVQAL.xml"},
    {"name": "وكالة الأنباء السعودية (واس)", "url": "https://www.spa.gov.sa/rss.xml"},
    {"name": "وكالة أنباء الإمارات (وام)", "url": "https://wam.ae/ar/rss"},
    {"name": "وكالة الأنباء الكويتية (كونا)", "url": "https://www.kuna.net.kw/RSS.aspx"},
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

def is_relevant(text):
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in KEYWORDS)

def send_telegram_message(title, link, source_name):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    # الصياغة الرسمية الجديدة مع رابط مباشر وقابل للنسخ
    message = (
        f"⚓ *النشرة البحرية | أخبار المضائق*\n"
        f"🏛️ المصدر: {source_name}\n\n"
        f"📌 {title}\n\n"
        f"🔗 الرابط المباشر:\n{link}"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"خطأ إرسال التليجرام: {e}")

def main():
    sent_posts = load_sent_posts()
    new_posts_found = False

    print("--- بدء فحص النشرة البحرية للمضائق ---")
    for source in SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:10]:
                title = entry.get("title", "بدون عنوان")
                summary = entry.get("summary", "")
                full_text = f"{title} {summary}"
                post_id = entry.get("id", entry.get("link", title))
                
                if post_id not in sent_posts and is_relevant(full_text):
                    link = entry.get("link", "")
                    
                    send_telegram_message(title, link, source["name"])
                    sent_posts.add(post_id)
                    new_posts_found = True
                    print(f"تم إرسال خبر: {title}")
                else:
                    sent_posts.add(post_id)
        except Exception as e:
            print(f"خطأ في جلب {source['name']}: {e}")

    if new_posts_found:
        save_sent_posts(sent_posts)
        print("تم تحديث النشرة بنجاح.")
    else:
        print("لا توجد أخبار جديدة تخص المضائق.")

if __name__ == "__main__":
    main()
