import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# Получаем настройки из переменных окружения Render (чтобы не палить токен на GitHub)
API_TOKEN = os.getenv("BOT_TOKEN")
BASE_WEBAPP_URL = os.getenv("WEBAPP_URL", "https://daiyndyq-app-2026.web.app/")

if not API_TOKEN:
    raise ValueError("ОШИБКА: Переменная окружения BOT_TOKEN не задана!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Логика Бота ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    main_webapp = WebAppInfo(url=BASE_WEBAPP_URL)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Открыть Daiyndyq", web_app=main_webapp)]],
        resize_keyboard=True
    )
    await message.answer(
        "Сәлем! Добро пожаловать в тренажер казахского языка **Daiyndyq**! 🚀\n\n"
        "Вы можете открыть полное приложение по кнопке ниже.\n"
        "Или **отправьте мне любой документ/фото**, и я создам тест прямо по нему!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def get_telegram_file_url(file_id: str) -> str:
    file_info = await bot.get_file(file_id)
    return f"https://api.telegram.org/file/bot{API_TOKEN}/{file_info.file_path}"

@dp.message(lambda message: message.document is not None)
async def handle_document(message: types.Message):
    await message.answer("🔄 Обрабатываю документ... Секунду.")
    file_url = await get_telegram_file_url(message.document.file_id)
    webapp_url_with_file = f"{BASE_WEBAPP_URL}?file={file_url}"
    
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Пройти тест по документу", web_app=WebAppInfo(url=webapp_url_with_file))]
    ])
    await message.answer(
        "🎯 Документ успешно привязан! Нажмите на кнопку ниже, чтобы запустить ИИ-генерацию теста внутри приложения.",
        reply_markup=inline_kb
    )

@dp.message(lambda message: message.photo is not None)
async def handle_photo(message: types.Message):
    await message.answer("🔄 Обрабатываю изображение... Секунду.")
    best_photo = message.photo[-1]
    file_url = await get_telegram_file_url(best_photo.file_id)
    webapp_url_with_file = f"{BASE_WEBAPP_URL}?file={file_url}"
    
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Пройти тест по фото", web_app=WebAppInfo(url=webapp_url_with_file))]
    ])
    await message.answer(
        "🎯 Фотография получена! Нажмите на кнопку ниже, чтобы ИИ в приложении прочитал текст с фото и составил тест.",
        reply_markup=inline_kb
    )

# --- Настройка Веб-сервера для Render и Cron-Job ---

async def handle_ping(request):
    return web.Response(text="Бот работает!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render автоматически выделяет порт и записывает его в переменную PORT
    port = int(os.getenv("PORT", 10000)) 
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Веб-сервер запущен на порту {port}")

async def main():
    # Запускаем фоновый сервер для пинга
    await start_web_server()
    # Запускаем опрос Telegram
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
