from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import uuid
from yookassa import Configuration, Payment

from database.database import Database
from keyboards.inline import (
    get_model_menu_keyboard_with_subscription,
    get_customer_menu_keyboard_with_subscription,
    get_payment_keyboard,
    get_customer_payment_keyboard,
    get_subscription_keyboard,
    get_customer_subscription_keyboard,
    get_back_keyboard
)
from config import Config

router = Router()

# Настройка ЮKassa
Configuration.account_id = Config.YUKASSA_SHOP_ID
Configuration.secret_key = Config.YUKASSA_API_KEY

# ============== ПОКУПКА ПОДПИСКИ МОДЕЛИ ==============

@router.callback_query(F.data == "buy_subscription")
async def process_buy_subscription(callback: CallbackQuery, db: Database):
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    
    if not user or user['role'] != 'model':
        await callback.answer("⚠️ Подписка доступна только для моделей!", show_alert=True)
        return
    
    # Проверяем текущую подписку
    sub_info = await db.get_subscription_info(callback.from_user.id)
    
    if sub_info['has_subscription']:
        await callback.message.edit_text(
            f"✅ У вас уже есть активная подписка!\n\n"
            f"📅 Действует до: {sub_info['end_date']}\n"
            f"⏰ Осталось дней: {sub_info['days_left']}",
            reply_markup=get_back_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "💎 Привилегированная подписка\n\n"
        f"💰 Стоимость: {Config.MODEL_SUBSCRIPTION_PRICE} руб/месяц\n"
        f"⏰ Длительность: {Config.MODEL_SUBSCRIPTION_DAYS} дней\n\n"
        "✨ Что вы получите:\n"
        "• Возможность создавать свои заявки 'Хочу быть моделью'\n"
        "• Заказчики смогут откликаться на ваши заявки\n"
        "• Увеличение видимости вашего профиля\n"
        "• Приоритетное размещение в канале\n\n"
        "Нажмите кнопку ниже для оплаты:",
        reply_markup=get_payment_keyboard()
    )

@router.callback_query(F.data == "proceed_payment")
async def proceed_payment(callback: CallbackQuery, bot: Bot, db: Database):
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    
    try:
        # Создаем уникальный идентификатор платежа
        idempotence_key = str(uuid.uuid4())
        
        # Создаем платеж через ЮKassa
        payment = Payment.create({
            "amount": {
                "value": f"{Config.MODEL_SUBSCRIPTION_PRICE}.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/{(await bot.get_me()).username}"
            },
            "capture": True,
            "description": f"Привилегированная подписка на {Config.MODEL_SUBSCRIPTION_DAYS} дней",
            "metadata": {
                "user_id": callback.from_user.id,
                "username": callback.from_user.username or "unknown",
                "subscription_type": "model"
            }
        }, idempotence_key)
        
        # Получаем ссылку для оплаты
        payment_url = payment.confirmation.confirmation_url
        
        # Отправляем ссылку пользователю
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="💳 Перейти к оплате", url=payment_url)
        builder.button(text="🔄 Проверить оплату", callback_data=f"check_payment_{payment.id}")
        builder.button(text="🔙 Назад", callback_data="back_to_menu")
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"💳 Счет на оплату создан!\n\n"
            f"💰 Сумма: {Config.MODEL_SUBSCRIPTION_PRICE} руб\n"
            f"📝 ID платежа: {payment.id}\n\n"
            f"Нажмите кнопку ниже для перехода к оплате.\n"
            f"После оплаты нажмите 'Проверить оплату'.",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка создания платежа: {e}\n\n"
            f"Попробуйте позже или свяжитесь с администратором.",
            reply_markup=get_back_keyboard()
        )

@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment(callback: CallbackQuery, db: Database):
    await callback.answer("🔄 Проверяем статус платежа...")
    
    payment_id = callback.data.split("_")[2]
    
    try:
        # Получаем информацию о платеже
        payment = Payment.find_one(payment_id)
        
        if payment.status == "succeeded":
            # Платеж успешен - активируем подписку
            await db.add_subscription(
                user_id=callback.from_user.id,
                days=Config.MODEL_SUBSCRIPTION_DAYS,
                payment_id=payment_id
            )
            
            user = await db.get_user(callback.from_user.id)
            
            await callback.message.edit_text(
                "✅ Оплата успешно завершена!\n\n"
                "🎉 Подписка активирована!\n"
                f"📅 Действует до: {(await db.get_subscription_info(callback.from_user.id))['end_date']}\n\n"
                "Теперь вам доступна функция 'Хочу быть моделью'!\n"
                "Вы можете создавать свои заявки, на которые будут откликаться заказчики.",
                reply_markup=get_model_menu_keyboard_with_subscription(
                    is_privileged=True,
                    has_subscription=True
                )
            )
            
        elif payment.status == "pending":
            await callback.answer("⏳ Платеж в обработке. Попробуйте проверить позже.", show_alert=True)
            
        elif payment.status == "canceled":
            await callback.message.edit_text(
                "❌ Платеж отменен.\n\n"
                "Попробуйте оформить подписку снова.",
                reply_markup=get_back_keyboard()
            )
        else:
            await callback.answer(f"⚠️ Статус платежа: {payment.status}", show_alert=True)
            
    except Exception as e:
        await callback.answer(f"❌ Ошибка проверки платежа: {e}", show_alert=True)

@router.callback_query(F.data == "subscription_info")
async def subscription_info(callback: CallbackQuery, db: Database):
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    sub_info = await db.get_subscription_info(callback.from_user.id)
    
    if sub_info['has_subscription']:
        text = (
            "💎 Ваша привилегированная подписка\n\n"
            f"✅ Статус: Активна\n"
            f"📅 Действует до: {sub_info['end_date']}\n"
            f"⏰ Осталось дней: {sub_info['days_left']}\n\n"
            "🎁 Ваши привилегии:\n"
            "• Создание заявок 'Хочу быть моделью'\n"
            "• Получение откликов от заказчиков\n"
            "• Приоритетное размещение в канале\n"
            "• Увеличенная видимость профиля\n\n"
            "Спасибо, что с нами! ❤️"
        )
    else:
        text = (
            "⚠️ У вас нет активной подписки\n\n"
            "Оформите привилегированную подписку, чтобы получить:\n"
            "• Возможность создавать свои заявки\n"
            "• Отклики от заказчиков\n"
            "• Приоритет в поиске\n\n"
            f"Стоимость: всего {Config.MODEL_SUBSCRIPTION_PRICE} руб/месяц"
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_subscription_keyboard()
    )

# ============== ПОКУПКА ПОДПИСКИ ЗАКАЗЧИКА ==============

@router.callback_query(F.data == "buy_customer_subscription")
async def process_buy_customer_subscription(callback: CallbackQuery, db: Database):
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    
    if not user or user['role'] != 'customer':
        await callback.answer("⚠️ Эта подписка доступна только для заказчиков!", show_alert=True)
        return
    
    # Проверяем текущую подписку
    has_subscription = await db.check_customer_subscription(callback.from_user.id)
    
    if has_subscription:
        sub_info = await db.get_customer_subscription_info(callback.from_user.id)
        await callback.message.edit_text(
            f"✅ У вас уже есть активная подписка!\n\n"
            f"📅 Действует до: {sub_info['end_date']}\n"
            f"⏰ Осталось дней: {sub_info['days_left']}",
            reply_markup=get_back_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "💼 Подписка заказчика\n\n"
        f"💰 Стоимость: {Config.CUSTOMER_SUBSCRIPTION_PRICE} руб/месяц\n"
        f"⏰ Длительность: {Config.CUSTOMER_SUBSCRIPTION_DAYS} дней\n\n"
        "✨ Что вы получите:\n"
        "• Неограниченное количество заявок\n"
        "• Отклики от моделей\n"
        "• Управление набором моделей\n"
        "• Просмотр рейтингов моделей\n"
        "• Приоритетная поддержка\n\n"
        "Нажмите кнопку ниже для оплаты:",
        reply_markup=get_customer_payment_keyboard()
    )

@router.callback_query(F.data == "proceed_customer_payment")
async def proceed_customer_payment(callback: CallbackQuery, bot: Bot, db: Database):
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    
    try:
        # Создаем уникальный идентификатор платежа
        idempotence_key = str(uuid.uuid4())
        
        # Создаем платеж через ЮKassa
        payment = Payment.create({
            "amount": {
                "value": f"{Config.CUSTOMER_SUBSCRIPTION_PRICE}.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/{(await bot.get_me()).username}"
            },
            "capture": True,
            "description": f"Подписка заказчика на {Config.CUSTOMER_SUBSCRIPTION_DAYS} дней",
            "metadata": {
                "user_id": callback.from_user.id,
                "username": callback.from_user.username or "unknown",
                "subscription_type": "customer"
            }
        }, idempotence_key)
        
        # Получаем ссылку для оплаты
        payment_url = payment.confirmation.confirmation_url
        
        # Отправляем ссылку пользователю
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="💳 Перейти к оплате", url=payment_url)
        builder.button(text="🔄 Проверить оплату", callback_data=f"check_customer_payment_{payment.id}")
        builder.button(text="🔙 Назад", callback_data="back_to_menu")
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"💳 Счет на оплату создан!\n\n"
            f"💰 Сумма: {Config.CUSTOMER_SUBSCRIPTION_PRICE} руб\n"
            f"📝 ID платежа: {payment.id}\n\n"
            f"Нажмите кнопку ниже для перехода к оплате.\n"
            f"После оплаты нажмите 'Проверить оплату'.",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка создания платежа: {e}\n\n"
            f"Попробуйте позже или свяжитесь с администратором.",
            reply_markup=get_back_keyboard()
        )

@router.callback_query(F.data.startswith("check_customer_payment_"))
async def check_customer_payment(callback: CallbackQuery, db: Database):
    await callback.answer("🔄 Проверяем статус платежа...")
    
    payment_id = callback.data.split("_")[3]
    
    try:
        # Получаем информацию о платеже
        payment = Payment.find_one(payment_id)
        
        if payment.status == "succeeded":
            # Платеж успешен - активируем подписку
            await db.add_subscription(
                user_id=callback.from_user.id,
                days=Config.CUSTOMER_SUBSCRIPTION_DAYS,
                payment_id=payment_id
            )
            
            user = await db.get_user(callback.from_user.id)
            
            await callback.message.edit_text(
                "✅ Оплата успешно завершена!\n\n"
                "🎉 Подписка активирована!\n"
                f"📅 Действует до: {(await db.get_customer_subscription_info(callback.from_user.id))['end_date']}\n\n"
                "Теперь вы можете создавать заявки на поиск моделей!",
                reply_markup=get_customer_menu_keyboard_with_subscription(has_subscription=True)
            )
            
        elif payment.status == "pending":
            await callback.answer("⏳ Платеж в обработке. Попробуйте проверить позже.", show_alert=True)
            
        elif payment.status == "canceled":
            await callback.message.edit_text(
                "❌ Платеж отменен.\n\n"
                "Попробуйте оформить подписку снова.",
                reply_markup=get_back_keyboard()
            )
        else:
            await callback.answer(f"⚠️ Статус платежа: {payment.status}", show_alert=True)
            
    except Exception as e:
        await callback.answer(f"❌ Ошибка проверки платежа: {e}", show_alert=True)

@router.callback_query(F.data == "customer_subscription_info")
async def customer_subscription_info(callback: CallbackQuery, db: Database):
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    sub_info = await db.get_customer_subscription_info(callback.from_user.id)
    
    if sub_info['has_subscription']:
        text = (
            "💼 Ваша подписка заказчика\n\n"
            f"✅ Статус: Активна\n"
            f"📅 Действует до: {sub_info['end_date']}\n"
            f"⏰ Осталось дней: {sub_info['days_left']}\n\n"
            "🎁 Ваши возможности:\n"
            "• Неограниченное количество заявок\n"
            "• Отклики от моделей\n"
            "• Управление набором моделей\n"
            "• Просмотр рейтингов моделей\n"
            "• Приоритетная поддержка\n\n"
            "Спасибо, что с нами! ❤️"
        )
    else:
        text = (
            "⚠️ У вас нет активной подписки\n\n"
            "Оформите подписку, чтобы получить:\n"
            "• Возможность создавать заявки\n"
            "• Отклики от моделей\n"
            "• Управление набором\n\n"
            f"Стоимость: {Config.CUSTOMER_SUBSCRIPTION_PRICE} руб/месяц"
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_customer_subscription_keyboard()
    )