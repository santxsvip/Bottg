import asyncio
import sqlite3

from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- Налаштування ---
TOKEN = "7834904438:AAHubO40vClDMquA36JXozqkDMVnV9kMPNQ"
ADMIN_IDS = [6167391728, 6668526095, 5343772278]  # Список telegram user_id адмінів
GROUP_LINK = "https://t.me/dniproallo"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()

# --- Підключення бази ---
conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER,
    username TEXT,
    q1 TEXT,
    q2 TEXT,
    q3 TEXT,
    q4 TEXT,
    q5 TEXT,
    q6 TEXT,
    video_file_id TEXT
)
""")
conn.commit()

# --- FSM стани ---
class JoinForm(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()
    q4 = State()
    q5 = State()
    q6 = State()
    video = State()

# --- /start ---
@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await message.answer(
        "Увасап!) Я — бот-провідник. Якщо хочеш знайти дрогу до нашої групи, треба пройти обов'язкове опитування. Будь готовий, що в кінці попрошу кружечок для підтвердження, що ти реальна людина.\n\n"
        "Готовий(-а) почати?",
        reply_markup=InlineKeyboardBuilder()
            .button(text="Почати", callback_data="start_form")
            .as_markup()
    )
    await state.clear()

@router.callback_query(F.data == "start_form")
async def start_form(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("1.Скільки тобі років?")
    await state.set_state(JoinForm.q1)
    await callback.answer()

@router.message(JoinForm.q1)
async def process_q1(message: types.Message, state: FSMContext):
    await state.update_data(q1=message.text)
    await message.answer("2.На якому районі проживаєш?")
    await state.set_state(JoinForm.q2)

@router.message(JoinForm.q2)
async def process_q2(message: types.Message, state: FSMContext):
    await state.update_data(q2=message.text)
    await message.answer("3.Якщо ти не хочеш світити обличчя в соцмережах, чи готовий допомогти з реквізитами, людьми або ідеями?")
    await state.set_state(JoinForm.q3)

@router.message(JoinForm.q3)
async def process_q3(message: types.Message, state: FSMContext):
    await state.update_data(q3=message.text)
    await message.answer("4.Чи є різниця якою мовою говорить людина?")
    await state.set_state(JoinForm.q4)

@router.message(JoinForm.q4)
async def process_q4(message: types.Message, state: FSMContext):
    await state.update_data(q4=message.text)
    await message.answer("5.Наскільки ти відкритий In Real Life? І якшо слабо, то скільки часу на адаптацію тобі потрібно?")
    await state.set_state(JoinForm.q5)

@router.message(JoinForm.q5)
async def process_q5(message: types.Message, state: FSMContext):
    await state.update_data(q5=message.text)
    await message.answer("6.Як ставишся до шкідливих звичок?")
    await state.set_state(JoinForm.q6)

@router.message(JoinForm.q6)
async def process_q6(message: types.Message, state: FSMContext):
    await state.update_data(q6=message.text)
    await message.answer("7.Запиши кружечок зі словами: Повір мені провідник, я справжній.")
    await state.set_state(JoinForm.video)

@router.message(JoinForm.video)
async def process_video_note(message: types.Message, state: FSMContext):
    if not message.video_note:
        await message.answer("❗ Це звісно цікаво, а кружечок буде сьодні?).")
        return

    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    video_id = message.video_note.file_id

    # Зберігаємо в базу
    try:
        cursor.execute(
    "INSERT INTO users (user_id, username, q1, q2, q3, q4, q5, q6, video_file_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (
        user_id,
        username,
        data['q1'],
        data['q2'],
        data['q3'],
        data['q4'],
        data['q5'],
        data['q6'],
        video_id
    )
)
        conn.commit()
    except Exception as e:
        await message.answer("Ой, шось я накрився походу, спробуй трохи пізже.")
        print(f"DB error: {e}")
        return

    # Відправляємо адмінам
    for admin_id in ADMIN_IDS:
        try:
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Годиться", callback_data=f"approve:{user_id}")
            builder.adjust(1)  # одна кнопка в ряд

            text = (
                f"🧾 <b>Заявка від:</b> @{username}\n\n"
                f"1. Скільки тобі років? - {data['q1']}\n"
                f"2. Район? - {data['q2']}\n"
                f"3. Прийняття участі в відео - {data['q3']}\n"
                f"4. Чи є різниця якою мовою говорить людина? - {data['q4']}\n"
                f"5. Відкритість людини - {data['q5']}\n"
                f"6. Як ставишся до шкідливих звичок? Які сам маєш? - {data['q6']}"
            )

            await bot.send_message(admin_id, text, reply_markup=builder.as_markup())

            if video_id:
                await bot.send_video_note(admin_id, video_note=video_id)

            print(f"📬 Заявка надіслана адміну {admin_id}")

        except Exception as e:
            print(f"❌ Помилка надсилання адміну {admin_id}: {e}")

    await message.answer("✅ Чекай доки адміни перевірять шо ти понаписував(ла).")
    await state.clear()

# --- Обробка кнопки підтвердження адміністратором ---
@router.callback_query(F.data.startswith("approve:"))
async def approve_handler(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    try:
        await bot.send_message(user_id, f"🎉 Оййй бл*ь, нарешті ці шкіряні підтвердили тебе і тепер я покажу дорогу: {GROUP_LINK}")
        await callback.answer("Йому дійшло повідомлення, хай дума заходить чи нє ✅", show_alert=True)
    except Exception as e:
        await callback.answer("Не вдалося написати користувачу ❌", show_alert=True)
        print(f"Помилка повідомлення користувачу {user_id}: {e}")

# --- Підключаємо роутер та запускаємо бота ---
dp.include_router(router)

async def main():
    print("Бот запущено...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())