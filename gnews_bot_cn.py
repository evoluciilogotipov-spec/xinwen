import os
import feedparser
import requests
import time

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# СПИСОК НАДЕЖНЫХ RSS-ИСТОЧНИКОВ ПРО БАРСЕЛОНУ
RSS_URLS = [
    "https://www.euro-football.ru/team/barselona/rss", # Евро-Футбол.ру
    "https://news.google.com/rss/search?q=%D0%91%D0%B0%D1%80%D1%81%D0%B5%D0%BB%D0%BE%D0%BD%D0%B0&hl=ru&gl=RU&ceid=RU:ru", # Google Новости (запасной)
]

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"Ошибка отправки: {response.text}")
    except Exception as e:
        print(f"Ошибка соединения: {e}")

def main():
    print("Начинаем проверку новостей...")
    feed = None
    
    # Пробуем источники по очереди, пока не найдем рабочий
    for url in RSS_URLS:
        print(f"Проверяем источник: {url}")
        temp_feed = feedparser.parse(url)
        if temp_feed.entries:
            feed = temp_feed
            print(f"Успешно! Найдено новостей: {len(feed.entries)}")
            break
        else:
            print("Источник пуст или недоступен, пробуем следующий...")
    
    if not feed or not feed.entries:
        print("Не удалось получить новости ни с одного источника.")
        return

    # Берем 2 самые свежие новости
    for entry in feed.entries[:2]:
        title = entry.title
        link = entry.link
        message = f"<b>{title}</b>\n\n<a href='{link}'>Читать полностью</a>"
        send_to_telegram(message)
        print(f"Отправлено: {title}")
        time.sleep(2)

if __name__ == "__main__":
    main()


