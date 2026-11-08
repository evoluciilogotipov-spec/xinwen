import os
import feedparser
import requests
import time
import re

# Секреты из GitHub
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Список новостных лент
RSS_URLS = [
    "https://www.sports.ru/rss/barcelona.xml",
    "https://www.championat.com/rss/football.xml",
    "https://www.euro-football.ru/team/barselona/rss",
    "https://news.google.com/rss/search?q=%D0%91%D0%B0%D1%80%D1%81%D0%B5%D0%BB%D0%BE%D0%BD%D0%B0&hl=ru&gl=RU&ceid=RU:ru"
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
            print(f"Ошибка отправки в Телеграм: {response.text}")
    except Exception as e:
        print(f"Ошибка соединения с Телеграм: {e}")

def generate_post_with_gemini(news_title, news_link):
    print(f"Генерируем пост для новости: {news_title}")
    
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

# Храним память прямо в коде (список строк)
MEMORY = []

def get_keywords(text):
    sums = re.findall(r'\d+[\.,]?\d*\s*(?:млн|млрд|миллион|миллиард)', text.lower())
    names = re.findall(r'\b[А-ЯA-Z][а-яa-z]{3,}\b', text)
    return set(sums + names)

def main():
    print("Начинаем проверку...")
    
    # Ищем память в текущем файле
    global MEMORY
    try:
        with open(__file__, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"MEMORY = \[(.*?)\]", content, re.DOTALL)
            if match:
                # Восстанавливаем список из строки
                mem_str = match.group(1).strip()
                if mem_str:
                    MEMORY = eval(f"[{mem_str}]")
    except Exception as e:
        print(f"Ошибка чтения памяти: {e}")

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
                
            title = entry.title
            link = entry.link
            
            current_keywords = get_keywords(title)
            
            is_duplicate = False
            for past_kw in MEMORY:
                past_set = set(past_kw.split(','))
                if len(current_keywords.intersection(past_set)) >= 2:
                    is_duplicate = True
                    break
                    
            if is_duplicate:
                continue
                
            print(f"НОВАЯ новость: {title}")
            post_text = generate_post_with_gemini(title, link)
            
            if post_text:
                send_to_telegram(post_text)
                
                # Добавляем в память
                MEMORY.append(",".join(current_keywords))
                # Оставляем только последние 30 записей (чтобы код не разрастался)
                if len(MEMORY) > 30:
                    MEMORY = MEMORY[-30:]
                    
                total_new_news += 1
                news_from_this_source += 1
        
        time.sleep(2)

    # Сохраняем память обратно в код
    try:
        with open(__file__, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Формируем новую строку для MEMORY
        new_memory_str = ", ".join([f'"{k}"' for k in MEMORY])
        new_content = re.sub(r"MEMORY = \[(.*?)\]", f"MEMORY = [{new_memory_str}]", content, flags=re.DOTALL)
        
        with open(__file__, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        print(f"Ошибка сохранения памяти: {e}")

    if total_new_news == 0:
        print("Новых новостей нет.")

if __name__ == "__main__":
    main()
