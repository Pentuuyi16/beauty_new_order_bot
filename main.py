import asyncio
import logging
import sys
from handlers.payments import router as payments_router
from pathlib import Path

# Добавляем папку bot в путь
sys.path.insert(0, str(Path(__file__).parent / "bot"))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from database.database import Database
from middlewares.registration_check import RegistrationCheckMiddleware

# Импортируем роутеры напрямую
from handlers.start import router as start_router
from handlers.registration import router as registration_router
from handlers.customer import router as customer_router
from handlers.model import router as model_router
from handlers.viewer import router as viewer_router
from handlers.admin import router as admin_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=Config.TELEGRAM_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Инициализация БД
    db = Database()
    await db.init_db()
    logger.info("База данных инициализирована")
    
    # Регистрация middleware
    dp.message.middleware(RegistrationCheckMiddleware(db))
    dp.callback_query.middleware(RegistrationCheckMiddleware(db))
    
    # Регистрация хендлеров
    dp.include_router(start_router)
    dp.include_router(registration_router)
    dp.include_router(customer_router)
    dp.include_router(model_router)
    dp.include_router(viewer_router)
    dp.include_router(admin_router)
    dp.include_router(payments_router)
    # Передача зависимостей
    dp['db'] = db
    
    # Запуск бота
    logger.info("Бот запущен")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())