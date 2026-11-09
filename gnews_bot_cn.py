import os
import feedparser
import requests
import time
import hashlib
import re

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Оставляем только Google, так как остальные блокируют GitHub
RSS_URLS = [
    "https://news.google.com/rss/search?q=%D0%91%D0%B0%D1%80%D1%81%D0%B5%D0%BB%D0%BE%D0%BD%D0%B0&hl=ru&gl=RU&ceid=RU:ru"
]

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Ошибка Телеграм: {e}")

def generate_post_with_gemini(news_title, news_link):
    prompt = "Ты — спортивный аналитик и редактор Telegram-канала о ФК «Барселона».\n"
    prompt += f"Напиши пост на основе этой новости: {news_title}\n\n"
    prompt += "ТВОЙ СТИЛЬ:\n- Пиши строго, фактологически, с цифрами.\n- Никаких лишних эмоций.\n\n"
    prompt += "ФОРМАТ:\n1. Один эмодзи в начале.\n2. 2-3 абзаца.\n"
    prompt += f"3. Ссылка на источник: <a href='{news_link}'>Источник</a>\n"
    prompt += "4. Ссылка на канал: <a href='https://t.me/newsbarca4'>@newsbarca4</a>\n"
    
    models = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            response = requests.post(url, headers={'Content-Type': 'application/json'}, json=data)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 503:
                time.sleep(10)
        except Exception as e:
            print(f"Ошибка {model_name}: {e}")
    return None

def get_strict_hash(text):
    if not text:
        return None
    clean = re.sub(r'<[^>]+>', '', text)
    clean = re.sub(r'[^а-яА-ЯёЁa-zA-Z0-9]', '', clean).lower()
    if len(clean) < 20:
        return None
    return hashlib.sha256(clean.encode('utf-8')).hexdigest()

def main():
    print("Начинаем проверку...")
    
    sent_hashes = []
    if os.path.exists("sent_hashes.txt"):
        with open("sent_hashes.txt", "r", encoding="utf-8") as f:
            sent_hashes = [line.strip() for line in f.readlines() if line.strip()]
    print(f"В памяти сейчас {len(sent_hashes)} хэшей.")

    total_new_news = 0
    
    for url in RSS_URLS:
        print(f"Источник: {url}")
        feed = feedparser.parse(url)
        
        if not feed.entries:
            continue
            
        news_from_this_source = 0
        
        for entry in feed.entries:
            if news_from_this_source >= 1:
                break
                
            # Очищаем заголовок от мусора Google (убираем " - Матч ТВ" в конце)
            raw_title = entry.title
            title = raw_title.split(' - ')[0].strip() 
            
            link = entry.link
            
            summary = entry.get('summary', '')
            
            title_hash = get_strict_hash(title)
            summary_hash = get_strict_hash(summary)
            
            if (title_hash and title_hash in sent_hashes) or (summary_hash and summary_hash in sent_hashes):
                print(f"СТОП! Дубль: {title}")
                continue
                
            print(f"НОВАЯ новость: {title}")
            post_text = generate_post_with_gemini(title, link)
            
            if post_text:
                send_to_telegram(post_text)
                print("Пост отправлен!")
                
                with open("sent_hashes.txt", "a", encoding="utf-8") as f:
                    if title_hash: f.write(title_hash + "\n")
                    if summary_hash: f.write(summary_hash + "\n")
                    
                total_new_news += 1
                news_from_this_source += 1
        
        time.sleep(2)

    if total_new_news == 0:
        print("Новых новостей нет.")

if __name__ == "__main__":
    main()
