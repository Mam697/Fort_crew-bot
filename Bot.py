import time
import cloudscraper
from bs4 import BeautifulSoup

# ==================== НАСТРОЙКИ ====================
TELEGRAM_TOKEN = "8487889885:AAFJlgyXetNj_o067dWGseWIeqcXt0Y0eVM"
CHAT_ID = "1220067520"
MAX_PRICE = 250  # Твой лимит по цене

# Ссылка на раздел
FUNPAY_URL = "https://funpay.com/lots/1208/" 
# ====================================================

seen_deals = set()

# Создаем скрейпер для обхода защиты
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        scraper.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Ошибка отправки в Telegram: {e}")

def check_funpay():
    try:
        response = scraper.get(FUNPAY_URL, timeout=15)
        
        if response.status_code != 200:
            print(f"⚠️ FunPay ответил с кодом: {response.status_code}")
            return 0

        soup = BeautifulSoup(response.text, 'html.parser')
        lots = soup.select('.tc-item')
        found_count = 0

        for lot in lots:
            title_elem = lot.select_one('.tc-desc-text')
            price_elem = lot.select_one('.tc-price div')
            link_elem = lot.get('href')

            if not title_elem or not price_elem:
                continue

            title = title_elem.text.strip()
            title_lower = title.lower()
            
            # Ищем нужные слова
            if any(word in title_lower for word in ["отряд", "crew"]):
                price_text = price_elem.text.strip().replace(' ', '').replace('₽', '')
                try:
                    price = float(price_text)
                except ValueError:
                    continue

                if price <= MAX_PRICE:
                    found_count += 1
                    deal_id = link_elem
                    
                    if deal_id not in seen_deals:
                        seen_deals.add(deal_id)
                        message = (
                            f"🔥 [FunPay] Найден Отряд Fortnite до {MAX_PRICE} ₽!\n\n"
                            f"📌 Название: {title}\n"
                            f"💰 Цена: {price} ₽\n"
                            f"🔗 Ссылка: {link_elem}"
                        )
                        send_telegram_message(message)
                        print(f"✅ Найдено выгодное предложение: {price} ₽")

        return found_count

    except Exception as e:
        print(f"⚠️ Ошибка подключения: {e}")
        return 0

print("🚀 Бот запущен в облаке!")
send_telegram_message(f"🤖 Бот запущен на сервере! Ищем Отряды до {MAX_PRICE} ₽...")

while True:
    fp_found = check_funpay()
    current_time = time.strftime("%H:%M:%S")
    print(f"[{current_time}] Проверка выполнена. Найдено: {fp_found}")
    time.sleep(30)
