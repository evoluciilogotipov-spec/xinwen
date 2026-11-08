import os
import feedparser
import requests
import time

# Секреты из GitHub
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Ссылка на новостную ленту про Барселону
RSS_URL = "https://www.euro-football.ru/team/barselona/rss"

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

def generate_post_with_gemini(news_title, news_link):
    """Отправляет запрос нейросети и просит написать пост."""
    print(f"Генерируем пост для новости: {news_title}")
    
    prompt = f"""
    Ты — профессиональный спортивный журналист, который ведёт Telegram-канал о ФК «Барселона».
    Напиши интересный и живой пост на основе этой новости: "{news_title}".
    
    Требования:
    - Длина поста: 3-5 предложений.
    - Добавь немного эмоций и анализа (например, как это повлияет на команду).
    - Не используй канцелярит, пиши как для болельщиков.
    - В конце обязательно добавь ссылку на источник: {news_link}
    - Оформи пост с помощью HTML-тегов (например, <b>жирный</b> для важных слов).
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        post_text = result['candidates'][0]['content']['parts'][0]['text']
        return post_text
    except Exception as e:
        print(f"Ошибка при обращении к Gemini: {e}")
        return None

def main():
    print("Начинаем проверку новостей...")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("Новостей не найдено.")
        return

    # Берем 1 самую свежую новость (чтобы не спамить)
    entry = feed.entries[0]
    title = entry.title
    link = entry.link
    
    # Генерируем текст с помощью нейросети
    post_text = generate_post_with_gemini(title, link)
    
    if post_text:
        send_to_telegram(post_text)
        print("Пост успешно сгенерирован и отправлен!")
    else:
        print("Не удалось сгенерировать пост, пропускаем.")
        # На случай ошибки ИИ, можно отправить просто заголовок
        # send_to_telegram(f"<b>{title}</b>\n\n<a href='{link}'>Читать полностью</a>")

if __name__ == "__main__":
    main()
