import asyncio
import logging
from aiogram import Bot
import quiz_operations
from aiogram.filters.command import Command
from aiogram import Dispatcher, types, F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters.command import Command
import quiz_operations

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

API_TOKEN = '7925649354:AAEJqD7l3ggP9Qh5T_KKTMT7_VxQBl82NB8'

# Объект бота
bot = Bot(token=API_TOKEN)

# Диспетчер
dp = Dispatcher()

DB_NAME = 'quiz_bot.db'

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем сборщика клавиатур типа Reply
    builder = ReplyKeyboardBuilder()
    # Добавляем в сборщик одну кнопку
    builder.add(types.KeyboardButton(text="Начать игру"))
    # Прикрепляем кнопки к сообщению
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))

# Хэндлер на команды /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    # Отправляем новое сообщение без кнопок
    await message.answer(f"Давайте начнем квиз!")
    # Запускаем новый квиз
    await quiz_operations.new_quiz(message)

@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса для данного пользователя
    current_question_index = await quiz_operations.get_quiz_index(callback.from_user.id)
    correct_answers = await quiz_operations.get_quiz_answers(callback.from_user.id)
    # Отправляем в чат сообщение, что ответ верный
    await callback.message.answer("Верно!")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    correct_answers += 1
    await quiz_operations.update_quiz_index(callback.from_user.id, current_question_index, correct_answers)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_operations.quiz_data):
        # Следующий вопрос
        await quiz_operations.get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
        result_string = await quiz_operations.get_users_answers()
        await callback.message.answer("Результаты участников: ")
        await callback.message.answer(result_string)

@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса для данного пользователя
    current_question_index = await quiz_operations.get_quiz_index(callback.from_user.id)
    correct_answers = await quiz_operations.get_quiz_answers(callback.from_user.id)
    correct_option = quiz_operations.quiz_data[current_question_index]['correct_option']

    # Отправляем в чат сообщение об ошибке с указанием верного ответа
    await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_operations.quiz_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await quiz_operations.update_quiz_index(callback.from_user.id, current_question_index, correct_answers)

    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_operations.quiz_data):
        # Следующий вопрос
        await quiz_operations.get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
        result_string = await quiz_operations.get_users_answers()
        await callback.message.answer("Результаты участников: ")
        await callback.message.answer(result_string)

# Запуск процесса поллинга новых апдейтов
async def main():
    await quiz_operations.create_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
