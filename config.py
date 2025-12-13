import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('CHAT_ID')
    ADMIN_IDS = [123456789]  # Список ID администраторов
    
    # ЮKassa
    YUKASSA_SHOP_ID = os.getenv('YUKASSA_SHOP_ID')
    YUKASSA_API_KEY = os.getenv('YUKASSA_API_KEY')
    
    # Подписки
    MODEL_SUBSCRIPTION_PRICE = 100  # Цена подписки модели в рублях
    MODEL_SUBSCRIPTION_DAYS = 30  # Длительность подписки модели
    
    CUSTOMER_SUBSCRIPTION_PRICE = 500  # Цена подписки заказчика в рублях
    CUSTOMER_SUBSCRIPTION_DAYS = 30  # Длительность подписки заказчика
    
    # Лимиты
    MAX_APPLICATIONS_PER_MODEL = 1  # Для привилегированных моделей за 48 часов
    MAX_RESPONSES_MULTIPLIER = 2  # Заказчик получает в 2 раза больше откликов
    
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
    
    # Подкатегории
    SERVICE_SUBCATEGORIES = [
        "Практика",
        "Обучение",
        "Контент-съёмка",
        "Коммерческая работа"
    ]
    
    # Типы участия
    PARTICIPATION_TYPES = [
        "Бесплатно",
        "Оплачиваемо",
        "Бартер",
        "Обучение"
    ]