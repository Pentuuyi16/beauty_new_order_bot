from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.database import Database
from utils.states import RegistrationStates
from keyboards.inline import (
    get_gdpr_keyboard, 
    get_customer_menu_keyboard_with_subscription,
    get_model_menu_keyboard_with_subscription,
    get_experience_keyboard,
    get_yes_no_keyboard
)
from keyboards.reply import get_done_keyboard, remove_keyboard
from utils.texts import *
from config import Config

router = Router()

# ============== ВЫБОР РОЛИ ==============

@router.callback_query(F.data.startswith("role_"))
async def process_role_selection(callback: CallbackQuery, state: FSMContext, db: Database):
    await callback.answer()
    
    role = callback.data.split("_")[1]
    
    if role == "viewer":
        await db.add_user(callback.from_user.id, callback.from_user.username, "viewer")
        
        from keyboards.inline import get_viewer_menu_keyboard
        
        await callback.message.edit_text(
            f"✅ Вы зарегистрированы как зритель!\n\n"
            f"Перейдите в канал для просмотра заявок:\n"
            f"https://t.me/model_cheby\n\n"
            f"💡 Если вас заинтересует тематика, вы всегда можете сменить роль на модель или заказчика!",
            reply_markup=get_viewer_menu_keyboard()
        )
        await state.clear()
    elif role == "customer":
        await state.update_data(role="customer")
        await state.set_state(RegistrationStates.customer_full_name)
        await callback.message.edit_text(CUSTOMER_REGISTRATION_START)
    elif role == "model":
        await state.update_data(role="model")
        await state.set_state(RegistrationStates.model_full_name)
        await callback.message.edit_text(MODEL_REGISTRATION_START)

# ============== РЕГИСТРАЦИЯ ЗАКАЗЧИКА ==============

@router.message(RegistrationStates.customer_full_name)
async def process_customer_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(RegistrationStates.customer_city)
    await message.answer(CUSTOMER_CITY)

@router.message(RegistrationStates.customer_city)
async def process_customer_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(RegistrationStates.customer_district)
    await message.answer(CUSTOMER_DISTRICT)

@router.message(RegistrationStates.customer_district)
async def process_customer_district(message: Message, state: FSMContext):
    await state.update_data(district=message.text)
    await state.set_state(RegistrationStates.customer_activity)
    await message.answer(CUSTOMER_ACTIVITY)

@router.message(RegistrationStates.customer_activity)
async def process_customer_activity(message: Message, state: FSMContext):
    await state.update_data(activity_type=message.text)
    await state.set_state(RegistrationStates.customer_address)
    await message.answer(CUSTOMER_ADDRESS)

@router.message(RegistrationStates.customer_address)
async def process_customer_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(RegistrationStates.customer_phone_1)
    await message.answer(CUSTOMER_PHONE_1)

@router.message(RegistrationStates.customer_phone_1)
async def process_customer_phone_1(message: Message, state: FSMContext):
    await state.update_data(phone_1=message.text)
    await state.set_state(RegistrationStates.customer_phone_2)
    await message.answer(CUSTOMER_PHONE_2)

@router.message(RegistrationStates.customer_phone_2)
async def process_customer_phone_2(message: Message, state: FSMContext):
    phone_2 = message.text if message.text != "-" else None
    await state.update_data(phone_2=phone_2)
    await state.set_state(RegistrationStates.customer_photo)
    await message.answer(CUSTOMER_PHOTO)

@router.message(RegistrationStates.customer_photo, F.photo)
async def process_customer_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.set_state(RegistrationStates.customer_gdpr)
    await message.answer(CUSTOMER_GDPR, reply_markup=get_gdpr_keyboard())

@router.callback_query(RegistrationStates.customer_gdpr, F.data == "gdpr_accept")
async def process_customer_gdpr_accept(callback: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    await callback.answer()
    
    data = await state.get_data()
    
    # Создаем пользователя
    await db.add_user(callback.from_user.id, callback.from_user.username, "customer")
    
    # Обновляем данные
    await db.update_user(
        callback.from_user.id,
        full_name=data.get('full_name'),
        city=data.get('city'),
        district=data.get('district'),
        activity_type=data.get('activity_type'),
        address=data.get('address'),
        phone_1=data.get('phone_1'),
        phone_2=data.get('phone_2'),
        photo_id=data.get('photo_id'),
        gdpr_consent=True
    )
    
    await state.clear()
    await callback.message.edit_text(REGISTRATION_SUCCESS)
    
    await callback.message.answer(
        f"🎉 Регистрация завершена!\n\n"
        f"Перейдите в чат:\nhttps://t.me/model_cheby\n\n"
        f"💼 Для создания заявок необходимо оформить подписку - 500 руб/месяц\n\n"
        f"После перехода вам будут доступны все функции.",
        reply_markup=get_customer_menu_keyboard_with_subscription(has_subscription=False)
    )

@router.callback_query(RegistrationStates.customer_gdpr, F.data == "gdpr_decline")
async def process_customer_gdpr_decline(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text("❌ Без согласия на обработку данных регистрация невозможна.\n\nОтправьте /start для повторной попытки.")

# ============== РЕГИСТРАЦИЯ МОДЕЛИ ==============

@router.message(RegistrationStates.model_full_name)
async def process_model_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(RegistrationStates.model_age)
    await message.answer(MODEL_AGE)

@router.message(RegistrationStates.model_age)
async def process_model_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        await state.update_data(age=age)
        await state.set_state(RegistrationStates.model_city)
        await message.answer(MODEL_CITY)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите возраст числом.")

@router.message(RegistrationStates.model_city)
async def process_model_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(RegistrationStates.model_district)
    await message.answer(MODEL_DISTRICT)

@router.message(RegistrationStates.model_district)
async def process_model_district(message: Message, state: FSMContext):
    await state.update_data(district=message.text)
    await state.set_state(RegistrationStates.model_height)
    await message.answer(MODEL_HEIGHT)

@router.message(RegistrationStates.model_height)
async def process_model_height(message: Message, state: FSMContext):
    try:
        height = int(message.text)
        await state.update_data(height=height)
        await state.set_state(RegistrationStates.model_skin_type)
        await message.answer(MODEL_SKIN_TYPE)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите рост числом.")

@router.message(RegistrationStates.model_skin_type)
async def process_model_skin_type(message: Message, state: FSMContext):
    await state.update_data(skin_type=message.text)
    await state.set_state(RegistrationStates.model_contraindications)
    await message.answer(MODEL_CONTRAINDICATIONS)

@router.message(RegistrationStates.model_contraindications)
async def process_model_contraindications(message: Message, state: FSMContext):
    contra = message.text if message.text != "-" else None
    await state.update_data(contraindications=contra)
    await state.set_state(RegistrationStates.model_available_days)
    await message.answer(MODEL_AVAILABLE_DAYS)

@router.message(RegistrationStates.model_available_days)
async def process_model_available_days(message: Message, state: FSMContext):
    await state.update_data(available_days=message.text)
    await state.set_state(RegistrationStates.model_experience)
    await message.answer(MODEL_EXPERIENCE, reply_markup=get_experience_keyboard())

@router.callback_query(RegistrationStates.model_experience, F.data.startswith("exp_"))
async def process_model_experience(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    exp_map = {
        "exp_none": "Нет опыта",
        "exp_beginner": "Начинающий",
        "exp_experienced": "Опытная"
    }
    
    experience = exp_map.get(callback.data, "Нет опыта")
    await state.update_data(experience=experience)
    await state.set_state(RegistrationStates.model_photo_video)
    await callback.message.edit_text(MODEL_PHOTO_VIDEO, reply_markup=get_yes_no_keyboard("photo_video"))

@router.callback_query(RegistrationStates.model_photo_video, F.data.startswith("photo_video_"))
async def process_model_photo_video(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    agree = callback.data == "photo_video_yes"
    await state.update_data(photo_video_agree=agree)
    await state.set_state(RegistrationStates.model_phone)
    await callback.message.edit_text(MODEL_PHONE)

@router.message(RegistrationStates.model_phone)
async def process_model_phone(message: Message, state: FSMContext):
    await state.update_data(phone_1=message.text)
    await state.set_state(RegistrationStates.model_photos)
    await message.answer(MODEL_PHOTOS, reply_markup=get_done_keyboard())
    await state.update_data(photos=[])

@router.message(RegistrationStates.model_photos, F.photo)
async def process_model_photos(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Фото {len(photos)} добавлено. Отправьте ещё или /done для завершения.")

@router.message(RegistrationStates.model_photos, F.text == "/done")
async def process_model_photos_done(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    
    if not photos:
        await message.answer("⚠️ Необходимо отправить хотя бы одно фото!")
        return
    
    portfolio_ids = ",".join(photos)
    await state.update_data(portfolio_ids=portfolio_ids)
    await state.set_state(RegistrationStates.model_gdpr)
    await message.answer(MODEL_GDPR, reply_markup=get_gdpr_keyboard())

@router.callback_query(RegistrationStates.model_gdpr, F.data == "gdpr_accept")
async def process_model_gdpr_accept(callback: CallbackQuery, state: FSMContext, db: Database, bot: Bot):
    await callback.answer()
    
    data = await state.get_data()
    
    # Создаем пользователя
    await db.add_user(callback.from_user.id, callback.from_user.username, "model")
    
    # Проверяем есть ли активная подписка МОДЕЛИ
    sub_info = await db.get_subscription_info(callback.from_user.id)
    is_privileged = sub_info['has_subscription']
    
    # Обновляем данные
    await db.update_user(
        callback.from_user.id,
        full_name=data.get('full_name'),
        age=data.get('age'),
        city=data.get('city'),
        district=data.get('district'),
        height=data.get('height'),
        skin_type=data.get('skin_type'),
        contraindications=data.get('contraindications'),
        available_days=data.get('available_days'),
        experience=data.get('experience'),
        photo_video_agree=data.get('photo_video_agree'),
        phone_1=data.get('phone_1'),
        portfolio_ids=data.get('portfolio_ids'),
        gdpr_consent=True,
        is_privileged=is_privileged  # Ставим на основе подписки МОДЕЛИ
    )
    
    await state.clear()
    await callback.message.edit_text(REGISTRATION_SUCCESS)
    
    await callback.message.answer(
        f"🎉 Регистрация завершена!\n\n"
        f"Перейдите в чат:\nhttps://t.me/model_cheby\n\n"
        f"💡 Хотите создавать свои заявки?\n"
        f"Оформите привилегированную подписку всего за 100 руб/месяц!\n\n"
        f"После перехода вам будут доступны все функции.",
        reply_markup=get_model_menu_keyboard_with_subscription(
            is_privileged=is_privileged,
            has_subscription=sub_info['has_subscription']
        )
    )

@router.callback_query(RegistrationStates.model_gdpr, F.data == "gdpr_decline")
async def process_model_gdpr_decline(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text("❌ Без согласия на обработку данных регистрация невозможна.\n\nОтправьте /start для повторной попытки.")