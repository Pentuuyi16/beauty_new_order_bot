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

def get_role_change_keyboard(current_role: str) -> InlineKeyboardMarkup:
    """Клавиатура смены роли (без текущей роли)"""
    builder = InlineKeyboardBuilder()
    
    if current_role != "viewer":
        builder.button(text="👀 Зритель", callback_data="change_to_viewer")
    if current_role != "customer":
        builder.button(text="🧑‍💼 Заказчик", callback_data="change_to_customer")
    if current_role != "model":
        builder.button(text="💃 Модель", callback_data="change_to_model")
    
    builder.button(text="❌ Не сменять роль", callback_data="cancel_role_change")
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
        builder.button(text="📝 Хочу быть моделью", callback_data="create_model_application")
        builder.button(text="📊 Моя подписка", callback_data="subscription_info")
    else:
        builder.button(text="💎 Стать привилегированной", callback_data="buy_subscription")
    
    builder.button(text="👤 Моя роль", callback_data="show_my_role")
    builder.button(text="🔄 Сменить роль", callback_data="change_role")
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
    
    builder.button(text="👤 Моя роль", callback_data="show_my_role")
    builder.button(text="🔄 Сменить роль", callback_data="change_role")
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

def get_edit_fields_keyboard_with_id(app_id: int, is_model_app: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура выбора поля для редактирования с ID заявки"""
    builder = InlineKeyboardBuilder()
    
    if is_model_app:
        fields = [
            ("📅 Дата", f"editf_{app_id}_date"),
            ("📍 Район", f"editf_{app_id}_district"),
            ("💆 Категория", f"editf_{app_id}_category"),
            ("🔹 Зоны", f"editf_{app_id}_zones"),
            ("🕐 Время", f"editf_{app_id}_time_range"),
            ("🎥 Фото/видео", f"editf_{app_id}_photo_video"),
            ("💰 Тип участия", f"editf_{app_id}_participation_type"),
            ("📝 Примечание", f"editf_{app_id}_note"),
        ]
    else:
        fields = [
            ("💆 Категория", f"editf_{app_id}_category"),
            ("📂 Подкатегория", f"editf_{app_id}_subcategory"),
            ("🏙️ Город", f"editf_{app_id}_city"),
            ("📍 Район", f"editf_{app_id}_district"),
            ("📅 Дата", f"editf_{app_id}_date"),
            ("🕐 Время", f"editf_{app_id}_time"),
            ("⏱️ Длительность", f"editf_{app_id}_duration"),
            ("📋 Требования", f"editf_{app_id}_requirements"),
            ("👥 Кол-во моделей", f"editf_{app_id}_models_needed"),
            ("🎓 Нужен опыт", f"editf_{app_id}_experience_required"),
            ("👁️ Зрители", f"editf_{app_id}_viewers_count"),
            ("🎥 Фото/видео", f"editf_{app_id}_photo_video"),
            ("🧴 Оплата материалов", f"editf_{app_id}_materials_payment"),
            ("💰 Тип участия", f"editf_{app_id}_participation_type"),
            ("💵 Сумма оплаты", f"editf_{app_id}_payment_amount"),
            ("👗 Дресс-код", f"editf_{app_id}_dress_code"),
            ("💬 Комментарий", f"editf_{app_id}_comment"),
        ]
    
    for text, callback in fields:
        builder.button(text=text, callback_data=callback)
    
    builder.button(text="🔙 Назад", callback_data=f"view_app_{app_id}")
    builder.adjust(2)
    return builder.as_markup()

def get_viewer_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню зрителя с кнопкой смены роли"""
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Моя роль", callback_data="show_my_role")
    builder.button(text="🔄 Сменить роль", callback_data="change_role")
    builder.adjust(1)
    return builder.as_markup()

def get_rating_keyboard(response_id: int, rating_type: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для оценки (1-10)
    rating_type: 'model' или 'customer'
    """
    builder = InlineKeyboardBuilder()
    
    for i in range(1, 11):
        builder.button(text=str(i), callback_data=f"rate_{rating_type}_{response_id}_{i}")
    
    builder.adjust(5)
    return builder.as_markup()

# НОВЫЕ КЛАВИАТУРЫ ДЛЯ МОДЕЛЕЙ (ПО ТЗ)

def get_model_welcome_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после успешной регистрации модели"""
    from config import Config
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Перейти к заявкам", callback_data="model_view_applications")
    builder.button(text="💬 Открыть канал заявок", url=Config.CHAT_LINK)
    builder.button(text="❓ Как это работает (1 мин)", callback_data="model_help")
    builder.adjust(1)
    return builder.as_markup()

def get_model_main_menu(is_privileged: bool = False) -> InlineKeyboardMarkup:
    """Главное меню модели"""
    from config import Config
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Лента заявок", callback_data="model_view_applications")
    builder.button(text="🔍 Найти услугу", callback_data="model_search_service")
    builder.button(text="📝 Мои отклики", callback_data="model_my_responses")
    
    if not is_privileged:
        builder.button(text="💎 Стать привилегированной", callback_data="buy_subscription")
    
    builder.button(text="💬 Канал заявок", url=Config.CHAT_LINK)
    builder.button(text="❓ Помощь", callback_data="model_help")
    builder.adjust(1)
    return builder.as_markup()

def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню модели"""
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад в меню", callback_data="model_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_search_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора категории для поиска"""
    from config import Config
    builder = InlineKeyboardBuilder()
    for category in Config.SERVICE_CATEGORIES:
        builder.button(text=category, callback_data=f"search_cat_{category}")
    builder.button(text="◀️ Назад", callback_data="model_menu")
    builder.adjust(2)
    return builder.as_markup()