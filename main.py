import os
import json
import requests
import feedparser
from bs4 import BeautifulSoup
from ntscraper import Nitter

# جلب المتغيرات السرية من GitHub Secrets
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 1. قائمة حسابات X الرسمية (بدون @)
X_OFFICIAL_ACCOUNTS = [
    {"name": "وزارة الدفاع السعودية", "username": "modgovksa"},
    {"name": "المتحدث الرسمي لوزارة الدفاع", "username": "spokesman_mod"},
    {"name": "حرس الحدود السعودي", "username": "FG_KSA"},
    {"name": "وزارة الخارجية السعودية", "username": "KSAMOFA"},
    {"name": "المتحدث العسكري للقوات المسلحة المصرية", "username": "EgyArmySpox"},
]

# 2. المصادر الرسمية عبر RSS (وكالات الأنباء)
RSS_SOURCES = [
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

def send_telegram_message(title, link, source_name):
    message = f"🚨 **رصد رسمي | {source_name}**\n\n📌 {title}\n\n🔗 [المصدر الرسمى]({link})"
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
        print(f"خطأ أثناء الإرسال للتليجرام: {e}")

# جلب تغريدات منصة X
def fetch_x_tweets(scraper, account_info, sent_posts):
    new_found = False
    try:
        # جلب أحدث 5 تغريدات من الحساب
        tweets = scraper.get_tweets(account_info["username"], mode='user', number=5)
        for tweet in tweets.get('tweets', []):
            tweet_id = tweet.get('link')
            text = tweet.get('text', '')
            
            # يتأكد أن التغريدة لم ترسل سابقاً وليست إعادة تغريد (Retweet)
            if tweet_id and tweet_id not in sent_posts and not tweet.get('is-retweet', False):
                # اقتطاع النص للتنبيه إن كان طويلاً
                clean_text = text.replace('\n', ' ')
                display_text = clean_text[:280] + "..." if len(clean_text) > 280 else clean_text
                
                send_telegram_message(display_text, tweet_id, account_info["name"])
                sent_posts.add(tweet_id)
                new_found = True
    except Exception as e:
        print(f"خطأ في جلب حساب {account_info['name']}: {e}")
    return new_found

def main():
    sent_posts = load_sent_posts()
    new_posts_found = False

    # أولاً: جلب التغريدات الرسمية من منصة X
    print("--- بدء فحص حسابات X الرسمية ---")
    scraper = Nitter(log_level=1)
    for acc in X_OFFICIAL_ACCOUNTS:
        if fetch_x_tweets(scraper, acc, sent_posts):
            new_posts_found = True

    # ثانياً: جلب الأخبار من وكالات الأنباء (RSS)
    print("--- بدء فحص وكالات الأنباء ---")
    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:5]:
                post_id = entry.get("id", entry.get("link", entry.get("title")))
                
                if post_id not in sent_posts:
                    title = entry.get("title", "بدون عنوان")
                    link = entry.get("link", "")
                    
                    send_telegram_message(title, link, source["name"])
                    sent_posts.add(post_id)
                    new_posts_found = True
        except Exception as e:
            print(f"خطأ في جلب {source['name']}: {e}")

    # حفظ السجل إذا تم إرسال شيء جديد
    if new_posts_found:
        save_sent_posts(sent_posts)
        print("تم إرسال التحديثات بنجاح إلى تليجرام.")
    else:
        print("لا توجد أخبار أو تحديثات جديدة.")

if __name__ == "__main__":
    main()
