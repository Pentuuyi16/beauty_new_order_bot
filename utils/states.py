from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    choosing_role = State()
    
    # Заказчик
    customer_full_name = State()
    customer_city = State()
    customer_district = State()
    customer_activity = State()
    customer_address = State()
    customer_phone_1 = State()
    customer_phone_2 = State()
    customer_photo = State()
    customer_gdpr = State()
    
    # Модель
    model_full_name = State()
    model_age = State()
    model_city = State()
    model_district = State()
    model_height = State()
    model_skin_type = State()
    model_contraindications = State()
    model_available_days = State()
    model_experience = State()
    model_photo_video = State()
    model_phone = State()
    model_photos = State()
    model_gdpr = State()

class ApplicationStates(StatesGroup):
    category = State()
    subcategory = State()
    city = State()
    district = State()
    date = State()
    time = State()
    duration = State()
    requirements = State()
    models_needed = State()
    experience_required = State()
    viewers_count = State()
    photo_video = State()
    materials_payment = State()
    participation_type = State()
    payment_amount = State()
    dress_code = State()
    comment = State()
    confirm = State()
    
    # Редактирование
    edit_field = State()
    edit_value = State()

class ModelApplicationStates(StatesGroup):
    date = State()
    district = State()
    category = State()
    zones = State()
    time_range = State()
    photo_video = State()
    participation_type = State()
    note = State()
    confirm = State()
    
    # Редактирование
    edit_field = State()
    edit_value = State()

class RatingStates(StatesGroup):
    # Для заказчика
    customer_came = State()
    customer_prepared = State()
    customer_requirements = State()
    customer_work_again = State()
    
    # Для модели
    model_location = State()
    model_conditions = State()
    model_attitude = State()
    model_cooperate = State()