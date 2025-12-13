from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List

def get_role_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора роли"""
    builder = InlineKeyboardBuilder()
    builder.button(text="👀 Зритель", callback_data="role_viewer")
    builder.button(text="🧑‍💼 Заказчик", callback_data="role_customer")
    builder.button(text="💃 Модель", callback_data="role_model")
    builder.adjust(1)
    return builder.as_markup()

def get_gdpr_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура согласия на обработку данных"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Согласен", callback_data="gdpr_accept")
    builder.button(text="❌ Не согласен", callback_data="gdpr_decline")
    builder.adjust(2)
    return builder.as_markup()

def get_customer_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню заказчика"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Создать заявку", callback_data="create_application")
    builder.button(text="📋 Мои заявки", callback_data="my_applications")
    builder.button(text="⭐ Мой рейтинг", callback_data="my_rating")
    builder.adjust(1)
    return builder.as_markup()

def get_model_menu_keyboard(is_privileged: bool = False) -> InlineKeyboardMarkup:
    """Меню модели (старая версия - не используется)"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Мои отклики", callback_data="my_responses")
    builder.button(text="⭐ Мой рейтинг", callback_data="my_rating")
    if is_privileged:
        builder.button(text="📝 Хочу быть моделью", callback_data="create_model_application")
    builder.adjust(1)
    return builder.as_markup()

def get_model_menu_keyboard_with_subscription(is_privileged: bool = False, has_subscription: bool = False) -> InlineKeyboardMarkup:
    """Меню модели с подпиской"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Мои отклики", callback_data="my_responses")
    builder.button(text="⭐ Мой рейтинг", callback_data="my_rating")
    
    if is_privileged and has_subscription:
        # У модели есть активная подписка
        builder.button(text="📝 Хочу быть моделью", callback_data="create_model_application")
        builder.button(text="📊 Моя подписка", callback_data="subscription_info")
    else:
        # У модели нет подписки
        builder.button(text="💎 Стать привилегированной", callback_data="buy_subscription")
    
    builder.adjust(1)
    return builder.as_markup()

def get_category_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура выбора категории"""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category, callback_data=f"cat_{category}")
    builder.adjust(2)
    return builder.as_markup()

def get_subcategory_keyboard(subcategories: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура выбора подкатегории"""
    builder = InlineKeyboardBuilder()
    for subcategory in subcategories:
        builder.button(text=subcategory, callback_data=f"subcat_{subcategory}")
    builder.adjust(2)
    return builder.as_markup()

def get_yes_no_keyboard(callback_prefix: str) -> InlineKeyboardMarkup:
    """Клавиатура Да/Нет"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data=f"{callback_prefix}_yes")
    builder.button(text="❌ Нет", callback_data=f"{callback_prefix}_no")
    builder.adjust(2)
    return builder.as_markup()

def get_participation_keyboard(types: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура типа участия"""
    builder = InlineKeyboardBuilder()
    for ptype in types:
        builder.button(text=ptype, callback_data=f"part_{ptype}")
    builder.adjust(2)
    return builder.as_markup()

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Опубликовать", callback_data="confirm_publish")
    builder.button(text="✏️ Редактировать", callback_data="confirm_edit")
    builder.button(text="❌ Отменить", callback_data="confirm_cancel")
    builder.adjust(1)
    return builder.as_markup()

def get_application_keyboard(app_id: int, is_closed: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура заявки в канале"""
    builder = InlineKeyboardBuilder()
    if not is_closed:
        builder.button(text="🔘 Откликнуться", callback_data=f"respond_{app_id}")
    else:
        builder.button(text="🔒 Набор закрыт", callback_data="closed")
    builder.adjust(1)
    return builder.as_markup()

def get_model_application_keyboard(app_id: int, is_closed: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура заявки модели в канале"""
    builder = InlineKeyboardBuilder()
    if not is_closed:
        builder.button(text="🔘 Предложить мастера", callback_data=f"offer_{app_id}")
    else:
        builder.button(text="🔒 Заявка закрыта", callback_data="closed")
    builder.adjust(1)
    return builder.as_markup()

def get_response_keyboard(response_id: int) -> InlineKeyboardMarkup:
    """Клавиатура принятия/отклонения отклика"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять", callback_data=f"accept_{response_id}")
    builder.button(text="❌ Отклонить", callback_data=f"reject_{response_id}")
    builder.adjust(2)
    return builder.as_markup()

def get_my_applications_keyboard(applications: List[dict]) -> InlineKeyboardMarkup:
    """Клавиатура списка заявок"""
    builder = InlineKeyboardBuilder()
    for app in applications:
        status = "🔒" if app['is_closed'] else "🟢"
        builder.button(
            text=f"{status} {app['category']} - {app['date']}",
            callback_data=f"view_app_{app['id']}"
        )
    builder.adjust(1)
    return builder.as_markup()

def get_application_actions_keyboard(app_id: int, is_closed: bool) -> InlineKeyboardMarkup:
    """Клавиатура действий с заявкой"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"edit_app_{app_id}")
    if not is_closed:
        builder.button(text="🔒 Закрыть набор", callback_data=f"close_app_{app_id}")
    builder.button(text="📊 Отклики", callback_data=f"responses_app_{app_id}")
    builder.button(text="🔙 Назад", callback_data="my_applications")
    builder.adjust(1)
    return builder.as_markup()

def get_edit_fields_keyboard(is_model_app: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура выбора поля для редактирования"""
    builder = InlineKeyboardBuilder()
    
    if is_model_app:
        fields = [
            ("📅 Дата", "edit_field_date"),
            ("📍 Район", "edit_field_district"),
            ("💆 Категория", "edit_field_category"),
            ("🔹 Зоны", "edit_field_zones"),
            ("🕐 Время", "edit_field_time_range"),
            ("🎥 Фото/видео", "edit_field_photo_video"),
            ("💰 Тип участия", "edit_field_participation_type"),
            ("📝 Примечание", "edit_field_note"),
        ]
    else:
        fields = [
            ("💆 Категория", "edit_field_category"),
            ("📂 Подкатегория", "edit_field_subcategory"),
            ("🏙️ Город", "edit_field_city"),
            ("📍 Район", "edit_field_district"),
            ("📅 Дата", "edit_field_date"),
            ("🕐 Время", "edit_field_time"),
            ("⏱️ Длительность", "edit_field_duration"),
            ("📋 Требования", "edit_field_requirements"),
            ("👥 Кол-во моделей", "edit_field_models_needed"),
            ("🎓 Нужен опыт", "edit_field_experience_required"),
            ("👁️ Зрители", "edit_field_viewers_count"),
            ("🎥 Фото/видео", "edit_field_photo_video"),
            ("🧴 Оплата материалов", "edit_field_materials_payment"),
            ("💰 Тип участия", "edit_field_participation_type"),
            ("💵 Сумма оплаты", "edit_field_payment_amount"),
            ("👗 Дресс-код", "edit_field_dress_code"),
            ("💬 Комментарий", "edit_field_comment"),
        ]
    
    for text, callback in fields:
        builder.button(text=text, callback_data=callback)
    
    builder.button(text="🔙 Назад", callback_data="cancel_edit")
    builder.adjust(2)
    return builder.as_markup()

def get_experience_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора опыта"""
    builder = InlineKeyboardBuilder()
    builder.button(text="Нет опыта", callback_data="exp_none")
    builder.button(text="Начинающий", callback_data="exp_beginner")
    builder.button(text="Опытная", callback_data="exp_experienced")
    builder.adjust(1)
    return builder.as_markup()

def get_photo_video_options_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора фото/видео"""
    builder = InlineKeyboardBuilder()
    builder.button(text="Да", callback_data="pv_yes")
    builder.button(text="Нет", callback_data="pv_no")
    builder.button(text="По договорённости", callback_data="pv_negotiable")
    builder.adjust(1)
    return builder.as_markup()

def get_materials_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура оплаты материалов"""
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, нужно оплатить", callback_data="mat_yes")
    builder.button(text="Нет, включено", callback_data="mat_no")
    builder.adjust(1)
    return builder.as_markup()

def get_model_participation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура типа участия для модели"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Готова оплатить материалы", callback_data="mpart_pay")
    builder.button(text="🎓 Хочу на бесплатную практику", callback_data="mpart_free")
    builder.button(text="⚖️ Рассмотрю бартер", callback_data="mpart_barter")
    builder.adjust(1)
    return builder.as_markup()

def get_payment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура оплаты"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить", callback_data="proceed_payment")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура информации о подписке"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка назад"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()
# Добавьте в конец файла:

def get_customer_menu_keyboard_with_subscription(has_subscription: bool = False) -> InlineKeyboardMarkup:
    """Меню заказчика с подпиской"""
    builder = InlineKeyboardBuilder()
    
    if has_subscription:
        builder.button(text="📝 Создать заявку", callback_data="create_application")
        builder.button(text="📋 Мои заявки", callback_data="my_applications")
        builder.button(text="⭐ Мой рейтинг", callback_data="my_rating")
        builder.button(text="📊 Моя подписка", callback_data="customer_subscription_info")
    else:
        builder.button(text="💼 Оформить подписку", callback_data="buy_customer_subscription")
        builder.button(text="⭐ Мой рейтинг", callback_data="my_rating")
    
    builder.adjust(1)
    return builder.as_markup()

def get_customer_payment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура оплаты для заказчика"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить", callback_data="proceed_customer_payment")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_customer_subscription_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура информации о подписке заказчика"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()