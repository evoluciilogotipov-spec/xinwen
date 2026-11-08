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
            print(f"Ошибка отправки в Телеграм: {response.text}")
    except Exception as e:
        print(f"Ошибка соединения с Телеграм: {e}")

def generate_post_with_gemini(news_title, news_link):
    print(f"Генерируем пост для новости: {news_title}")
    
    # Собираем текст по кусочкам (без длинных кавычек)
    prompt = "Ты — спортивный аналитик и редактор Telegram-канала о ФК «Барселона».\n"
    prompt += f"Напиши пост на основе этой новости: {news_title}\n\n"
    prompt += "ТВОЙ СТИЛЬ:\n"
    prompt += "- Пиши строго, фактологически, с цифрами и аналитикой.\n"
    prompt += "- Никаких лишних эмоций и кликбейта.\n"
    prompt += "- Используй короткие и четкие предложения.\n\n"
    prompt += "ФОРМАТ ПОСТА:\n"
    prompt += "1. Начни с одного эмодзи (например: ⚽️, 📰, 📊, 🏟, 💰).\n"
    prompt += "2. Напиши 2-3 абзаца с сутью новости.\n"
    prompt += f"3. В конце добавь ссылку на источник: <a href='{news_link}'>Источник</a>\n"
    prompt += "4. И сразу под источником добавь ссылку на наш канал: <a href='https://t.me/newsbarca4'>@newsbarca4</a>\n\n"
    prompt += "ПРИМЕР:\n"
    prompt += "🏟 «Метрополитано» станет проверкой для Флика: научилась ли команда побеждать разными способами.\n\n"
    prompt += f"<a href='{news_link}'>Источник</a>\n"
    prompt += "<a href='https://t.me/newsbarca4'>@newsbarca4</a>"
    
    # Список моделей
    models = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
    
    for model_name in models:
        print(f"Пробуем модель: {model_name}...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 503:
                print(f"Модель {model_name} перегружена. Ждем 10 секунд...")
                time.sleep(10)
                continue
                
            if response.status_code != 200:
                print(f"Ошибка API ({model_name}): {response.text}")
                continue
                
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
            
        except Exception as e:
            print(f"Ошибка при обращении к {model_name}: {e}")
            
    return None

def main():
    print("Начинаем проверку новостей...")
    
    sent_links = []
    if os.path.exists("sent_news.txt"):
        with open("sent_news.txt", "r", encoding="utf-8") as f:
            sent_links = [line.strip() for line in f.readlines()]

    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("Новостей не найдено.")
        return

    new_news_found = 0
    
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        
        if link in sent_links:
            continue
            
        print(f"Найдена НОВАЯ новость: {title}")
        
        post_text = generate_post_with_gemini(title, link)
        if post_text:
            send_to_telegram(post_text)
            print("Пост успешно отправлен!")
            
            with open("sent_news.txt", "a", encoding="utf-8") as f:
                f.write(link + "\n")
                
            new_news_found += 1
            
            if new_news_found >= 2:
                break
                
        time.sleep(2)

    if new_news_found == 0:
        print("Новых новостей нет. Все уже опубликованы.")

if __name__ == "__main__":
    main()
