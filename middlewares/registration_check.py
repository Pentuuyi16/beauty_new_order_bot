from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.database import Database

class RegistrationCheckMiddleware(BaseMiddleware):
    def __init__(self, db: Database):
        self.db = db
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        state: FSMContext = data.get('state')
        
        # Проверяем, находится ли пользователь в процессе регистрации
        if state:
            current_state = await state.get_state()
            
            # Если пользователь в процессе регистрации и отправил команду /start
            if current_state and current_state.startswith("RegistrationStates"):
                if isinstance(event, Message) and event.text and event.text.startswith('/start'):
                    await event.answer(
                        "⚠️ Вы находитесь в процессе регистрации!\n\n"
                        "Пожалуйста, завершите заполнение анкеты или отправьте /cancel для отмены."
                    )
                    return
        
        # Передаем db в data
        data['db'] = self.db
        
        return await handler(event, data)