from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.database import Database
from utils.states import ApplicationStates
from keyboards.inline import *
from utils.texts import *
from config import Config

router = Router()

# ============== МЕНЮ ЗАКАЗЧИКА ==============

@router.callback_query(F.data == "create_application")
async def start_create_application(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    if not user or user['role'] != 'customer':
        await callback.message.answer(ACCESS_DENIED)
        return
    
    # ПРОВЕРЯЕМ ПОДПИСКУ ЗАКАЗЧИКА
    has_subscription = await db.check_customer_subscription(callback.from_user.id)
    if not has_subscription:
        await callback.message.edit_text(
            CUSTOMER_SUBSCRIPTION_REQUIRED,
            reply_markup=get_customer_payment_keyboard()
        )
        return
    
    await state.set_state(ApplicationStates.category)
    await callback.message.edit_text(
        APPLICATION_CATEGORY,
        reply_markup=get_category_keyboard(Config.SERVICE_CATEGORIES)
    )

@router.callback_query(F.data == "my_applications")
async def show_my_applications(callback: CallbackQuery, db: Database):
    await callback.answer()
    
    applications = await db.get_customer_applications(callback.from_user.id)
    
    if not applications:
        await callback.message.edit_text(
            "У вас пока нет заявок.",
            reply_markup=get_back_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "📋 Ваши заявки:",
        reply_markup=get_my_applications_keyboard(applications)
    )

@router.callback_query(F.data.startswith("view_app_"))
async def view_application(callback: CallbackQuery, db: Database):
    await callback.answer()
    
    app_id = int(callback.data.split("_")[2])
    app = await db.get_application(app_id)
    
    if not app:
        await callback.message.answer("❌ Заявка не найдена.")
        return
    
    app_text = format_application(app)
    
    await callback.message.edit_text(
        app_text,
        reply_markup=get_application_actions_keyboard(app_id, app['is_closed'])
    )

@router.callback_query(F.data.startswith("close_app_"))
async def close_application(callback: CallbackQuery, db: Database, bot: Bot):
    await callback.answer()
    
    app_id = int(callback.data.split("_")[2])
    app = await db.get_application(app_id)
    
    if not app:
        await callback.message.answer("❌ Заявка не найдена.")
        return
    
    await db.close_application(app_id)
    
    # Обновляем сообщение в канале
    if app['message_id']:
        try:
            await bot.edit_message_reply_markup(
                chat_id=Config.CHAT_ID,
                message_id=app['message_id'],
                reply_markup=get_application_keyboard(app_id, is_closed=True)
            )
        except Exception:
            pass
    
    await callback.message.edit_text(
        "✅ Набор закрыт!",
        reply_markup=get_back_keyboard()
    )

@router.callback_query(F.data.startswith("responses_app_"))
async def view_responses(callback: CallbackQuery, db: Database):
    await callback.answer()
    
    app_id = int(callback.data.split("_")[2])
    responses = await db.get_application_responses(app_id)
    
    if not responses:
        await callback.message.answer("На эту заявку пока нет откликов.")
        return
    
    text = f"📊 Отклики на заявку ({len(responses)}):\n\n"
    
    for resp in responses:
        model = await db.get_user(resp['model_id'])
        status_emoji = {
            'pending': '⏳',
            'accepted': '✅',
            'rejected': '❌'
        }
        emoji = status_emoji.get(resp['status'], '⏳')
        text += f"{emoji} {model['full_name']} - {resp['status']}\n"
    
    await callback.message.answer(text)

# ============== СОЗДАНИЕ ЗАЯВКИ ==============

@router.callback_query(ApplicationStates.category, F.data.startswith("cat_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    category = callback.data.replace("cat_", "")
    await state.update_data(category=category)
    await state.set_state(ApplicationStates.subcategory)
    
    await callback.message.edit_text(
        APPLICATION_SUBCATEGORY,
        reply_markup=get_subcategory_keyboard(Config.SERVICE_SUBCATEGORIES)
    )

@router.callback_query(ApplicationStates.subcategory, F.data.startswith("subcat_"))
async def process_subcategory(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    subcategory = callback.data.replace("subcat_", "")
    await state.update_data(subcategory=subcategory)
    await state.set_state(ApplicationStates.city)
    
    await callback.message.edit_text(APPLICATION_CITY)

@router.message(ApplicationStates.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(ApplicationStates.district)
    await message.answer(APPLICATION_DISTRICT)

@router.message(ApplicationStates.district)
async def process_district(message: Message, state: FSMContext):
    await state.update_data(district=message.text)
    await state.set_state(ApplicationStates.date)
    await message.answer(APPLICATION_DATE)

@router.message(ApplicationStates.date)
async def process_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await state.set_state(ApplicationStates.time)
    await message.answer(APPLICATION_TIME)

@router.message(ApplicationStates.time)
async def process_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    await state.set_state(ApplicationStates.duration)
    await message.answer(APPLICATION_DURATION)

@router.message(ApplicationStates.duration)
async def process_duration(message: Message, state: FSMContext):
    await state.update_data(duration=message.text)
    await state.set_state(ApplicationStates.requirements)
    await message.answer(APPLICATION_REQUIREMENTS)

@router.message(ApplicationStates.requirements)
async def process_requirements(message: Message, state: FSMContext):
    await state.update_data(requirements=message.text)
    await state.set_state(ApplicationStates.models_needed)
    await message.answer(APPLICATION_MODELS_NEEDED)

@router.message(ApplicationStates.models_needed)
async def process_models_needed(message: Message, state: FSMContext):
    try:
        models_needed = int(message.text)
        await state.update_data(models_needed=models_needed)
        await state.set_state(ApplicationStates.experience_required)
        await message.answer(APPLICATION_EXPERIENCE, reply_markup=get_yes_no_keyboard("exp_req"))
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")

@router.callback_query(ApplicationStates.experience_required, F.data.startswith("exp_req_"))
async def process_experience_required(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    exp_required = callback.data == "exp_req_yes"
    await state.update_data(experience_required=exp_required)
    await state.set_state(ApplicationStates.viewers_count)
    await callback.message.edit_text(APPLICATION_VIEWERS)

@router.message(ApplicationStates.viewers_count)
async def process_viewers_count(message: Message, state: FSMContext):
    try:
        viewers = int(message.text)
        await state.update_data(viewers_count=viewers)
        await state.set_state(ApplicationStates.photo_video)
        await message.answer(APPLICATION_PHOTO_VIDEO, reply_markup=get_photo_video_options_keyboard())
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число.")

@router.callback_query(ApplicationStates.photo_video, F.data.startswith("pv_"))
async def process_photo_video(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    pv_map = {
        "pv_yes": "Да",
        "pv_no": "Нет",
        "pv_negotiable": "По договорённости"
    }
    
    photo_video = pv_map.get(callback.data, "Нет")
    await state.update_data(photo_video=photo_video)
    await state.set_state(ApplicationStates.materials_payment)
    await callback.message.edit_text(APPLICATION_MATERIALS, reply_markup=get_materials_keyboard())

@router.callback_query(ApplicationStates.materials_payment, F.data.startswith("mat_"))
async def process_materials_payment(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    mat_map = {
        "mat_yes": "Да, нужно оплатить",
        "mat_no": "Нет, включено"
    }
    
    materials = mat_map.get(callback.data, "Нет, включено")
    await state.update_data(materials_payment=materials)
    await state.set_state(ApplicationStates.participation_type)
    await callback.message.edit_text(
        APPLICATION_PARTICIPATION,
        reply_markup=get_participation_keyboard(Config.PARTICIPATION_TYPES)
    )

@router.callback_query(ApplicationStates.participation_type, F.data.startswith("part_"))
async def process_participation_type(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    participation = callback.data.replace("part_", "")
    await state.update_data(participation_type=participation)
    await state.set_state(ApplicationStates.payment_amount)
    await callback.message.edit_text(APPLICATION_PAYMENT)

@router.message(ApplicationStates.payment_amount)
async def process_payment_amount(message: Message, state: FSMContext):
    amount = message.text if message.text != "-" else None
    await state.update_data(payment_amount=amount)
    await state.set_state(ApplicationStates.dress_code)
    await message.answer(APPLICATION_DRESS_CODE)

@router.message(ApplicationStates.dress_code)
async def process_dress_code(message: Message, state: FSMContext):
    dress_code = message.text if message.text != "-" else None
    await state.update_data(dress_code=dress_code)
    await state.set_state(ApplicationStates.comment)
    await message.answer(APPLICATION_COMMENT)

@router.message(ApplicationStates.comment)
async def process_comment(message: Message, state: FSMContext, db: Database):
    comment = message.text if message.text != "-" else None
    await state.update_data(comment=comment)
    await state.set_state(ApplicationStates.confirm)
    
    data = await state.get_data()
    customer = await db.get_user(message.from_user.id)
    
    preview_text = format_application_preview(data, customer)
    
    await message.answer(
        APPLICATION_CONFIRM + "\n\n" + preview_text,
        reply_markup=get_confirm_keyboard()
    )

@router.callback_query(ApplicationStates.confirm, F.data == "confirm_publish")
async def confirm_publish_application(callback: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    await callback.answer()
    
    data = await state.get_data()
    
    # Проверяем - это новая заявка или редактирование
    app_id = data.get('editing_app_id')
    
    if app_id:
        # Редактирование - просто завершаем
        app = await db.get_application(app_id)
        await state.clear()
        await callback.message.edit_text(
            f"✅ Изменения сохранены!\n\n{format_application(app)}",
            reply_markup=get_application_actions_keyboard(app_id, app['is_closed'])
        )
        return
    
    # Новая заявка - публикуем
    customer = await db.get_user(callback.from_user.id)
    
    # Создаем заявку в БД
    app_id = await db.create_application(
        customer_id=callback.from_user.id,
        category=data['category'],
        subcategory=data['subcategory'],
        city=data['city'],
        district=data['district'],
        date=data['date'],
        time=data['time'],
        duration=data['duration'],
        requirements=data['requirements'],
        models_needed=data['models_needed'],
        experience_required=data['experience_required'],
        viewers_count=data['viewers_count'],
        photo_video=data['photo_video'],
        materials_payment=data['materials_payment'],
        participation_type=data['participation_type'],
        payment_amount=data.get('payment_amount'),
        dress_code=data.get('dress_code'),
        comment=data.get('comment')
    )
    
    # Форматируем текст для канала
    app_text = format_application_for_channel(data, customer)
    
    # Публикуем в канал
    try:
        msg = await bot.send_message(
            chat_id=Config.CHAT_ID,
            text=app_text,
            reply_markup=get_application_keyboard(app_id, is_closed=False)
        )
        
        # Сохраняем message_id
        await db.update_application(app_id, message_id=msg.message_id)
        
        await callback.message.edit_text(APPLICATION_CREATED)
        await state.clear()
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка публикации: {e}")
        await state.clear()

@router.callback_query(ApplicationStates.confirm, F.data == "confirm_edit")
async def confirm_edit_application(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    await state.set_state(ApplicationStates.edit_field)
    await callback.message.edit_text(
        "Выберите поле для редактирования:",
        reply_markup=get_edit_fields_keyboard(is_model_app=False)
    )

@router.callback_query(ApplicationStates.confirm, F.data == "confirm_cancel")
async def confirm_cancel_application(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()
    
    data = await state.get_data()
    app_id = data.get('editing_app_id')
    
    await state.clear()
    
    if app_id:
        # Отменяем редактирование
        app = await db.get_application(app_id)
        await callback.message.edit_text(
            format_application(app),
            reply_markup=get_application_actions_keyboard(app_id, app['is_closed'])
        )
    else:
        # Отменяем создание
        has_subscription = await db.check_customer_subscription(callback.from_user.id)
        await callback.message.edit_text(
            "❌ Создание заявки отменено.",
            reply_markup=get_customer_menu_keyboard_with_subscription(has_subscription=has_subscription)
        )

# ============== РЕДАКТИРОВАНИЕ ЗАЯВКИ ==============

@router.callback_query(F.data.startswith("edit_app_"))
async def start_edit_application(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()
    
    app_id = int(callback.data.split("_")[2])
    app = await db.get_application(app_id)
    
    if not app:
        await callback.message.answer("❌ Заявка не найдена.")
        return
    
    # Загружаем ВСЕ данные заявки в state (КАК У МОДЕЛИ!)
    await state.update_data(
        editing_app_id=app_id,
        category=app['category'],
        subcategory=app['subcategory'],
        city=app['city'],
        district=app['district'],
        date=app['date'],
        time=app['time'],
        duration=app['duration'],
        requirements=app['requirements'],
        models_needed=app['models_needed'],
        experience_required=app['experience_required'],
        viewers_count=app['viewers_count'],
        photo_video=app['photo_video'],
        materials_payment=app['materials_payment'],
        participation_type=app['participation_type'],
        payment_amount=app.get('payment_amount'),
        dress_code=app.get('dress_code'),
        comment=app.get('comment')
    )
    
    await state.set_state(ApplicationStates.edit_field)
    
    await callback.message.edit_text(
        "Выберите поле для редактирования:",
        reply_markup=get_edit_fields_keyboard(is_model_app=False)
    )

@router.callback_query(ApplicationStates.edit_field, F.data.startswith("edit_field_"))
async def process_edit_field_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    field = callback.data.replace("edit_field_", "")
    await state.update_data(edit_field_name=field)
    await state.set_state(ApplicationStates.edit_value)
    
    field_prompts = {
        "category": "Выберите новую категорию:",
        "subcategory": "Выберите новую подкатегорию:",
        "city": "Введите новый город:",
        "district": "Введите новый район:",
        "date": "Введите новую дату:",
        "time": "Введите новое время:",
        "duration": "Введите новую длительность:",
        "requirements": "Введите новые требования:",
        "models_needed": "Введите новое количество моделей:",
        "experience_required": "Требуется ли опыт?",
        "viewers_count": "Введите новое количество зрителей:",
        "photo_video": "Будет ли фото/видео?",
        "materials_payment": "Оплата материалов?",
        "participation_type": "Выберите новый тип участия:",
        "payment_amount": "Введите новую сумму оплаты:",
        "dress_code": "Введите новый дресс-код:",
        "comment": "Введите новый комментарий:"
    }
    
    prompt = field_prompts.get(field, "Введите новое значение:")
    
    if field == "category":
        await callback.message.edit_text(prompt, reply_markup=get_category_keyboard(Config.SERVICE_CATEGORIES))
    elif field == "subcategory":
        await callback.message.edit_text(prompt, reply_markup=get_subcategory_keyboard(Config.SERVICE_SUBCATEGORIES))
    elif field == "experience_required":
        await callback.message.edit_text(prompt, reply_markup=get_yes_no_keyboard("exp_req"))
    elif field == "photo_video":
        await callback.message.edit_text(prompt, reply_markup=get_photo_video_options_keyboard())
    elif field == "materials_payment":
        await callback.message.edit_text(prompt, reply_markup=get_materials_keyboard())
    elif field == "participation_type":
        await callback.message.edit_text(prompt, reply_markup=get_participation_keyboard(Config.PARTICIPATION_TYPES))
    else:
        await callback.message.edit_text(prompt)

@router.message(ApplicationStates.edit_value)
async def process_edit_value_text(message: Message, state: FSMContext, db: Database, bot: Bot):
    data = await state.get_data()
    field_name = data.get('edit_field_name')
    app_id = data.get('editing_app_id')
    
    # Обновляем значение в state
    await state.update_data(**{field_name: message.text})
    
    # Обновляем в БД
    await db.update_application(app_id, **{field_name: message.text})
    
    # Получаем обновленную заявку
    app = await db.get_application(app_id)
    customer = await db.get_user(message.from_user.id)
    
    # Обновляем сообщение в канале
    if app and app.get('message_id'):
        try:
            app_text = format_application_for_channel_from_db(app, customer)
            await bot.edit_message_text(
                chat_id=Config.CHAT_ID,
                message_id=app['message_id'],
                text=app_text,
                reply_markup=get_application_keyboard(app_id, app['is_closed'])
            )
        except Exception as e:
            print(f"Ошибка обновления сообщения в канале: {e}")
    
    # Получаем обновленные данные из state
    updated_data = await state.get_data()
    
    # Показываем обновленную анкету
    app_preview = format_application_preview(updated_data, customer)
    
    await message.answer(
        f"✅ Поле '{field_name}' обновлено!\n\n{app_preview}",
        reply_markup=get_confirm_keyboard()
    )
    
    await state.set_state(ApplicationStates.confirm)

@router.callback_query(ApplicationStates.edit_value, F.data.startswith("cat_"))
async def process_edit_category(callback: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    await callback.answer()
    
    category = callback.data.replace("cat_", "")
    data = await state.get_data()
    app_id = data.get('editing_app_id')
    
    # Обновляем в state
    await state.update_data(category=category)
    
    # Обновляем в БД
    await db.update_application(app_id, category=category)
    
    # Получаем обновленную заявку
    app = await db.get_application(app_id)
    customer = await db.get_user(callback.from_user.id)
    
    # Обновляем в канале
    if app and app.get('message_id'):
        try:
            app_text = format_application_for_channel_from_db(app, customer)
            await bot.edit_message_text(
                chat_id=Config.CHAT_ID,
                message_id=app['message_id'],
                text=app_text,
                reply_markup=get_application_keyboard(app_id, app['is_closed'])
            )
        except Exception:
            pass
    
    # Получаем обновленные данные
    updated_data = await state.get_data()
    
    # Показываем обновленную анкету
    app_preview = format_application_preview(updated_data, customer)
    
    await callback.message.edit_text(
        f"✅ Категория обновлена!\n\n{app_preview}",
        reply_markup=get_confirm_keyboard()
    )
    
    await state.set_state(ApplicationStates.confirm)

@router.callback_query(ApplicationStates.edit_value, F.data.startswith("subcat_"))
async def process_edit_subcategory(callback: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    await callback.answer()
    
    subcategory = callback.data.replace("subcat_", "")
    data = await state.get_data()
    app_id = data.get('editing_app_id')
    
    # Обновляем в state
    await state.update_data(subcategory=subcategory)
    
    # Обновляем в БД
    await db.update_application(app_id, subcategory=subcategory)
    
    # Получаем обновленную заявку
    app = await db.get_application(app_id)
    customer = await db.get_user(callback.from_user.id)
    
    # Обновляем в канале
    if app and app.get('message_id'):
        try:
            app_text = format_application_for_channel_from_db(app, customer)
            await bot.edit_message_text(
                chat_id=Config.CHAT_ID,
                message_id=app['message_id'],
                text=app_text,
                reply_markup=get_application_keyboard(app_id, app['is_closed'])
            )
        except Exception:
            pass
    
    # Получаем обновленные данные
    updated_data = await state.get_data()
    
    # Показываем обновленную анкету
    app_preview = format_application_preview(updated_data, customer)
    
    await callback.message.edit_text(
        f"✅ Подкатегория обновлена!\n\n{app_preview}",
        reply_markup=get_confirm_keyboard()
    )
    
    await state.set_state(ApplicationStates.confirm)

@router.callback_query(ApplicationStates.edit_value)
async def process_edit_value_callback(callback: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    await callback.answer()
    
    data = await state.get_data()
    field_name = data.get('edit_field_name')
    app_id = data.get('editing_app_id')
    
    # Обработка различных callback данных
    value_map = {
        "exp_req_yes": True,
        "exp_req_no": False,
        "pv_yes": "Да",
        "pv_no": "Нет",
        "pv_negotiable": "По договорённости",
        "mat_yes": "Да, нужно оплатить",
        "mat_no": "Нет, включено"
    }
    
    if callback.data.startswith("part_"):
        value = callback.data.replace("part_", "")
    else:
        value = value_map.get(callback.data)
    
    if value is not None:
        # Обновляем в state
        await state.update_data(**{field_name: value})
        
        # Обновляем в БД
        await db.update_application(app_id, **{field_name: value})
        
        # Получаем обновленную заявку
        app = await db.get_application(app_id)
        customer = await db.get_user(callback.from_user.id)
        
        # Обновляем в канале
        if app and app.get('message_id'):
            try:
                app_text = format_application_for_channel_from_db(app, customer)
                await bot.edit_message_text(
                    chat_id=Config.CHAT_ID,
                    message_id=app['message_id'],
                    text=app_text,
                    reply_markup=get_application_keyboard(app_id, app['is_closed'])
                )
            except Exception:
                pass
        
        # Получаем обновленные данные
        updated_data = await state.get_data()
        
        # Показываем обновленную анкету
        app_preview = format_application_preview(updated_data, customer)
        
        await callback.message.edit_text(
            f"✅ Поле обновлено!\n\n{app_preview}",
            reply_markup=get_confirm_keyboard()
        )
        
        await state.set_state(ApplicationStates.confirm)

@router.callback_query(ApplicationStates.edit_field, F.data == "cancel_edit")
async def cancel_edit(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()
    
    data = await state.get_data()
    app_id = data.get('editing_app_id')
    
    if app_id:
        # Если редактировали существующую заявку
        app = await db.get_application(app_id)
        await state.clear()
        await callback.message.edit_text(
            format_application(app),
            reply_markup=get_application_actions_keyboard(app_id, app['is_closed'])
        )
    else:
        # Если создавали новую заявку
        customer = await db.get_user(callback.from_user.id)
        app_preview = format_application_preview(data, customer)
        
        await callback.message.edit_text(
            "Проверьте данные заявки:\n\n" + app_preview,
            reply_markup=get_confirm_keyboard()
        )
        
        await state.set_state(ApplicationStates.confirm)

# ============== РЕЙТИНГ ==============

@router.callback_query(F.data == "my_rating")
async def show_my_rating_customer(callback: CallbackQuery, db: Database):
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

# ============== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==============

def format_application_preview(data: dict, customer: dict) -> str:
    """Форматирование превью заявки для подтверждения"""
    text = f"""
📌 Нужны модели: {data['category']}
📂 Подкатегория: {data['subcategory']}
🏙️ Город: {data['city']}
📍 Район: {data['district']}
📅 Дата: {data['date']}
🕐 Время: {data['time']}
⏱️ Длительность: {data['duration']}
👥 Нужно моделей: {data['models_needed']}
🎓 Опыт: {'Требуется' if data['experience_required'] else 'Не требуется'}
👁️ Зрителей: {data['viewers_count']}
🎥 Фото/видео: {data['photo_video']}
🧴 Материалы: {data['materials_payment']}
💰 Тип участия: {data['participation_type']}
💵 Оплата: {data.get('payment_amount', '-')}
📋 Требования: {data['requirements']}
👗 Дресс-код: {data.get('dress_code', '-')}
💬 Комментарий: {data.get('comment', '-')}
⭐ Рейтинг заказчика: {customer.get('rating', 0.0)}/10.0
    """
    return text.strip()

def format_application_for_channel(data: dict, customer: dict) -> str:
    """Форматирование заявки для канала"""
    text = f"""
🔵 Нужны модели: {data['category']}
📂 {data['subcategory']}
📅 Дата: {data['date']}, {data['time']}
⏱️ Длительность: {data['duration']}
📍 Район: {data['district']}
👥 Нужно: {data['models_needed']} модели(ей)
🎥 Фото/видео: {data['photo_video']}
💰 Тип участия: {data['participation_type']}
🧴 Материалы: {data['materials_payment']}
🎓 Опыт: {'Требуется' if data['experience_required'] else 'Не требуется'}
⚡ Требования: {data['requirements']}
👗 Дресс-код: {data.get('dress_code', '-')}
⭐ Рейтинг заказчика: {customer.get('rating', 0.0)}/10.0
    """
    
    if data.get('comment'):
        text += f"\n💬 {data['comment']}"
    
    return text.strip()

def format_application_for_channel_from_db(app: dict, customer: dict) -> str:
    """Форматирование заявки из БД для канала"""
    text = f"""
🔵 Нужны модели: {app['category']}
📂 {app['subcategory']}
📅 Дата: {app['date']}, {app['time']}
⏱️ Длительность: {app['duration']}
📍 Район: {app['district']}
👥 Нужно: {app['models_needed']} модели(ей)
🎥 Фото/видео: {app['photo_video']}
💰 Тип участия: {app['participation_type']}
🧴 Материалы: {app['materials_payment']}
🎓 Опыт: {'Требуется' if app['experience_required'] else 'Не требуется'}
⚡ Требования: {app['requirements']}
👗 Дресс-код: {app.get('dress_code', '-')}
⭐ Рейтинг заказчика: {customer.get('rating', 0.0)}/10.0
    """
    
    if app.get('comment'):
        text += f"\n💬 {app['comment']}"
    
    return text.strip()

def format_application(app: dict) -> str:
    """Форматирование заявки для просмотра"""
    status = "🔒 Закрыта" if app['is_closed'] else "🟢 Активна"
    
    text = f"""
Статус: {status}

📌 Категория: {app['category']}
📂 Подкатегория: {app['subcategory']}
🏙️ Город: {app['city']}
📍 Район: {app['district']}
📅 Дата: {app['date']}
🕐 Время: {app['time']}
⏱️ Длительность: {app['duration']}
👥 Нужно моделей: {app['models_needed']}
🎓 Опыт: {'Требуется' if app['experience_required'] else 'Не требуется'}
👁️ Зрителей: {app['viewers_count']}
🎥 Фото/видео: {app['photo_video']}
🧴 Материалы: {app['materials_payment']}
💰 Тип участия: {app['participation_type']}
💵 Оплата: {app.get('payment_amount', '-')}
📋 Требования: {app['requirements']}
👗 Дресс-код: {app.get('dress_code', '-')}
💬 Комментарий: {app.get('comment', '-')}
    """
    return text.strip()