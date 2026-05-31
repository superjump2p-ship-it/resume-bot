import asyncio
import sqlite3

from aiogram import Bot, Dispatcher, Router
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message,
)
from aiogram.filters import CommandStart, Command


TOKEN = ""

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()


# =====================================
# ПОДКЛЮЧЕНИЕ SQLITE
# =====================================

# Создаем файл database.db
conn = sqlite3.connect("database.db")

# Объект для SQL команд
cursor = conn.cursor()

# Создаем таблицу resumes если ее нет
cursor.execute("""
CREATE TABLE IF NOT EXISTS resumes (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    age INTEGER,
    position TEXT,
    experience TEXT
)
""")

# Сохраняем изменения
conn.commit()


# =====================================
# STATES
# =====================================

# Тут храним состояние пользователя
states = {}


# =====================================
# START
# =====================================


@router.message(CommandStart())
async def cmd_start(message: Message):

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋Create a Resume",
                    callback_data="resume"
                )
            ],
            [
                InlineKeyboardButton(
                    text = "📝Edit Resume",
                    callback_data = "edit"
                )
            ],
            [
                InlineKeyboardButton(
                    text = "🗑Delete resume",
                    callback_data = "delete"
                )
            ]
        ]
    )

    await message.answer(
        "Hi! I am a bot that will help you create a resume.\n"
        "Click the button below to start creating your resume.\n",
        "You can write /cancel to cancelled form and /myresume for check your resume",
        reply_markup=kb
    )


# =====================================
# BUTTONS
# =====================================

@router.callback_query()
async def button(callback: CallbackQuery):
    user_id = callback.from_user.id
    # Проверяем какая кнопка нажата
    if callback.data == "resume":


        # Устанавливаем первое состояние
        states[user_id] = "wait_name"
        await callback.message.answer("What is your name?")
    elif callback.data == "delete":
        cursor.execute(
            """
            SELECT *
            FROM resumes
            WHERE user_id = ?
            """,
            (user_id,)
        )

        data = cursor.fetchone()

        if data is None:
            await callback.message.answer(
                "You haven't created a resume yet."
            )
        else:
            cursor.execute(
                """
                DELETE FROM resumes
                WHERE user_id = ?
                """,
                (user_id,)
            )

            conn.commit()

            await callback.message.answer(
                "Resume deleted"
            )


        
    elif callback.data == "edit":
        cursor.execute(
            """
            SELECT * FROM resumes 
            WHERE user_id = ?
            """,
            (user_id,)
        )
        data = cursor.fetchone()
        if data is None or None in data:
            await callback.message.answer("You haven't created a resume yet.")
        else:
            fb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Name",
                            callback_data="edit_name"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Age",
                            callback_data="edit_age"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Position",
                            callback_data="edit_position"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Experience",
                            callback_data="edit_e"
                        )
                    ]
                ]
            )
            await callback.message.answer(
                f"📋Here is your resume data:\n\n"
                f"👤Name: {data[1]}\n"
                f"🎂Age: {data[2]}\n"
                f"💼Position: {data[3]}\n"
                f"🚀Experience: {data[4]}\n\n\n"
                f"Whats do you want to edit?",
                reply_markup=fb
            )
    if callback.data == "edit_name":
        states[user_id] = "edit_name"
        await callback.message.answer("Enter new name:")
        await callback.answer()

    if callback.data == "edit_age":
        states[user_id] = "edit_age"
        await callback.message.answer("Enter new age:")
        await callback.answer()

    if callback.data == "edit_position":
        states[user_id] = "edit_position"
        await callback.message.answer("Enter new position:")
        await callback.answer()

    if callback.data == "edit_e":
        states[user_id] = "edit_e"
        await callback.message.answer("Enter new experience:")
        await callback.answer()
    await callback.answer()


@router.message(Command("cancel"))
async def cancel(message: Message):
    user_id = message.from_user.id
    if user_id in states:
        states.pop(user_id, None)
        await message.answer("You dont have an active form.")
    else:

        await message.answer("Form cancelled")


@router.message(Command("myresume"))
async def my_resume(message: Message):

    user_id = message.from_user.id

    # Ищем resume пользователя
    cursor.execute(
        """
        SELECT name, age, position, experience
        FROM resumes
        WHERE user_id = ?
        """,
        (user_id,)
    )

    data = cursor.fetchone()

    # Если resume нет
    if data is None:
        await message.answer("You do not have a resume yet")
        return

    # Отправляем resume
    await message.answer(
        f"📋Your resume:\n\n"
        f"👤Name: {data[0]}\n"
        f"🎂Age: {data[1]}\n"
        f"💼Position: {data[2]}\n"
        f"🚀Experience: {data[3]}"
    )
# =====================================
# FORM
# =====================================

@router.message()
async def form(message: Message):

    user_id = message.from_user.id

    # Если пользователь не начал анкету
    if user_id not in states:
        return

    # Получаем текущее состояние
    state = states[user_id]

    if state == "edit_name":
        cursor.execute(
            """
            UPDATE resumes
            SET name = ?
            WHERE user_id = ?
            """,
            (message.text, user_id)
        )
        conn.commit()
        states.pop(user_id, None)
        await message.answer("Name updated🤓")
        return
    if state == "edit_age":
        if not message.text.isdigit():
            await message.answer("Age must be a number😕")
            return
        cursor.execute(
            """
            UPDATE resumes
            SET age = ?
            WHERE user_id = ?
            """,
            (int(message.text), user_id)
        )
        conn.commit()
        states.pop(user_id, None)
        await message.answer("Age updated😁")
        return
    if state == "edit_position":
        cursor.execute(
            """
            UPDATE resumes
            SET position = ?
            WHERE user_id = ?
            """,
            (message.text, user_id)
        )
        conn.commit()
        states.pop(user_id, None)
        await message.answer("Position updated🧐")
        return
    if state == "edit_e":
        cursor.execute(
            """
            UPDATE resumes
            SET experience = ?
            WHERE user_id = ?
            """,
            (message.text, user_id)
        )
        conn.commit()
        await message.answer("Experience updated👨‍💻")
        states.pop(user_id, None)
        return
    #проверка на нажатие кнопки edit resume

    
    
    if state == "wait_name":

        # Создаем resume и сохраняем имя
        cursor.execute(
            """
            INSERT OR REPLACE INTO resumes (user_id, name)
            VALUES (?, ?)
            """,
            (user_id, message.text)
        )

        conn.commit()

        # Меняем состояние
        states[user_id] = "wait_age"

        await message.answer("How old are you?")

        return

    # =========================
    # ВВОД ВОЗРАСТА
    # =========================
    if state == "wait_age":

        # Проверяем что введены цифры
        if not message.text.isdigit():
            await message.answer("Age must be a number")
            return

        # Сохраняем возраст
        cursor.execute(
            """
            UPDATE resumes
            SET age = ?
            WHERE user_id = ?
            """,
            (int(message.text), user_id)
        )

        conn.commit()

        # Следующее состояние
        states[user_id] = "wait_position"

        await message.answer("What position do you want to work in?")

        return

    # =========================
    # ВВОД ДОЛЖНОСТИ
    # =========================
    if state == "wait_position":

        # Сохраняем должность
        cursor.execute(
            """
            UPDATE resumes
            SET position = ?
            WHERE user_id = ?
            """,
            (message.text, user_id)
        )

        conn.commit()

        states[user_id] = "wait_experience"

        await message.answer(
            "How many years of work experience do you have?"
        )

        return

    # =========================
    # ВВОД ОПЫТА
    # =========================
    if state == "wait_experience":
        if not message.text.isdigit():
            await message.answer("Experience must be a number😕")
            return
        # Сохраняем опыт
        else:

            cursor.execute(
                """
                UPDATE resumes
                SET experience = ?
                WHERE user_id = ?
                """,
                (message.text, user_id)
            )

            conn.commit()

        # Получаем данные пользователя
            cursor.execute(
                """
                SELECT name, age, position, experience
                FROM resumes
                WHERE user_id = ?
                """,
                (user_id,)
            )

            data = cursor.fetchone()

        # Отправляем резюме
            await message.answer(
                f"📋Here is your resume:\n\n"
                f"👤Name: {data[0]}\n"
                f"🎂Age: {data[1]}\n"
                f"💼Position: {data[2]}\n"
                f"🚀Experience: {data[3]}"
            )

        # Очищаем состояние
            del states[user_id]

            return


# =====================================
# /MYRESUME
# =====================================




# =====================================
# ROUTER
# =====================================

dp.include_router(router)


# =====================================
# START BOT
# =====================================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())