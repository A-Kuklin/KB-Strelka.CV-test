from aiogram import executor

from config import TELEGRAM_CHAT_ID
from load_all import bot, storage


async def on_shutdown(dp):
    await bot.close()
    await storage.close()


async def on_startup(dp):
    await bot.send_message(TELEGRAM_CHAT_ID, "Я запущен!")


if __name__ == '__main__':
    from handlers import dp

    executor.start_polling(dp, on_shutdown=on_shutdown, on_startup=on_startup)
