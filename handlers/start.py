from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.database import Database
from keyboards.inline import (
    get_role_keyboard, 
    get_customer_menu_keyboard_with_subscription, 
    get_model_menu_keyboard_with_subscription,
    get_viewer_menu_keyboard,
    get_role_change_keyboard,
    get_back_keyboard
)
from utils.texts import WELCOME_MESSAGE, CHOOSE_ROLE, CUSTOMER_MENU, MODEL_MENU, VIEWER_MENU
from utils.states import RegistrationStates

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

@router.callback_query(F.data == "show_my_role")
async def show_my_role(callback: CallbackQuery, db: Database):
    """Показать текущую роль пользователя"""
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    
    if not user:
        await callback.message.answer("⚠️ Вы не зарегистрированы. Отправьте /start")
        return
    
    role = user['role']
    role_names = {
        'viewer': '👀 Зритель',
        'customer': '🧑‍💼 Заказчик',
        'model': '💃 Модель'
    }
    
    role_descriptions = {
        'viewer': 'Вы можете просматривать заявки в канале',
        'customer': 'Вы можете создавать заявки на поиск моделей',
        'model': 'Вы можете откликаться на заявки заказчиков'
    }
    
    await callback.message.answer(
        f"👤 Ваша текущая роль:\n\n"
        f"{role_names.get(role, role)}\n\n"
        f"📝 {role_descriptions.get(role, '')}"
    )

@router.callback_query(F.data == "change_role")
async def change_role(callback: CallbackQuery, db: Database, state: FSMContext):
    """Начать процесс смены роли"""
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    
    if not user:
        await callback.message.answer("⚠️ Вы не зарегистрированы. Отправьте /start")
        return
    
    current_role = user['role']
    role_names = {
        'viewer': '👀 Зритель',
        'customer': '🧑‍💼 Заказчик',
        'model': '💃 Модель'
    }
    
    await callback.message.edit_text(
        f"🔄 Смена роли\n\n"
        f"Ваша текущая роль: {role_names.get(current_role, current_role)}\n\n"
        f"На какую роль вы хотите поменять?",
        reply_markup=get_role_change_keyboard(current_role)
    )

@router.callback_query(F.data == "cancel_role_change")
async def cancel_role_change(callback: CallbackQuery, db: Database):
    """Отмена смены роли"""
    await callback.answer("Смена роли отменена")
    
    user = await db.get_user(callback.from_user.id)
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

@router.callback_query(F.data.startswith("change_to_"))
async def process_role_change(callback: CallbackQuery, db: Database, state: FSMContext):
    """Обработка смены роли"""
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    current_role = user['role']
    new_role = callback.data.replace("change_to_", "")
    
    # Проверка на ту же роль
    if current_role == new_role:
        role_names = {
            'viewer': 'зрителем',
            'customer': 'заказчиком',
            'model': 'моделью'
        }
        await callback.message.edit_text(
            f"ℹ️ Вы итак уже {role_names.get(new_role, new_role)}!",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Удаляем только данные пользователя (подписки остаются)
    await db.delete_user_keep_subscription(callback.from_user.id)
    await state.clear()
    
    # Запускаем регистрацию для новой роли
    if new_role == "viewer":
        await db.add_user(callback.from_user.id, callback.from_user.username, "viewer")
        
        await callback.message.edit_text(
            f"✅ Вы успешно сменили роль на зрителя!\n\n"
            f"Перейдите в канал для просмотра заявок:\n"
            f"https://t.me/model_cheby\n\n"
            f"💡 Если вас заинтересует тематика, вы всегда можете сменить роль на модель или заказчика!",
            reply_markup=get_viewer_menu_keyboard()
        )
    elif new_role == "customer":
        await state.update_data(role="customer")
        await state.set_state(RegistrationStates.customer_full_name)
        
        # Проверяем подписку ЗАКАЗЧИКА
        has_subscription = await db.check_customer_subscription(callback.from_user.id)
        subscription_text = ""
        if has_subscription:
            sub_info = await db.get_customer_subscription_info(callback.from_user.id)
            subscription_text = f"\n\n💎 Отлично! У вас есть активная подписка заказчика до {sub_info['end_date']}!"
        
        await callback.message.edit_text(
            "🔄 Вы меняете роль на заказчика!\n\n" +
            "📝 Начинаем регистрацию заказчика.\n\n"
            "⚠️ ВНИМАНИЕ:\n"
            "Для размещения заявок необходима подписка - 500 руб/месяц" +
            subscription_text + "\n\n"
            "Что вы получите:\n"
            "✨ Неограниченное количество заявок\n"
            "✨ Отклики от моделей\n"
            "✨ Управление набором моделей\n"
            "✨ Просмотр рейтингов моделей\n\n"
            "Введите ваше ФИО:"
        )
    elif new_role == "model":
        await state.update_data(role="model")
        await state.set_state(RegistrationStates.model_full_name)
        
        # Проверяем подписку МОДЕЛИ
        sub_info = await db.get_subscription_info(callback.from_user.id)
        subscription_text = ""
        if sub_info['has_subscription']:
            subscription_text = f"\n\n💎 Отлично! У вас есть активная подписка модели до {sub_info['end_date']}!"
        
        await callback.message.edit_text(
            "🔄 Вы меняете роль на модель!\n\n" +
            "📝 Начинаем регистрацию модели.\n\n"
            "💡 Обратите внимание:\n"
            "Обычные модели могут откликаться на заявки заказчиков (бесплатно).\n\n"
            "💎 Привилегированные модели (100 руб/месяц) дополнительно могут:\n"
            "   • Создавать свои заявки \"Хочу быть моделью\"\n"
            "   • Получать отклики от заказчиков\n"
            "   • Иметь приоритет в поиске" +
            subscription_text + "\n\n"
            "Введите ваше ФИО:"
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