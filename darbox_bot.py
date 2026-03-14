"""
🎁 DARBOX v2 — Telegram-бот подписки на аромабоксы
DAR Perfum | @dararomabox_bot
Premium version with extended questionnaire & visuals
"""

import asyncio
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
from aiogram.client.default import DefaultBotProperties

# ===================== НАСТРОЙКИ =====================
BOT_TOKEN = "8054022324:AAHK2bUZ1lLEDk8FREDbAEl5En040OtEHg0"
ADMIN_USERNAME = "nasomato"
ADMIN_CHAT_ID = None

PAYMENT_DETAILS = """💳 <b>Реквизиты для оплаты:</b>

🏦 Сбербанк: <code>2202 XXXX XXXX XXXX</code>
👤 Получатель: Имя Фамилия

Или по номеру телефона:
📱 <code>+7 977 573 31 79</code> (Сбербанк)

После перевода нажмите «✅ Я оплатил» ниже."""

# ===================== ТАРИФЫ =====================
BOXES = {
    "8x3": {"name": "8 ароматов × 3 мл", "short": "8×3мл", "price": 1980, "count": 8, "vol": "3 мл", "emoji": "🧪"},
    "6x6": {"name": "6 ароматов × 6 мл", "short": "6×6мл", "price": 2380, "count": 6, "vol": "6 мл", "emoji": "🧴"},
    "5x10": {"name": "5 ароматов × 10 мл", "short": "5×10мл", "price": 3580, "count": 5, "vol": "10 мл", "emoji": "✨"},
}
DURATIONS = {
    2: {"discount": 0, "label": "2 месяца"},
    4: {"discount": 5, "label": "4 месяца", "badge": "−5%"},
    6: {"discount": 10, "label": "6 месяцев", "badge": "−10% 🔥"},
}

def calc_price(box_key, months):
    base = BOXES[box_key]["price"]
    d = DURATIONS[months]["discount"]
    monthly = round(base * (100 - d) / 100)
    return monthly, monthly * months

# ===================== ВИЗУАЛЬНЫЕ ЭЛЕМЕНТЫ =====================
def progress_bar(current, total, length=12):
    filled = round(length * current / total)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {current}/{total}"

def step_header(num, total, title, emoji=""):
    bar = progress_bar(num, total)
    return f"{emoji} <b>{title}</b>\n\n{bar}"

DIVIDER = "━━━━━━━━━━━━━━━━━━━━"
DIVIDER_THIN = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"

TOTAL_STEPS = 20

# ===================== БАЗА ДАННЫХ =====================
DB_PATH = "darbox.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT, first_name TEXT, created_at TEXT,
        gender TEXT, age TEXT, lifestyle TEXT, occasions TEXT,
        intensity TEXT, experience TEXT,
        fav_notes TEXT, disliked_notes TEXT, current_perfumes TEXT,
        season_pref TEXT, time_of_day TEXT, mood TEXT,
        associations TEXT, longevity TEXT, discovery TEXT,
        budget TEXT, wardrobe TEXT, allergies TEXT,
        goal TEXT, extra_wishes TEXT,
        box_type TEXT, duration_months INTEGER,
        monthly_price INTEGER, total_price INTEGER,
        full_name TEXT, phone TEXT, address TEXT,
        status TEXT DEFAULT 'new'
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, month_num INTEGER,
        aroma_name TEXT, rating INTEGER, comment TEXT,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, direction TEXT, text TEXT, created_at TEXT
    )""")
    conn.commit(); conn.close()

def save_user(uid, data):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    fields = list(data.keys())
    ph = ", ".join(fields)
    vph = ", ".join(["?"] * len(fields))
    upd = ", ".join([f"{f}=excluded.{f}" for f in fields])
    c.execute(f"INSERT INTO users (user_id, {ph}) VALUES (?, {vph}) ON CONFLICT(user_id) DO UPDATE SET {upd}",
              [uid] + [data[f] for f in fields])
    conn.commit(); conn.close()

def get_user(uid):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    c = conn.cursor(); c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = c.fetchone(); conn.close()
    return dict(row) if row else None

def get_all_subscribers():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    c = conn.cursor(); c.execute("SELECT * FROM users WHERE box_type IS NOT NULL ORDER BY created_at DESC")
    rows = c.fetchall(); conn.close()
    return [dict(r) for r in rows]

def save_feedback(uid, month, aroma, rating, comment):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT INTO feedback (user_id,month_num,aroma_name,rating,comment,created_at) VALUES (?,?,?,?,?,?)",
              (uid, month, aroma, rating, comment, datetime.now().isoformat()))
    conn.commit(); conn.close()

def get_feedback(uid):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    c = conn.cursor(); c.execute("SELECT * FROM feedback WHERE user_id=? ORDER BY month_num, id", (uid,))
    rows = c.fetchall(); conn.close()
    return [dict(r) for r in rows]

def save_message(uid, direction, text):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT INTO messages (user_id,direction,text,created_at) VALUES (?,?,?,?)",
              (uid, direction, text, datetime.now().isoformat()))
    conn.commit(); conn.close()

# ===================== СОСТОЯНИЯ =====================
class Q(StatesGroup):
    gender = State(); age = State(); lifestyle = State()
    occasions = State(); intensity = State(); experience = State()
    fav_notes = State(); disliked_notes = State(); current_perfumes = State()
    season_pref = State(); time_of_day = State(); mood = State()
    associations = State(); longevity = State(); discovery = State()
    budget = State(); wardrobe = State(); allergies = State()
    goal = State(); extra_wishes = State()
    box_type = State(); duration = State()
    full_name = State(); phone = State(); address = State()
    confirm = State()

class Fb(StatesGroup):
    month = State(); aroma = State(); rating = State()
    comment = State(); more = State()

class Broadcast(StatesGroup):
    text = State()

class AdminChat(StatesGroup):
    chatting = State()

# ===================== КЛАВИАТУРЫ =====================
def kb(buttons, row_width=2):
    rows = []; row = []
    for text, cb in buttons:
        row.append(InlineKeyboardButton(text=text, callback_data=cb))
        if len(row) >= row_width: rows.append(row); row = []
    if row: rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

admin_chatting_with = {}

# ===================== БОТ =====================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# ──────────────── /start ────────────────
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    save_user(message.from_user.id, {
        "username": message.from_user.username or "",
        "first_name": message.from_user.first_name or "",
        "created_at": datetime.now().isoformat(),
    })
    text = f"""
{DIVIDER}
        🖤  <b>DAR PERFUM</b>
   Парфюмерная Лаборатория
{DIVIDER}

🎁 <b>DARBOX — подписка на аромабоксы</b>

Каждый месяц — новый набор ароматов,
собранный специально для вас.

✦ Вы проходите парфюмерную анкету
✦ Мы узнаём ваш ольфакторный портрет
✦ Собираем бокс-сюрприз под ваш вкус
✦ Каждый месяц — новые открытия

{DIVIDER_THIN}

<b>Форматы:</b>
🧪  8 × 3 мл  —  <b>1 980 ₽</b>/мес
🧴  6 × 6 мл  —  <b>2 380 ₽</b>/мес
✨  5 × 10 мл —  <b>3 580 ₽</b>/мес

🔥 <i>4 мес → скидка 5%  |  6 мес → скидка 10%</i>

{DIVIDER}"""

    await message.answer(text, reply_markup=kb([
        ("🌸 Пройти анкету и оформить", "start_q"),
        ("📋 Мои подписки", "my_sub"),
        ("💬 Оставить отзыв", "fb_start"),
        ("✉️ Написать нам", "client_msg"),
    ], row_width=1))

# ──────────────── АНКЕТА: 20 ВОПРОСОВ ────────────────

@router.callback_query(F.data == "start_q")
async def start_questionnaire(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.answer(
        f"🌿 <b>Парфюмерная анкета</b>\n\n"
        f"Мы зададим вам {TOTAL_STEPS} вопросов, чтобы составить\n"
        f"ваш <b>ольфакторный портрет</b> — уникальную\n"
        f"карту ваших парфюмерных предпочтений.\n\n"
        f"Это поможет нам подобрать ароматы,\n"
        f"которые станут именно <b>вашими</b>.\n\n"
        f"<i>Займёт 3-5 минут ✨</i>"
    )
    await asyncio.sleep(1.0)
    # Q1: Gender
    await cb.message.answer(
        step_header(1, TOTAL_STEPS, "Для кого подбираем?", "👤") +
        "\n\n<i>Это определит базовое направление ароматов</i>",
        reply_markup=kb([
            ("🙋‍♂️ Для мужчины", "g_m"),
            ("🙋‍♀️ Для женщины", "g_f"),
            ("🎁 В подарок", "g_gift"),
        ], row_width=2)
    )
    await state.set_state(Q.gender)

# Q1
@router.callback_query(Q.gender, F.data.startswith("g_"))
async def q1(cb: CallbackQuery, state: FSMContext):
    v = {"g_m": "Мужчина", "g_f": "Женщина", "g_gift": "В подарок"}[cb.data]
    await state.update_data(gender=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(2, TOTAL_STEPS, "Возраст", "📅") +
        "\n\n<i>Помогает подобрать стилистику ароматов</i>",
        reply_markup=kb([
            ("18-24", "a_18"), ("25-34", "a_25"),
            ("35-44", "a_35"), ("45+", "a_45"),
        ])
    )
    await state.set_state(Q.age)

# Q2
@router.callback_query(Q.age, F.data.startswith("a_"))
async def q2(cb: CallbackQuery, state: FSMContext):
    v = {"a_18":"18-24","a_25":"25-34","a_35":"35-44","a_45":"45+"}[cb.data]
    await state.update_data(age=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(3, TOTAL_STEPS, "Образ жизни", "🏃") +
        "\n\n<i>Ваш ритм определяет характер аромата</i>",
        reply_markup=kb([
            ("💼 Деловой / офис", "ls_office"),
            ("🎨 Творческий / свободный", "ls_creative"),
            ("🏋️ Спортивный / активный", "ls_sport"),
            ("🌙 Размеренный / домашний", "ls_home"),
        ], row_width=1)
    )
    await state.set_state(Q.lifestyle)

# Q3
@router.callback_query(Q.lifestyle, F.data.startswith("ls_"))
async def q3(cb: CallbackQuery, state: FSMContext):
    v = {"ls_office":"Деловой","ls_creative":"Творческий","ls_sport":"Спортивный","ls_home":"Размеренный"}[cb.data]
    await state.update_data(lifestyle=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(4, TOTAL_STEPS, "Где носите ароматы?", "🎭") +
        "\n\n<i>Разные ситуации — разные ароматы</i>",
        reply_markup=kb([
            ("📆 На каждый день", "oc_daily"),
            ("🌃 На выход / свидание", "oc_eve"),
            ("🏢 На работу", "oc_work"),
            ("🔀 Везде по-разному", "oc_mix"),
        ], row_width=1)
    )
    await state.set_state(Q.occasions)

# Q4
@router.callback_query(Q.occasions, F.data.startswith("oc_"))
async def q4(cb: CallbackQuery, state: FSMContext):
    v = {"oc_daily":"На каждый день","oc_eve":"На выход","oc_work":"На работу","oc_mix":"Везде по-разному"}[cb.data]
    await state.update_data(occasions=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(5, TOTAL_STEPS, "Интенсивность", "💨") +
        "\n\n<i>Насколько «громким» должен быть аромат?</i>",
        reply_markup=kb([
            ("🌬 Шёпот — лёгкий, близко к коже", "in_light"),
            ("☁️ Разговор — умеренный, для себя", "in_med"),
            ("🔥 Заявление — мощный шлейф", "in_heavy"),
            ("🎲 Зависит от настроения", "in_mix"),
        ], row_width=1)
    )
    await state.set_state(Q.intensity)

# Q5
@router.callback_query(Q.intensity, F.data.startswith("in_"))
async def q5(cb: CallbackQuery, state: FSMContext):
    v = {"in_light":"Лёгкие","in_med":"Умеренные","in_heavy":"Мощные","in_mix":"Разные"}[cb.data]
    await state.update_data(intensity=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(6, TOTAL_STEPS, "Ваш парфюмерный опыт", "🎓") +
        "\n\n<i>Это влияет на сложность ароматов в боксе</i>",
        reply_markup=kb([
            ("🌱 Новичок — только начинаю", "ex_new"),
            ("🌿 Любитель — есть несколько любимых", "ex_mid"),
            ("🌳 Энтузиаст — разбираюсь в нотах", "ex_pro"),
            ("👑 Гуру — обширная коллекция", "ex_guru"),
        ], row_width=1)
    )
    await state.set_state(Q.experience)

# Q6
@router.callback_query(Q.experience, F.data.startswith("ex_"))
async def q6(cb: CallbackQuery, state: FSMContext):
    v = {"ex_new":"Новичок","ex_mid":"Любитель","ex_pro":"Энтузиаст","ex_guru":"Гуру"}[cb.data]
    await state.update_data(experience=v); await cb.answer(f"✓ {v}")
    await state.update_data(_fav=[])
    await cb.message.edit_text(
        step_header(7, TOTAL_STEPS, "Любимые ноты ❤️", "🌸") +
        "\n\n<i>Выберите всё, что нравится. Нажмите «Готово» когда закончите.</i>",
        reply_markup=_note_kb("fn", [])
    )
    await state.set_state(Q.fav_notes)

NOTE_MAP = {
    "citrus": "🍋 Цитрусовые", "floral": "🌹 Цветочные", "woody": "🌳 Древесные",
    "sweet": "🍦 Сладкие/ванильные", "fresh": "🌊 Свежие/морские", "spicy": "🌶 Пряные/восточные",
    "leather": "🧥 Кожаные", "tobacco": "🚬 Табачные/дымные", "coffee": "☕ Кофейные",
    "fruit": "🍑 Фруктовые", "gourmand": "🍫 Гурманские", "musk": "🤍 Мускусные",
}

def _note_kb(prefix, selected):
    buttons = []
    for key, label in NOTE_MAP.items():
        check = " ✓" if label in selected else ""
        buttons.append((f"{label}{check}", f"{prefix}_{key}"))
    if selected:
        buttons.append((f"✅ Готово ({len(selected)})", f"{prefix}_done"))
    else:
        buttons.append(("⏭ Пропустить", f"{prefix}_done"))
    return kb(buttons, row_width=2)

# Q7 — Fav notes (multi-select)
@router.callback_query(Q.fav_notes, F.data.startswith("fn_"))
async def q7(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data(); fav = data.get("_fav", [])
    key = cb.data.replace("fn_", "")
    if key == "done":
        await state.update_data(fav_notes=", ".join(fav) if fav else "Не выбрано")
        await state.update_data(_dis=[])
        await cb.answer()
        await cb.message.edit_text(
            step_header(8, TOTAL_STEPS, "Нелюбимые ноты 🚫", "❌") +
            "\n\n<i>Что точно НЕ должно быть в вашем боксе?</i>",
            reply_markup=_note_kb("dn", [])
        )
        await state.set_state(Q.disliked_notes); return
    label = NOTE_MAP.get(key, key)
    if label in fav: fav.remove(label)
    else: fav.append(label)
    await state.update_data(_fav=fav); await cb.answer(f"{'✓' if label in fav else '✗'} {label}")
    await cb.message.edit_reply_markup(reply_markup=_note_kb("fn", fav))

# Q8 — Disliked notes (multi-select)
@router.callback_query(Q.disliked_notes, F.data.startswith("dn_"))
async def q8(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data(); dis = data.get("_dis", [])
    key = cb.data.replace("dn_", "")
    if key == "done":
        await state.update_data(disliked_notes=", ".join(dis) if dis else "Нет ограничений")
        await cb.answer()
        await cb.message.edit_text(
            step_header(9, TOTAL_STEPS, "Текущие ароматы", "👃") +
            "\n\n<i>Напишите ароматы, которые вам нравятся или которые носите.\n"
            "Это поможет понять ваш вкус.</i>\n\n"
            "Например: <code>Sauvage, Baccarat Rouge 540</code>\n\n"
            "Или напишите «нет» если затрудняетесь."
        )
        await state.set_state(Q.current_perfumes); return
    label = NOTE_MAP.get(key, key)
    if label in dis: dis.remove(label)
    else: dis.append(label)
    await state.update_data(_dis=dis); await cb.answer(f"{'✓' if label in dis else '✗'} {label}")
    await cb.message.edit_reply_markup(reply_markup=_note_kb("dn", dis))

# Q9 — Current perfumes (text)
@router.message(Q.current_perfumes)
async def q9(message: Message, state: FSMContext):
    await state.update_data(current_perfumes=message.text.strip())
    await message.answer(
        step_header(10, TOTAL_STEPS, "Любимый сезон ароматов", "🌤") +
        "\n\n<i>Когда вы чувствуете себя в своей стихии?</i>",
        reply_markup=kb([
            ("🌸 Весна — свежесть, пробуждение", "se_spring"),
            ("☀️ Лето — лёгкость, море, цитрус", "se_summer"),
            ("🍂 Осень — тепло, уют, пряности", "se_autumn"),
            ("❄️ Зима — глубина, сладость, дым", "se_winter"),
            ("🔄 Разные сезоны", "se_mix"),
        ], row_width=1)
    )
    await state.set_state(Q.season_pref)

# Q10
@router.callback_query(Q.season_pref, F.data.startswith("se_"))
async def q10(cb: CallbackQuery, state: FSMContext):
    v = {"se_spring":"Весна","se_summer":"Лето","se_autumn":"Осень","se_winter":"Зима","se_mix":"Все сезоны"}[cb.data]
    await state.update_data(season_pref=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(11, TOTAL_STEPS, "Время суток", "🕐") +
        "\n\n<i>Когда вам важнее всего пахнуть?</i>",
        reply_markup=kb([
            ("🌅 День — свежесть и энергия", "td_day"),
            ("🌙 Вечер — глубина и соблазн", "td_eve"),
            ("🔄 Универсально", "td_uni"),
        ], row_width=1)
    )
    await state.set_state(Q.time_of_day)

# Q11
@router.callback_query(Q.time_of_day, F.data.startswith("td_"))
async def q11(cb: CallbackQuery, state: FSMContext):
    v = {"td_day":"Дневные","td_eve":"Вечерние","td_uni":"Универсальные"}[cb.data]
    await state.update_data(time_of_day=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(12, TOTAL_STEPS, "Какое настроение хотите?", "🎭") +
        "\n\n<i>Аромат — это эмоция. Какую выбираете?</i>",
        reply_markup=kb([
            ("❤️ Романтика и нежность", "mo_romance"),
            ("💪 Уверенность и сила", "mo_power"),
            ("🧘 Спокойствие и гармония", "mo_calm"),
            ("⚡ Энергия и драйв", "mo_energy"),
            ("🔮 Загадочность и магия", "mo_mystery"),
        ], row_width=1)
    )
    await state.set_state(Q.mood)

# Q12
@router.callback_query(Q.mood, F.data.startswith("mo_"))
async def q12(cb: CallbackQuery, state: FSMContext):
    v = {"mo_romance":"Романтика","mo_power":"Уверенность","mo_calm":"Спокойствие","mo_energy":"Энергия","mo_mystery":"Загадочность"}[cb.data]
    await state.update_data(mood=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(13, TOTAL_STEPS, "Ассоциации", "🌍") +
        "\n\n<i>Закройте глаза. Где вы чувствуете себя счастливым?\nЭто место определит ваш аромат.</i>",
        reply_markup=kb([
            ("🌲 Лес после дождя", "as_forest"),
            ("🌊 Морской берег", "as_sea"),
            ("🏙 Ночной город", "as_city"),
            ("🕌 Восточный базар", "as_east"),
            ("🍰 Кондитерская / кофейня", "as_sweet"),
            ("🏔 Горный воздух", "as_mountain"),
        ], row_width=2)
    )
    await state.set_state(Q.associations)

# Q13
@router.callback_query(Q.associations, F.data.startswith("as_"))
async def q13(cb: CallbackQuery, state: FSMContext):
    v = {"as_forest":"Лес","as_sea":"Море","as_city":"Город","as_east":"Восток","as_sweet":"Кондитерская","as_mountain":"Горы"}[cb.data]
    await state.update_data(associations=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(14, TOTAL_STEPS, "Желаемая стойкость", "⏱") +
        "\n\n<i>Сколько должен держаться аромат?</i>",
        reply_markup=kb([
            ("🕐 2-4 часа — лёгкий намёк", "lo_short"),
            ("🕕 6-8 часов — рабочий день", "lo_med"),
            ("🕛 12+ часов — с утра до ночи", "lo_long"),
        ], row_width=1)
    )
    await state.set_state(Q.longevity)

# Q14
@router.callback_query(Q.longevity, F.data.startswith("lo_"))
async def q14(cb: CallbackQuery, state: FSMContext):
    v = {"lo_short":"2-4 часа","lo_med":"6-8 часов","lo_long":"12+ часов"}[cb.data]
    await state.update_data(longevity=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(15, TOTAL_STEPS, "Готовность к экспериментам", "🚀") +
        "\n\n<i>Хотите только привычное или готовы удивляться?</i>",
        reply_markup=kb([
            ("🚀 Удивляйте! Люблю новое", "di_yes"),
            ("😌 Лучше проверенную классику", "di_safe"),
            ("⚖️ 50/50 — и то, и другое", "di_mix"),
        ], row_width=1)
    )
    await state.set_state(Q.discovery)

# Q15
@router.callback_query(Q.discovery, F.data.startswith("di_"))
async def q15(cb: CallbackQuery, state: FSMContext):
    v = {"di_yes":"Люблю эксперименты","di_safe":"Проверенная классика","di_mix":"50/50"}[cb.data]
    await state.update_data(discovery=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(16, TOTAL_STEPS, "Ценовой сегмент", "💎") +
        "\n\n<i>Какой уровень ароматов вам ближе?</i>",
        reply_markup=kb([
            ("🛒 Масс-маркет (Zara, H&M)", "bu_mass"),
            ("⭐ Средний (Boss, Versace)", "bu_mid"),
            ("💫 Ниша (Byredo, Le Labo)", "bu_niche"),
            ("👑 Люкс (Tom Ford, Creed)", "bu_lux"),
            ("🎲 Все сегменты", "bu_mix"),
        ], row_width=1)
    )
    await state.set_state(Q.budget)

# Q16
@router.callback_query(Q.budget, F.data.startswith("bu_"))
async def q16(cb: CallbackQuery, state: FSMContext):
    v = {"bu_mass":"Масс-маркет","bu_mid":"Средний","bu_niche":"Ниша","bu_lux":"Люкс","bu_mix":"Все сегменты"}[cb.data]
    await state.update_data(budget=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(17, TOTAL_STEPS, "Ваш гардероб", "👔") +
        "\n\n<i>Стиль одежды подсказывает стиль аромата</i>",
        reply_markup=kb([
            ("👕 Casual / повседневный", "wr_casual"),
            ("👔 Классика / деловой", "wr_classic"),
            ("🧢 Streetwear / спортивный", "wr_street"),
            ("👗 Элегантный / вечерний", "wr_elegant"),
            ("🎨 Творческий / эклектика", "wr_creative"),
        ], row_width=1)
    )
    await state.set_state(Q.wardrobe)

# Q17
@router.callback_query(Q.wardrobe, F.data.startswith("wr_"))
async def q17(cb: CallbackQuery, state: FSMContext):
    v = {"wr_casual":"Casual","wr_classic":"Классика","wr_street":"Streetwear","wr_elegant":"Элегантный","wr_creative":"Творческий"}[cb.data]
    await state.update_data(wardrobe=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(18, TOTAL_STEPS, "Аллергии и ограничения", "⚠️") +
        "\n\n<i>Есть ли аллергия на компоненты?\n"
        "Напишите или нажмите «Нет».</i>",
        reply_markup=kb([("✅ Нет аллергий", "al_no")])
    )
    await state.set_state(Q.allergies)

# Q18
@router.callback_query(Q.allergies, F.data == "al_no")
async def q18a(cb: CallbackQuery, state: FSMContext):
    await state.update_data(allergies="Нет"); await cb.answer()
    await _ask_goal(cb.message, state)

@router.message(Q.allergies)
async def q18b(message: Message, state: FSMContext):
    await state.update_data(allergies=message.text.strip())
    await _ask_goal(message, state)

async def _ask_goal(msg, state):
    await msg.answer(
        step_header(19, TOTAL_STEPS, "Цель подписки", "🎯") +
        "\n\n<i>Зачем вам DARBOX?</i>",
        reply_markup=kb([
            ("🔍 Найти свой идеальный аромат", "go_find"),
            ("🌍 Попробовать максимум нового", "go_explore"),
            ("📚 Пополнить коллекцию", "go_collect"),
            ("🎁 Подарок близкому человеку", "go_gift"),
        ], row_width=1)
    )
    await state.set_state(Q.goal)

# Q19
@router.callback_query(Q.goal, F.data.startswith("go_"))
async def q19(cb: CallbackQuery, state: FSMContext):
    v = {"go_find":"Найти свой аромат","go_explore":"Попробовать новое","go_collect":"Пополнить коллекцию","go_gift":"Подарок"}[cb.data]
    await state.update_data(goal=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        step_header(20, TOTAL_STEPS, "Свободные пожелания", "💬") +
        "\n\n<i>Что ещё важно? Любые мысли, мечты об аромате.\n"
        "Или нажмите «Пропустить».</i>",
        reply_markup=kb([("⏭ Пропустить", "ew_skip")])
    )
    await state.set_state(Q.extra_wishes)

# Q20
@router.callback_query(Q.extra_wishes, F.data == "ew_skip")
async def q20a(cb: CallbackQuery, state: FSMContext):
    await state.update_data(extra_wishes="—"); await cb.answer()
    await _show_box_choice(cb.message, state)

@router.message(Q.extra_wishes)
async def q20b(message: Message, state: FSMContext):
    await state.update_data(extra_wishes=message.text.strip())
    await _show_box_choice(message, state)

# ──────────────── ВЫБОР БОКСА ────────────────
async def _show_box_choice(msg, state):
    await msg.answer(
        f"🎉 <b>Анкета завершена!</b>\n\n"
        f"Теперь выберите формат вашего DARBOX:\n\n"
        f"{DIVIDER_THIN}\n\n"
        f"🧪 <b>8 × 3 мл</b> — знакомство\n"
        f"    Попробовать максимум ароматов\n"
        f"    <b>1 980 ₽</b>/мес\n\n"
        f"🧴 <b>6 × 6 мл</b> — золотая середина\n"
        f"    Хватит на 2-3 недели каждого\n"
        f"    <b>2 380 ₽</b>/мес\n\n"
        f"✨ <b>5 × 10 мл</b> — полное погружение\n"
        f"    Полноценный флакон каждого аромата\n"
        f"    <b>3 580 ₽</b>/мес\n\n"
        f"{DIVIDER_THIN}",
        reply_markup=kb([
            ("🧪 8×3мл — 1 980 ₽", "box_8x3"),
            ("🧴 6×6мл — 2 380 ₽", "box_6x6"),
            ("✨ 5×10мл — 3 580 ₽", "box_5x10"),
        ], row_width=1)
    )
    await state.set_state(Q.box_type)

@router.callback_query(Q.box_type, F.data.startswith("box_"))
async def pick_box(cb: CallbackQuery, state: FSMContext):
    key = cb.data.replace("box_", "")
    await state.update_data(box_type=key); await cb.answer()
    box = BOXES[key]
    lines = []
    for m, dur in DURATIONS.items():
        mo, tot = calc_price(key, m)
        badge = f" {dur.get('badge','')}" if dur.get('badge') else ""
        lines.append(f"{'▸ ' if m==2 else '▸ '}<b>{dur['label']}</b>{badge}\n   {mo:,} ₽/мес → итого <b>{tot:,} ₽</b>")
    await cb.message.edit_text(
        f"⏳ <b>Срок подписки</b>\n\n"
        f"Формат: {box['emoji']} {box['name']}\n\n" +
        "\n\n".join(lines) +
        f"\n\n<i>Чем дольше — тем выгоднее!</i>",
        reply_markup=kb([
            ("2 месяца", "dur_2"),
            ("4 месяца (−5%)", "dur_4"),
            ("6 месяцев (−10%) 🔥", "dur_6"),
        ], row_width=1)
    )
    await state.set_state(Q.duration)

@router.callback_query(Q.duration, F.data.startswith("dur_"))
async def pick_dur(cb: CallbackQuery, state: FSMContext):
    months = int(cb.data.replace("dur_",""))
    data = await state.get_data()
    mo, tot = calc_price(data["box_type"], months)
    await state.update_data(duration_months=months, monthly_price=mo, total_price=tot)
    await cb.answer()
    await cb.message.edit_text("👤 <b>ФИО получателя</b>\n\nНапишите полное имя для доставки:")
    await state.set_state(Q.full_name)

@router.message(Q.full_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await message.answer("📱 <b>Телефон</b>\n\nНомер для связи по доставке:")
    await state.set_state(Q.phone)

@router.message(Q.phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await message.answer("🏠 <b>Адрес доставки</b>\n\n<i>Город, улица, дом, квартира, индекс</i>")
    await state.set_state(Q.address)

@router.message(Q.address)
async def get_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    d = await state.get_data()
    box = BOXES[d["box_type"]]
    dur = DURATIONS[d["duration_months"]]
    mo, tot = calc_price(d["box_type"], d["duration_months"])

    summary = f"""{DIVIDER}
📋 <b>ВАША ЗАЯВКА</b>
{DIVIDER}

<b>Ольфакторный портрет:</b>
┊ 👤 {d.get('gender','—')} · {d.get('age','—')}
┊ 🏃 {d.get('lifestyle','—')} · {d.get('occasions','—')}
┊ 💨 {d.get('intensity','—')} · 🎓 {d.get('experience','—')}
┊ ❤️ {d.get('fav_notes','—')}
┊ 🚫 {d.get('disliked_notes','—')}
┊ 👃 {d.get('current_perfumes','—')}
┊ 🌤 {d.get('season_pref','—')} · 🕐 {d.get('time_of_day','—')}
┊ 🎭 {d.get('mood','—')} · 🌍 {d.get('associations','—')}
┊ ⏱ {d.get('longevity','—')} · 🚀 {d.get('discovery','—')}
┊ 💎 {d.get('budget','—')} · 👔 {d.get('wardrobe','—')}
┊ ⚠️ {d.get('allergies','—')}
┊ 🎯 {d.get('goal','—')}
┊ 💬 {d.get('extra_wishes','—')}

{DIVIDER_THIN}

<b>Подписка:</b>
┊ {box['emoji']} {box['name']}
┊ ⏳ {dur['label']}
┊ 💰 {mo:,} ₽/мес → итого <b>{tot:,} ₽</b>

<b>Доставка:</b>
┊ 👤 {d.get('full_name','—')}
┊ 📱 {d.get('phone','—')}
┊ 🏠 {d.get('address','—')}

{DIVIDER}"""

    await message.answer(summary + "\n\n<b>Всё верно?</b>", reply_markup=kb([
        ("✅ Подтвердить заявку", "cf_yes"),
        ("✏️ Начать заново", "cf_redo"),
    ], row_width=1))
    await state.set_state(Q.confirm)

@router.callback_query(Q.confirm, F.data == "cf_yes")
async def confirm_yes(cb: CallbackQuery, state: FSMContext):
    d = await state.get_data(); await cb.answer("✅")
    save_user(cb.from_user.id, {
        "username": cb.from_user.username or "", "first_name": cb.from_user.first_name or "",
        "gender": d.get("gender",""), "age": d.get("age",""), "lifestyle": d.get("lifestyle",""),
        "occasions": d.get("occasions",""), "intensity": d.get("intensity",""),
        "experience": d.get("experience",""), "fav_notes": d.get("fav_notes",""),
        "disliked_notes": d.get("disliked_notes",""), "current_perfumes": d.get("current_perfumes",""),
        "season_pref": d.get("season_pref",""), "time_of_day": d.get("time_of_day",""),
        "mood": d.get("mood",""), "associations": d.get("associations",""),
        "longevity": d.get("longevity",""), "discovery": d.get("discovery",""),
        "budget": d.get("budget",""), "wardrobe": d.get("wardrobe",""),
        "allergies": d.get("allergies",""), "goal": d.get("goal",""),
        "extra_wishes": d.get("extra_wishes",""),
        "box_type": d.get("box_type",""), "duration_months": d.get("duration_months",0),
        "monthly_price": d.get("monthly_price",0), "total_price": d.get("total_price",0),
        "full_name": d.get("full_name",""), "phone": d.get("phone",""),
        "address": d.get("address",""), "status": "pending",
    })

    box = BOXES[d["box_type"]]; dur = DURATIONS[d["duration_months"]]
    mo, tot = calc_price(d["box_type"], d["duration_months"])

    await cb.message.edit_text(
        f"🎉 <b>Заявка оформлена!</b>\n\n"
        f"Мы свяжемся с вами в Telegram\n"
        f"для подтверждения и оплаты.\n\n"
        f"💬 @nasomato — если есть вопросы\n\n"
        f"Спасибо, что выбрали <b>DARBOX</b>! 🖤"
    )
    await asyncio.sleep(1)
    await cb.message.answer(
        f"💰 <b>Оплата подписки</b>\n\n"
        f"Сумма: <b>{tot:,} ₽</b>\n"
        f"({d['duration_months']} мес × {mo:,} ₽/мес)\n\n"
        f"{PAYMENT_DETAILS}",
        reply_markup=kb([("✅ Я оплатил(а)", "pay_done"), ("💬 Написать нам", "client_msg")], row_width=1)
    )

    # Notify admin
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        admin_text = (
            f"🆕 <b>НОВАЯ ЗАЯВКА DARBOX!</b>\n\n"
            f"👤 @{cb.from_user.username or '?'} ({cb.from_user.first_name})\n"
            f"🆔 <code>{cb.from_user.id}</code>\n\n"
            f"📦 {box['name']} × {dur['label']}\n"
            f"💰 {mo:,} ₽/мес → {tot:,} ₽\n\n"
            f"❤️ {d.get('fav_notes','—')}\n"
            f"🚫 {d.get('disliked_notes','—')}\n"
            f"👃 {d.get('current_perfumes','—')}\n"
            f"🎭 {d.get('mood','—')} · 🌍 {d.get('associations','—')}\n"
            f"🎓 {d.get('experience','—')} · 💎 {d.get('budget','—')}\n"
            f"🎯 {d.get('goal','—')}\n\n"
            f"📱 {d.get('phone','—')}\n"
            f"🏠 {d.get('address','—')}"
        )
        try:
            await bot.send_message(ADMIN_CHAT_ID, admin_text, reply_markup=kb([
                (f"💬 Написать", f"achat_{cb.from_user.id}"),
                (f"✅ Оплата ОК", f"apay_{cb.from_user.id}"),
                (f"👤 Профиль", f"apro_{cb.from_user.id}"),
            ]))
        except: pass
    await state.clear()

@router.callback_query(Q.confirm, F.data == "cf_redo")
async def confirm_redo(cb: CallbackQuery, state: FSMContext):
    await state.clear(); await cb.answer()
    await cb.message.edit_text("🔄 Начинаем заново...")
    await cmd_start(cb.message, state)

# ──────────────── ОПЛАТА ────────────────
@router.callback_query(F.data == "pay_done")
async def pay_done(cb: CallbackQuery):
    await cb.answer("✅")
    await cb.message.edit_text(
        "⏳ <b>Проверяем оплату...</b>\n\n"
        "Обычно до 30 минут.\n"
        "Мы напишем вам как только подтвердим! 🖤",
        reply_markup=kb([("💬 Написать нам", "client_msg")])
    )
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        user = get_user(cb.from_user.id)
        try:
            await bot.send_message(ADMIN_CHAT_ID,
                f"💳 <b>Клиент сообщил об оплате!</b>\n\n"
                f"👤 @{cb.from_user.username or '?'}\n🆔 <code>{cb.from_user.id}</code>\n"
                f"💰 {user.get('total_price',0):,} ₽",
                reply_markup=kb([
                    (f"✅ Подтвердить", f"apay_{cb.from_user.id}"),
                    (f"💬 Написать", f"achat_{cb.from_user.id}"),
                ]))
        except: pass

@router.callback_query(F.data.startswith("apay_"))
async def admin_pay(cb: CallbackQuery):
    if cb.from_user.username != ADMIN_USERNAME: await cb.answer("⛔"); return
    uid = int(cb.data.replace("apay_","")); save_user(uid, {"status": "paid"})
    await cb.answer("✅"); await cb.message.edit_text(cb.message.text + "\n\n✅ <b>ОПЛАТА ОК</b>")
    try:
        await bot.send_message(uid,
            "🎉 <b>Оплата подтверждена!</b>\n\n"
            "Ваша подписка DARBOX активирована! 🖤\n"
            "Мы начнём собирать ваш аромабокс.\n\n"
            "💬 Пишите сюда если что!",
            reply_markup=kb([("💬 Написать нам", "client_msg")]))
    except: pass

# ──────────────── ЧАТ ────────────────
@router.callback_query(F.data == "client_msg")
async def client_msg_prompt(cb: CallbackQuery):
    await cb.answer()
    await cb.message.answer("💬 Напишите сообщение — мы ответим как можно скорее!")

@router.callback_query(F.data.startswith("achat_"))
async def admin_chat_start(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.username != ADMIN_USERNAME: await cb.answer("⛔"); return
    uid = int(cb.data.replace("achat_","")); admin_chatting_with[cb.chat.id] = uid
    user = get_user(uid); await cb.answer()
    await cb.message.answer(f"💬 Чат с @{user.get('username','?')} (<code>{uid}</code>)\nПишите. /endchat для выхода.")
    await state.set_state(AdminChat.chatting)

@router.message(Command("chat"))
async def cmd_chat(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME: return
    parts = message.text.split()
    if len(parts) < 2: await message.answer("/chat <code>user_id</code>"); return
    uid = int(parts[1]); admin_chatting_with[message.chat.id] = uid
    await message.answer(f"💬 Чат с <code>{uid}</code>. /endchat для выхода.")
    await state.set_state(AdminChat.chatting)

@router.message(Command("endchat"))
async def cmd_endchat(message: Message, state: FSMContext):
    admin_chatting_with.pop(message.chat.id, None); await state.clear()
    await message.answer("✅ Чат завершён.")

@router.message(AdminChat.chatting)
async def admin_sends(message: Message, state: FSMContext):
    uid = admin_chatting_with.get(message.chat.id)
    if not uid: await state.clear(); return
    try:
        await bot.send_message(uid, f"💬 <b>DAR Perfum:</b>\n\n{message.text}",
                               reply_markup=kb([("💬 Ответить", "client_msg")]))
        save_message(uid, "admin→client", message.text)
        await message.answer(f"✅ → {uid}")
    except Exception as e: await message.answer(f"❌ {e}")

# ──────────────── МОИ ПОДПИСКИ ────────────────
@router.callback_query(F.data == "my_sub")
async def my_sub(cb: CallbackQuery):
    await cb.answer(); user = get_user(cb.from_user.id)
    if not user or not user.get("box_type"):
        await cb.message.answer("У вас пока нет подписок.\nНажмите /start чтобы оформить! 🌸"); return
    box = BOXES.get(user["box_type"], {})
    await cb.message.answer(
        f"📋 <b>Ваша подписка:</b>\n\n"
        f"{box.get('emoji','')} {box.get('name','?')}\n"
        f"⏳ {user.get('duration_months','?')} мес\n"
        f"💰 {user.get('monthly_price',0):,} ₽/мес\n"
        f"📊 Статус: {user.get('status','new')}")

# ──────────────── ОБРАТНАЯ СВЯЗЬ ────────────────
@router.callback_query(F.data == "fb_start")
async def fb_start_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer(); await _fb_start(cb.message, state)

@router.message(Command("feedback"))
async def fb_start_cmd(message: Message, state: FSMContext):
    await _fb_start(message, state)

async def _fb_start(msg, state):
    await state.clear()
    await msg.answer("💬 <b>Обратная связь</b>\n\nКакой месяц подписки?", reply_markup=kb([
        (f"{i}-й месяц", f"fbm_{i}") for i in range(1, 7)
    ]))
    await state.set_state(Fb.month)

@router.callback_query(Fb.month, F.data.startswith("fbm_"))
async def fb_month(cb: CallbackQuery, state: FSMContext):
    m = int(cb.data.replace("fbm_","")); await state.update_data(fb_month=m); await cb.answer()
    await cb.message.edit_text(f"📝 <b>Отзыв за {m}-й месяц</b>\n\nНазвание аромата:")
    await state.set_state(Fb.aroma)

@router.message(Fb.aroma)
async def fb_aroma(message: Message, state: FSMContext):
    await state.update_data(fb_aroma=message.text.strip())
    await message.answer(f"⭐ Оценка «{message.text.strip()}»:", reply_markup=kb([
        ("😍 Обожаю", "fbr_5"), ("👍 Нравится", "fbr_4"), ("😐 Норм", "fbr_3"),
        ("👎 Не моё", "fbr_2"), ("🤢 Ужас", "fbr_1"),
    ], row_width=3))
    await state.set_state(Fb.rating)

@router.callback_query(Fb.rating, F.data.startswith("fbr_"))
async def fb_rating(cb: CallbackQuery, state: FSMContext):
    r = int(cb.data.replace("fbr_","")); await state.update_data(fb_rating=r); await cb.answer()
    await cb.message.edit_text("💬 Комментарий?", reply_markup=kb([("⏭ Пропустить", "fbc_skip")]))
    await state.set_state(Fb.comment)

@router.callback_query(Fb.comment, F.data == "fbc_skip")
async def fb_com_skip(cb: CallbackQuery, state: FSMContext):
    await state.update_data(fb_comment="—"); await cb.answer()
    await _fb_save(cb.message, state, cb.from_user.id)

@router.message(Fb.comment)
async def fb_com_text(message: Message, state: FSMContext):
    await state.update_data(fb_comment=message.text.strip())
    await _fb_save(message, state, message.from_user.id)

async def _fb_save(msg, state, uid):
    d = await state.get_data()
    save_feedback(uid, d["fb_month"], d["fb_aroma"], d["fb_rating"], d["fb_comment"])
    stars = "⭐" * d["fb_rating"]
    await msg.answer(f"✅ Сохранено!\n🧴 {d['fb_aroma']} — {stars}\n\nЕщё один аромат?",
                     reply_markup=kb([("🧴 Да", "fb_more_y"), ("✅ Всё", "fb_more_n")]))
    await state.set_state(Fb.more)
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        try: await bot.send_message(ADMIN_CHAT_ID, f"💬 Отзыв от {uid}: {d['fb_aroma']} — {stars}\n{d['fb_comment']}")
        except: pass

@router.callback_query(Fb.more, F.data == "fb_more_y")
async def fb_more(cb: CallbackQuery, state: FSMContext):
    d = await state.get_data(); await cb.answer()
    await cb.message.edit_text(f"📝 Аромат (месяц {d['fb_month']}):")
    await state.set_state(Fb.aroma)

@router.callback_query(Fb.more, F.data == "fb_more_n")
async def fb_done(cb: CallbackQuery, state: FSMContext):
    await cb.answer(); await state.clear()
    await cb.message.edit_text("🙏 Спасибо! Учтём в следующем боксе 🖤\n\n/start — меню")

# ──────────────── АДМИН ────────────────
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.username != ADMIN_USERNAME: await message.answer("⛔"); return
    global ADMIN_CHAT_ID; ADMIN_CHAT_ID = message.chat.id
    subs = get_all_subscribers()
    await message.answer(
        f"🔐 <b>Админ DARBOX</b>\n\n📊 Подписчиков: {len(subs)}\n🔔 Уведомления: ВКЛ\n\n"
        f"/subs — список\n/profile ID — профиль\n/reviews ID — отзывы\n"
        f"/chat ID — чат\n/broadcast — рассылка")

@router.message(Command("subs"))
async def cmd_subs(message: Message):
    if message.from_user.username != ADMIN_USERNAME: return
    subs = get_all_subscribers()
    if not subs: await message.answer("Пусто."); return
    lines = [f"• @{s['username'] or '?'} — {BOXES.get(s['box_type'],{}).get('short','?')} × {s['duration_months']}мес ({s['status']})" for s in subs[:30]]
    await message.answer(f"📋 <b>Подписчики ({len(subs)}):</b>\n\n" + "\n".join(lines))

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    if message.from_user.username != ADMIN_USERNAME: return
    parts = message.text.split()
    if len(parts) < 2: await message.answer("/profile <code>ID</code>"); return
    u = get_user(int(parts[1]))
    if not u: await message.answer("Не найден."); return
    await message.answer(
        f"👤 @{u.get('username','?')} | {u.get('full_name','?')}\n"
        f"📱 {u.get('phone','?')} | 📊 {u.get('status','?')}\n\n"
        f"Пол: {u.get('gender','?')} | Возраст: {u.get('age','?')}\n"
        f"Стиль: {u.get('lifestyle','?')} | Повод: {u.get('occasions','?')}\n"
        f"Интенс: {u.get('intensity','?')} | Опыт: {u.get('experience','?')}\n"
        f"❤️ {u.get('fav_notes','?')}\n🚫 {u.get('disliked_notes','?')}\n"
        f"👃 {u.get('current_perfumes','?')}\n"
        f"Сезон: {u.get('season_pref','?')} | Время: {u.get('time_of_day','?')}\n"
        f"Настроение: {u.get('mood','?')} | Ассоц: {u.get('associations','?')}\n"
        f"Стойкость: {u.get('longevity','?')} | Открытия: {u.get('discovery','?')}\n"
        f"Бюджет: {u.get('budget','?')} | Гардероб: {u.get('wardrobe','?')}\n"
        f"Аллергии: {u.get('allergies','?')} | Цель: {u.get('goal','?')}\n"
        f"💬 {u.get('extra_wishes','?')}")

@router.callback_query(F.data.startswith("apro_"))
async def admin_quick_profile(cb: CallbackQuery):
    if cb.from_user.username != ADMIN_USERNAME: await cb.answer("⛔"); return
    uid = int(cb.data.replace("apro_","")); u = get_user(uid)
    if not u: await cb.answer("?"); return
    await cb.answer()
    await cb.message.answer(
        f"👤 @{u.get('username','?')} | {u.get('full_name','?')}\n"
        f"❤️ {u.get('fav_notes','?')}\n🚫 {u.get('disliked_notes','?')}\n"
        f"🎭 {u.get('mood','?')} · 🌍 {u.get('associations','?')}\n"
        f"🎓 {u.get('experience','?')} · 💎 {u.get('budget','?')}")

@router.message(Command("reviews"))
async def cmd_reviews(message: Message):
    if message.from_user.username != ADMIN_USERNAME: return
    parts = message.text.split()
    if len(parts) < 2: await message.answer("/reviews <code>ID</code>"); return
    fbs = get_feedback(int(parts[1]))
    if not fbs: await message.answer("Отзывов нет."); return
    lines = [f"📦 М{f['month_num']} | {f['aroma_name']} — {'⭐'*f['rating']}\n   {f['comment']}" for f in fbs]
    await message.answer("💬 <b>Отзывы:</b>\n\n" + "\n\n".join(lines))

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME: return
    await message.answer("📢 Текст рассылки:"); await state.set_state(Broadcast.text)

@router.message(Broadcast.text)
async def do_broadcast(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME: return
    subs = get_all_subscribers(); sent = 0
    for s in subs:
        try: await bot.send_message(s["user_id"], message.text); sent += 1
        except: pass
        await asyncio.sleep(0.1)
    await message.answer(f"✅ {sent}/{len(subs)}"); await state.clear()

# ──────────────── ПЕРЕСЫЛКА СООБЩЕНИЙ ────────────────
@router.message(F.text)
async def client_to_admin(message: Message, state: FSMContext):
    if message.from_user.username == ADMIN_USERNAME: return
    cs = await state.get_state()
    if cs and (cs.startswith("Q:") or cs.startswith("Fb:")): return
    save_message(message.from_user.id, "client→admin", message.text)
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(ADMIN_CHAT_ID,
                f"💬 @{message.from_user.username or '?'} (<code>{message.from_user.id}</code>):\n\n{message.text}",
                reply_markup=kb([
                    (f"💬 Ответить", f"achat_{message.from_user.id}"),
                    (f"👤 Профиль", f"apro_{message.from_user.id}"),
                ]))
        except: pass
    await message.answer("✅ Отправлено! Мы ответим скоро 🖤")

# ──────────────── ЗАПУСК ────────────────
async def main():
    init_db()
    print("🚀 DARBOX v2 запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
