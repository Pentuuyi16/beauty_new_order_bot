from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.database import Database

router = Router()

@router.callback_query(F.data == "closed")
async def closed_application(callback: CallbackQuery):
    await callback.answer("Эта заявка закрыта.", show_alert=True)