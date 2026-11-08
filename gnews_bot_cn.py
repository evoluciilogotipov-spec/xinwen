import os
import feedparser
import requests
import time

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

RSS_URLS = [
    "https://www.sports.ru/rss/barcelona.xml",        # Sports.ru (нормальные новости)
    "https://www.championat.com/rss/football.xml",    # Championat (нормальные новости)
    "https://news.google.com/rss/search?q=%D0%91%D0%B0%D1%80%D1%81%D0%B5%D0%BB%D0%BE%D0%BD%D0%B0&hl=ru&gl=RU&ceid=RU:ru" # Google
]

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Ошибка Телеграм: {e}")

def ask_gemini(prompt):
    models = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            response = requests.post(url, headers={'Content-Type': 'application/json'}, json=data)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            elif response.status_code == 503:
                time.sleep(10)
        except Exception as e:
            print(f"Ошибка {model_name}: {e}")
    return None

def is_duplicate(news_title, past_titles):
    if not past_titles:
        return False
        
    prompt = "Ты — редактор новостного канала. Твоя задача — не допускать повторов.\n"
    prompt += f"Вот заголовок новой новости: '{news_title}'\n\n"
    prompt += "Вот список заголовков, которые я УЖЕ публиковал ранее:\n"
    for t in past_titles:
        prompt += f"- {t}\n"
    prompt += "\nВопрос: эта новая новость описывает ТО ЖЕ САМОЕ событие, что и одна из старых? (Даже если слова другие, но суть та же — например, 'продажа Фермина за 120 млн').\n"
    prompt += "Ответь строго ОДНИМ словом: ДА или НЕТ."
    
    answer = ask_gemini(prompt)
    if answer and "ДА" in answer.upper():
        return True
    return False

def generate_post_with_gemini(news_title, news_link):
    prompt = "Ты — спортивный аналитик и редактор Telegram-канала о ФК «Барселона».\n"
    prompt += f"Напиши пост на основе этой новости: {news_title}\n\n"
    prompt += "ТВОЙ СТИЛЬ:\n- Пиши строго, фактологически, с цифрами.\n- Никаких лишних эмоций.\n\n"
    prompt += "ФОРМАТ:\n1. Один эмодзи в начале.\n2. 2-3 абзаца.\n"
    prompt += f"3. Ссылка на источник: <a href='{news_link}'>Источник</a>\n"
    prompt += "4. Ссылка на канал: <a href='https://t.me/newsbarca4'>@newsbarca4</a>\n"
    return ask_gemini(prompt)

def main():
    print("Начинаем проверку...")
    
    # 1. Читаем память (заголовки)
    past_titles = []
    if os.path.exists("sent_titles.txt"):
        with open("sent_titles.txt", "r", encoding="utf-8") as f:
            past_titles = [line.strip() for line in f.readlines() if line.strip()]

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
            
            # --- ФИЛЬТР GOOGLE: если новость ведет на Euro-Football, пропускаем ---
            if "euro-football.ru" in link:
                print(f"Игнорируем Euro-Football (спам): {title}")
                continue
            # --------------------------------------------------------------------
            
            # 2. Спрашиваем нейросеть: это дубль?
            if is_duplicate(title, past_titles):
                print(f"ИИ сказал, что это дубль: {title}")
                continue
                
            print(f"НОВАЯ новость: {title}")
            post_text = generate_post_with_gemini(title, link)
            
            if post_text:
                send_to_telegram(post_text)
                print("Пост отправлен!")
                
                # 3. Сохраняем заголовок
                with open("sent_titles.txt", "a", encoding="utf-8") as f:
                    f.write(title + "\n")
                    
                total_new_news += 1
                news_from_this_source += 1
        
        time.sleep(2)

    if total_new_news == 0:
        print("Новых новостей нет.")

if __name__ == "__main__":
    main()
