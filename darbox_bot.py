"""
🎁 DARBOX v5 — Premium Telegram Aroma Subscription Bot
DAR Perfum | @dararomabox_bot
Mini App first — all UI in WebApp, bot handles admin + payments + notifications
"""
import asyncio, sqlite3, json, hashlib, os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (Message, CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, WebAppInfo, MenuButtonWebApp)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

# ═══════════════════════════════════════
#              CONFIG
# ═══════════════════════════════════════
BOT_TOKEN = "8054022324:AAHK2bUZ1lLEDk8FREDbAEl5En040OtEHg0"
ADMIN_USERNAME = "nasomato"
ADMIN_CHAT_ID = None
CONTACT = "@darperf"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 8080))
WEBAPP_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
if WEBAPP_URL and not WEBAPP_URL.startswith("http"):
    WEBAPP_URL = f"https://{WEBAPP_URL}"

def gen_ref(uid): return hashlib.md5(f"dar{uid}".encode()).hexdigest()[:8]

# ═══════════════════════════════════════
#              DATABASE
# ═══════════════════════════════════════
DB = "darbox_v5.db"
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
        text TEXT, mood TEXT, occasion TEXT, rating INTEGER, created_at TEXT
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
class Bcast(StatesGroup):
    text = State()

class AChat(StatesGroup):
    chatting = State()

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

achat_with = {}
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage()); router = Router(); dp.include_router(router)

# ═══════════════════════════════════════
#           WEB SERVER (Mini App)
# ═══════════════════════════════════════
async def handle_index(request):
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except FileNotFoundError:
        return web.Response(text="<h1>DARBOX</h1><p>index.html not found</p>", content_type="text/html")

async def handle_health(request):
    return web.Response(text="OK")

# ═══════════════════════════════════════
#           API ENDPOINTS (for Mini App)
# ═══════════════════════════════════════
async def api_user(request):
    """Get user data for Mini App"""
    uid = request.query.get("uid")
    if not uid: return web.json_response({"error": "no uid"}, status=400)
    u = getu(int(uid))
    return web.json_response(u if u else {"status": "new"})

async def api_submit_order(request):
    """Submit order from Mini App"""
    try:
        data = await request.json()
        uid = data.get("user_id")
        if not uid: return web.json_response({"error": "no user_id"}, status=400)
        savu(int(uid), {
            k: data.get(k, "") for k in [
                "box_type", "full_name", "phone", "city", "address", "postal_code",
                "delivery_type", "gender", "fav_notes", "disliked_notes", "mood",
                "associations", "experience", "budget"
            ]
        })
        savu(int(uid), {
            "duration_months": data.get("duration_months", 2),
            "monthly_price": data.get("monthly_price", 0),
            "total_price": data.get("total_price", 0),
            "delivery_cost": data.get("delivery_cost", 0),
            "status": "pending"
        })
        # Notify admin
        global ADMIN_CHAT_ID
        if ADMIN_CHAT_ID:
            try:
                await bot.send_message(ADMIN_CHAT_ID,
                    f"🆕 <b>ЗАЯВКА из Mini App!</b>\n"
                    f"👤 {data.get('full_name', '?')} · 📱 {data.get('phone', '?')}\n"
                    f"📦 {data.get('box_type', '?')} × {data.get('duration_months', '?')} мес\n"
                    f"💰 {data.get('total_price', 0) + data.get('delivery_cost', 0):,} ₽\n"
                    f"🏙 {data.get('city', '?')} · {data.get('address', '?')}",
                    reply_markup=K([("✅ Оплата", f"ap_{uid}"), ("💬 Чат", f"ac_{uid}")]))
            except: pass
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def api_submit_feedback(request):
    """Submit feedback from Mini App"""
    try:
        data = await request.json()
        uid = data.get("user_id")
        cn = sqlite3.connect(DB); c = cn.cursor()
        c.execute("INSERT INTO feedback(user_id,month_num,aroma_name,rating_overall,rating_longevity,rating_sillage,comment,created_at) VALUES(?,?,?,?,?,?,?,?)",
                  (uid, data.get("month", 1), data.get("aroma", ""), data.get("overall", 0),
                   data.get("longevity", 0), data.get("sillage", 0), data.get("comment", ""),
                   datetime.now().isoformat()))
        cn.commit(); cn.close()
        # Notify admin
        global ADMIN_CHAT_ID
        if ADMIN_CHAT_ID:
            try:
                await bot.send_message(ADMIN_CHAT_ID,
                    f"⭐ Отзыв: {data.get('aroma','')} {'⭐'*data.get('overall',0)}\n"
                    f"⏱{data.get('longevity',0)} 💨{data.get('sillage',0)}\n{data.get('comment','')}")
            except: pass
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def api_chat_send(request):
    """Send chat message from Mini App"""
    try:
        data = await request.json()
        uid = data.get("user_id"); text = data.get("text", "")
        if not uid or not text: return web.json_response({"error": "missing data"}, status=400)
        savmsg(int(uid), "client→admin", text)
        global ADMIN_CHAT_ID
        if ADMIN_CHAT_ID:
            try:
                u = getu(int(uid))
                await bot.send_message(ADMIN_CHAT_ID,
                    f"💬 @{u.get('username','?') if u else '?'} (<code>{uid}</code>):\n{text}",
                    reply_markup=K([("💬", f"ac_{uid}")]))
            except: pass
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def api_confirm_payment(request):
    """User confirms payment from Mini App"""
    try:
        data = await request.json()
        uid = data.get("user_id")
        global ADMIN_CHAT_ID
        if ADMIN_CHAT_ID:
            u = getu(int(uid))
            try:
                total = (u.get('total_price', 0) or 0) + (u.get('delivery_cost', 0) or 0)
                await bot.send_message(ADMIN_CHAT_ID,
                    f"💳 <b>Оплата!</b> @{u.get('username','?')} <code>{uid}</code>\n💰 {total:,} ₽",
                    reply_markup=K([("✅ Подтвердить", f"ap_{uid}"), ("💬", f"ac_{uid}")]))
            except: pass
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def start_web_server():
    app = web.Application()
    # Pages
    app.router.add_get("/", handle_index)
    app.router.add_get("/health", handle_health)
    # API for Mini App
    app.router.add_get("/api/user", api_user)
    app.router.add_post("/api/order", api_submit_order)
    app.router.add_post("/api/feedback", api_submit_feedback)
    app.router.add_post("/api/chat", api_chat_send)
    app.router.add_post("/api/payment", api_confirm_payment)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()
    print(f"🌐 Web: {WEBAPP_HOST}:{WEBAPP_PORT}")
    if WEBAPP_URL: print(f"🔗 {WEBAPP_URL}")

# ═══════════════════════════════════════
#     /start — ONLY Mini App
# ═══════════════════════════════════════
@router.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    ref = msg.text.split()[1] if len(msg.text.split()) > 1 else None
    rc = gen_ref(msg.from_user.id)
    data = {"username": msg.from_user.username or "", "first_name": msg.from_user.first_name or "",
            "created_at": datetime.now().isoformat(), "ref_code": rc}
    if ref and ref != rc: data["referred_by"] = ref
    savu(msg.from_user.id, data)

    if WEBAPP_URL:
        try:
            await bot.set_chat_menu_button(chat_id=msg.chat.id,
                menu_button=MenuButtonWebApp(text="DARBOX", web_app=WebAppInfo(url=WEBAPP_URL)))
        except: pass
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Открыть DARBOX", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
        await msg.answer(
            "🖤 <b>DAR PERFUM</b>\n\n"
            "Добро пожаловать в <b>DARBOX</b> —\n"
            "персональную парфюмерную подписку ✨\n\n"
            "Нажмите кнопку ниже:", reply_markup=kb)
    else:
        await msg.answer("🖤 <b>DARBOX</b> загружается...")

# ═══════════════════════════════════════
#           ADMIN: Payment confirm
# ═══════════════════════════════════════
@router.callback_query(F.data.startswith("ap_"))
async def adminpay(cb: CallbackQuery):
    if cb.from_user.username != ADMIN_USERNAME: await cb.answer("⛔"); return
    uid = int(cb.data[3:]); now = datetime.now()
    nd = (now + timedelta(days=30)).strftime("%Y-%m-%d")
    savu(uid, {"status": "paid", "paid_at": now.isoformat(), "next_delivery": nd, "months_received": 0})
    await cb.answer("✅")
    await cb.message.edit_text(cb.message.text + f"\n\n✅ ОПЛАТА OK · {now.strftime('%d.%m.%Y')}")
    try: await bot.send_message(uid, "🎉 <b>Подписка активна!</b>\n\nМы собираем ваш аромабокс 🖤")
    except: pass

# ═══════════════════════════════════════
#           ADMIN: Chat
# ═══════════════════════════════════════
@router.callback_query(F.data.startswith("ac_"))
async def acstart(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.username != ADMIN_USERNAME: await cb.answer("⛔"); return
    uid = int(cb.data[3:]); achat_with[cb.chat.id] = uid; await cb.answer()
    await cb.message.answer(f"💬 Чат с <code>{uid}</code>. /endchat")
    await state.set_state(AChat.chatting)

@router.message(Command("chat"))
async def cchat(msg: Message, state: FSMContext):
    if msg.from_user.username != ADMIN_USERNAME: return
    p = msg.text.split()
    if len(p) < 2: await msg.answer("/chat <code>ID</code>"); return
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
        await bot.send_message(uid, f"💬 <b>DAR Perfum:</b>\n\n{msg.text}")
        savmsg(uid, "admin→client", msg.text); await msg.answer(f"✅ → {uid}")
    except Exception as ex: await msg.answer(f"❌ {ex}")

# ═══════════════════════════════════════
#           ADMIN: Panel
# ═══════════════════════════════════════
@router.message(Command("admin"))
async def cadmin(msg: Message):
    if msg.from_user.username != ADMIN_USERNAME: await msg.answer("⛔"); return
    global ADMIN_CHAT_ID; ADMIN_CHAT_ID = msg.chat.id
    s = get_subs(); paid = [x for x in s if x.get("status") == "paid"]
    await msg.answer(
        f"🔐 <b>Админ DARBOX v5</b>\n\n"
        f"📊 Заявок: {len(s)} · 💳 Оплат: {len(paid)}\n🔔 Уведомления: ВКЛ\n\n"
        f"/subs · /profile ID\n/chat ID · /endchat · /broadcast")

@router.message(Command("subs"))
async def csubs(msg: Message):
    if msg.from_user.username != ADMIN_USERNAME: return
    s = get_subs()
    if not s: await msg.answer("Пусто."); return
    lines = [f"• @{x['username'] or '?'} — {x.get('box_type','?')} {x.get('duration_months','?')}мес ({x.get('status','?')})" for x in s[:30]]
    await msg.answer(f"📋 ({len(s)}):\n\n" + "\n".join(lines))

@router.message(Command("profile"))
async def cprofile(msg: Message):
    if msg.from_user.username != ADMIN_USERNAME: return
    p = msg.text.split()
    if len(p) < 2: await msg.answer("/profile <code>ID</code>"); return
    u = getu(int(p[1]))
    if not u: await msg.answer("?"); return
    await msg.answer(
        f"👤 @{u.get('username','?')} | {u.get('full_name','?')}\n"
        f"📊 {u.get('status','?')} | 💳 {(u.get('paid_at','')or'—')[:10]}\n"
        f"❤️ {u.get('fav_notes','?')}\n🚫 {u.get('disliked_notes','?')}\n"
        f"🎭 {u.get('mood','?')} | 🌍 {u.get('associations','?')}")

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

# Client → Admin forwarding
@router.message(F.text)
async def c2a(msg: Message, state: FSMContext):
    if msg.from_user.username == ADMIN_USERNAME: return
    cs = await state.get_state()
    if cs: return
    savmsg(msg.from_user.id, "client→admin", msg.text)
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        try: await bot.send_message(ADMIN_CHAT_ID,
            f"💬 @{msg.from_user.username or '?'} (<code>{msg.from_user.id}</code>):\n{msg.text}",
            reply_markup=K([("💬", f"ac_{msg.from_user.id}")]))
        except: pass
    await msg.answer("✅ Отправлено! 🖤")

# ═══════════════════════════════════════
#           SCHEDULED TASKS
# ═══════════════════════════════════════
async def check_reminders():
    """Check for upcoming deliveries and send reminders"""
    while True:
        try:
            cn = sqlite3.connect(DB); cn.row_factory = sqlite3.Row; c = cn.cursor()
            target = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            today = datetime.now().strftime("%Y-%m-%d")
            c.execute("SELECT * FROM users WHERE status='paid' AND next_delivery<=? AND next_delivery>?", (target, today))
            users = [dict(r) for r in c.fetchall()]; cn.close()

            for u in users:
                uid = u["user_id"]
                try:
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Отправляем туда же", callback_data=f"addr_ok_{uid}")],
                        [InlineKeyboardButton(text="📍 Изменить адрес", callback_data=f"addr_new_{uid}")]
                    ])
                    await bot.send_message(uid,
                        f"📦 <b>Новый DARBOX скоро!</b>\n\n"
                        f"Доставка: {u.get('next_delivery','?')}\n"
                        f"Адрес: {u.get('city','?')}, {u.get('address','?')}\n\n"
                        f"Всё верно?", reply_markup=kb)
                except: pass
        except: pass
        await asyncio.sleep(86400)  # Check once per day

@router.callback_query(F.data.startswith("addr_ok_"))
async def addr_ok(cb: CallbackQuery):
    await cb.answer("✅")
    await cb.message.edit_text("✅ Адрес подтверждён! Бокс скоро отправим 🖤")
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        u = getu(int(cb.data.replace("addr_ok_", "")))
        try: await bot.send_message(ADMIN_CHAT_ID, f"✅ @{u.get('username','?')} адрес ОК")
        except: pass

@router.callback_query(F.data.startswith("addr_new_"))
async def addr_new(cb: CallbackQuery):
    await cb.answer()
    await cb.message.edit_text("📍 Напишите новый адрес (город, улица, дом, кв):")

# ═══════════════════════════════════════
#           LAUNCH
# ═══════════════════════════════════════
async def main():
    init_db()
    print("🎩 DARBOX v5 Premium!")
    await start_web_server()
    # Start reminder checker in background
    asyncio.create_task(check_reminders())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
