from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.database import Database
from keyboards.inline import (
    get_role_keyboard, 
    get_customer_menu_keyboard_with_subscription, 
    get_model_menu_keyboard_with_subscription,
    get_viewer_menu_keyboard
)
from utils.texts import WELCOME_MESSAGE, CHOOSE_ROLE, CUSTOMER_MENU, MODEL_MENU, VIEWER_MENU

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: Database):
    user = await db.get_user(message.from_user.id)
    
    # Проверяем, в процессе ли регистрации
    current_state = await state.get_state()
    if current_state and current_state.startswith("RegistrationStates"):
        await message.answer(
            "⚠️ Вы находитесь в процессе регистрации!\n\n"
            "Пожалуйста, завершите заполнение анкеты или отправьте /cancel для отмены."
        )
        return
    
    if not user:
        await message.answer(WELCOME_MESSAGE)
        await message.answer(CHOOSE_ROLE, reply_markup=get_role_keyboard())
    else:
        role = user['role']
        if role == 'customer':
            # Проверяем подписку заказчика
            has_subscription = await db.check_customer_subscription(message.from_user.id)
            await message.answer(
                CUSTOMER_MENU, 
                reply_markup=get_customer_menu_keyboard_with_subscription(has_subscription=has_subscription)
            )
        elif role == 'model':
            is_privileged = user.get('is_privileged', False)
            # Проверяем подписку модели
            sub_info = await db.get_subscription_info(message.from_user.id)
            await message.answer(
                MODEL_MENU, 
                reply_markup=get_model_menu_keyboard_with_subscription(
                    is_privileged=is_privileged,
                    has_subscription=sub_info['has_subscription']
                )
            )
        elif role == 'viewer':
            await message.answer(VIEWER_MENU, reply_markup=get_viewer_menu_keyboard())

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять.")
        return
    
    await state.clear()
    await message.answer("✅ Действие отменено. Отправьте /start для начала.")

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, db: Database):
    await callback.answer()
    user = await db.get_user(callback.from_user.id)
    
    if user:
        role = user['role']
        if role == 'customer':
            has_subscription = await db.check_customer_subscription(callback.from_user.id)
            await callback.message.edit_text(
                CUSTOMER_MENU, 
                reply_markup=get_customer_menu_keyboard_with_subscription(has_subscription=has_subscription)
            )
        elif role == 'model':
            is_privileged = user.get('is_privileged', False)
            sub_info = await db.get_subscription_info(callback.from_user.id)
            await callback.message.edit_text(
                MODEL_MENU, 
                reply_markup=get_model_menu_keyboard_with_subscription(
                    is_privileged=is_privileged,
                    has_subscription=sub_info['has_subscription']
                )
            )
        elif role == 'viewer':
            await callback.message.edit_text(VIEWER_MENU, reply_markup=get_viewer_menu_keyboard())

@router.callback_query(F.data == "change_role")
async def change_role(callback: CallbackQuery, db: Database, state: FSMContext):
    await callback.answer()
    
    # Удаляем пользователя из базы данных
    await db.delete_user(callback.from_user.id)
    
    # Очищаем state на всякий случай
    await state.clear()
    
    # Показываем выбор роли заново
    await callback.message.edit_text(
        "🔄 Вы решили сменить роль!\n\n" + CHOOSE_ROLE,
        reply_markup=get_role_keyboard()
    )

@router.callback_query(F.data == "my_rating")
async def show_my_rating(callback: CallbackQuery, db: Database):
    await callback.answer()
    
    # Пересчитываем рейтинг
    rating = await db.calculate_simple_rating(callback.from_user.id)
    await db.update_user(callback.from_user.id, rating=rating)
    
    # Получаем количество оценок
    ratings_count = await db.get_simple_ratings_count(callback.from_user.id)
    
    await callback.message.answer(
        f"⭐ Ваш рейтинг: {rating}/10.0\n"
        f"📊 Количество оценок: {ratings_count}"
    )