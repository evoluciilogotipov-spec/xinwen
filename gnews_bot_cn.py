import os
import feedparser
import requests
import time

# Берем наши секреты
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Ссылка на RSS-ленту с новостями Барселоны (например, от Спорт-Экспресс или другого сайта)
SS_URL = "https://news.google.com/rss/search?q=%D0%91%D0%B0%D1%80%D1%81%D0%B5%D0%BB%D0%BE%D0%BD%D0%B0&hl=ru&gl=RU&ceid=RU:ru"

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print(f"Ошибка отправки: {response.text}")

def main():
    print("Начинаем проверку новостей...")
    feed = feedparser.parse(RSS_URL)
    
    # Берем 2 самые свежие новости
    for entry in feed.entries[:2]:
        title = entry.title
        link = entry.link
        
        # Форматируем сообщение
        message = f"<b>{title}</b>\n\n<a href='{link}'>Читать полностью</a>"
        
        send_to_telegram(message)
        print(f"Отправлено: {title}")
        time.sleep(2) # Пауза, чтобы Телеграм не забанил за спам

if __name__ == "__main__":
    main()


