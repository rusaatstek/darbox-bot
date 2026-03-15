"""
🎁 DARBOX v4 — Premium Telegram Aroma Subscription Bot
DAR Perfum | @dararomabox_bot
Features: Personal cabinet, perfume diary, rating system,
taste analytics, referrals, admin panel, chat system, Mini App
"""
import asyncio, sqlite3, json, hashlib, random, string, os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, MenuButtonWebApp
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

# ═══════════════════════════════════════
#              CONFIGURATION
# ═══════════════════════════════════════
BOT_TOKEN = "8054022324:AAHK2bUZ1lLEDk8FREDbAEl5En040OtEHg0"
ADMIN_USERNAME = "nasomato"
ADMIN_CHAT_ID = None
CONTACT = "@darperf"
PAYMENT_INFO = ("💳 <b>Реквизиты для оплаты:</b>\n\n"
    "📱 По номеру телефона:\n<code>+7 963 991 80 48</code>\n"
    "(Сбербанк / Тинькофф / Альфабанк)\n\n"
    "После перевода нажмите «✅ Я оплатил».")
DEL_COST = {"post":280,"cdek":280,"courier":350}
DEL_NAME = {"post":"📦 Почта России","cdek":"🚚 СДЭК","courier":"🏍 Курьер по Москве"}
BOXES = {
    "8x3":{"name":"8 ароматов × 3 мл","short":"8×3мл","price":1980,"em":"🧪","desc":"Максимум открытий"},
    "6x6":{"name":"6 ароматов × 6 мл","short":"6×6мл","price":2380,"em":"🧴","desc":"Золотая середина"},
    "5x10":{"name":"5 ароматов × 10 мл","short":"5×10мл","price":3580,"em":"✨","desc":"Полное погружение"},
}
DURS = {2:{"d":0,"l":"2 месяца","b":""},4:{"d":5,"l":"4 месяца","b":" (−5%)"},6:{"d":10,"l":"6 месяцев","b":" (−10%) 🔥"}}
def cprice(bk,m):
    base=BOXES[bk]["price"];disc=DURS[m]["d"];mo=round(base*(100-disc)/100);return mo,mo*m
TOTAL_Q = 20
DIV = "━━━━━━━━━━━━━━━━━━━━"
div = "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"
def pbar(c,t,l=14): f=round(l*c/t);return f"{'█'*f}{'░'*(l-f)}  {c}/{t}"
def hdr(n,title,em=""): return f"{em} <b>{title}</b>\n\n{pbar(n,TOTAL_Q)}"
def gen_ref(uid): return hashlib.md5(f"dar{uid}".encode()).hexdigest()[:8]

# Web App URL — will be set dynamically from RAILWAY_PUBLIC_DOMAIN or PORT
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 8080))
WEBAPP_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
if WEBAPP_URL and not WEBAPP_URL.startswith("http"):
    WEBAPP_URL = f"https://{WEBAPP_URL}"

NM = {
    "citrus":"🍋 Цитрусовые","floral":"🌹 Цветочные","woody":"🌳 Древесные",
    "sweet":"🍦 Сладкие/ванильные","fresh":"🌊 Свежие/морские","spicy":"🌶 Пряные/восточные",
    "leather":"🧥 Кожаные","tobacco":"🚬 Табачные/дымные","coffee":"☕ Кофейные",
    "fruit":"🍑 Фруктовые","gourmand":"🍫 Гурманские","musk":"🤍 Мускусные",
    "oud":"🕌 Удовые","amber":"🐳 Амбровые","herbal":"🌿 Травяные",
    "powder":"💄 Пудровые","aqua":"💧 Акватические","boozy":"🥃 Алкогольные",
}
ASSOC_MAP = {"z1":"Лес после дождя","z2":"Морской берег","z3":"Ночной мегаполис","z4":"Восточный базар","z5":"Кондитерская","z6":"Горный воздух","z7":"Старая библиотека","z8":"Цветущий луг","z9":"Тропический остров","z10":"Камин в шале","z11":"Утро в кофейне","z12":"Крыша небоскрёба"}

# ═══════════════════════════════════════
#              DATABASE
# ═══════════════════════════════════════
DB = "darbox_v4.db"
def init_db():
    cn = sqlite3.connect(DB); c = cn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, created_at TEXT,
        gender TEXT, gift_gender TEXT, age TEXT, lifestyle TEXT, occasions TEXT,
        intensity TEXT, experience TEXT, fav_notes TEXT, disliked_notes TEXT,
        current_perfumes TEXT, season_pref TEXT, time_of_day TEXT, mood TEXT,
        associations TEXT, longevity TEXT, discovery TEXT, budget TEXT, wardrobe TEXT,
        allergies TEXT, goal TEXT, extra_wishes TEXT,
        box_type TEXT, duration_months INTEGER, monthly_price INTEGER, total_price INTEGER,
        delivery_type TEXT, delivery_cost INTEGER,
        full_name TEXT, phone TEXT, city TEXT, address TEXT, postal_code TEXT,
        status TEXT DEFAULT 'new', paid_at TEXT, next_delivery TEXT, months_received INTEGER DEFAULT 0,
        ref_code TEXT, referred_by TEXT, ref_discount INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, month_num INTEGER, aroma_name TEXT,
        rating_overall INTEGER, rating_longevity INTEGER, rating_sillage INTEGER,
        comment TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS diary(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, aroma_name TEXT, entry_type TEXT,
        text TEXT, mood TEXT, occasion TEXT, rating INTEGER,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, direction TEXT, text TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS box_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, month_num INTEGER, aromas TEXT,
        sent_at TEXT, tracking TEXT
    )""")
    cn.commit(); cn.close()

def savu(uid, data):
    cn = sqlite3.connect(DB); c = cn.cursor()
    fs = list(data.keys()); ph = ",".join(fs); vp = ",".join(["?"]*len(fs))
    up = ",".join([f"{f}=excluded.{f}" for f in fs])
    c.execute(f"INSERT INTO users(user_id,{ph}) VALUES(?,{vp}) ON CONFLICT(user_id) DO UPDATE SET {up}",
              [uid]+[data[f] for f in fs])
    cn.commit(); cn.close()

def getu(uid):
    cn = sqlite3.connect(DB); cn.row_factory = sqlite3.Row; c = cn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,)); r = c.fetchone(); cn.close()
    return dict(r) if r else None

def get_subs():
    cn = sqlite3.connect(DB); cn.row_factory = sqlite3.Row; c = cn.cursor()
    c.execute("SELECT * FROM users WHERE box_type IS NOT NULL ORDER BY created_at DESC")
    rs = c.fetchall(); cn.close(); return [dict(r) for r in rs]

def get_due(days=7):
    cn = sqlite3.connect(DB); cn.row_factory = sqlite3.Row; c = cn.cursor()
    t = (datetime.now()+timedelta(days=days)).strftime("%Y-%m-%d")
    n = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT * FROM users WHERE status='paid' AND next_delivery<=? AND next_delivery>?", (t, n))
    rs = c.fetchall(); cn.close(); return [dict(r) for r in rs]

def savfb(uid, mo, ar, ro, rl, rs_, co):
    cn = sqlite3.connect(DB); c = cn.cursor()
    c.execute("INSERT INTO feedback(user_id,month_num,aroma_name,rating_overall,rating_longevity,rating_sillage,comment,created_at) VALUES(?,?,?,?,?,?,?,?)",
              (uid, mo, ar, ro, rl, rs_, co, datetime.now().isoformat()))
    cn.commit(); cn.close()

def getfb(uid):
    cn = sqlite3.connect(DB); cn.row_factory = sqlite3.Row; c = cn.cursor()
    c.execute("SELECT * FROM feedback WHERE user_id=? ORDER BY created_at DESC", (uid,))
    rs = c.fetchall(); cn.close(); return [dict(r) for r in rs]

def get_taste_stats(uid):
    fbs = getfb(uid)
    if not fbs: return None
    total = len(fbs); avg_overall = sum(f["rating_overall"] for f in fbs) / total
    avg_long = sum(f["rating_longevity"] or 0 for f in fbs) / total
    avg_sill = sum(f["rating_sillage"] or 0 for f in fbs) / total
    top = sorted(fbs, key=lambda x: x["rating_overall"], reverse=True)[:3]
    bottom = sorted(fbs, key=lambda x: x["rating_overall"])[:3]
    return {"total": total, "avg_overall": round(avg_overall, 1), "avg_longevity": round(avg_long, 1),
            "avg_sillage": round(avg_sill, 1), "top": top, "bottom": bottom}

def sav_diary(uid, aroma, entry_type, text, mood="", occasion="", rating=0):
    cn = sqlite3.connect(DB); c = cn.cursor()
    c.execute("INSERT INTO diary(user_id,aroma_name,entry_type,text,mood,occasion,rating,created_at) VALUES(?,?,?,?,?,?,?,?)",
              (uid, aroma, entry_type, text, mood, occasion, rating, datetime.now().isoformat()))
    cn.commit(); cn.close()

def get_diary(uid, limit=20):
    cn = sqlite3.connect(DB); cn.row_factory = sqlite3.Row; c = cn.cursor()
    c.execute("SELECT * FROM diary WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (uid, limit))
    rs = c.fetchall(); cn.close(); return [dict(r) for r in rs]

def savmsg(uid, d, t):
    cn = sqlite3.connect(DB); c = cn.cursor()
    c.execute("INSERT INTO messages(user_id,direction,text,created_at) VALUES(?,?,?,?)",
              (uid, d, t, datetime.now().isoformat()))
    cn.commit(); cn.close()

def count_referrals(ref_code):
    cn = sqlite3.connect(DB); c = cn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE referred_by=? AND status='paid'", (ref_code,))
    r = c.fetchone()[0]; cn.close(); return r

# ═══════════════════════════════════════
#              STATES
# ═══════════════════════════════════════
class Q(StatesGroup):
    gender=State();gift_gender=State();age=State();lifestyle=State();occasions=State()
    intensity=State();experience=State();fav_notes=State();disliked_notes=State()
    current_perfumes=State();season_pref=State();time_of_day=State();mood=State()
    associations=State();longevity=State();discovery=State();budget=State()
    wardrobe=State();allergies=State();goal=State();extra_wishes=State()
    box_type=State();duration=State()
    delivery_type=State();full_name=State();phone=State();city=State();address=State();postal_code=State()
    confirm=State()

class Fb(StatesGroup):
    month=State();aroma=State();overall=State();longevity=State();sillage=State()
    comment=State();more=State()

class Diary(StatesGroup):
    aroma=State();entry=State();mood_tag=State()

class Bcast(StatesGroup):
    text=State()

class AChat(StatesGroup):
    chatting=State()

class AddrConfirm(StatesGroup):
    address=State()

# ═══════════════════════════════════════
#              HELPERS
# ═══════════════════════════════════════
def K(btns, rw=2):
    rows = []; row = []
    for t, cb in btns:
        row.append(InlineKeyboardButton(text=t, callback_data=cb))
        if len(row) >= rw: rows.append(row); row = []
    if row: rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _nkb(pf, sel):
    btns = []
    for k, lb in NM.items():
        ch = " ✓" if lb in sel else ""
        btns.append((f"{lb}{ch}", f"{pf}_{k}"))
    if sel: btns.append((f"✅ Готово ({len(sel)})", f"{pf}_done"))
    else: btns.append(("⏭ Пропустить", f"{pf}_done"))
    return K(btns, 2)

def main_menu_kb():
    return K([
        ("🏠 Главное меню", "menu"),
    ], 1)

def menu_kb():
    btns = []
    # Mini App button at the top if URL is available
    if WEBAPP_URL:
        btns_rows = [[InlineKeyboardButton(text="✨ Открыть DARBOX App", web_app=WebAppInfo(url=WEBAPP_URL))]]
    else:
        btns_rows = []
    # Regular menu buttons
    menu_btns = [
        ("🌸 Оформить подписку", "sq"),
        ("👤 Мой профиль", "profile"),
        ("📖 Парфюмерный дневник", "diary_menu"),
        ("⭐ Мои оценки", "my_ratings"),
        ("📊 Карта вкуса", "taste_map"),
        ("💬 Оставить отзыв", "fbs"),
        ("📋 Моя подписка", "mysub"),
        ("🎁 Пригласить друга", "referral"),
        ("✉️ Написать нам", "cmsg"),
    ]
    row = []
    for t, cb in menu_btns:
        row.append(InlineKeyboardButton(text=t, callback_data=cb))
        if len(row) >= 2: btns_rows.append(row); row = []
    if row: btns_rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=btns_rows)

achat_with = {}
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage()); router = Router(); dp.include_router(router)

# ═══════════════════════════════════════
#           WEB SERVER (Mini App)
# ═══════════════════════════════════════
async def handle_index(request):
    """Serve the Mini App HTML"""
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except FileNotFoundError:
        return web.Response(text="<h1>DARBOX Mini App</h1><p>index.html not found</p>", content_type="text/html")

async def handle_health(request):
    """Health check endpoint"""
    return web.Response(text="OK")

async def start_web_server():
    """Start aiohttp web server for Mini App"""
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/health", handle_health)
    # Serve static files from templates folder
    app.router.add_static("/static/", path="templates/", name="static")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()
    print(f"🌐 Web server started on {WEBAPP_HOST}:{WEBAPP_PORT}")
    if WEBAPP_URL:
        print(f"🔗 Mini App URL: {WEBAPP_URL}")
    else:
        print(f"⚠️  RAILWAY_PUBLIC_DOMAIN not set — Mini App button will be hidden")
        print(f"   Set it in Railway: Settings → Networking → Generate Domain")

# ═══════════════════════════════════════
#           /start & MAIN MENU
# ═══════════════════════════════════════
@router.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    ref = msg.text.split()[1] if len(msg.text.split()) > 1 else None
    rc = gen_ref(msg.from_user.id)
    data = {"username": msg.from_user.username or "", "first_name": msg.from_user.first_name or "",
            "created_at": datetime.now().isoformat(), "ref_code": rc}
    if ref and ref != rc:
        data["referred_by"] = ref
    savu(msg.from_user.id, data)

    # Set Mini App as menu button if URL is available
    if WEBAPP_URL:
        try:
            await bot.set_chat_menu_button(
                chat_id=msg.chat.id,
                menu_button=MenuButtonWebApp(text="DARBOX", web_app=WebAppInfo(url=WEBAPP_URL))
            )
        except Exception as e:
            print(f"Menu button error: {e}")

    webapp_line = ""
    if WEBAPP_URL:
        webapp_line = "\n💎 <b>Нажмите кнопку ниже для премиум-интерфейса!</b>\n"

    welcome = f"""
{DIV}
          🖤  <b>DAR PERFUM</b>
     Парфюмерная Лаборатория
{DIV}

🎁 <b>DARBOX — аромабокс по подписке</b>

Каждый месяц — уникальный набор ароматов,
собранный специально для вас ✨

┊ 🧪  8 × 3 мл  —  <b>1 980 ₽</b>/мес
┊ 🧴  6 × 6 мл  —  <b>2 380 ₽</b>/мес
┊ ✨  5 × 10 мл —  <b>3 580 ₽</b>/мес

🔥 <i>4 мес → −5%  ·  6 мес → −10%</i>
{webapp_line}
{div}

Выберите раздел:"""

    await msg.answer(welcome, reply_markup=menu_kb())

@router.callback_query(F.data == "menu")
async def show_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear(); await cb.answer()
    await cb.message.answer(f"🏠 <b>Главное меню DARBOX</b>\n\n{div}\n\nВыберите раздел:", reply_markup=menu_kb())

# ═══════════════════════════════════════
#           PERSONAL PROFILE
# ═══════════════════════════════════════
@router.callback_query(F.data == "profile")
async def show_profile(cb: CallbackQuery):
    await cb.answer()
    u = getu(cb.from_user.id)
    if not u:
        await cb.message.answer("Профиль пока пуст.\nПройдите анкету: /start"); return

    stats = get_taste_stats(cb.from_user.id)
    diary_count = len(get_diary(cb.from_user.id, 100))
    refs = count_referrals(u.get("ref_code", ""))

    status_emoji = {"new": "⏳", "pending": "📝", "paid": "✅", "paused": "⏸"}.get(u.get("status", ""), "❓")

    txt = f"""{DIV}
👤 <b>МОЙ ПРОФИЛЬ</b>
{DIV}

<b>{u.get('first_name', '')} {u.get('full_name', '')}</b>
@{u.get('username', '—')}

{div}
<b>Ольфакторный портрет:</b>
┊ 👤 {u.get('gender', '—')} · {u.get('age', '—')}
┊ 🏃 {u.get('lifestyle', '—')} · 🎭 {u.get('occasions', '—')}
┊ 💨 {u.get('intensity', '—')} · 🎓 {u.get('experience', '—')}
┊ ❤️ {u.get('fav_notes', '—')}
┊ 🚫 {u.get('disliked_notes', '—')}
┊ 🎭 {u.get('mood', '—')} · 🌍 {u.get('associations', '—')}
┊ 💎 {u.get('budget', '—')} · 👔 {u.get('wardrobe', '—')}

{div}
<b>Статистика:</b>
┊ {status_emoji} Статус: {u.get('status', 'нет подписки')}
┊ 📦 Получено боксов: {u.get('months_received', 0)}
┊ ⭐ Оценок: {stats['total'] if stats else 0}
┊ 📖 Записей в дневнике: {diary_count}
┊ 👥 Рефералов: {refs}
{DIV}"""

    await cb.message.answer(txt, reply_markup=K([
        ("📊 Карта вкуса", "taste_map"),
        ("📖 Дневник", "diary_menu"),
        ("⭐ Мои оценки", "my_ratings"),
        ("✏️ Пройти анкету заново", "sq"),
        ("🏠 Меню", "menu"),
    ], 2))

# ═══════════════════════════════════════
#           TASTE MAP (Analytics)
# ═══════════════════════════════════════
@router.callback_query(F.data == "taste_map")
async def taste_map(cb: CallbackQuery):
    await cb.answer()
    stats = get_taste_stats(cb.from_user.id)
    if not stats:
        await cb.message.answer("📊 <b>Карта вкуса</b>\n\nПока нет данных. Оставьте отзывы после получения бокса!\n\n/feedback — оставить отзыв",
                                reply_markup=K([("🏠 Меню", "menu")])); return

    def bar(val, mx=5, l=10):
        f = round(l * val / mx); return "▓" * f + "░" * (l - f)

    top_txt = "\n".join([f"  🏆 {t['aroma_name']} — {'⭐'*t['rating_overall']}" for t in stats["top"]])
    bot_txt = "\n".join([f"  💤 {t['aroma_name']} — {'⭐'*t['rating_overall']}" for t in stats["bottom"]])

    txt = f"""{DIV}
📊 <b>КАРТА ВКУСА</b>
{DIV}

Ваш парфюмерный DNA на основе {stats['total']} оценок:

<b>Общее впечатление:</b>
{bar(stats['avg_overall'])} {stats['avg_overall']}/5

<b>Стойкость:</b>
{bar(stats['avg_longevity'])} {stats['avg_longevity']}/5

<b>Шлейф:</b>
{bar(stats['avg_sillage'])} {stats['avg_sillage']}/5

{div}
<b>Топ-3 ваших фаворита:</b>
{top_txt}

<b>Не зашли:</b>
{bot_txt}

{div}
<i>Чем больше оценок — тем точнее подбор!</i>
{DIV}"""
    await cb.message.answer(txt, reply_markup=K([("⭐ Оценить ароматы", "fbs"), ("🏠 Меню", "menu")]))

# ═══════════════════════════════════════
#           MY RATINGS
# ═══════════════════════════════════════
@router.callback_query(F.data == "my_ratings")
async def my_ratings(cb: CallbackQuery):
    await cb.answer()
    fbs = getfb(cb.from_user.id)
    if not fbs:
        await cb.message.answer("⭐ <b>Мои оценки</b>\n\nПока пусто. После получения бокса нажмите «Оставить отзыв»!",
                                reply_markup=K([("💬 Оставить отзыв", "fbs"), ("🏠 Меню", "menu")])); return

    lines = []
    for f in fbs[:15]:
        stars = "⭐" * f["rating_overall"]
        lines.append(f"🧴 <b>{f['aroma_name']}</b> — {stars}\n"
                     f"   ⏱{f.get('rating_longevity',0) or '—'}/5 · 💨{f.get('rating_sillage',0) or '—'}/5"
                     f"{' · 💬 '+f['comment'] if f['comment'] and f['comment']!='—' else ''}")

    await cb.message.answer(
        f"⭐ <b>Мои оценки</b> ({len(fbs)} всего)\n\n" + "\n\n".join(lines),
        reply_markup=K([("💬 Оценить ещё", "fbs"), ("📊 Карта вкуса", "taste_map"), ("🏠 Меню", "menu")]))

# ═══════════════════════════════════════
#           PERFUME DIARY
# ═══════════════════════════════════════
@router.callback_query(F.data == "diary_menu")
async def diary_menu(cb: CallbackQuery):
    await cb.answer()
    entries = get_diary(cb.from_user.id, 10)
    txt = f"📖 <b>Парфюмерный дневник</b>\n\n"
    if entries:
        txt += f"Последние записи ({len(entries)}):\n\n"
        for e in entries[:5]:
            date = e["created_at"][:10]
            txt += f"┊ {date} · <b>{e['aroma_name']}</b>\n┊ <i>{e['text'][:80]}{'...' if len(e['text'])>80 else ''}</i>\n\n"
    else:
        txt += "<i>Пока пусто. Напишите о любом аромате — сохраним для вас!</i>\n\n"

    txt += f"{div}\n<i>Записывайте впечатления — мы учтём их при подборе!</i>"
    await cb.message.answer(txt, reply_markup=K([
        ("✏️ Новая запись", "diary_new"),
        ("📖 Все записи", "diary_all"),
        ("🏠 Меню", "menu"),
    ], 2))

@router.callback_query(F.data == "diary_new")
async def diary_new(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.answer("📖 <b>Новая запись в дневнике</b>\n\n🧴 Напишите название аромата:")
    await state.set_state(Diary.aroma)

@router.message(Diary.aroma)
async def diary_aroma(msg: Message, state: FSMContext):
    await state.update_data(d_aroma=msg.text.strip())
    await msg.answer(
        f"✏️ <b>{msg.text.strip()}</b>\n\n"
        "Напишите ваши впечатления, мысли, ассоциации:\n\n"
        "<i>Например: «Носил на свидание — комплименты!\n"
        "Держится 6 часов. Чувствую ваниль и кожу.\n"
        "Идеален на осень»</i>"
    )
    await state.set_state(Diary.entry)

@router.message(Diary.entry)
async def diary_entry(msg: Message, state: FSMContext):
    await state.update_data(d_entry=msg.text.strip())
    await msg.answer("🎭 Настроение при ношении?", reply_markup=K([
        ("❤️ Романтика", "dm_rom"), ("💪 Уверенность", "dm_pow"),
        ("🧘 Спокойствие", "dm_calm"), ("⚡ Энергия", "dm_ene"),
        ("🔮 Загадочность", "dm_mys"), ("⏭ Пропустить", "dm_skip"),
    ], 2))
    await state.set_state(Diary.mood_tag)

@router.callback_query(Diary.mood_tag, F.data.startswith("dm_"))
async def diary_mood(cb: CallbackQuery, state: FSMContext):
    moods = {"dm_rom": "Романтика", "dm_pow": "Уверенность", "dm_calm": "Спокойствие",
             "dm_ene": "Энергия", "dm_mys": "Загадочность", "dm_skip": "—"}
    m = moods.get(cb.data, "—")
    d = await state.get_data()
    sav_diary(cb.from_user.id, d["d_aroma"], "impression", d["d_entry"], m)
    await cb.answer("✅")
    await cb.message.edit_text(
        f"✅ <b>Запись сохранена!</b>\n\n"
        f"🧴 {d['d_aroma']}\n"
        f"🎭 {m}\n"
        f"📝 {d['d_entry'][:100]}{'...' if len(d['d_entry'])>100 else ''}\n\n"
        f"<i>Мы учтём это при подборе ваших ароматов</i> 🖤",
        reply_markup=K([("📖 Ещё запись", "diary_new"), ("🏠 Меню", "menu")]))
    await state.clear()

    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        try: await bot.send_message(ADMIN_CHAT_ID,
            f"📖 Дневник @{cb.from_user.username or '?'}: {d['d_aroma']}\n{d['d_entry'][:200]}")
        except: pass

@router.callback_query(F.data == "diary_all")
async def diary_all(cb: CallbackQuery):
    await cb.answer()
    entries = get_diary(cb.from_user.id, 20)
    if not entries:
        await cb.message.answer("📖 Дневник пуст.", reply_markup=K([("✏️ Новая запись", "diary_new"), ("🏠 Меню", "menu")])); return
    lines = []
    for e in entries:
        date = e["created_at"][:10]
        mood = f" · 🎭{e['mood']}" if e.get("mood") and e["mood"] != "—" else ""
        lines.append(f"<b>{date}</b> · 🧴 {e['aroma_name']}{mood}\n<i>{e['text'][:100]}</i>")
    await cb.message.answer(f"📖 <b>Все записи</b> ({len(entries)})\n\n" + "\n\n".join(lines),
                            reply_markup=K([("✏️ Новая запись", "diary_new"), ("🏠 Меню", "menu")]))

# ═══════════════════════════════════════
#           REFERRAL SYSTEM
# ═══════════════════════════════════════
@router.callback_query(F.data == "referral")
async def referral(cb: CallbackQuery):
    await cb.answer()
    u = getu(cb.from_user.id)
    rc = u.get("ref_code", gen_ref(cb.from_user.id))
    refs = count_referrals(rc)
    link = f"https://t.me/dararomabox_bot?start={rc}"

    await cb.message.answer(
        f"🎁 <b>Пригласите друга</b>\n\n"
        f"За каждого друга, который оформит подписку,\n"
        f"вы получите <b>скидку 10%</b> на следующий бокс!\n\n"
        f"{div}\n\n"
        f"🔗 Ваша ссылка:\n<code>{link}</code>\n\n"
        f"👥 Приглашено: <b>{refs}</b>\n"
        f"💰 Накоплено скидок: <b>{refs * 10}%</b>\n\n"
        f"{div}\n"
        f"<i>Поделитесь ссылкой с друзьями!</i>",
        reply_markup=K([("🏠 Меню", "menu")]))

# ═══════════════════════════════════════
#           QUESTIONNAIRE (20 Q)
# ═══════════════════════════════════════
@router.callback_query(F.data == "sq")
async def sq(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.answer(
        f"🌿 <b>Парфюмерная анкета</b>\n\n"
        f"20 вопросов · 3-5 минут\n\n"
        f"Мы составим ваш <b>ольфакторный портрет</b> ✨\n\n"
        f"<i>Каждый ответ → ближе к идеальному аромату</i>")
    await asyncio.sleep(0.8)
    await cb.message.answer(hdr(1,"Для кого подбираем?","👤")+"\n\n<i>Определим направление</i>",
        reply_markup=K([("🙋‍♂️ Для себя (М)","g_m"),("🙋‍♀️ Для себя (Ж)","g_f"),("🎁 В подарок","g_gift")],2))
    await state.set_state(Q.gender)

# Q1
@router.callback_query(Q.gender, F.data.startswith("g_"))
async def q1(cb: CallbackQuery, state: FSMContext):
    v = {"g_m":"Мужчина","g_f":"Женщина","g_gift":"В подарок"}[cb.data]
    await state.update_data(gender=v); await cb.answer(f"✓ {v}")
    if cb.data == "g_gift":
        await cb.message.edit_text(hdr(1,"Кому дарим?","🎁"),
            reply_markup=K([("🙋‍♂️ Мужчине","gf_m"),("🙋‍♀️ Женщине","gf_f"),("← Назад","bk0")]))
        await state.set_state(Q.gift_gender); return
    await state.update_data(gift_gender="—"); await _q2(cb, state)

@router.callback_query(Q.gift_gender, F.data.startswith("gf_"))
async def q1b(cb: CallbackQuery, state: FSMContext):
    v = {"gf_m":"Мужчине","gf_f":"Женщине"}[cb.data]
    await state.update_data(gift_gender=v); await cb.answer(f"✓ {v}"); await _q2(cb, state)

async def _q2(cb, state):
    await cb.message.edit_text(hdr(2,"Возраст","📅"),
        reply_markup=K([("18-24","a1"),("25-34","a2"),("35-44","a3"),("45+","a4"),("← Назад","bk1")]))
    await state.set_state(Q.age)

@router.callback_query(Q.age, F.data.startswith("a"))
async def q2(cb: CallbackQuery, state: FSMContext):
    v = {"a1":"18-24","a2":"25-34","a3":"35-44","a4":"45+"}[cb.data]
    await state.update_data(age=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(3,"Образ жизни","🏃")+"\n\n<i>Ваш ритм → характер аромата</i>",
        reply_markup=K([("💼 Деловой","l1"),("🎨 Творческий","l2"),("🏋️ Активный","l3"),("🌙 Размеренный","l4"),("← Назад","bk2")],1))
    await state.set_state(Q.lifestyle)

@router.callback_query(Q.lifestyle, F.data.startswith("l"))
async def q3(cb: CallbackQuery, state: FSMContext):
    v = {"l1":"Деловой","l2":"Творческий","l3":"Активный","l4":"Размеренный"}[cb.data]
    await state.update_data(lifestyle=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(4,"Где носите?","🎭"),
        reply_markup=K([("📆 Каждый день","o1"),("🌃 На выход","o2"),("🏢 На работу","o3"),("🔀 По-разному","o4"),("← Назад","bk3")],1))
    await state.set_state(Q.occasions)

@router.callback_query(Q.occasions, F.data.startswith("o"))
async def q4(cb: CallbackQuery, state: FSMContext):
    v = {"o1":"Каждый день","o2":"На выход","o3":"На работу","o4":"По-разному"}[cb.data]
    await state.update_data(occasions=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(5,"Интенсивность","💨"),
        reply_markup=K([("🌬 Шёпот","i1"),("☁️ Умеренный","i2"),("🔥 Мощный шлейф","i3"),("🎲 По настроению","i4"),("← Назад","bk4")],1))
    await state.set_state(Q.intensity)

@router.callback_query(Q.intensity, F.data.startswith("i"))
async def q5(cb: CallbackQuery, state: FSMContext):
    v = {"i1":"Лёгкие","i2":"Умеренные","i3":"Мощные","i4":"По настроению"}[cb.data]
    await state.update_data(intensity=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(6,"Парфюмерный опыт","🎓"),
        reply_markup=K([("🌱 Новичок","e1"),("🌿 Любитель","e2"),("🌳 Энтузиаст","e3"),("👑 Гуру","e4"),("← Назад","bk5")],1))
    await state.set_state(Q.experience)

@router.callback_query(Q.experience, F.data.startswith("e"))
async def q6(cb: CallbackQuery, state: FSMContext):
    v = {"e1":"Новичок","e2":"Любитель","e3":"Энтузиаст","e4":"Гуру"}[cb.data]
    await state.update_data(experience=v); await cb.answer(f"✓ {v}")
    await state.update_data(_fav=[])
    await cb.message.edit_text(hdr(7,"Любимые ноты ❤️","🌸")+"\n\n<i>Выберите всё что нравится</i>",reply_markup=_nkb("f",[]))
    await state.set_state(Q.fav_notes)

@router.callback_query(Q.fav_notes, F.data.startswith("f_"))
async def q7(cb: CallbackQuery, state: FSMContext):
    d = await state.get_data(); fav = d.get("_fav", [])
    k = cb.data[2:]
    if k == "done":
        await state.update_data(fav_notes=", ".join(fav) if fav else "Не выбрано", _dis=[])
        await cb.answer()
        await cb.message.edit_text(hdr(8,"Нелюбимые ноты 🚫","❌")+"\n\n<i>Что НЕ должно быть?</i>",reply_markup=_nkb("d",[]))
        await state.set_state(Q.disliked_notes); return
    lb = NM.get(k, k)
    if lb in fav: fav.remove(lb)
    else: fav.append(lb)
    await state.update_data(_fav=fav); await cb.answer(f"{'✓' if lb in fav else '✗'} {lb}")
    await cb.message.edit_reply_markup(reply_markup=_nkb("f", fav))

@router.callback_query(Q.disliked_notes, F.data.startswith("d_"))
async def q8(cb: CallbackQuery, state: FSMContext):
    d = await state.get_data(); dis = d.get("_dis", [])
    k = cb.data[2:]
    if k == "done":
        await state.update_data(disliked_notes=", ".join(dis) if dis else "Нет")
        await cb.answer()
        await cb.message.edit_text(hdr(9,"Ваши ароматы","👃")+"\n\n<i>Что носите сейчас?\nНапишите или «нет».</i>")
        await state.set_state(Q.current_perfumes); return
    lb = NM.get(k, k)
    if lb in dis: dis.remove(lb)
    else: dis.append(lb)
    await state.update_data(_dis=dis); await cb.answer()
    await cb.message.edit_reply_markup(reply_markup=_nkb("d", dis))

@router.message(Q.current_perfumes)
async def q9(msg: Message, state: FSMContext):
    await state.update_data(current_perfumes=msg.text.strip())
    await msg.answer(hdr(10,"Сезон","🌤"),
        reply_markup=K([("🌸 Весна","s1"),("☀️ Лето","s2"),("🍂 Осень","s3"),("❄️ Зима","s4"),("🔄 Все","s5"),("← Назад","bk9")],2))
    await state.set_state(Q.season_pref)

@router.callback_query(Q.season_pref, F.data.startswith("s"))
async def q10(cb: CallbackQuery, state: FSMContext):
    v = {"s1":"Весна","s2":"Лето","s3":"Осень","s4":"Зима","s5":"Все"}[cb.data]
    await state.update_data(season_pref=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(11,"Время суток","🕐"),
        reply_markup=K([("🌅 День","t1"),("🌙 Вечер","t2"),("🔄 Универсально","t3"),("← Назад","bk10")],1))
    await state.set_state(Q.time_of_day)

@router.callback_query(Q.time_of_day, F.data.startswith("t"))
async def q11(cb: CallbackQuery, state: FSMContext):
    v = {"t1":"День","t2":"Вечер","t3":"Универсально"}[cb.data]
    await state.update_data(time_of_day=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(12,"Настроение","🎭")+"\n\n<i>Какую эмоцию хотите?</i>",
        reply_markup=K([("❤️ Романтика","m1"),("💪 Уверенность","m2"),("🧘 Спокойствие","m3"),("⚡ Энергия","m4"),("🔮 Загадочность","m5"),("😏 Соблазн","m6"),("← Назад","bk11")],2))
    await state.set_state(Q.mood)

@router.callback_query(Q.mood, F.data.startswith("m"))
async def q12(cb: CallbackQuery, state: FSMContext):
    v = {"m1":"Романтика","m2":"Уверенность","m3":"Спокойствие","m4":"Энергия","m5":"Загадочность","m6":"Соблазн"}[cb.data]
    await state.update_data(mood=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(13,"Ассоциации","🌍")+"\n\n<i>Закройте глаза... Где вы счастливы?</i>",
        reply_markup=K([("🌲 Лес","z1"),("🌊 Море","z2"),("🏙 Город","z3"),("🕌 Восток","z4"),("🍰 Кондитерская","z5"),("🏔 Горы","z6"),("📚 Библиотека","z7"),("🌾 Луг","z8"),("🏖 Тропики","z9"),("🪵 Камин","z10"),("☕ Кофейня","z11"),("🌃 Крыша","z12"),("← Назад","bk12")],3))
    await state.set_state(Q.associations)

@router.callback_query(Q.associations, F.data.startswith("z"))
async def q13(cb: CallbackQuery, state: FSMContext):
    v = ASSOC_MAP.get(cb.data, "?")
    await state.update_data(associations=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(14,"Стойкость","⏱"),
        reply_markup=K([("🕐 2-4ч","r1"),("🕕 6-8ч","r2"),("🕛 12+ч","r3"),("← Назад","bk13")],1))
    await state.set_state(Q.longevity)

@router.callback_query(Q.longevity, F.data.startswith("r"))
async def q14(cb: CallbackQuery, state: FSMContext):
    v = {"r1":"2-4ч","r2":"6-8ч","r3":"12+ч"}[cb.data]
    await state.update_data(longevity=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(15,"Эксперименты","🚀"),
        reply_markup=K([("🚀 Удивляйте!","x1"),("😌 Классику","x2"),("⚖️ 50/50","x3"),("← Назад","bk14")],1))
    await state.set_state(Q.discovery)

@router.callback_query(Q.discovery, F.data.startswith("x"))
async def q15(cb: CallbackQuery, state: FSMContext):
    v = {"x1":"Эксперименты","x2":"Классика","x3":"50/50"}[cb.data]
    await state.update_data(discovery=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(16,"Ценовой сегмент","💎"),
        reply_markup=K([("🛒 Масс","b1"),("⭐ Средний","b2"),("💫 Ниша","b3"),("👑 Люкс","b4"),("🎲 Все","b5"),("← Назад","bk15")],2))
    await state.set_state(Q.budget)

@router.callback_query(Q.budget, F.data.startswith("b"))
async def q16(cb: CallbackQuery, state: FSMContext):
    v = {"b1":"Масс","b2":"Средний","b3":"Ниша","b4":"Люкс","b5":"Все"}[cb.data]
    await state.update_data(budget=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(17,"Гардероб","👔"),
        reply_markup=K([("👕 Casual","w1"),("👔 Классика","w2"),("🧢 Street","w3"),("👗 Элегантный","w4"),("🎨 Эклектика","w5"),("← Назад","bk16")],2))
    await state.set_state(Q.wardrobe)

@router.callback_query(Q.wardrobe, F.data.startswith("w"))
async def q17(cb: CallbackQuery, state: FSMContext):
    v = {"w1":"Casual","w2":"Классика","w3":"Street","w4":"Элегантный","w5":"Эклектика"}[cb.data]
    await state.update_data(wardrobe=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(18,"Аллергии","⚠️")+"\n\n<i>Напишите или нажмите «Нет»</i>",
        reply_markup=K([("✅ Нет","al0"),("← Назад","bk17")]))
    await state.set_state(Q.allergies)

@router.callback_query(Q.allergies, F.data == "al0")
async def q18a(cb: CallbackQuery, state: FSMContext):
    await state.update_data(allergies="Нет"); await cb.answer(); await _q19(cb.message, state)
@router.message(Q.allergies)
async def q18b(msg: Message, state: FSMContext):
    await state.update_data(allergies=msg.text.strip()); await _q19(msg, state)

async def _q19(msg, state):
    await msg.answer(hdr(19,"Цель","🎯"),
        reply_markup=K([("🔍 Найти свой","g1"),("🌍 Новое","g2"),("📚 Коллекция","g3"),("🎁 Подарок","g4"),("← Назад","bk18")],1))
    await state.set_state(Q.goal)

@router.callback_query(Q.goal, F.data.startswith("g"))
async def q19(cb: CallbackQuery, state: FSMContext):
    v = {"g1":"Найти свой","g2":"Новое","g3":"Коллекция","g4":"Подарок"}[cb.data]
    await state.update_data(goal=v); await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(20,"Пожелания","💬")+"\n\n<i>Любые мысли. Или «Пропустить».</i>",
        reply_markup=K([("⏭ Пропустить","ew0"),("← Назад","bk19")]))
    await state.set_state(Q.extra_wishes)

@router.callback_query(Q.extra_wishes, F.data == "ew0")
async def q20a(cb: CallbackQuery, state: FSMContext):
    await state.update_data(extra_wishes="—"); await cb.answer(); await _box(cb.message, state)
@router.message(Q.extra_wishes)
async def q20b(msg: Message, state: FSMContext):
    await state.update_data(extra_wishes=msg.text.strip()); await _box(msg, state)

# ═══════════════════════════════════════
#       BOX, DURATION, DELIVERY, CONFIRM
# ═══════════════════════════════════════
async def _box(msg, state):
    txt = f"🎉 <b>Анкета завершена!</b>\n\n{pbar(TOTAL_Q,TOTAL_Q)}\n\nВыберите формат:\n\n"
    for bk, b in BOXES.items(): txt += f"{b['em']} <b>{b['name']}</b>\n<i>{b['desc']}</i> · <b>{b['price']:,} ₽</b>/мес\n\n"
    await msg.answer(txt, reply_markup=K([("🧪 8×3мл","bx_8x3"),("🧴 6×6мл","bx_6x6"),("✨ 5×10мл","bx_5x10"),("← Назад","bk20")],1))
    await state.set_state(Q.box_type)

@router.callback_query(Q.box_type, F.data.startswith("bx_"))
async def pickbox(cb: CallbackQuery, state: FSMContext):
    bk = cb.data[3:]; await state.update_data(box_type=bk); await cb.answer()
    bx = BOXES[bk]
    lines = [f"▸ <b>{DURS[m]['l']}{DURS[m]['b']}</b>\n   {cprice(bk,m)[0]:,} ₽/мес → <b>{cprice(bk,m)[1]:,} ₽</b>" for m in DURS]
    await cb.message.edit_text(f"⏳ <b>Срок</b> · {bx['em']} {bx['name']}\n\n"+"\n\n".join(lines),
        reply_markup=K([("2 мес","du2"),("4 мес (−5%)","du4"),("6 мес (−10%) 🔥","du6"),("← Назад","bkbox")],1))
    await state.set_state(Q.duration)

@router.callback_query(Q.duration, F.data.startswith("du"))
async def pickdur(cb: CallbackQuery, state: FSMContext):
    m = int(cb.data[2:]); d = await state.get_data(); mo, tot = cprice(d["box_type"], m)
    await state.update_data(duration_months=m, monthly_price=mo, total_price=tot); await cb.answer()
    await cb.message.edit_text("🚚 <b>Доставка</b>",
        reply_markup=K([("📦 Почта — 280₽","dl_post"),("🚚 СДЭК — 280₽","dl_cdek"),("🏍 Курьер Мск — 350₽","dl_courier"),("← Назад","bkdur")],1))
    await state.set_state(Q.delivery_type)

@router.callback_query(Q.delivery_type, F.data.startswith("dl_"))
async def pickdel(cb: CallbackQuery, state: FSMContext):
    dt = cb.data[3:]; dc = DEL_COST[dt]
    await state.update_data(delivery_type=dt, delivery_cost=dc); await cb.answer()
    await cb.message.edit_text("👤 <b>ФИО получателя</b>\n\nНапишите <b>Фамилию Имя Отчество</b> полностью:\n\n<i>Например: Иванов Иван Иванович</i>")
    await state.set_state(Q.full_name)

@router.message(Q.full_name)
async def fn(msg: Message, state: FSMContext):
    await state.update_data(full_name=msg.text.strip()); await msg.answer("📱 <b>Телефон:</b>"); await state.set_state(Q.phone)
@router.message(Q.phone)
async def ph(msg: Message, state: FSMContext):
    await state.update_data(phone=msg.text.strip()); await msg.answer("🏙 <b>Город:</b>"); await state.set_state(Q.city)
@router.message(Q.city)
async def ct(msg: Message, state: FSMContext):
    await state.update_data(city=msg.text.strip())
    d = await state.get_data(); dt = d.get("delivery_type", "post")
    if dt == "cdek": await msg.answer("📍 <b>Полный адрес отделения СДЭК</b>\n\n<i>Например: г. Москва, ул. Тверская, д. 5, отд. СДЭК №123</i>")
    elif dt == "courier": await msg.answer("🏠 <b>Адрес</b> (внутри МКАД):")
    else: await msg.answer("🏠 <b>Адрес</b> (улица, дом, кв):")
    await state.set_state(Q.address)
@router.message(Q.address)
async def ad(msg: Message, state: FSMContext):
    await state.update_data(address=msg.text.strip())
    d = await state.get_data()
    if d.get("delivery_type") == "post":
        await msg.answer("📮 <b>Индекс:</b>"); await state.set_state(Q.postal_code)
    else: await state.update_data(postal_code="—"); await _summary(msg, state)
@router.message(Q.postal_code)
async def pc(msg: Message, state: FSMContext):
    await state.update_data(postal_code=msg.text.strip()); await _summary(msg, state)

async def _summary(msg, state):
    d = await state.get_data(); bx = BOXES[d["box_type"]]; du = DURS[d["duration_months"]]
    mo, tot = cprice(d["box_type"], d["duration_months"]); dc = d.get("delivery_cost", 0); grand = tot + dc
    dln = DEL_NAME.get(d.get("delivery_type", "post"), "?")

    txt = f"""{DIV}
📋 <b>ЗАЯВКА</b>
{DIV}
<b>Подписка:</b> {bx['em']} {bx['name']}
⏳ {du['l']}{du['b']} · {mo:,}₽/мес
{dln} · {dc}₽
<b>💳 ИТОГО: {grand:,} ₽</b>

<b>Доставка:</b>
👤 {d.get('full_name','—')} · 📱 {d.get('phone','—')}
🏙 {d.get('city','—')} · 🏠 {d.get('address','—')}
{DIV}"""
    await msg.answer(txt+"\n<b>Всё верно?</b>",reply_markup=K([("✅ Подтвердить","cf1"),("✏️ Заново","cf0")],1))
    await state.set_state(Q.confirm)

@router.callback_query(Q.confirm, F.data == "cf1")
async def cfyes(cb: CallbackQuery, state: FSMContext):
    d = await state.get_data(); await cb.answer("✅")
    savu(cb.from_user.id, {
        "username":cb.from_user.username or "","first_name":cb.from_user.first_name or "",
        **{k:d.get(k,"") for k in ["gender","gift_gender","age","lifestyle","occasions","intensity","experience",
        "fav_notes","disliked_notes","current_perfumes","season_pref","time_of_day","mood","associations",
        "longevity","discovery","budget","wardrobe","allergies","goal","extra_wishes",
        "box_type","full_name","phone","city","address","postal_code","delivery_type"]},
        "duration_months":d.get("duration_months",0),"monthly_price":d.get("monthly_price",0),
        "total_price":d.get("total_price",0),"delivery_cost":d.get("delivery_cost",0),"status":"pending",
    })
    bx = BOXES[d["box_type"]]; mo, tot = cprice(d["box_type"], d["duration_months"])
    dc = d.get("delivery_cost", 0); grand = tot + dc

    await cb.message.edit_text(f"🎉 <b>Заявка оформлена!</b>\n\n💬 {CONTACT} — если есть вопросы\nСпасибо за <b>DARBOX</b>! 🖤")
    await asyncio.sleep(1)
    await cb.message.answer(f"💰 <b>Оплата: {grand:,} ₽</b>\n\n{PAYMENT_INFO}",
        reply_markup=K([("✅ Я оплатил(а)","pd"),("💬 Написать нам","cmsg")],1))

    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        try: await bot.send_message(ADMIN_CHAT_ID,
            f"🆕 <b>ЗАЯВКА!</b> @{cb.from_user.username or '?'} <code>{cb.from_user.id}</code>\n"
            f"📦 {bx['name']}×{d['duration_months']}мес · 💰{grand:,}₽\n"
            f"❤️ {d.get('fav_notes','—')}\n🚫 {d.get('disliked_notes','—')}\n👃 {d.get('current_perfumes','—')}\n"
            f"🎭 {d.get('mood','—')} · 🌍 {d.get('associations','—')}\n📱 {d.get('phone','—')}",
            reply_markup=K([(f"💬","ac_{cb.from_user.id}"),(f"✅ Оплата","ap_{cb.from_user.id}"),(f"👤","apr_{cb.from_user.id}")]))
        except: pass
    await state.clear()

@router.callback_query(Q.confirm, F.data == "cf0")
async def cfno(cb: CallbackQuery, state: FSMContext):
    await state.clear(); await cb.answer()
    await cb.message.edit_text("🔄 Заново..."); await cmd_start(cb.message, state)

# ═══════════════════════════════════════
#           PAYMENT & STATUS
# ═══════════════════════════════════════
@router.callback_query(F.data == "pd")
async def paydone(cb: CallbackQuery):
    await cb.answer("✅")
    await cb.message.edit_text("⏳ Проверяем оплату... До 30 мин 🖤",reply_markup=K([("💬 Написать","cmsg"),("🏠 Меню","menu")]))
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        u = getu(cb.from_user.id)
        try: await bot.send_message(ADMIN_CHAT_ID,f"💳 Оплата! @{cb.from_user.username or '?'} <code>{cb.from_user.id}</code> {u.get('total_price',0)+u.get('delivery_cost',0):,}₽",
            reply_markup=K([(f"✅ OK","ap_{cb.from_user.id}"),(f"💬","ac_{cb.from_user.id}")]))
        except: pass

@router.callback_query(F.data.startswith("ap_"))
async def adminpay(cb: CallbackQuery):
    if cb.from_user.username != ADMIN_USERNAME: await cb.answer("⛔"); return
    uid = int(cb.data[3:]); now = datetime.now()
    nd = (now + timedelta(days=30)).strftime("%Y-%m-%d")
    savu(uid, {"status":"paid","paid_at":now.isoformat(),"next_delivery":nd,"months_received":0})
    await cb.answer("✅"); await cb.message.edit_text(cb.message.text + f"\n\n✅ ОПЛАТА OK · {now.strftime('%d.%m.%Y')}")
    try: await bot.send_message(uid,"🎉 <b>Подписка активна!</b>\n\nМы собираем ваш аромабокс 🖤",reply_markup=K([("🏠 Меню","menu")]))
    except: pass

# ═══════════════════════════════════════
#           ENHANCED FEEDBACK (3 ratings)
# ═══════════════════════════════════════
@router.callback_query(F.data == "fbs")
async def fbs(cb: CallbackQuery, state: FSMContext):
    await cb.answer(); await state.clear()
    await cb.message.answer("⭐ <b>Оценка аромата</b>\n\nКакой месяц?",reply_markup=K([(f"{i}-й","fb_{i}") for i in range(1,7)]+[("🏠 Меню","menu")]))
    await state.set_state(Fb.month)

@router.message(Command("feedback"))
async def fbcmd(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("⭐ <b>Оценка</b>\n\nМесяц?",reply_markup=K([(f"{i}-й","fb_{i}") for i in range(1,7)]))
    await state.set_state(Fb.month)

@router.callback_query(Fb.month, F.data.startswith("fb_"))
async def fbm(cb: CallbackQuery, state: FSMContext):
    m = int(cb.data[3:]); await state.update_data(fm=m); await cb.answer()
    await cb.message.edit_text(f"📝 Месяц {m} — название аромата:"); await state.set_state(Fb.aroma)

@router.message(Fb.aroma)
async def fba(msg: Message, state: FSMContext):
    await state.update_data(fa=msg.text.strip())
    await msg.answer(f"⭐ <b>Общее впечатление</b> от «{msg.text.strip()}»:",
        reply_markup=K([("😍 5","fo5"),("👍 4","fo4"),("😐 3","fo3"),("👎 2","fo2"),("🤢 1","fo1")],5))
    await state.set_state(Fb.overall)

@router.callback_query(Fb.overall, F.data.startswith("fo"))
async def fbo(cb: CallbackQuery, state: FSMContext):
    r = int(cb.data[2:]); await state.update_data(fo=r); await cb.answer()
    await cb.message.edit_text("⏱ <b>Стойкость</b> (как долго держится?):",
        reply_markup=K([("🔥 5","fl5"),("4","fl4"),("3","fl3"),("2","fl2"),("💨 1","fl1")],5))
    await state.set_state(Fb.longevity)

@router.callback_query(Fb.longevity, F.data.startswith("fl"))
async def fbl(cb: CallbackQuery, state: FSMContext):
    r = int(cb.data[2:]); await state.update_data(fl=r); await cb.answer()
    await cb.message.edit_text("💨 <b>Шлейф</b> (чувствуют ли окружающие?):",
        reply_markup=K([("🔥 5","fs5"),("4","fs4"),("3","fs3"),("2","fs2"),("💨 1","fs1")],5))
    await state.set_state(Fb.sillage)

@router.callback_query(Fb.sillage, F.data.startswith("fs"))
async def fbs_(cb: CallbackQuery, state: FSMContext):
    r = int(cb.data[2:]); await state.update_data(fs=r); await cb.answer()
    await cb.message.edit_text("💬 Комментарий?",reply_markup=K([("⏭ Пропустить","fcs")]))
    await state.set_state(Fb.comment)

@router.callback_query(Fb.comment, F.data == "fcs")
async def fcs(cb: CallbackQuery, state: FSMContext):
    await state.update_data(fc="—"); await cb.answer(); await _fbs(cb.message, state, cb.from_user.id)
@router.message(Fb.comment)
async def fct(msg: Message, state: FSMContext):
    await state.update_data(fc=msg.text.strip()); await _fbs(msg, state, msg.from_user.id)

async def _fbs(msg, state, uid):
    d = await state.get_data()
    savfb(uid, d["fm"], d["fa"], d["fo"], d["fl"], d["fs"], d["fc"])
    await msg.answer(
        f"✅ <b>Оценка сохранена!</b>\n\n"
        f"🧴 {d['fa']}\n"
        f"⭐ Общее: {'⭐'*d['fo']} · ⏱ Стойкость: {d['fl']}/5 · 💨 Шлейф: {d['fs']}/5\n"
        f"{('💬 '+d['fc']) if d['fc']!='—' else ''}\n\nЕщё один аромат?",
        reply_markup=K([("🧴 Да","fb_more"),("✅ Всё","fb_done"),("🏠 Меню","menu")]))
    await state.set_state(Fb.more)
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        try: await bot.send_message(ADMIN_CHAT_ID,f"⭐ @{msg.chat.username if hasattr(msg.chat,'username') else '?'} ({uid}): {d['fa']} — {'⭐'*d['fo']} ⏱{d['fl']} 💨{d['fs']}\n{d['fc']}")
        except: pass

@router.callback_query(Fb.more, F.data == "fb_more")
async def fbmore(cb: CallbackQuery, state: FSMContext):
    d = await state.get_data(); await cb.answer()
    await cb.message.edit_text(f"📝 Месяц {d['fm']} — аромат:"); await state.set_state(Fb.aroma)
@router.callback_query(Fb.more, F.data == "fb_done")
async def fbdone(cb: CallbackQuery, state: FSMContext):
    await cb.answer(); await state.clear()
    await cb.message.edit_text("🙏 Спасибо! Учтём 🖤\n\n📊 Посмотрите вашу карту вкуса!",
        reply_markup=K([("📊 Карта вкуса","taste_map"),("🏠 Меню","menu")]))

# ═══════════════════════════════════════
#           MY SUBSCRIPTION
# ═══════════════════════════════════════
@router.callback_query(F.data == "mysub")
async def mysub(cb: CallbackQuery):
    await cb.answer(); u = getu(cb.from_user.id)
    if not u or not u.get("box_type"):
        await cb.message.answer("Нет подписки.",reply_markup=K([("🌸 Оформить","sq"),("🏠 Меню","menu")])); return
    bx = BOXES.get(u["box_type"], {})
    st = {"new":"⏳ Ожидает","pending":"📝 Заявка","paid":"✅ Активна","paused":"⏸ Пауза"}.get(u.get("status",""),"?")
    await cb.message.answer(
        f"📋 <b>Подписка</b>\n\n{bx.get('em','')} {bx.get('name','?')}\n⏳ {u.get('duration_months','?')} мес · {u.get('monthly_price',0):,}₽/мес\n"
        f"📊 {st}\n📦 Получено: {u.get('months_received',0)} боксов\n📅 След: {u.get('next_delivery','—')}",
        reply_markup=K([("⭐ Оценить","fbs"),("🏠 Меню","menu")]))

# ═══════════════════════════════════════
#           CHAT SYSTEM
# ═══════════════════════════════════════
@router.callback_query(F.data == "cmsg")
async def cmsg(cb: CallbackQuery): await cb.answer(); await cb.message.answer("💬 Напишите — ответим!")

@router.callback_query(F.data.startswith("ac_"))
async def acstart(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.username != ADMIN_USERNAME: await cb.answer("⛔"); return
    uid = int(cb.data[3:]); achat_with[cb.chat.id] = uid; await cb.answer()
    await cb.message.answer(f"💬 Чат с <code>{uid}</code>. /endchat"); await state.set_state(AChat.chatting)

@router.message(Command("chat"))
async def cchat(msg: Message, state: FSMContext):
    if msg.from_user.username != ADMIN_USERNAME: return
    p = msg.text.split()
    if len(p)<2: await msg.answer("/chat <code>ID</code>"); return
    achat_with[msg.chat.id] = int(p[1])
    await msg.answer(f"💬 → <code>{p[1]}</code>. /endchat"); await state.set_state(AChat.chatting)

@router.message(Command("endchat"))
async def echat(msg: Message, state: FSMContext):
    achat_with.pop(msg.chat.id, None); await state.clear(); await msg.answer("✅")

@router.message(AChat.chatting)
async def asend(msg: Message, state: FSMContext):
    uid = achat_with.get(msg.chat.id)
    if not uid: await state.clear(); return
    try:
        await bot.send_message(uid, f"💬 <b>DAR Perfum:</b>\n\n{msg.text}", reply_markup=K([("💬 Ответить","cmsg"),("🏠 Меню","menu")]))
        savmsg(uid, "admin→client", msg.text); await msg.answer(f"✅ → {uid}")
    except Exception as ex: await msg.answer(f"❌ {ex}")

# ═══════════════════════════════════════
#           ADDRESS CONFIRM
# ═══════════════════════════════════════
@router.callback_query(F.data.startswith("addr_same_"))
async def addr_same(cb: CallbackQuery):
    await cb.answer("✅"); await cb.message.edit_text("✅ Адрес подтверждён! Бокс скоро отправим 🖤")
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        u = getu(int(cb.data.replace("addr_same_","")))
        try: await bot.send_message(ADMIN_CHAT_ID, f"✅ @{u.get('username','?')} адрес ОК: {u.get('city','?')}, {u.get('address','?')}")
        except: pass

@router.callback_query(F.data.startswith("addr_new_"))
async def addr_new(cb: CallbackQuery, state: FSMContext):
    uid = int(cb.data.replace("addr_new_","")); await cb.answer()
    await cb.message.edit_text("🏠 <b>Новый адрес:</b>\n\nГород, улица, дом, кв:")
    await state.update_data(confirm_uid=uid); await state.set_state(AddrConfirm.address)

@router.message(AddrConfirm.address)
async def new_addr(msg: Message, state: FSMContext):
    d = await state.get_data(); uid = d.get("confirm_uid", msg.from_user.id)
    savu(uid, {"address": msg.text.strip()})
    await msg.answer("✅ Адрес обновлён! 🖤",reply_markup=K([("🏠 Меню","menu")])); await state.clear()
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        try: await bot.send_message(ADMIN_CHAT_ID, f"📍 {uid} новый адрес: {msg.text.strip()}")
        except: pass

# ═══════════════════════════════════════
#           BACK BUTTONS
# ═══════════════════════════════════════
@router.callback_query(F.data.startswith("bk"))
async def goback(cb: CallbackQuery, state: FSMContext):
    n = cb.data[2:]; await cb.answer("←")
    backs = {
        "0": (Q.gender, hdr(1,"Для кого?","👤"), [("🙋‍♂️ М","g_m"),("🙋‍♀️ Ж","g_f"),("🎁 Подарок","g_gift")]),
        "1": (Q.gender, hdr(1,"Для кого?","👤"), [("🙋‍♂️ М","g_m"),("🙋‍♀️ Ж","g_f"),("🎁 Подарок","g_gift")]),
        "2": (Q.age, hdr(2,"Возраст","📅"), [("18-24","a1"),("25-34","a2"),("35-44","a3"),("45+","a4"),("← Назад","bk1")]),
        "3": (Q.lifestyle, hdr(3,"Образ жизни","🏃"), [("💼 Деловой","l1"),("🎨 Творческий","l2"),("🏋️ Активный","l3"),("🌙 Размеренный","l4"),("← Назад","bk2")]),
        "4": (Q.occasions, hdr(4,"Где носите?","🎭"), [("📆 Каждый день","o1"),("🌃 На выход","o2"),("🏢 Работа","o3"),("🔀 По-разному","o4"),("← Назад","bk3")]),
        "5": (Q.intensity, hdr(5,"Интенсивность","💨"), [("🌬 Шёпот","i1"),("☁️ Умеренный","i2"),("🔥 Мощный","i3"),("🎲 Разный","i4"),("← Назад","bk4")]),
        "9": (Q.current_perfumes, hdr(9,"Ваши ароматы","👃")+"\n\n<i>Напишите</i>", None),
        "10": (Q.season_pref, hdr(10,"Сезон","🌤"), [("🌸","s1"),("☀️","s2"),("🍂","s3"),("❄️","s4"),("🔄","s5"),("← Назад","bk9")]),
        "11": (Q.time_of_day, hdr(11,"Время","🕐"), [("🌅 День","t1"),("🌙 Вечер","t2"),("🔄 Универс","t3"),("← Назад","bk10")]),
        "12": (Q.mood, hdr(12,"Настроение","🎭"), [("❤️","m1"),("💪","m2"),("🧘","m3"),("⚡","m4"),("🔮","m5"),("😏","m6"),("← Назад","bk11")]),
        "13": (Q.associations, hdr(13,"Ассоциации","🌍"), [("🌲","z1"),("🌊","z2"),("🏙","z3"),("🕌","z4"),("🍰","z5"),("🏔","z6"),("📚","z7"),("🌾","z8"),("🏖","z9"),("🪵","z10"),("☕","z11"),("🌃","z12"),("←","bk12")]),
        "14": (Q.longevity, hdr(14,"Стойкость","⏱"), [("🕐 2-4ч","r1"),("🕕 6-8ч","r2"),("🕛 12+ч","r3"),("← Назад","bk13")]),
        "15": (Q.discovery, hdr(15,"Эксперименты","🚀"), [("🚀 Да","x1"),("😌 Нет","x2"),("⚖️ 50/50","x3"),("← Назад","bk14")]),
        "16": (Q.budget, hdr(16,"Сегмент","💎"), [("🛒","b1"),("⭐","b2"),("💫","b3"),("👑","b4"),("🎲","b5"),("←","bk15")]),
        "17": (Q.wardrobe, hdr(17,"Гардероб","👔"), [("👕","w1"),("👔","w2"),("🧢","w3"),("👗","w4"),("🎨","w5"),("←","bk16")]),
        "18": (Q.allergies, hdr(18,"Аллергии","⚠️"), [("✅ Нет","al0"),("← Назад","bk17")]),
        "19": (Q.goal, hdr(19,"Цель","🎯"), [("🔍","g1"),("🌍","g2"),("📚","g3"),("🎁","g4"),("←","bk18")]),
        "20": (Q.extra_wishes, hdr(20,"Пожелания","💬"), [("⏭ Пропустить","ew0"),("← Назад","bk19")]),
    }
    if n == "box": await _box(cb.message, state); return
    if n == "dur":
        d = await state.get_data(); bk = d.get("box_type", "8x3")
        await _box(cb.message, state); return
    if n in backs:
        st, txt, btns = backs[n]
        await state.set_state(st)
        if btns: await cb.message.edit_text(txt, reply_markup=K(btns, 2 if len(btns)>5 else 1))
        else: await cb.message.edit_text(txt)

# ═══════════════════════════════════════
#           ADMIN PANEL
# ═══════════════════════════════════════
@router.message(Command("admin"))
async def cadmin(msg: Message):
    if msg.from_user.username != ADMIN_USERNAME: await msg.answer("⛔"); return
    global ADMIN_CHAT_ID; ADMIN_CHAT_ID = msg.chat.id
    s = get_subs(); paid = [x for x in s if x.get("status")=="paid"]
    await msg.answer(
        f"🔐 <b>Админ DARBOX v4</b>\n\n📊 Заявок: {len(s)} · 💳 Оплат: {len(paid)}\n🔔 Уведомления: ВКЛ\n\n"
        f"/subs · /profile ID · /reviews ID\n/chat ID · /endchat\n/broadcast · /remind · /due")

@router.message(Command("subs"))
async def csubs(msg: Message):
    if msg.from_user.username != ADMIN_USERNAME: return
    s = get_subs()
    if not s: await msg.answer("Пусто."); return
    lines = [f"• @{x['username'] or '?'} — {BOXES.get(x['box_type'],{}).get('short','?')} {x['duration_months']}мес ({x['status']}) {('💳'+x.get('paid_at','')[:10]) if x.get('paid_at') else ''}" for x in s[:30]]
    await msg.answer(f"📋 ({len(s)}):\n\n"+"\n".join(lines))

@router.message(Command("due"))
async def cdue(msg: Message):
    if msg.from_user.username != ADMIN_USERNAME: return
    d = get_due(7)
    if not d: await msg.answer("Нет отправок."); return
    lines = [f"• @{x['username'] or '?'} · {x.get('city','?')} · {x.get('address','?')}\n  📅 {x.get('next_delivery','?')}" for x in d]
    await msg.answer(f"📦 <b>Отправки ({len(d)}):</b>\n\n"+"\n\n".join(lines))

@router.message(Command("remind"))
async def cremind(msg: Message):
    if msg.from_user.username != ADMIN_USERNAME: return
    d = get_due(3); sent = 0
    for u in d:
        try:
            await bot.send_message(u["user_id"],
                f"📦 <b>DARBOX скоро!</b>\n\nАдрес: {u.get('city','?')}, {u.get('address','?')}\n\nВерно?",
                reply_markup=K([(f"✅ Да","addr_same_{u['user_id']}"),(f"📍 Изменить","addr_new_{u['user_id']}")],1))
            sent += 1
        except: pass
        await asyncio.sleep(0.1)
    await msg.answer(f"✅ {sent}/{len(d)}")

@router.message(Command("profile"))
async def cprofile(msg: Message):
    if msg.from_user.username != ADMIN_USERNAME: return
    p = msg.text.split()
    if len(p)<2: await msg.answer("/profile <code>ID</code>"); return
    u = getu(int(p[1]))
    if not u: await msg.answer("?"); return
    stats = get_taste_stats(int(p[1]))
    await msg.answer(
        f"👤 @{u.get('username','?')} | {u.get('full_name','?')} | 📊 {u.get('status','?')}\n"
        f"💳 {u.get('paid_at','—')[:10] if u.get('paid_at') else '—'} | 📅 {u.get('next_delivery','—')}\n\n"
        f"{u.get('gender','?')} {u.get('age','?')} | {u.get('lifestyle','?')} | {u.get('experience','?')}\n"
        f"❤️ {u.get('fav_notes','?')}\n🚫 {u.get('disliked_notes','?')}\n👃 {u.get('current_perfumes','?')}\n"
        f"🎭 {u.get('mood','?')} | 🌍 {u.get('associations','?')} | ⏱ {u.get('longevity','?')}\n"
        f"💎 {u.get('budget','?')} | 👔 {u.get('wardrobe','?')} | 🎯 {u.get('goal','?')}\n"
        f"⚠️ {u.get('allergies','?')}\n💬 {u.get('extra_wishes','?')}\n\n"
        f"📊 Оценок: {stats['total'] if stats else 0}" + (f" | Средн: {stats['avg_overall']}/5" if stats else ""))

@router.callback_query(F.data.startswith("apr_"))
async def aqp(cb: CallbackQuery):
    if cb.from_user.username != ADMIN_USERNAME: await cb.answer("⛔"); return
    uid = int(cb.data[4:]); u = getu(uid); await cb.answer()
    if u: await cb.message.answer(f"👤 @{u.get('username','?')}\n❤️ {u.get('fav_notes','?')}\n🚫 {u.get('disliked_notes','?')}\n🎭 {u.get('mood','?')} 🌍 {u.get('associations','?')}")

@router.message(Command("reviews"))
async def crev(msg: Message):
    if msg.from_user.username != ADMIN_USERNAME: return
    p = msg.text.split()
    if len(p)<2: await msg.answer("/reviews <code>ID</code>"); return
    fs = getfb(int(p[1]))
    if not fs: await msg.answer("Нет."); return
    lines = [f"М{f['month_num']} | {f['aroma_name']} {'⭐'*f['rating_overall']} ⏱{f.get('rating_longevity','—')} 💨{f.get('rating_sillage','—')}\n   {f['comment']}" for f in fs]
    await msg.answer("💬 Отзывы:\n\n"+"\n\n".join(lines))

@router.message(Command("broadcast"))
async def cbcast(msg: Message, state: FSMContext):
    if msg.from_user.username != ADMIN_USERNAME: return
    await msg.answer("📢 Текст:"); await state.set_state(Bcast.text)

@router.message(Bcast.text)
async def dobcast(msg: Message, state: FSMContext):
    if msg.from_user.username != ADMIN_USERNAME: return
    s = get_subs(); sent = 0
    for x in s:
        try: await bot.send_message(x["user_id"], msg.text); sent += 1
        except: pass
        await asyncio.sleep(0.1)
    await msg.answer(f"✅ {sent}/{len(s)}"); await state.clear()

# ═══════════════════════════════════════
#           CLIENT → ADMIN
# ═══════════════════════════════════════
@router.message(F.text)
async def c2a(msg: Message, state: FSMContext):
    if msg.from_user.username == ADMIN_USERNAME: return
    cs = await state.get_state()
    if cs and any(cs.startswith(p) for p in ["Q:","Fb:","Diary:","AddrConfirm:","Bcast:"]): return
    savmsg(msg.from_user.id, "client→admin", msg.text)
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        try: await bot.send_message(ADMIN_CHAT_ID,
            f"💬 @{msg.from_user.username or '?'} (<code>{msg.from_user.id}</code>):\n{msg.text}",
            reply_markup=K([(f"💬","ac_{msg.from_user.id}"),(f"👤","apr_{msg.from_user.id}")]))
        except: pass
    await msg.answer("✅ Отправлено! 🖤", reply_markup=K([("🏠 Меню","menu")]))

# ═══════════════════════════════════════
#           LAUNCH
# ═══════════════════════════════════════
async def main():
    init_db()
    print("🎩 DARBOX v4 Premium!")

    # Start web server for Mini App
    await start_web_server()

    # Start bot polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
