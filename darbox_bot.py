"""
🎁 DARBOX — Telegram-бот подписки на аромабоксы
DAR Perfum (@nasomato)

Запуск:
1. pip install aiogram
2. Вставить токен бота в BOT_TOKEN
3. python darbox_bot.py
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode

# ===================== НАСТРОЙКИ =====================
BOT_TOKEN = "8054022324:AAHK2bUZ1lLEDk8FREDbAEl5En040OtEHg0"
ADMIN_USERNAME = "nasomato"  # Твой username без @
ADMIN_CHAT_ID = None  # Заполнится автоматически при /admin

# Реквизиты для оплаты (измени на свои)
PAYMENT_DETAILS = """💳 <b>Реквизиты для оплаты:</b>

🏦 Сбербанк: <code>2202 XXXX XXXX XXXX</code>
👤 Получатель: Имя Фамилия

Или по номеру телефона:
📱 <code>+7 977 573 31 79</code> (Сбербанк)

После перевода нажмите кнопку «Я оплатил» ниже."""

# ===================== ТАРИФЫ =====================
BOXES = {
    "8x3": {"name": "8 ароматов × 3 мл", "short": "8×3мл", "price": 1980, "count": 8, "vol": "3 мл"},
    "6x6": {"name": "6 ароматов × 6 мл", "short": "6×6мл", "price": 2380, "count": 6, "vol": "6 мл"},
    "5x10": {"name": "5 ароматов × 10 мл", "short": "5×10мл", "price": 3580, "count": 5, "vol": "10 мл"},
}

DURATIONS = {
    2: {"months": 2, "discount": 0, "label": "2 месяца"},
    4: {"months": 4, "discount": 5, "label": "4 месяца (−5%)"},
    6: {"months": 6, "discount": 10, "label": "6 месяцев (−10%)"},
}

def calc_price(box_key, months):
    base = BOXES[box_key]["price"]
    discount = DURATIONS[months]["discount"]
    monthly = round(base * (100 - discount) / 100)
    total = monthly * months
    return monthly, total

# ===================== БАЗА ДАННЫХ =====================
DB_PATH = "darbox.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        created_at TEXT,
        -- Анкета
        gender TEXT,
        age TEXT,
        lifestyle TEXT,
        occasions TEXT,
        intensity TEXT,
        fav_notes TEXT,
        disliked_notes TEXT,
        current_perfumes TEXT,
        season_pref TEXT,
        discovery TEXT,
        allergies TEXT,
        extra_wishes TEXT,
        -- Подписка
        box_type TEXT,
        duration_months INTEGER,
        monthly_price INTEGER,
        total_price INTEGER,
        -- Доставка
        full_name TEXT,
        phone TEXT,
        address TEXT,
        -- Статус
        status TEXT DEFAULT 'new',
        subscription_start TEXT,
        subscription_end TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        month_num INTEGER,
        aroma_name TEXT,
        rating INTEGER,
        comment TEXT,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS admin_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        note TEXT,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        direction TEXT,
        text TEXT,
        created_at TEXT
    )""")
    conn.commit()
    conn.close()

def save_user(user_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    fields = list(data.keys())
    placeholders = ", ".join(fields)
    values_ph = ", ".join(["?"] * len(fields))
    updates = ", ".join([f"{f}=excluded.{f}" for f in fields])
    vals = [data[f] for f in fields]
    c.execute(f"""INSERT INTO users (user_id, {placeholders}) VALUES (?, {values_ph})
        ON CONFLICT(user_id) DO UPDATE SET {updates}""", [user_id] + vals)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_subscribers():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE box_type IS NOT NULL ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_feedback(user_id, month_num, aroma_name, rating, comment):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO feedback (user_id, month_num, aroma_name, rating, comment, created_at) VALUES (?,?,?,?,?,?)",
              (user_id, month_num, aroma_name, rating, comment, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_feedback(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM feedback WHERE user_id=? ORDER BY month_num, id", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_message(user_id, direction, text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO messages (user_id, direction, text, created_at) VALUES (?,?,?,?)",
              (user_id, direction, text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# Track which user the admin is chatting with
admin_chatting_with = {}  # {admin_chat_id: user_id}

# ===================== СОСТОЯНИЯ =====================
class Reg(StatesGroup):
    gender = State()
    age = State()
    lifestyle = State()
    occasions = State()
    intensity = State()
    fav_notes = State()
    disliked_notes = State()
    current_perfumes = State()
    season_pref = State()
    discovery = State()
    allergies = State()
    extra_wishes = State()
    box_type = State()
    duration = State()
    full_name = State()
    phone = State()
    address = State()
    confirm = State()

class Fb(StatesGroup):
    month = State()
    aroma = State()
    rating = State()
    comment = State()
    more = State()

class Broadcast(StatesGroup):
    text = State()

class AdminChat(StatesGroup):
    chatting = State()  # Админ общается с конкретным клиентом

class PaymentConfirm(StatesGroup):
    waiting = State()  # Клиент подтверждает оплату

# ===================== КЛАВИАТУРЫ =====================
def inline_kb(buttons, row_width=2):
    """buttons = [(text, callback_data), ...]"""
    rows = []
    row = []
    for text, cb in buttons:
        row.append(InlineKeyboardButton(text=text, callback_data=cb))
        if len(row) >= row_width:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ===================== БОТ =====================
bot = Bot(token=BOT_TOKEN, default={"parse_mode": "HTML"})
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# ---- /start ----
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    save_user(message.from_user.id, {
        "username": message.from_user.username or "",
        "first_name": message.from_user.first_name or "",
        "created_at": datetime.now().isoformat(),
    })

    text = """🖤 <b>DAR PERFUM</b> — Парфюмерная Лаборатория

━━━━━━━━━━━━━━━━━━

🎁 <b>DARBOX — подписка на аромабоксы</b>

Каждый месяц мы собираем для вас уникальный набор ароматов, подобранных по вашему вкусу.

Вы не знаете, что внутри — это сюрприз 🎉
Но мы знаем ваши предпочтения и подбираем ароматы, которые вам точно понравятся.

<b>Как это работает:</b>
1️⃣ Вы проходите парфюмерную анкету
2️⃣ Выбираете формат и срок подписки
3️⃣ Каждый месяц получаете бокс-сюрприз
4️⃣ Оставляете отзыв — мы учитываем ваш вкус

<b>Форматы:</b>
• 8 ароматов × 3 мл — <b>1 980 ₽/мес</b>
• 6 ароматов × 6 мл — <b>2 380 ₽/мес</b>
• 5 ароматов × 10 мл — <b>3 580 ₽/мес</b>

🔥 <i>Подписка на 4 мес — скидка 5%
Подписка на 6 мес — скидка 10%</i>

━━━━━━━━━━━━━━━━━━"""

    kb = inline_kb([
        ("🌸 Пройти анкету и оформить", "start_questionnaire"),
        ("📋 Мои подписки", "my_sub"),
        ("💬 Оставить отзыв", "feedback_start"),
    ], row_width=1)

    await message.answer(text, reply_markup=kb)

# ---- АНКЕТА ----
@router.callback_query(F.data == "start_questionnaire")
async def start_q(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "🌿 <b>Парфюмерная анкета</b>\n\n"
        "Ответьте на несколько вопросов, чтобы мы подобрали идеальные ароматы для вас.\n\n"
        "Это займёт 2-3 минуты ✨"
    )
    await asyncio.sleep(0.5)
    await callback.message.answer(
        "👤 <b>Шаг 1/12 — Пол</b>\n\nДля кого подбираем ароматы?",
        reply_markup=inline_kb([
            ("🙋‍♂️ Мужской", "g_male"),
            ("🙋‍♀️ Женский", "g_female"),
            ("🎁 В подарок", "g_gift"),
        ])
    )
    await state.set_state(Reg.gender)

@router.callback_query(Reg.gender, F.data.startswith("g_"))
async def q_gender(cb: CallbackQuery, state: FSMContext):
    val = {"g_male": "Мужской", "g_female": "Женский", "g_gift": "В подарок"}[cb.data]
    await state.update_data(gender=val)
    await cb.answer()
    await cb.message.edit_text(
        "📅 <b>Шаг 2/12 — Возраст</b>\n\nВаша возрастная группа?",
        reply_markup=inline_kb([
            ("18-25", "a_18"), ("26-35", "a_26"),
            ("36-45", "a_36"), ("46+", "a_46"),
        ])
    )
    await state.set_state(Reg.age)

@router.callback_query(Reg.age, F.data.startswith("a_"))
async def q_age(cb: CallbackQuery, state: FSMContext):
    val = {"a_18": "18-25", "a_26": "26-35", "a_36": "36-45", "a_46": "46+"}[cb.data]
    await state.update_data(age=val)
    await cb.answer()
    await cb.message.edit_text(
        "🏃 <b>Шаг 3/12 — Образ жизни</b>\n\nКак бы вы описали свой стиль?",
        reply_markup=inline_kb([
            ("💼 Офис / деловой", "l_office"),
            ("🎨 Творческий / свободный", "l_creative"),
            ("🏋️ Спортивный / активный", "l_sport"),
            ("🌙 Домашний / уютный", "l_home"),
        ], row_width=1)
    )
    await state.set_state(Reg.lifestyle)

@router.callback_query(Reg.lifestyle, F.data.startswith("l_"))
async def q_lifestyle(cb: CallbackQuery, state: FSMContext):
    vals = {"l_office": "Деловой/офис", "l_creative": "Творческий", "l_sport": "Спортивный", "l_home": "Домашний/уютный"}
    await state.update_data(lifestyle=vals[cb.data])
    await cb.answer()
    await cb.message.edit_text(
        "🎭 <b>Шаг 4/12 — Повод</b>\n\nГде вы чаще носите ароматы?",
        reply_markup=inline_kb([
            ("📆 На каждый день", "o_daily"),
            ("🌃 На выход / свидание", "o_evening"),
            ("🏢 На работу", "o_work"),
            ("🔀 Везде по-разному", "o_mixed"),
        ], row_width=1)
    )
    await state.set_state(Reg.occasions)

@router.callback_query(Reg.occasions, F.data.startswith("o_"))
async def q_occasions(cb: CallbackQuery, state: FSMContext):
    vals = {"o_daily": "На каждый день", "o_evening": "На выход", "o_work": "На работу", "o_mixed": "Везде по-разному"}
    await state.update_data(occasions=vals[cb.data])
    await cb.answer()
    await cb.message.edit_text(
        "💨 <b>Шаг 5/12 — Интенсивность</b>\n\nКакие ароматы предпочитаете?",
        reply_markup=inline_kb([
            ("🌬 Лёгкие, еле заметные", "i_light"),
            ("☁️ Умеренные", "i_medium"),
            ("🔥 Мощные, шлейфовые", "i_heavy"),
            ("🎲 Люблю разные", "i_mixed"),
        ], row_width=1)
    )
    await state.set_state(Reg.intensity)

@router.callback_query(Reg.intensity, F.data.startswith("i_"))
async def q_intensity(cb: CallbackQuery, state: FSMContext):
    vals = {"i_light": "Лёгкие", "i_medium": "Умеренные", "i_heavy": "Мощные", "i_mixed": "Разные"}
    await state.update_data(intensity=vals[cb.data])
    await cb.answer()
    await cb.message.edit_text(
        "🌸 <b>Шаг 6/12 — Любимые ноты</b>\n\nЧто вам нравится? Можно выбрать несколько.",
        reply_markup=inline_kb([
            ("🍋 Цитрусовые", "fn_citrus"), ("🌹 Цветочные", "fn_floral"),
            ("🌳 Древесные", "fn_woody"), ("🍦 Ванильные/сладкие", "fn_sweet"),
            ("🌊 Свежие/морские", "fn_fresh"), ("🌶 Пряные", "fn_spicy"),
            ("💼 Кожаные", "fn_leather"), ("☕ Кофейные/табачные", "fn_dark"),
            ("🥥 Кокос/тропики", "fn_tropical"), ("⏭ Пропустить", "fn_skip"),
        ], row_width=2)
    )
    await state.update_data(_fav_notes=[])
    await state.set_state(Reg.fav_notes)

NOTE_LABELS = {
    "fn_citrus": "🍋 Цитрусовые", "fn_floral": "🌹 Цветочные", "fn_woody": "🌳 Древесные",
    "fn_sweet": "🍦 Ванильные/сладкие", "fn_fresh": "🌊 Свежие/морские", "fn_spicy": "🌶 Пряные",
    "fn_leather": "💼 Кожаные", "fn_dark": "☕ Кофейные/табачные", "fn_tropical": "🥥 Тропические",
}

@router.callback_query(Reg.fav_notes, F.data.startswith("fn_"))
async def q_fav(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fav = data.get("_fav_notes", [])

    if cb.data == "fn_skip" or cb.data == "fn_done":
        await state.update_data(fav_notes=", ".join(fav) if fav else "Не выбрано")
        await cb.answer()
        await cb.message.edit_text(
            "🚫 <b>Шаг 7/12 — Нелюбимые ноты</b>\n\nЧего точно НЕ хотите в боксе?",
            reply_markup=inline_kb([
                ("🍋 Цитрусовые", "dn_citrus"), ("🌹 Цветочные", "dn_floral"),
                ("🌳 Древесные", "dn_woody"), ("🍦 Сладкие", "dn_sweet"),
                ("🌊 Морские", "dn_fresh"), ("🌶 Пряные", "dn_spicy"),
                ("💼 Кожаные", "dn_leather"), ("☕ Табачные", "dn_dark"),
                ("⏭ Ничего, всё ок", "dn_skip"),
            ], row_width=2)
        )
        await state.update_data(_dis_notes=[])
        await state.set_state(Reg.disliked_notes)
        return

    label = NOTE_LABELS.get(cb.data, cb.data)
    if label not in fav:
        fav.append(label)
    await state.update_data(_fav_notes=fav)
    await cb.answer(f"✓ {label} добавлено")

    # Update keyboard to show "Готово"
    buttons = [
        ("🍋 Цитрусовые", "fn_citrus"), ("🌹 Цветочные", "fn_floral"),
        ("🌳 Древесные", "fn_woody"), ("🍦 Ванильные/сладкие", "fn_sweet"),
        ("🌊 Свежие/морские", "fn_fresh"), ("🌶 Пряные", "fn_spicy"),
        ("💼 Кожаные", "fn_leather"), ("☕ Кофейные/табачные", "fn_dark"),
        ("🥥 Кокос/тропики", "fn_tropical"),
        (f"✅ Готово ({len(fav)} выбрано)", "fn_done"),
    ]
    await cb.message.edit_reply_markup(reply_markup=inline_kb(buttons, row_width=2))

DIS_LABELS = {
    "dn_citrus": "Цитрусовые", "dn_floral": "Цветочные", "dn_woody": "Древесные",
    "dn_sweet": "Сладкие", "dn_fresh": "Морские", "dn_spicy": "Пряные",
    "dn_leather": "Кожаные", "dn_dark": "Табачные",
}

@router.callback_query(Reg.disliked_notes, F.data.startswith("dn_"))
async def q_dis(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    dis = data.get("_dis_notes", [])

    if cb.data == "dn_skip" or cb.data == "dn_done":
        await state.update_data(disliked_notes=", ".join(dis) if dis else "Нет ограничений")
        await cb.answer()
        await cb.message.edit_text(
            "👃 <b>Шаг 8/12 — Текущие ароматы</b>\n\n"
            "Напишите ароматы, которые вы носите сейчас или носили раньше и вам нравились.\n\n"
            "<i>Например: Sauvage, Baccarat Rouge 540, Lost Cherry</i>\n\n"
            "Или напишите «Нет» если не знаете."
        )
        await state.set_state(Reg.current_perfumes)
        return

    label = DIS_LABELS.get(cb.data, cb.data)
    if label not in dis:
        dis.append(label)
    await state.update_data(_dis_notes=dis)
    await cb.answer(f"✓ {label} исключено")
    buttons = [
        ("🍋 Цитрусовые", "dn_citrus"), ("🌹 Цветочные", "dn_floral"),
        ("🌳 Древесные", "dn_woody"), ("🍦 Сладкие", "dn_sweet"),
        ("🌊 Морские", "dn_fresh"), ("🌶 Пряные", "dn_spicy"),
        ("💼 Кожаные", "dn_leather"), ("☕ Табачные", "dn_dark"),
        (f"✅ Готово ({len(dis)} исключено)", "dn_done"),
    ]
    await cb.message.edit_reply_markup(reply_markup=inline_kb(buttons, row_width=2))

@router.message(Reg.current_perfumes)
async def q_current(message: Message, state: FSMContext):
    await state.update_data(current_perfumes=message.text.strip())
    await message.answer(
        "🌤 <b>Шаг 9/12 — Сезон</b>\n\nКакой сезон для ароматов предпочитаете?",
        reply_markup=inline_kb([
            ("🌸 Весна/лето (свежие)", "s_spring"),
            ("🍂 Осень/зима (тёплые)", "s_autumn"),
            ("🔄 Люблю разные", "s_mixed"),
        ], row_width=1)
    )
    await state.set_state(Reg.season_pref)

@router.callback_query(Reg.season_pref, F.data.startswith("s_"))
async def q_season(cb: CallbackQuery, state: FSMContext):
    vals = {"s_spring": "Весна/лето", "s_autumn": "Осень/зима", "s_mixed": "Разные сезоны"}
    await state.update_data(season_pref=vals[cb.data])
    await cb.answer()
    await cb.message.edit_text(
        "🔬 <b>Шаг 10/12 — Открытия</b>\n\nГотовы ли вы к экспериментам с неожиданными ароматами?",
        reply_markup=inline_kb([
            ("🚀 Да, люблю новое!", "d_yes"),
            ("😌 Лучше проверенное", "d_safe"),
            ("⚖️ 50/50", "d_mix"),
        ], row_width=1)
    )
    await state.set_state(Reg.discovery)

@router.callback_query(Reg.discovery, F.data.startswith("d_"))
async def q_discovery(cb: CallbackQuery, state: FSMContext):
    vals = {"d_yes": "Люблю эксперименты", "d_safe": "Проверенное", "d_mix": "50/50"}
    await state.update_data(discovery=vals[cb.data])
    await cb.answer()
    await cb.message.edit_text(
        "⚠️ <b>Шаг 11/12 — Аллергии</b>\n\n"
        "Есть ли аллергия на какие-то компоненты?\n\n"
        "Напишите или нажмите «Нет».",
        reply_markup=inline_kb([("✅ Нет аллергий", "al_no")], row_width=1)
    )
    await state.set_state(Reg.allergies)

@router.callback_query(Reg.allergies, F.data == "al_no")
async def q_allergy_no(cb: CallbackQuery, state: FSMContext):
    await state.update_data(allergies="Нет")
    await cb.answer()
    await ask_extra(cb.message, state)

@router.message(Reg.allergies)
async def q_allergy_text(message: Message, state: FSMContext):
    await state.update_data(allergies=message.text.strip())
    await ask_extra(message, state)

async def ask_extra(msg, state):
    await msg.answer(
        "💬 <b>Шаг 12/12 — Пожелания</b>\n\n"
        "Хотите что-то добавить? Любые пожелания по ароматам.\n\n"
        "Или нажмите «Пропустить».",
        reply_markup=inline_kb([("⏭ Пропустить", "ex_skip")], row_width=1)
    )
    await state.set_state(Reg.extra_wishes)

@router.callback_query(Reg.extra_wishes, F.data == "ex_skip")
async def q_extra_skip(cb: CallbackQuery, state: FSMContext):
    await state.update_data(extra_wishes="—")
    await cb.answer()
    await show_box_choice(cb.message, state)

@router.message(Reg.extra_wishes)
async def q_extra_text(message: Message, state: FSMContext):
    await state.update_data(extra_wishes=message.text.strip())
    await show_box_choice(message, state)

# ---- ВЫБОР БОКСА ----
async def show_box_choice(msg, state):
    await msg.answer(
        "📦 <b>Выберите формат DARBOX</b>\n\n"
        f"• <b>8 × 3 мл</b> — {BOXES['8x3']['price']:,} ₽/мес\n"
        f"• <b>6 × 6 мл</b> — {BOXES['6x6']['price']:,} ₽/мес\n"
        f"• <b>5 × 10 мл</b> — {BOXES['5x10']['price']:,} ₽/мес\n",
        reply_markup=inline_kb([
            ("8 × 3 мл — 1 980 ₽", "box_8x3"),
            ("6 × 6 мл — 2 380 ₽", "box_6x6"),
            ("5 × 10 мл — 3 580 ₽", "box_5x10"),
        ], row_width=1)
    )
    await state.set_state(Reg.box_type)

@router.callback_query(Reg.box_type, F.data.startswith("box_"))
async def q_box(cb: CallbackQuery, state: FSMContext):
    key = cb.data.replace("box_", "")
    await state.update_data(box_type=key)
    await cb.answer()

    box = BOXES[key]
    lines = []
    for m, dur in DURATIONS.items():
        monthly, total = calc_price(key, m)
        lines.append(f"• <b>{dur['label']}</b> — {monthly:,} ₽/мес (итого {total:,} ₽)")

    await cb.message.edit_text(
        f"⏳ <b>Срок подписки</b>\n\n"
        f"Формат: {box['name']}\n\n" +
        "\n".join(lines),
        reply_markup=inline_kb([
            ("2 месяца", "dur_2"),
            ("4 месяца (−5%)", "dur_4"),
            ("6 месяцев (−10%)", "dur_6"),
        ], row_width=1)
    )
    await state.set_state(Reg.duration)

@router.callback_query(Reg.duration, F.data.startswith("dur_"))
async def q_dur(cb: CallbackQuery, state: FSMContext):
    months = int(cb.data.replace("dur_", ""))
    data = await state.get_data()
    monthly, total = calc_price(data["box_type"], months)
    await state.update_data(duration_months=months, monthly_price=monthly, total_price=total)
    await cb.answer()
    await cb.message.edit_text(
        "👤 <b>ФИО получателя</b>\n\nНапишите полное имя для доставки:"
    )
    await state.set_state(Reg.full_name)

@router.message(Reg.full_name)
async def q_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await message.answer("📱 <b>Телефон</b>\n\nНапишите номер телефона для связи:")
    await state.set_state(Reg.phone)

@router.message(Reg.phone)
async def q_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await message.answer(
        "🏠 <b>Адрес доставки</b>\n\n"
        "Напишите полный адрес:\n"
        "<i>Город, улица, дом, квартира, индекс</i>"
    )
    await state.set_state(Reg.address)

@router.message(Reg.address)
async def q_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    data = await state.get_data()

    box = BOXES[data["box_type"]]
    dur = DURATIONS[data["duration_months"]]
    monthly, total = calc_price(data["box_type"], data["duration_months"])

    summary = f"""📋 <b>Ваша заявка:</b>

━━━ <b>Парфюмерный профиль</b> ━━━
👤 Пол: {data.get('gender', '—')}
📅 Возраст: {data.get('age', '—')}
🏃 Стиль: {data.get('lifestyle', '—')}
🎭 Повод: {data.get('occasions', '—')}
💨 Интенсивность: {data.get('intensity', '—')}
🌸 Любимые ноты: {data.get('fav_notes', '—')}
🚫 Не любит: {data.get('disliked_notes', '—')}
👃 Текущие ароматы: {data.get('current_perfumes', '—')}
🌤 Сезон: {data.get('season_pref', '—')}
🔬 Открытия: {data.get('discovery', '—')}
⚠️ Аллергии: {data.get('allergies', '—')}
💬 Пожелания: {data.get('extra_wishes', '—')}

━━━ <b>Подписка</b> ━━━
📦 {box['name']}
⏳ {dur['label']}
💰 {monthly:,} ₽/мес (итого {total:,} ₽)

━━━ <b>Доставка</b> ━━━
👤 {data.get('full_name', '—')}
📱 {data.get('phone', '—')}
🏠 {data.get('address', '—')}"""

    await message.answer(
        summary + "\n\n<b>Всё верно?</b>",
        reply_markup=inline_kb([
            ("✅ Подтвердить", "confirm_yes"),
            ("✏️ Начать заново", "confirm_redo"),
        ])
    )
    await state.set_state(Reg.confirm)

@router.callback_query(Reg.confirm, F.data == "confirm_yes")
async def confirm_yes(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await cb.answer("✅ Заявка отправлена!")

    # Save to DB
    save_user(cb.from_user.id, {
        "username": cb.from_user.username or "",
        "first_name": cb.from_user.first_name or "",
        "gender": data.get("gender", ""),
        "age": data.get("age", ""),
        "lifestyle": data.get("lifestyle", ""),
        "occasions": data.get("occasions", ""),
        "intensity": data.get("intensity", ""),
        "fav_notes": data.get("fav_notes", ""),
        "disliked_notes": data.get("disliked_notes", ""),
        "current_perfumes": data.get("current_perfumes", ""),
        "season_pref": data.get("season_pref", ""),
        "discovery": data.get("discovery", ""),
        "allergies": data.get("allergies", ""),
        "extra_wishes": data.get("extra_wishes", ""),
        "box_type": data.get("box_type", ""),
        "duration_months": data.get("duration_months", 0),
        "monthly_price": data.get("monthly_price", 0),
        "total_price": data.get("total_price", 0),
        "full_name": data.get("full_name", ""),
        "phone": data.get("phone", ""),
        "address": data.get("address", ""),
        "status": "pending",
    })

    await cb.message.edit_text(
        "🎉 <b>Заявка оформлена!</b>\n\n"
        "Наш парфюмер свяжется с вами в ближайшее время через Telegram для подтверждения и оплаты.\n\n"
        "💬 Если у вас есть вопросы — напишите @nasomato\n\n"
        "Спасибо, что выбрали <b>DARBOX</b>! 🖤"
    )

    # Notify admin
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        box = BOXES[data["box_type"]]
        dur = DURATIONS[data["duration_months"]]
        monthly, total = calc_price(data["box_type"], data["duration_months"])

        admin_text = f"""🆕 <b>НОВАЯ ЗАЯВКА DARBOX!</b>

👤 @{cb.from_user.username or 'нет username'} ({cb.from_user.first_name})
🆔 ID: <code>{cb.from_user.id}</code>

━━━ Профиль ━━━
Пол: {data.get('gender')}
Возраст: {data.get('age')}
Стиль: {data.get('lifestyle')}
Повод: {data.get('occasions')}
Интенсивность: {data.get('intensity')}
❤️ Любимые: {data.get('fav_notes')}
🚫 Не любит: {data.get('disliked_notes')}
👃 Носит: {data.get('current_perfumes')}
Сезон: {data.get('season_pref')}
Открытия: {data.get('discovery')}
⚠️ Аллергии: {data.get('allergies')}
💬 Пожелания: {data.get('extra_wishes')}

━━━ Заказ ━━━
📦 {box['name']}
⏳ {dur['label']}
💰 {monthly:,} ₽/мес → итого {total:,} ₽

━━━ Доставка ━━━
👤 {data.get('full_name')}
📱 {data.get('phone')}
🏠 {data.get('address')}"""
        try:
            await bot.send_message(ADMIN_CHAT_ID, admin_text,
                reply_markup=inline_kb([
                    (f"💬 Написать клиенту", f"achat_{cb.from_user.id}"),
                    (f"✅ Подтвердить оплату", f"apay_{cb.from_user.id}"),
                ], row_width=1))
        except Exception as e:
            print(f"Admin notify error: {e}")

    # Send payment details to client
    data = await state.get_data()
    monthly, total = calc_price(data["box_type"], data["duration_months"])
    await asyncio.sleep(1)
    await cb.message.answer(
        f"💰 <b>Оплата подписки</b>\n\n"
        f"Сумма: <b>{total:,} ₽</b>\n"
        f"({data['duration_months']} мес × {monthly:,} ₽/мес)\n\n"
        f"{PAYMENT_DETAILS}",
        reply_markup=inline_kb([
            ("✅ Я оплатил(а)", "payment_done"),
            ("💬 Написать нам", "client_msg_start"),
        ], row_width=1)
    )

    await state.clear()

# ---- ОПЛАТА ----
@router.callback_query(F.data == "payment_done")
async def payment_done(cb: CallbackQuery):
    await cb.answer("✅ Спасибо!")
    await cb.message.edit_text(
        "⏳ <b>Проверяем оплату...</b>\n\n"
        "Мы проверим поступление средств и подтвердим вашу подписку.\n"
        "Обычно это занимает до 30 минут.\n\n"
        "Если есть вопросы — нажмите «Написать нам» ниже 👇",
        reply_markup=inline_kb([("💬 Написать нам", "client_msg_start")], row_width=1)
    )
    # Notify admin
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        user = get_user(cb.from_user.id)
        try:
            await bot.send_message(ADMIN_CHAT_ID,
                f"💳 <b>Клиент сообщил об оплате!</b>\n\n"
                f"👤 @{cb.from_user.username or '?'} ({cb.from_user.first_name})\n"
                f"🆔 <code>{cb.from_user.id}</code>\n"
                f"💰 {user.get('total_price', 0):,} ₽\n\n"
                f"Проверь поступление и подтверди:",
                reply_markup=inline_kb([
                    (f"✅ Подтвердить оплату", f"apay_{cb.from_user.id}"),
                    (f"💬 Написать клиенту", f"achat_{cb.from_user.id}"),
                ], row_width=1)
            )
        except:
            pass

# Admin confirms payment
@router.callback_query(F.data.startswith("apay_"))
async def admin_confirm_pay(cb: CallbackQuery):
    if cb.from_user.username != ADMIN_USERNAME:
        await cb.answer("⛔ Только админ"); return
    uid = int(cb.data.replace("apay_", ""))
    save_user(uid, {"status": "paid"})
    await cb.answer("✅ Оплата подтверждена!")
    await cb.message.edit_text(cb.message.text + "\n\n✅ <b>ОПЛАТА ПОДТВЕРЖДЕНА</b>")
    # Notify client
    try:
        await bot.send_message(uid,
            "🎉 <b>Оплата подтверждена!</b>\n\n"
            "Ваша подписка DARBOX активирована! 🖤\n"
            "Мы начнём собирать ваш первый аромабокс.\n\n"
            "Вы получите уведомление, когда бокс будет отправлен.\n\n"
            "💬 Если что — пишите прямо сюда, мы ответим!",
            reply_markup=inline_kb([("💬 Написать нам", "client_msg_start")], row_width=1)
        )
    except:
        pass

# ---- ЧАТ: КЛИЕНТ → АДМИН ----
@router.callback_query(F.data == "client_msg_start")
async def client_msg_start(cb: CallbackQuery):
    await cb.answer()
    await cb.message.answer(
        "💬 Напишите ваше сообщение, и мы ответим как можно скорее!\n\n"
        "<i>Просто отправьте текст в этот чат.</i>"
    )

# ---- ЧАТ: АДМИН → КЛИЕНТ ----
@router.callback_query(F.data.startswith("achat_"))
async def admin_start_chat(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.username != ADMIN_USERNAME:
        await cb.answer("⛔ Только админ"); return
    uid = int(cb.data.replace("achat_", ""))
    admin_chatting_with[cb.chat.id] = uid
    user = get_user(uid)
    uname = user.get('username', '?') if user else '?'
    await cb.answer()
    await cb.message.answer(
        f"💬 <b>Чат с @{uname}</b> (ID: <code>{uid}</code>)\n\n"
        f"Пишите сообщения — они будут пересланы клиенту.\n"
        f"Для выхода из чата: /endchat"
    )
    await state.set_state(AdminChat.chatting)

@router.message(Command("endchat"))
async def end_chat(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    admin_chatting_with.pop(message.chat.id, None)
    await state.clear()
    await message.answer("✅ Чат завершён. Вы в обычном режиме.")

@router.message(Command("chat"))
async def cmd_chat(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /chat <code>user_id</code>\n\nНачнёт чат с клиентом.")
        return
    uid = int(parts[1])
    admin_chatting_with[message.chat.id] = uid
    user = get_user(uid)
    uname = user.get('username', '?') if user else '?'
    await message.answer(
        f"💬 <b>Чат с @{uname}</b> (ID: <code>{uid}</code>)\n\n"
        f"Пишите сообщения — они будут пересланы клиенту.\n"
        f"Для выхода: /endchat"
    )
    await state.set_state(AdminChat.chatting)

# Admin sends message to client
@router.message(AdminChat.chatting)
async def admin_sends_msg(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    uid = admin_chatting_with.get(message.chat.id)
    if not uid:
        await state.clear()
        await message.answer("❌ Нет активного чата. /chat <user_id>")
        return
    try:
        await bot.send_message(uid,
            f"💬 <b>Сообщение от DAR Perfum:</b>\n\n{message.text}",
            reply_markup=inline_kb([("💬 Ответить", "client_msg_start")], row_width=1)
        )
        save_message(uid, "admin→client", message.text)
        await message.answer(f"✅ Отправлено клиенту ({uid})")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@router.callback_query(Reg.confirm, F.data == "confirm_redo")
async def confirm_redo(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.answer()
    await cb.message.edit_text("🔄 Начинаем заново...")
    await cmd_start(cb.message, state)

# ---- МОИ ПОДПИСКИ ----
@router.callback_query(F.data == "my_sub")
async def my_sub(cb: CallbackQuery):
    await cb.answer()
    user = get_user(cb.from_user.id)
    if not user or not user.get("box_type"):
        await cb.message.answer("У вас пока нет активных подписок.\n\nНажмите /start чтобы оформить! 🌸")
        return
    box = BOXES.get(user["box_type"], {})
    await cb.message.answer(
        f"📋 <b>Ваша подписка:</b>\n\n"
        f"📦 {box.get('name', '?')}\n"
        f"⏳ {user.get('duration_months', '?')} мес\n"
        f"💰 {user.get('monthly_price', 0):,} ₽/мес\n"
        f"📊 Статус: {user.get('status', 'new')}\n\n"
        f"💬 Оставить отзыв — /feedback"
    )

# ---- ОБРАТНАЯ СВЯЗЬ ----
@router.callback_query(F.data == "feedback_start")
async def fb_start_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await fb_start(cb.message, state)

@router.message(Command("feedback"))
async def fb_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "💬 <b>Обратная связь по аромабоксу</b>\n\n"
        "Какой это месяц подписки?",
        reply_markup=inline_kb([
            ("1-й месяц", "fbm_1"), ("2-й месяц", "fbm_2"),
            ("3-й месяц", "fbm_3"), ("4-й месяц", "fbm_4"),
            ("5-й месяц", "fbm_5"), ("6-й месяц", "fbm_6"),
        ])
    )
    await state.set_state(Fb.month)

@router.callback_query(Fb.month, F.data.startswith("fbm_"))
async def fb_month(cb: CallbackQuery, state: FSMContext):
    month = int(cb.data.replace("fbm_", ""))
    await state.update_data(fb_month=month)
    await cb.answer()
    await cb.message.edit_text(
        f"📝 <b>Отзыв за {month}-й месяц</b>\n\n"
        "Напишите название аромата:"
    )
    await state.set_state(Fb.aroma)

@router.message(Fb.aroma)
async def fb_aroma(message: Message, state: FSMContext):
    await state.update_data(fb_aroma=message.text.strip())
    await message.answer(
        f"⭐ <b>Оценка аромата «{message.text.strip()}»</b>",
        reply_markup=inline_kb([
            ("😍 Обожаю!", "fbr_5"), ("👍 Нравится", "fbr_4"),
            ("😐 Нормально", "fbr_3"), ("👎 Не моё", "fbr_2"),
            ("🤢 Ужасно", "fbr_1"),
        ], row_width=2)
    )
    await state.set_state(Fb.rating)

@router.callback_query(Fb.rating, F.data.startswith("fbr_"))
async def fb_rating(cb: CallbackQuery, state: FSMContext):
    rating = int(cb.data.replace("fbr_", ""))
    await state.update_data(fb_rating=rating)
    await cb.answer()
    await cb.message.edit_text(
        "💬 Комментарий к аромату (что понравилось/не понравилось)?\n\n"
        "Или нажмите «Пропустить».",
        reply_markup=inline_kb([("⏭ Пропустить", "fbc_skip")])
    )
    await state.set_state(Fb.comment)

@router.callback_query(Fb.comment, F.data == "fbc_skip")
async def fb_comment_skip(cb: CallbackQuery, state: FSMContext):
    await state.update_data(fb_comment="—")
    await cb.answer()
    await save_and_ask_more(cb.message, state, cb.from_user.id)

@router.message(Fb.comment)
async def fb_comment_text(message: Message, state: FSMContext):
    await state.update_data(fb_comment=message.text.strip())
    await save_and_ask_more(message, state, message.from_user.id)

async def save_and_ask_more(msg, state, user_id):
    data = await state.get_data()
    save_feedback(user_id, data["fb_month"], data["fb_aroma"], data["fb_rating"], data["fb_comment"])

    stars = "⭐" * data["fb_rating"]
    await msg.answer(
        f"✅ Отзыв сохранён!\n\n"
        f"🧴 {data['fb_aroma']} — {stars}\n\n"
        "Оценить ещё один аромат из этого бокса?",
        reply_markup=inline_kb([
            ("🧴 Да, ещё один", "fb_more_yes"),
            ("✅ Всё, спасибо", "fb_more_no"),
        ])
    )
    await state.set_state(Fb.more)

    # Notify admin
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        stars = "⭐" * data["fb_rating"]
        try:
            await bot.send_message(ADMIN_CHAT_ID,
                f"💬 <b>Новый отзыв</b>\n\n"
                f"👤 @{msg.chat.username if hasattr(msg.chat, 'username') else '?'} (ID: {user_id})\n"
                f"📦 Месяц: {data['fb_month']}\n"
                f"🧴 {data['fb_aroma']} — {stars}\n"
                f"💬 {data['fb_comment']}"
            )
        except:
            pass

@router.callback_query(Fb.more, F.data == "fb_more_yes")
async def fb_more(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await cb.answer()
    await cb.message.edit_text(f"📝 Аромат (месяц {data['fb_month']}):\n\nНапишите название:")
    await state.set_state(Fb.aroma)

@router.callback_query(Fb.more, F.data == "fb_more_no")
async def fb_done(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.edit_text(
        "🙏 <b>Спасибо за обратную связь!</b>\n\n"
        "Мы учтём ваши предпочтения при составлении следующего бокса. 🖤\n\n"
        "/start — главное меню"
    )
    await state.clear()

# ---- АДМИН ----
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.username != ADMIN_USERNAME:
        await message.answer("⛔ Доступ запрещён.")
        return

    global ADMIN_CHAT_ID
    ADMIN_CHAT_ID = message.chat.id

    subs = get_all_subscribers()
    await message.answer(
        f"🔐 <b>Админ-панель DARBOX</b>\n\n"
        f"📊 Подписчиков: {len(subs)}\n"
        f"🔔 Уведомления: включены\n\n"
        f"Команды:\n"
        f"/subs — список подписчиков\n"
        f"/profile <code>user_id</code> — профиль клиента\n"
        f"/reviews <code>user_id</code> — отзывы клиента\n"
        f"/broadcast — рассылка всем подписчикам"
    )

@router.message(Command("subs"))
async def cmd_subs(message: Message):
    if message.from_user.username != ADMIN_USERNAME:
        return
    subs = get_all_subscribers()
    if not subs:
        await message.answer("Подписчиков пока нет.")
        return
    lines = []
    for s in subs[:30]:
        box = BOXES.get(s["box_type"], {})
        lines.append(
            f"• @{s['username'] or '?'} — {box.get('short', '?')} × {s['duration_months']}мес "
            f"({s['status']})"
        )
    await message.answer(f"📋 <b>Подписчики ({len(subs)}):</b>\n\n" + "\n".join(lines))

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    if message.from_user.username != ADMIN_USERNAME:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /profile <code>user_id</code>")
        return
    user = get_user(int(parts[1]))
    if not user:
        await message.answer("Пользователь не найден.")
        return
    box = BOXES.get(user.get("box_type", ""), {})
    text = f"""👤 <b>Профиль клиента</b>

🆔 {user['user_id']} | @{user.get('username', '?')}
📛 {user.get('full_name', '?')}
📱 {user.get('phone', '?')}
🏠 {user.get('address', '?')}

━━━ Парфюмерный профиль ━━━
Пол: {user.get('gender', '?')}
Возраст: {user.get('age', '?')}
Стиль: {user.get('lifestyle', '?')}
Повод: {user.get('occasions', '?')}
Интенсивность: {user.get('intensity', '?')}
❤️ Любимые: {user.get('fav_notes', '?')}
🚫 Не любит: {user.get('disliked_notes', '?')}
👃 Носит: {user.get('current_perfumes', '?')}
Сезон: {user.get('season_pref', '?')}
Открытия: {user.get('discovery', '?')}
⚠️ Аллергии: {user.get('allergies', '?')}
💬 Пожелания: {user.get('extra_wishes', '?')}

━━━ Подписка ━━━
📦 {box.get('name', '?')}
⏳ {user.get('duration_months', '?')} мес
💰 {user.get('monthly_price', 0):,} ₽/мес
📊 Статус: {user.get('status', '?')}"""
    await message.answer(text)

@router.message(Command("reviews"))
async def cmd_reviews(message: Message):
    if message.from_user.username != ADMIN_USERNAME:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /reviews <code>user_id</code>")
        return
    fbs = get_feedback(int(parts[1]))
    if not fbs:
        await message.answer("Отзывов пока нет.")
        return
    lines = []
    for fb in fbs:
        stars = "⭐" * fb["rating"]
        lines.append(f"📦 Месяц {fb['month_num']} | {fb['aroma_name']} — {stars}\n   💬 {fb['comment']}")
    await message.answer(f"💬 <b>Отзывы клиента:</b>\n\n" + "\n\n".join(lines))

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    await message.answer("📢 Напишите текст рассылки (получат все подписчики):")
    await state.set_state(Broadcast.text)

@router.message(Broadcast.text)
async def do_broadcast(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    subs = get_all_subscribers()
    sent = 0
    for s in subs:
        try:
            await bot.send_message(s["user_id"], message.text)
            sent += 1
        except:
            pass
        await asyncio.sleep(0.1)
    await message.answer(f"✅ Рассылка отправлена: {sent}/{len(subs)}")
    await state.clear()

# ---- КЛИЕНТ ПИШЕТ → ПЕРЕСЫЛКА АДМИНУ ----
# Это ПОСЛЕДНИЙ обработчик — ловит все необработанные текстовые сообщения
@router.message(F.text)
async def client_sends_msg(message: Message, state: FSMContext):
    # Skip admin messages (handled by AdminChat state)
    if message.from_user.username == ADMIN_USERNAME:
        return
    # Skip if user is in a registration flow
    current_state = await state.get_state()
    if current_state and current_state.startswith("Reg:"):
        return
    if current_state and current_state.startswith("Fb:"):
        return

    # Forward client message to admin
    global ADMIN_CHAT_ID
    save_message(message.from_user.id, "client→admin", message.text)

    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(ADMIN_CHAT_ID,
                f"💬 <b>Сообщение от клиента:</b>\n\n"
                f"👤 @{message.from_user.username or '?'} ({message.from_user.first_name})\n"
                f"🆔 <code>{message.from_user.id}</code>\n\n"
                f"📩 {message.text}",
                reply_markup=inline_kb([
                    (f"💬 Ответить", f"achat_{message.from_user.id}"),
                    (f"👤 Профиль", f"aprofile_{message.from_user.id}"),
                ], row_width=2)
            )
        except:
            pass

    await message.answer(
        "✅ Сообщение отправлено!\n\n"
        "Мы ответим как можно скорее 🖤"
    )

# Quick profile view from chat
@router.callback_query(F.data.startswith("aprofile_"))
async def admin_quick_profile(cb: CallbackQuery):
    if cb.from_user.username != ADMIN_USERNAME:
        await cb.answer("⛔"); return
    uid = int(cb.data.replace("aprofile_", ""))
    user = get_user(uid)
    if not user:
        await cb.answer("Не найден"); return
    await cb.answer()
    box = BOXES.get(user.get("box_type", ""), {})
    await cb.message.answer(
        f"👤 @{user.get('username','?')} | {user.get('full_name','?')}\n"
        f"📦 {box.get('name','не оформлено')} | {user.get('status','new')}\n"
        f"❤️ {user.get('fav_notes','?')}\n"
        f"🚫 {user.get('disliked_notes','?')}\n"
        f"👃 Носит: {user.get('current_perfumes','?')}"
    )

# ---- ЗАПУСК ----
async def main():
    init_db()
    print("🚀 DARBOX бот запущен!")
    print(f"📌 Админ: @{ADMIN_USERNAME}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
