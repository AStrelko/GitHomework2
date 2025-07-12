import logging
import random
import re
import math
from math import sqrt
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

TOKEN = "7352584031:AAHDzO6SXIgaSpOqHueegy7sOhKIOI-5f-A"
#### SAV_calculatorBot ####
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
user_states = {}


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        f"Привіт, {message.from_user.first_name}!\nВибери, що ти бажаєш зробити:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Обчислити математичний вираз", callback_data="calculate_expr")],
            [InlineKeyboardButton(text="Обчислити площу геометричних фігур", callback_data="calculate_area")],
            [InlineKeyboardButton(text="Хочеш пограти в цікаву гру?", callback_data="calculate_game")],
            [InlineKeyboardButton(text="Розповісти щось цікаве про число", callback_data="number_fact")]
        ])
    )


def is_safe(expression):
    expr = expression.replace("sqrt", "")
    expr = expr.replace("**", "^")
    pattern = r"^[0-9+\-*/().\s^]*$"
    return re.fullmatch(pattern, expr) is not None

def safe_eval(expr):
    try:
        expr = expr.replace("^", "**")
        return eval(expr, {"__builtins__": {}}, {"sqrt": sqrt})
    except Exception:
        return "Помилка у виразі."

def generate_unique_number():
    while True:
        num = random.randint(1000, 9999)
        digits = str(num)
        if len(set(digits)) == 4:
            return digits


@dp.callback_query(F.data.in_([
    "calculate_expr", "calculate_area","calculate_game", "number_fact",
    "circle", "rectangle", "other_shapes"
]))
async def process_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if callback.data == "calculate_expr":
        user_states[user_id] = "wait_expression"
        await callback.message.answer("Надішли мені математичний вираз:\nНаприклад:\n 2 + 2 * 3\n sqrt(9)\n 2^3")

    elif callback.data == "calculate_area":
        await callback.message.answer("Оберіть фігуру:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Коло", callback_data="circle")],
            [InlineKeyboardButton(text="Прямокутник", callback_data="rectangle")],
            [InlineKeyboardButton(text="Інші фігури", callback_data="other_shapes")]
        ]))

    elif callback.data == "circle":
        user_states[user_id] = "wait_circle_radius"
        await callback.message.answer("Введи радіус кола:")

    elif callback.data == "rectangle":
        user_states[user_id] = "wait_rectangle"
        await callback.message.answer("Введи ширину і довжину прямокутника через пробіл (наприклад: 4 6):")

    elif callback.data == "other_shapes":
        user_states[user_id] = None
        await callback.message.answer("Дізнатись про інші фігури можна тут:\nhttps://uk.wikipedia.org/wiki/Площа_фігури")

    elif callback.data == "number_fact":
        user_states[user_id] = "wait_number"
        await callback.message.answer("Введи число, і я розповім щось цікаве!")
    elif callback.data == "calculate_game":
        user_states[user_id] = "game_number"
        await callback.message.answer("Я задумав число від 1000 до 9999 \n(цифри в якому не повторюються).\nСпробуй його вгадати")

    await callback.answer()


@dp.message(F.text)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)
    text = message.text.strip()
    if state == "wait_expression":
        if is_safe(text):
            result = safe_eval(text)
            await message.answer(f"Результат: {result}")
        else:
            await message.answer("У виразі знайдено заборонені символи.")
        user_states[user_id] = None

    elif state == "wait_circle_radius":
        try:
            radius = float(text)
            area = math.pi * radius ** 2
            await message.answer(f"Площа кола з радіусом {radius} = {area:.2f}")
        except ValueError:
            await message.answer("Будь ласка, введи число для радіуса.")
        user_states[user_id] = None

    elif state == "wait_rectangle":
        parts = text.split()
        if len(parts) == 2:
            try:
                area = float(parts[0]) * float(parts[1])
                await message.answer(f"Площа прямокутника: {float(parts[1])} × {float(parts[1])} = {area:.2f}")
            except ValueError:
                await message.answer("Будь ласка, введи два числа через пробіл.")
        else:
            await message.answer("Введи два числа через пробіл (наприклад: 5 10).")
        user_states[user_id] = None

    elif state == "wait_number":
        try:
            number = float(text)
            response = []

            if number.is_integer() and number > 0:
                response.append(f"{int(number)} — натуральне число.")
            else:
                response.append(f"{number} — не є натуральним числом.")

            if number.is_integer():
                if int(number) % 2 == 0:
                    response.append("Це парне число")
                else:
                    response.append("Це не парне число")
            else:
                response.append(" Не можна визначити ділення на 2 для дробового числа.")

            if number.is_integer():
                n = abs(int(number))
                divisors = [str(i) for i in range(1, n + 1) if n % i == 0]
                response.append(f" Дільники числа: {' , '.join(divisors)}")
            else:
                response.append(" У дробового числа немає цілочисельних дільників.")

            await message.answer("\n".join(response))

        except ValueError:
            await message.answer("Будь ласка, введи коректне число.")

        user_states[user_id] = None
    elif state == "game_number":
        guess = text.strip()
        secret = user_states.get(f"{user_id}_secret")

        if not secret:
            secret = generate_unique_number()
            user_states[f"{user_id}_secret"] = secret
            await message.answer("Чудово! Я загадав число з 4 різних цифр. Спробуй вгадати!")

        elif not guess.isdigit() or len(guess) != 4 or len(set(guess)) != 4:
            await message.answer("Введи 4-значне число з різними цифрами.")
        else:
            bulls = sum(secret[i] == guess[i] for i in range(4))  # на своїх місцях
            cows = sum(1 for d in guess if d in secret) - bulls  # правильні, але не на місці

            if guess == secret:
                await message.answer(" Ти вгадав число! Молодець!\nНатисни /start, щоб зіграти ще раз.")
                user_states[user_id] = None
                user_states.pop(f"{user_id}_secret", None)
            else:
                await message.answer(f" У числі є {cows + bulls} правильних цифр,\n✔ {bulls} стоять на своєму місці.")
    else:
        await message.answer("Натисни /start, щоб розпочати.")



async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())