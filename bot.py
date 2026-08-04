cat << 'EOF' > bot.py
import time
import threading
import cloudscraper
from bs4 import BeautifulSoup
import telebot
from telebot import types

# ==================== НАСТРОЙКИ ====================
TELEGRAM_TOKEN = "8487889885:AAFJlgyXetNj_o067dWGseWIeqcXt0Y0eVM"
CHAT_ID = "1220067520"
MAX_PRICE = 250
FUNPAY_URL = "https://funpay.com/lots/1208/"
CHECK_INTERVAL = 30  # Проверка каждые 30 секунд
# ====================================================

bot = telebot.TeleBot(TELEGRAM_TOKEN)
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

seen_deals = set()

def get_funpay_lots():
    """Сканирует FunPay и возвращает список всех подходящих лотов"""
    try:
        response = scraper.get(FUNPAY_URL, timeout=15)
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        lots = soup.select('.tc-item')
        results = []

        for lot in lots:
            title_elem = lot.select_one('.tc-desc-text')
            price_elem = lot.select_one('.tc-price div')
            link = lot.get('href')

            if title_elem and price_elem:
                title = title_elem.text.strip()
                if any(word in title.lower() for word in ["отряд", "crew"]):
                    price_text = price_elem.text.strip().replace(' ', '').replace('₽', '')
                    try:
                        price = float(price_text)
                        results.append({'title': title, 'price': price, 'link': link})
                    except ValueError:
                        continue
        return results
    except Exception as e:
        print(f"⚠️ Ошибка парсинга: {e}")
        return []

def auto_check_loop():
    """Фоновый поток для авто-поиска выгодных цен"""
    while True:
        try:
            lots = get_funpay_lots()
            for lot in lots:
                if lot['price'] <= MAX_PRICE and lot['link'] not in seen_deals:
                    seen_deals.add(lot['link'])
                    msg = (
                        f"🔥 [FunPay] Найден Отряд Fortnite до {MAX_PRICE} ₽!\n\n"
                        f"📌 Название: {lot['title']}\n"
                        f"💰 Цена: {lot['price']} ₽\n"
                        f"🔗 [Ссылка на лот]({lot['link']})"
                    )
                    bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                    print(f"✅ Найдено выгодное предложение: {lot['price']} ₽")
        except Exception as e:
            print(f"⚠️ Ошибка в фоновом потоке: {e}")
        time.sleep(CHECK_INTERVAL)

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("🔍 Проверить обстановку")
    markup.add(btn)
    return markup

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(
        message.chat.id, 
        "🤖 Бот запущен!\n\n"
        "1. Я в фоновом режиме ищу Отряды до 250 ₽ и сразу пришлю уведомление.\n"
        "2. Нажимай кнопку ниже в любой момент, чтобы увидеть топ-5 текущих цен.", 
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "🔍 Проверить обстановку")
def check_status(message):
    bot.send_message(message.chat.id, "⏳ Сканирую FunPay, секунду...")
    lots = get_funpay_lots()
    
    if not lots:
        bot.send_message(message.chat.id, "❌ Не удалось получить предложения или список пуст.")
        return

    top_lots = lots[:5]
    text = "📊 Текущая обстановка на FunPay (топ-5 лотов):\n\n"
    
    for idx, lot in enumerate(top_lots, 1):
        text += f"{idx}. {lot['price']} ₽ — {lot['title']}\n🔗 {lot['link']}\n\n"
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

if name == "main":
    print("🚀 Бот запущен (работает и авто-поиск, и кнопка)!")
    # Запуск авто-проверки в отдельном потоке
    threading.Thread(target=auto_check_loop, daemon=True).start()
    bot.infinity_polling()
EOF
