import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')
    CHAT_LINK = "https://t.me/model_cheby"  # Добавили ссылку на чат
    ADMIN_IDS = [123456789]
    
    # ЮKassa
    YUKASSA_SHOP_ID = os.getenv('YUKASSA_SHOP_ID')
    YUKASSA_API_KEY = os.getenv('YUKASSA_API_KEY')
    
    # Подписки
    MODEL_SUBSCRIPTION_PRICE = 100
    MODEL_SUBSCRIPTION_DAYS = 30
    
    CUSTOMER_SUBSCRIPTION_PRICE = 500
    CUSTOMER_SUBSCRIPTION_DAYS = 30
    
    # Лимиты
    MAX_APPLICATIONS_PER_MODEL = 1
    MAX_RESPONSES_MULTIPLIER = 2
    
    # Категории услуг
    SERVICE_CATEGORIES = [
        "Брови",
        "Ресницы", 
        "Депиляция",
        "Шугаринг",
        "Макияж",
        "Маникюр",
        "Педикюр",
        "Косметология",
        "Массаж",
        "Другое"
    ]
    
    SERVICE_SUBCATEGORIES = [
        "Практика",
        "Обучение",
        "Контент-съёмка",
        "Коммерческая работа"
    ]
    
    PARTICIPATION_TYPES = [
        "Бесплатно",
        "Оплачиваемо",
        "Бартер",
        "Обучение"
    ]