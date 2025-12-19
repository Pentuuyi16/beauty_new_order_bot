import asyncio
import logging
import sys
from handlers.payments import router as payments_router
from pathlib import Path
import aiosqlite
from datetime import datetime

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

async def check_expired_subscriptions(db: Database):
    """Фоновая задача проверки истекших подписок"""
    while True:
        try:
            async with aiosqlite.connect(db.db_path) as conn:
                # Находим все истекшие подписки
                async with conn.execute("""
                    SELECT user_id, role FROM subscriptions 
                    WHERE is_active = 1 AND end_date < ?
                """, (datetime.now().isoformat(),)) as cursor:
                    expired = await cursor.fetchall()
                
                for user_id, role in expired:
                    # Деактивируем подписку
                    await conn.execute("""
                        UPDATE subscriptions 
                        SET is_active = 0 
                        WHERE user_id = ? AND role = ? AND end_date < ?
                    """, (user_id, role, datetime.now().isoformat()))
                    
                    # Если это модель - убираем привилегии
                    if role == "model":
                        await db.update_user(user_id, is_privileged=False)
                    
                    logger.info(f"Подписка истекла для user_id={user_id}, role={role}")
                
                await conn.commit()
        except Exception as e:
            logger.error(f"Ошибка проверки подписок: {e}")
        
        # Проверяем каждые 24 часа (86400 секунд)
        await asyncio.sleep(86400)

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=Config.TELEGRAM_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Инициализация БД
    db = Database()
    await db.init_db()
    await db.migrate_subscriptions_add_role()
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
    
    # Запускаем фоновую проверку подписок
    asyncio.create_task(check_expired_subscriptions(db))
    logger.info("Запущена фоновая проверка подписок (каждые 24 часа)")
    
    # Запуск бота
    logger.info("Бот запущен")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())