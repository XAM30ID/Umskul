import os
import asyncio
import aiohttp
import logging
from random import choice

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = 'http://fastapi:8000'

storage = RedisStorage.from_url(os.getenv('REDIS_URL'))
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)



class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_surname = State()

class LessonStates(StatesGroup):
    lesson_adding = State()


@dp.message(Command("start"))
async def start(message: types.Message):
    user = None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/student/{message.from_user.id}") as response:
                if response.status == 200:
                    user = await response.json()
    except Exception as e:
        logging.error(f"Ошибка при получении пользователя: {e}")
        
    if user:
        return await message.answer(f"Привет, {user['name']}!👋 \nПомочь с отслеживанием прогресса?")
    
    return await message.answer(f"Привет, {message.from_user.first_name}!👋 \nЯ бот, который поможет тебе отслеживать перогресс в баллах по экзаменам.' \
                                '\nЧтобы зарегистрироваться, отправь команду /register")

@dp.message(Command("register"))
async def register(message: types.Message, state: FSMContext):
    user = None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/student/{message.from_user.id}") as response:
                if response.status == 200:
                    user = await response.json()
    except Exception as e:
        logging.error(f"Ошибка при получении пользователя: {e}")
        
    if user:
        return await message.answer(f"Вы уже зарегистрированы")
    await state.set_state(RegistrationStates.waiting_for_name)
    await state.update_data(user_id=message.from_user.id)
    await message.answer(f"Отлично! Для начала, отправьте Ваше имя")


@dp.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await state.set_state(RegistrationStates.waiting_for_surname)

    await message.answer(
        f"Имя *{name}* сохранено!\n\n"
        f"Теперь отправьте вашу *фамилию*:",
        parse_mode='Markdown'
    )


@dp.message(RegistrationStates.waiting_for_surname)
async def process_surname(message: types.Message, state: FSMContext):
    surname = message.text.strip()
    
    data = await state.get_data()
    name = data.get('name')
    user_id = data.get('user_id', message.from_user.id)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_URL}/api/student",
                json={
                    "telegram_id": user_id,
                    "name": name,
                    "surname": surname
                },
                timeout=10
            ) as response:
                if response.status == 200:
                    await message.answer(
                        f"✅ *Регистрация завершена!*\n\n"
                        f"*{name} {surname}* успешно зарегистрирован(а)!\n\n"
                        f"Теперь вы можете добавлять уроки и отслеживать свой прогресс.",
                        parse_mode="Markdown"
                    )
                else:
                    error_text = await response.text()
                    await message.answer(
                        f"❌ Ошибка при регистрации: {error_text}\n\n"
                        f"Попробуйте снова: /register"
                    )
    finally:
        await state.clear()


@dp.message(Command("view_scores"))
async def view_scores(message: types.Message):
    lessons = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/lessons/{message.from_user.id}") as response:
                if response.status == 200:
                    lessons = await response.json()
    except Exception as e:
        logging.error(f"Ошибка при получении предметов: {e}")
    print(lessons)
    text = '==Ваша успеваемость==\n'
    if len(lessons) > 0:
        for lesson in lessons:
            text += f'\n{lesson['title']}: *{lesson['score']}*'
        text += choice(["\n\nВы молодец!", "\n\nУ вас отличные результаты!", "\n\nЯ вижу большой прогресс!"])
    else:
        text += 'У вас нет сохранённых предметов'

    await message.answer(text, parse_mode='Markdown')


@dp.message(Command("enter_scores"))
async def enter_scores(message: types.Message):
    lessons = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/lessons/{message.from_user.id}") as response:
                if response.status == 200:
                    lessons = await response.json()
    except Exception as e:
        logging.error(f"Ошибка при получении предметов: {e}")
    
    keyboard = []
    if len(lessons) > 0:
        text = 'Выберите предмет для изменения или создайте новый:\n'
        for lesson in lessons:
            text += f'\n{lesson['title']}: *{lesson['score']}*'
            keyboard.append([types.InlineKeyboardButton(text=f'📝 Изменить {lesson['title']}', callback_data=f'edit_{lesson['id']}'),
                             types.InlineKeyboardButton(text=f'🗑️ Удалить {lesson['title']}', callback_data=f'del_{lesson['id']}')])
    else:
        text = 'У вас нет сохранённых предметов'
    keyboard.append([types.InlineKeyboardButton(text='➕ Добавить новый предмет', callback_data='add_lesson')])
    await message.answer(text, parse_mode='Markdown', reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard))


@dp.callback_query()
async def enter_scores_callback(callback: types.CallbackQuery, state: FSMContext):
    callback.answer()
    if callback.data == 'add_lesson':
        await state.set_state(LessonStates.lesson_adding)
        await state.update_data(user_id=callback.from_user.id)
        await callback.message.edit_text(f"Отправьте ваши баллы в формате: `Название предмета = 100`", parse_mode='Markdown', reply_markup=None)
    
    elif callback.data.startswith('edit_'):
        lesson_id = int(callback.data.split('_')[-1])
        await state.set_state(LessonStates.lesson_adding)
        await state.update_data(user_id=callback.from_user.id)
        await state.update_data(lesson_id=lesson_id)
        await callback.message.edit_text(f"Отправьте ваши баллы в формате: `Название предмета = 100`", parse_mode='Markdown', reply_markup=None)
    
    
    elif callback.data.startswith('del_'):
        lesson_id = int(callback.data.split('_')[-1])
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(f"{API_URL}/api/lessons/{lesson_id}") as response:
                    if response.status == 200:
                        result = await response.json()
                        print(result)
                        await callback.message.edit_text(f"Предмет был успешно удалён!", reply_markup=None)
        except Exception as e:
            logging.error(f"Ошибка при удалении занятия: {e}")
            await callback.message.edit_text(f"Ошибка при удалении предмета!", reply_markup=None)


@dp.message(LessonStates.lesson_adding)
async def process_lesson(message: types.Message, state: FSMContext):
    lesson_data = message.text.split('=')
    if len(lesson_data) != 2:
        await message.answer(
                        f"Неверно введён формат сообщения"
                        f"Текст сообщения должен соответствовать формату: `Название предмета = 100`"
                    )
        return
    data = await state.get_data()
    user_id = data.get('user_id', message.from_user.id)
    lesson_id = data.get('lesson_id', None)

    if lesson_id:        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{API_URL}/api/lessons",
                    json={
                        "id": int(lesson_id),
                        "telegram_id": int(user_id),
                        "title": lesson_data[0].strip() if lesson_data[1].strip().isdigit() else lesson_data[1],
                        "score": int(lesson_data[1].strip()) if lesson_data[1].strip().isdigit() else int(lesson_data[0])
                    },
                    timeout=10
                ) as response:
                    if response.status == 200:
                        await message.answer(
                            f"✅ *Предмет изменён!*\n\n",
                            parse_mode="Markdown"
                        )
                    else:
                        error_text = await response.text()
                        await message.answer(
                            f"❌ Ошибка при добавлении предмета: {error_text}\n\n"
                        )
        finally:
            await state.clear()

    else: 
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/api/lessons",
                    json={
                        "telegram_id": int(user_id),
                        "title": lesson_data[0].strip() if lesson_data[1].strip().isdigit() else lesson_data[1],
                        "score": int(lesson_data[1].strip()) if lesson_data[1].strip().isdigit() else int(lesson_data[0])
                    },
                    timeout=10
                ) as response:
                    if response.status == 200:
                        await message.answer(
                            f"✅ *Предмет добавлен!*\n\n",
                            parse_mode="Markdown"
                        )
                    else:
                        error_text = await response.text()
                        await message.answer(
                            f"❌ Ошибка при добавлении предмета: {error_text}\n\n"
                        )
        finally:
            await state.clear()

async def main():
    await bot.set_my_commands([
        types.BotCommand(command='start', description='Начать'), 
        types.BotCommand(command='register', description='Регистрация'),
        types.BotCommand(command='view_scores', description='Просмотр успеваемости'),
        types.BotCommand(command='enter_scores', description='Записать баллы')
    ])
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

