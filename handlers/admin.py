from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database.database import Database
from config import Config

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: Message, db: Database):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("⚠️ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "🔧 Админ-панель\n\n"
        "Доступные команды:\n"
        "/stats - Статистика\n"
        "/privileged <user_id> - Выдать привилегии модели\n"
        "/unprivileged <user_id> - Забрать привилегии\n"
        "/block <user_id> - Заблокировать пользователя\n"
        "/unblock <user_id> - Разблокировать пользователя"
    )

@router.message(Command("stats"))
async def show_stats(message: Message, db: Database):
    if message.from_user.id not in Config.ADMIN_IDS:
        return
    
    # Собираем статистику
    async with db.db_path as conn:
        async with conn.execute("SELECT COUNT(*) FROM users WHERE role = 'customer'") as cursor:
            customers = (await cursor.fetchone())[0]
        
        async with conn.execute("SELECT COUNT(*) FROM users WHERE role = 'model'") as cursor:
            models = (await cursor.fetchone())[0]
        
        async with conn.execute("SELECT COUNT(*) FROM users WHERE role = 'viewer'") as cursor:
            viewers = (await cursor.fetchone())[0]
        
        async with conn.execute("SELECT COUNT(*) FROM applications") as cursor:
            applications = (await cursor.fetchone())[0]
        
        async with conn.execute("SELECT COUNT(*) FROM model_applications") as cursor:
            model_apps = (await cursor.fetchone())[0]
        
        async with conn.execute("SELECT COUNT(*) FROM responses") as cursor:
            responses = (await cursor.fetchone())[0]
    
    stats_text = f"""
📊 Статистика платформы

👥 Пользователи:
  • Заказчики: {customers}
  • Модели: {models}
  • Зрители: {viewers}

📋 Заявки:
  • От заказчиков: {applications}
  • От моделей: {model_apps}

📩 Отклики: {responses}
    """
    
    await message.answer(stats_text)

@router.message(Command("privileged"))
async def set_privileged(message: Message, db: Database):
    if message.from_user.id not in Config.ADMIN_IDS:
        return
    
    try:
        user_id = int(message.text.split()[1])
        await db.set_privileged(user_id, True)
        await message.answer(f"✅ Пользователь {user_id} получил привилегии.")
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /privileged <user_id>")

@router.message(Command("unprivileged"))
async def unset_privileged(message: Message, db: Database):
    if message.from_user.id not in Config.ADMIN_IDS:
        return
    
    try:
        user_id = int(message.text.split()[1])
        await db.set_privileged(user_id, False)
        await message.answer(f"✅ У пользователя {user_id} забраны привилегии.")
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /unprivileged <user_id>")

@router.message(Command("block"))
async def block_user(message: Message, db: Database):
    if message.from_user.id not in Config.ADMIN_IDS:
        return
    
    try:
        user_id = int(message.text.split()[1])
        await db.block_user(user_id)
        await message.answer(f"✅ Пользователь {user_id} заблокирован.")
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /block <user_id>")

@router.message(Command("unblock"))
async def unblock_user(message: Message, db: Database):
    if message.from_user.id not in Config.ADMIN_IDS:
        return
    
    try:
        user_id = int(message.text.split()[1])
        await db.unblock_user(user_id)
        await message.answer(f"✅ Пользователь {user_id} разблокирован.")
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /unblock <user_id>")