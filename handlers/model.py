from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from database.database import Database
from utils.states import ModelApplicationStates
from keyboards.inline import *
from utils.texts import *
from config import Config

router = Router()

# ============== МЕНЮ МОДЕЛИ ==============

@router.callback_query(F.data == "my_responses")
async def show_my_responses(callback: CallbackQuery, db: Database):
    await callback.answer()
    
    responses = await db.get_model_responses(callback.from_user.id)
    
    if not responses:
        await callback.message.edit_text(
            "У вас пока нет откликов.",
            reply_markup=get_back_keyboard()
        )
        return
    
    text = "📋 Ваши отклики:\n\n"
    
    for resp in responses:
        app = await db.get_application(resp['application_id'])
        status_emoji = {
            'pending': '⏳',
            'accepted': '✅',
            'rejected': '❌'
        }
        emoji = status_emoji.get(resp['status'], '⏳')
        text += f"{emoji} {app['category']} - {app['date']} ({resp['status']})\n"
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard())

# ============== ОТКЛИК НА ЗАЯВКУ ЗАКАЗЧИКА ==============

@router.callback_query(F.data.startswith("respond_"))
async def respond_to_application(callback: CallbackQuery, db: Database, bot: Bot):
    app_id = int(callback.data.split("_")[1])
    
    # Проверяем роль
    user = await db.get_user(callback.from_user.id)
    if not user or user['role'] != 'model':
        await callback.answer("⚠️ Только модели могут откликаться на заявки!", show_alert=True)
        return
    
    # Проверяем заявку
    app = await db.get_application(app_id)
    if not app:
        await callback.answer("❌ Заявка не найдена.", show_alert=True)
        return
    
    if app['is_closed']:
        await callback.answer(APPLICATION_CLOSED, show_alert=True)
        return
    
    # Проверяем, не откликалась ли уже
    exists = await db.check_response_exists(app_id, callback.from_user.id)
    if exists:
        await callback.answer(RESPONSE_EXISTS, show_alert=True)
        return
    
    # Проверяем лимит откликов
    current_responses = await db.count_responses(app_id)
    max_responses = app['models_needed'] * Config.MAX_RESPONSES_MULTIPLIER
    
    if current_responses >= max_responses:
        await callback.answer("⚠️ Достигнут лимит откликов на эту заявку.", show_alert=True)
        return
    
    # Создаем отклик
    response_id = await db.add_response(app_id, callback.from_user.id)
    
    # Отправляем анкету модели заказчику
    model_profile = format_model_profile(user)
    
    try:
        await bot.send_message(
            chat_id=app['customer_id'],
            text=f"📩 Новый отклик на вашу заявку!\n\n{model_profile}",
            reply_markup=get_response_keyboard(response_id)
        )
        
        # ИСПРАВЛЕНИЕ 1: Всплывающее окно при отклике
        await callback.answer("✅ Вы откликнулись на заявку!", show_alert=True)
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка отправки: {e}", show_alert=True)

# ============== ПРИНЯТИЕ/ОТКЛОНЕНИЕ ОТКЛИКА ==============

@router.callback_query(F.data.startswith("accept_"))
async def accept_response(callback: CallbackQuery, db: Database, bot: Bot):
    await callback.answer()
    
    response_id = int(callback.data.split("_")[1])
    response = await db.get_response(response_id)
    
    if not response:
        await callback.message.answer("❌ Отклик не найден.")
        return
    
    # Обновляем статус
    await db.update_response_status(response_id, 'accepted')
    
    # Получаем данные
    model = await db.get_user(response['model_id'])
    app = await db.get_application(response['application_id'])
    customer = await db.get_user(app['customer_id'])
    
    # Отправляем уведомление модели с контактами заказчика
    customer_contacts = f"""
✅ Ваш отклик принят!

📞 Контакты заказчика:
ФИО: {customer['full_name']}
Телефон: {customer['phone_1']}
{f"Доп. телефон: {customer['phone_2']}" if customer.get('phone_2') else ''}
Адрес: {customer['address']}
    """
    
    try:
        await bot.send_message(
            chat_id=response['model_id'],
            text=customer_contacts.strip()
        )
        
        await callback.message.edit_text("✅ Отклик принят! Модель получила ваши контакты.")
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")

@router.callback_query(F.data.startswith("reject_"))
async def reject_response(callback: CallbackQuery, db: Database, bot: Bot):
    await callback.answer()
    
    response_id = int(callback.data.split("_")[1])
    response = await db.get_response(response_id)
    
    if not response:
        await callback.message.answer("❌ Отклик не найден.")
        return
    
    # Обновляем статус
    await db.update_response_status(response_id, 'rejected')
    
    # Уведомляем модель
    try:
        await bot.send_message(
            chat_id=response['model_id'],
            text=RESPONSE_REJECTED
        )
        
        await callback.message.edit_text("❌ Отклик отклонен.")
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")

# ============== СОЗДАНИЕ ЗАЯВКИ МОДЕЛИ ==============

@router.callback_query(F.data == "create_model_application")
async def start_create_model_application(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    if not user or user['role'] != 'model':
        await callback.message.answer(ACCESS_DENIED)
        return
    
    # Проверяем подписку
    if not user.get('is_privileged'):
        await callback.message.edit_text(
            SUBSCRIPTION_REQUIRED,
            reply_markup=get_payment_keyboard()
        )
        return
    
    # Проверяем, не истекла ли подписка
    expired = await db.check_subscription_expired(callback.from_user.id)
    if expired:
        await callback.message.edit_text(
            SUBSCRIPTION_EXPIRED,
            reply_markup=get_payment_keyboard()
        )
        return
    
    # Проверка лимита 1 заявка за 48 часов
    recent_apps = await db.get_model_applications_by_model(callback.from_user.id)
    
    if recent_apps:
        last_app = recent_apps[0]
        last_date = datetime.fromisoformat(last_app['created_at'])
        time_diff = datetime.now() - last_date
        
        if time_diff < timedelta(hours=48) and not last_app['is_closed']:
            hours_left = 48 - int(time_diff.total_seconds() / 3600)
            await callback.message.edit_text(
                f"⚠️ Привилегированные модели могут создавать только 1 заявку за 48 часов!\n\n"
                f"⏰ Следующую заявку можно создать через {hours_left} часов.\n\n"
                f"💡 Совет: Вы можете закрыть текущую заявку и создать новую.",
                reply_markup=get_back_keyboard()
            )
            return
    
    await state.set_state(ModelApplicationStates.date)
    await callback.message.edit_text("📅 Укажите дату, когда вы готовы прийти:")

@router.message(ModelApplicationStates.date)
async def process_model_app_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.set_state(ModelApplicationStates.district)
    await message.answer("📍 Укажите район или станцию метро:")

@router.message(ModelApplicationStates.district)
async def process_model_app_district(message: Message, state: FSMContext):
    await state.update_data(district=message.text)
    await state.set_state(ModelApplicationStates.category)
    await message.answer(
        "💆 Выберите категорию услуги:",
        reply_markup=get_category_keyboard(Config.SERVICE_CATEGORIES)
    )

@router.callback_query(ModelApplicationStates.category, F.data.startswith("cat_"))
async def process_model_app_category(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    category = callback.data.replace("cat_", "")
    await state.update_data(category=category)
    await state.set_state(ModelApplicationStates.zones)
    await callback.message.edit_text("🔹 Укажите зоны или области (например: ноги, подмышки):")

@router.message(ModelApplicationStates.zones)
async def process_model_app_zones(message: Message, state: FSMContext):
    await state.update_data(zones=message.text)
    await state.set_state(ModelApplicationStates.time_range)
    await message.answer("🕐 Укажите удобное время (например: 12:00-17:00):")

@router.message(ModelApplicationStates.time_range)
async def process_model_app_time(message: Message, state: FSMContext):
    await state.update_data(time_range=message.text)
    await state.set_state(ModelApplicationStates.photo_video)
    await message.answer(
        "🎥 Готовность к фото/видео:",
        reply_markup=get_photo_video_options_keyboard()
    )

@router.callback_query(ModelApplicationStates.photo_video, F.data.startswith("pv_"))
async def process_model_app_photo_video(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    pv_map = {
        "pv_yes": "Да",
        "pv_no": "Нет",
        "pv_negotiable": "По договорённости"
    }
    
    photo_video = pv_map.get(callback.data, "По договорённости")
    await state.update_data(photo_video=photo_video)
    await state.set_state(ModelApplicationStates.participation_type)
    await callback.message.edit_text(
        "💰 Тип участия:",
        reply_markup=get_model_participation_keyboard()
    )

@router.callback_query(ModelApplicationStates.participation_type, F.data.startswith("mpart_"))
async def process_model_app_participation(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    part_map = {
        "mpart_pay": "Готова оплатить материалы",
        "mpart_free": "Хочу на бесплатную практику",
        "mpart_barter": "Рассмотрю бартер"
    }
    
    participation = part_map.get(callback.data, "Рассмотрю бартер")
    await state.update_data(participation_type=participation)
    await state.set_state(ModelApplicationStates.note)
    await callback.message.edit_text("📝 Добавьте примечание (или '-' если нет):")

@router.message(ModelApplicationStates.note)
async def process_model_app_note(message: Message, state: FSMContext, db: Database):
    note = message.text if message.text != "-" else None
    await state.update_data(note=note)
    await state.set_state(ModelApplicationStates.confirm)
    
    data = await state.get_data()
    model = await db.get_user(message.from_user.id)
    
    preview_text = format_model_application_preview(data, model)
    
    await message.answer(
        "Проверьте данные заявки:\n\n" + preview_text,
        reply_markup=get_confirm_keyboard()
    )

@router.callback_query(ModelApplicationStates.confirm, F.data == "confirm_publish")
async def confirm_publish_model_application(callback: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    await callback.answer()
    
    data = await state.get_data()
    model = await db.get_user(callback.from_user.id)
    
    # Создаем заявку модели в БД
    app_id = await db.create_model_application(
        model_id=callback.from_user.id,
        date=data['date'],
        district=data['district'],
        category=data['category'],
        zones=data['zones'],
        time_range=data['time_range'],
        photo_video=data['photo_video'],
        participation_type=data['participation_type'],
        note=data.get('note')
    )
    
    # Форматируем текст для канала
    app_text = format_model_application_for_channel(data, model)
    
    # Публикуем в канал
    try:
        msg = await bot.send_message(
            chat_id=Config.CHAT_ID,
            text=app_text,
            reply_markup=get_model_application_keyboard(app_id, is_closed=False)
        )
        
        # Сохраняем message_id
        await db.update_model_application(app_id, message_id=msg.message_id)
        
        await callback.message.edit_text("✅ Заявка успешно создана и опубликована в канале!")
        await state.clear()
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка публикации: {e}")
        await state.clear()

@router.callback_query(ModelApplicationStates.confirm, F.data == "confirm_edit")
async def confirm_edit_model_application(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    await state.set_state(ModelApplicationStates.edit_field)
    await callback.message.edit_text(
        "Выберите поле для редактирования:",
        reply_markup=get_edit_fields_keyboard(is_model_app=True)
    )

@router.callback_query(ModelApplicationStates.confirm, F.data == "confirm_cancel")
async def confirm_cancel_model_application(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    await state.clear()
    
    sub_info = await db.get_subscription_info(callback.from_user.id)
    await callback.message.edit_text(
        "❌ Создание заявки отменено.",
        reply_markup=get_model_menu_keyboard_with_subscription(
            user.get('is_privileged', False),
            sub_info['has_subscription']
        )
    )

# ============== РЕДАКТИРОВАНИЕ ЗАЯВКИ МОДЕЛИ ==============

@router.callback_query(ModelApplicationStates.edit_field, F.data.startswith("edit_field_"))
async def process_edit_field_selection_model(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    field = callback.data.replace("edit_field_", "")
    await state.update_data(edit_field_name=field)
    await state.set_state(ModelApplicationStates.edit_value)
    
    field_prompts = {
        "date": "Введите новую дату:",
        "district": "Введите новый район:",
        "category": "Выберите новую категорию:",
        "zones": "Введите новые зоны:",
        "time_range": "Введите новое время:",
        "photo_video": "Готовность к фото/видео?",
        "participation_type": "Выберите новый тип участия:",
        "note": "Введите новое примечание:"
    }
    
    prompt = field_prompts.get(field, "Введите новое значение:")
    
    # Для некоторых полей показываем клавиатуры
    if field == "photo_video":
        await callback.message.edit_text(prompt, reply_markup=get_photo_video_options_keyboard())
    elif field == "participation_type":
        await callback.message.edit_text(prompt, reply_markup=get_model_participation_keyboard())
    elif field == "category":
        await callback.message.edit_text(prompt, reply_markup=get_category_keyboard(Config.SERVICE_CATEGORIES))
    else:
        await callback.message.edit_text(prompt)

@router.message(ModelApplicationStates.edit_value)
async def process_edit_value_text_model(message: Message, state: FSMContext, db: Database, bot: Bot):
    data = await state.get_data()
    field_name = data.get('edit_field_name')
    
    # Обновляем значение в state
    await state.update_data(**{field_name: message.text})
    
    # Получаем все данные
    updated_data = await state.get_data()
    model = await db.get_user(message.from_user.id)
    
    # ИСПРАВЛЕНИЕ 2: Показываем обновленную анкету после редактирования
    preview_text = format_model_application_preview(updated_data, model)
    
    await message.answer(
        f"✅ Поле '{field_name}' обновлено!\n\n{preview_text}",
        reply_markup=get_confirm_keyboard()
    )
    
    await state.set_state(ModelApplicationStates.confirm)

@router.callback_query(ModelApplicationStates.edit_value, F.data.startswith("cat_"))
async def process_edit_category_model(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()
    
    category = callback.data.replace("cat_", "")
    await state.update_data(category=category)
    
    # Получаем все данные
    updated_data = await state.get_data()
    model = await db.get_user(callback.from_user.id)
    
    # Показываем обновленную анкету
    preview_text = format_model_application_preview(updated_data, model)
    
    await callback.message.edit_text(
        f"✅ Категория обновлена!\n\n{preview_text}",
        reply_markup=get_confirm_keyboard()
    )
    
    await state.set_state(ModelApplicationStates.confirm)

@router.callback_query(ModelApplicationStates.edit_value)
async def process_edit_value_callback_model(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()
    
    data = await state.get_data()
    field_name = data.get('edit_field_name')
    
    # Обработка различных callback данных
    value_map = {
        "pv_yes": "Да",
        "pv_no": "Нет",
        "pv_negotiable": "По договорённости",
        "mpart_pay": "Готова оплатить материалы",
        "mpart_free": "Хочу на бесплатную практику",
        "mpart_barter": "Рассмотрю бартер"
    }
    
    value = value_map.get(callback.data)
    
    if value is not None:
        await state.update_data(**{field_name: value})
        
        # Получаем обновленные данные
        updated_data = await state.get_data()
        model = await db.get_user(callback.from_user.id)
        
        # Показываем обновленную анкету
        preview_text = format_model_application_preview(updated_data, model)
        
        await callback.message.edit_text(
            f"✅ Поле обновлено!\n\n{preview_text}",
            reply_markup=get_confirm_keyboard()
        )
        
        await state.set_state(ModelApplicationStates.confirm)

@router.callback_query(ModelApplicationStates.edit_field, F.data == "cancel_edit")
async def cancel_edit_model(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()
    
    # Получаем данные из state
    data = await state.get_data()
    model = await db.get_user(callback.from_user.id)
    
    # Возвращаемся к подтверждению
    preview_text = format_model_application_preview(data, model)
    
    await callback.message.edit_text(
        "Проверьте данные заявки:\n\n" + preview_text,
        reply_markup=get_confirm_keyboard()
    )
    
    await state.set_state(ModelApplicationStates.confirm)

# ============== ОТКЛИК ЗАКАЗЧИКА НА ЗАЯВКУ МОДЕЛИ ==============

@router.callback_query(F.data.startswith("offer_"))
async def offer_to_model(callback: CallbackQuery, db: Database, bot: Bot):
    app_id = int(callback.data.split("_")[1])
    
    # Проверяем роль
    user = await db.get_user(callback.from_user.id)
    if not user or user['role'] != 'customer':
        await callback.answer("⚠️ Только заказчики могут откликаться на заявки моделей!", show_alert=True)
        return
    
    # Проверяем заявку модели
    app = await db.get_model_application(app_id)
    if not app:
        await callback.answer("❌ Заявка не найдена.", show_alert=True)
        return
    
    if app['is_closed']:
        await callback.answer("⚠️ Заявка уже закрыта.", show_alert=True)
        return
    
    # Проверяем, не откликался ли уже
    exists = await db.check_customer_response_exists(app_id, callback.from_user.id)
    if exists:
        await callback.answer("⚠️ Вы уже откликнулись на эту заявку!", show_alert=True)
        return
    
    # Создаем отклик заказчика
    await db.add_customer_response(app_id, callback.from_user.id)
    
    # ИСПРАВЛЕНИЕ 3: Отправляем полную информацию о мастере модели
    customer_profile = format_customer_profile(user)
    
    try:
        await bot.send_message(
            chat_id=app['model_id'],
            text=f"📩 На вашу заявку откликнулся мастер!\n\n{customer_profile}"
        )
        
        # ИСПРАВЛЕНИЕ 1: Всплывающее окно при отклике
        await callback.answer("✅ Вы откликнулись на заявку модели!", show_alert=True)
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка отправки: {e}", show_alert=True)

# ============== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==============

def format_model_profile(model: dict) -> str:
    """Форматирование профиля модели"""
    text = f"""
👤 Модель: {model['full_name']}
📍 Район: {model['district']}
🎂 Возраст: {model['age']}
📏 Рост: {model['height']} см
🧴 Тип кожи: {model['skin_type']}
⚠️ Противопоказания: {model.get('contraindications', 'Нет')}
🕐 Удобное время: {model['available_days']}
🎓 Опыт: {model['experience']}
🎥 Фото/видео: {'Да' if model['photo_video_agree'] else 'Нет'}
⭐ Рейтинг: {model.get('rating', 0.0)}/10.0
    """
    return text.strip()

def format_customer_profile(customer: dict) -> str:
    """Форматирование профиля заказчика"""
    text = f"""
👤 Заказчик: {customer['full_name']}
🏢 Род деятельности: {customer['activity_type']}
🏙️ Город: {customer['city']}
📍 Район: {customer['district']}
📞 Телефон: {customer['phone_1']}
{f"📞 Доп. телефон: {customer['phone_2']}" if customer.get('phone_2') else ''}
📍 Адрес: {customer['address']}
⭐ Рейтинг: {customer.get('rating', 0.0)}/10.0
    """
    return text.strip()

def format_model_application_preview(data: dict, model: dict) -> str:
    """Форматирование превью заявки модели"""
    text = f"""
🙋♀️ Модель: {model['full_name']}
📅 Дата: {data['date']}
🕐 Время: {data['time_range']}
📍 Район: {data['district']}
💆 Услуга: {data['category']}
🔹 Зоны: {data['zones']}
🎥 Фото/видео: {data['photo_video']}
💰 Тип участия: {data['participation_type']}
📝 Примечание: {data.get('note', '-')}
    """
    return text.strip()

def format_model_application_for_channel(data: dict, model: dict) -> str:
    """Форматирование заявки модели для канала"""
    text = f"""
🟣 Модель ищет мастера
👤 {model['full_name']}
📅 Дата: {data['date']}
🕐 Время: {data['time_range']}
📍 Район: {data['district']}
💆 Услуга: {data['category']}
🔹 Зоны: {data['zones']}
🎥 Фото/видео: {data['photo_video']}
💰 Тип участия: {data['participation_type']}
⭐ Рейтинг модели: {model.get('rating', 0.0)}/10.0
    """
    
    if data.get('note'):
        text += f"\n📝 {data['note']}"
    
    return text.strip()