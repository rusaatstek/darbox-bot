"""
🎁 DARBOX v3 — Telegram-бот подписки на аромабоксы
DAR Perfum | @dararomabox_bot
"""
import asyncio, sqlite3, json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# ═══════════════ CONFIG ═══════════════
BOT_TOKEN = "8054022324:AAHK2bUZ1lLEDk8FREDbAEl5En040OtEHg0"
ADMIN_USERNAME = "nasomato"
ADMIN_CHAT_ID = None
CONTACT = "@darperf"
PAYMENT_INFO = (
    "💳 <b>Реквизиты для оплаты:</b>\n\n"
    "📱 По номеру телефона:\n"
    "<code>+7 963 991 80 48</code>\n"
    "(Сбербанк / Тинькофф / Альфабанк)\n\n"
    "После перевода нажмите «✅ Я оплатил»."
)
DEL_COST = {"post": 280, "cdek": 280, "courier": 350}
BOXES = {
    "8x3": {"name":"8 ароматов × 3 мл","short":"8×3мл","price":1980,"count":8,"vol":"3 мл","em":"🧪","desc":"Максимум открытий — попробуйте 8 направлений"},
    "6x6": {"name":"6 ароматов × 6 мл","short":"6×6мл","price":2380,"count":6,"vol":"6 мл","em":"🧴","desc":"Золотая середина — хватит на 2-3 недели каждого"},
    "5x10": {"name":"5 ароматов × 10 мл","short":"5×10мл","price":3580,"count":5,"vol":"10 мл","em":"✨","desc":"Полноценный флакон каждого аромата"},
}
DURS = {2:{"d":0,"l":"2 месяца","b":""},4:{"d":5,"l":"4 месяца","b":" (−5%)"},6:{"d":10,"l":"6 месяцев","b":" (−10%) 🔥"}}
def cprice(bk,m):
    base=BOXES[bk]["price"];disc=DURS[m]["d"];mo=round(base*(100-disc)/100);return mo,mo*m
T = 20 # total questions
DIV = "━━━━━━━━━━━━━━━━━━━━"
div = "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"
def pbar(c,t,l=14):
    f=round(l*c/t);return f"{'█'*f}{'░'*(l-f)}  {c}/{t}"
def hdr(n,title,em=""):
    return f"{em} <b>{title}</b>\n\n{pbar(n,T)}"

# ═══════════════ DB ═══════════════
DB = "darbox.db"
def init_db():
    cn=sqlite3.connect(DB);c=cn.cursor()
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
        status TEXT DEFAULT 'new', paid_at TEXT, next_delivery TEXT, months_received INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, month_num INTEGER, aroma_name TEXT, rating INTEGER, comment TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, direction TEXT, text TEXT, created_at TEXT
    )""")
    cn.commit();cn.close()

def savu(uid,data):
    cn=sqlite3.connect(DB);c=cn.cursor()
    fs=list(data.keys());ph=",".join(fs);vp=",".join(["?"]*len(fs));up=",".join([f"{f}=excluded.{f}" for f in fs])
    c.execute(f"INSERT INTO users(user_id,{ph}) VALUES(?,{vp}) ON CONFLICT(user_id) DO UPDATE SET {up}",[uid]+[data[f] for f in fs])
    cn.commit();cn.close()

def getu(uid):
    cn=sqlite3.connect(DB);cn.row_factory=sqlite3.Row;c=cn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?",(uid,));r=c.fetchone();cn.close()
    return dict(r) if r else None

def get_subs():
    cn=sqlite3.connect(DB);cn.row_factory=sqlite3.Row;c=cn.cursor()
    c.execute("SELECT * FROM users WHERE box_type IS NOT NULL ORDER BY created_at DESC")
    rs=c.fetchall();cn.close();return[dict(r) for r in rs]

def get_due_reminders(days_ahead=3):
    """Get users whose next_delivery is within N days"""
    cn=sqlite3.connect(DB);cn.row_factory=sqlite3.Row;c=cn.cursor()
    target=(datetime.now()+timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    c.execute("SELECT * FROM users WHERE status='paid' AND next_delivery<=? AND next_delivery>?",(target,datetime.now().strftime("%Y-%m-%d")))
    rs=c.fetchall();cn.close();return[dict(r) for r in rs]

def savfb(uid,mo,ar,ra,co):
    cn=sqlite3.connect(DB);c=cn.cursor()
    c.execute("INSERT INTO feedback(user_id,month_num,aroma_name,rating,comment,created_at) VALUES(?,?,?,?,?,?)",(uid,mo,ar,ra,co,datetime.now().isoformat()))
    cn.commit();cn.close()

def getfb(uid):
    cn=sqlite3.connect(DB);cn.row_factory=sqlite3.Row;c=cn.cursor()
    c.execute("SELECT * FROM feedback WHERE user_id=? ORDER BY month_num,id",(uid,));rs=c.fetchall();cn.close()
    return[dict(r) for r in rs]

def savmsg(uid,d,t):
    cn=sqlite3.connect(DB);c=cn.cursor()
    c.execute("INSERT INTO messages(user_id,direction,text,created_at) VALUES(?,?,?,?)",(uid,d,t,datetime.now().isoformat()))
    cn.commit();cn.close()

# ═══════════════ STATES ═══════════════
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
    month=State();aroma=State();rating=State();comment=State();more=State()
class Bcast(StatesGroup):
    text=State()
class AChat(StatesGroup):
    chatting=State()
class Confirm(StatesGroup):
    address=State()

def K(btns,rw=2):
    rows=[];row=[]
    for t,cb in btns:
        row.append(InlineKeyboardButton(text=t,callback_data=cb))
        if len(row)>=rw:rows.append(row);row=[]
    if row:rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

achat_with={}
bot=Bot(token=BOT_TOKEN,default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp=Dispatcher(storage=MemoryStorage());router=Router();dp.include_router(router)

# ═══════════════ /start ═══════════════
@router.message(Command("start"))
async def cmd_start(msg:Message,state:FSMContext):
    await state.clear()
    savu(msg.from_user.id,{"username":msg.from_user.username or "","first_name":msg.from_user.first_name or "","created_at":datetime.now().isoformat()})
    await msg.answer(f"""
{DIV}
          🖤  <b>DAR PERFUM</b>
     Парфюмерная Лаборатория
{DIV}

🎁 <b>DARBOX — аромабокс по подписке</b>

Каждый месяц — новый набор ароматов,
собранный специально для вас ✨

┊ 🧪  8 × 3 мл  —  <b>1 980 ₽</b>/мес
┊ 🧴  6 × 6 мл  —  <b>2 380 ₽</b>/мес
┊ ✨  5 × 10 мл —  <b>3 580 ₽</b>/мес

🔥 4 мес → −5%  ·  6 мес → −10%

{div}
<i>Пройдите анкету — мы составим
ваш ольфакторный портрет и подберём
ароматы, которые станут вашими</i>
{DIV}""",reply_markup=K([
        ("🌸 Пройти анкету","sq"),("📋 Мои подписки","mysub"),
        ("💬 Оставить отзыв","fbs"),("✉️ Написать нам","cmsg"),
    ],1))

# ═══════════════ QUESTIONNAIRE ═══════════════
@router.callback_query(F.data=="sq")
async def sq(cb:CallbackQuery,state:FSMContext):
    await cb.answer()
    await cb.message.answer(
        f"🌿 <b>Парфюмерная анкета</b>\n\n"
        f"20 вопросов · 3-5 минут\n\n"
        f"Мы составим ваш <b>ольфакторный портрет</b> —\n"
        f"уникальную карту парфюмерных предпочтений.\n\n"
        f"<i>Каждый ответ приближает вас к идеальному аромату</i> ✨"
    )
    await asyncio.sleep(0.8)
    await cb.message.answer(hdr(1,"Для кого подбираем?","👤")+"\n\n<i>Определим базовое направление</i>",
        reply_markup=K([("🙋‍♂️ Для себя (М)","g_m"),("🙋‍♀️ Для себя (Ж)","g_f"),("🎁 В подарок","g_gift")],2))
    await state.set_state(Q.gender)

# Q1 Gender
@router.callback_query(Q.gender,F.data.startswith("g_"))
async def q1(cb:CallbackQuery,state:FSMContext):
    v={"g_m":"Мужчина","g_f":"Женщина","g_gift":"В подарок"}[cb.data]
    await state.update_data(gender=v);await cb.answer(f"✓ {v}")
    if cb.data=="g_gift":
        await cb.message.edit_text(hdr(1,"Кому дарим?","🎁")+"\n\n<i>Это определит стиль ароматов в боксе</i>",
            reply_markup=K([("🙋‍♂️ Мужчине","gf_m"),("🙋‍♀️ Женщине","gf_f")]))
        await state.set_state(Q.gift_gender);return
    await state.update_data(gift_gender="—")
    await _q2(cb,state)

@router.callback_query(Q.gift_gender,F.data.startswith("gf_"))
async def q1b(cb:CallbackQuery,state:FSMContext):
    v={"gf_m":"Мужчине","gf_f":"Женщине"}[cb.data]
    await state.update_data(gift_gender=v);await cb.answer(f"✓ {v}")
    await _q2(cb,state)

# Q2 Age
async def _q2(cb,state):
    await cb.message.edit_text(hdr(2,"Возраст","📅")+"\n\n<i>Помогает подобрать стилистику</i>",
        reply_markup=K([("18-24","a1"),("25-34","a2"),("35-44","a3"),("45+","a4")]))
    await state.set_state(Q.age)

@router.callback_query(Q.age,F.data.startswith("a"))
async def q2(cb:CallbackQuery,state:FSMContext):
    v={"a1":"18-24","a2":"25-34","a3":"35-44","a4":"45+"}[cb.data]
    await state.update_data(age=v);await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(3,"Образ жизни","🏃")+"\n\n<i>Ваш ритм → характер аромата</i>",
        reply_markup=K([("💼 Деловой","l1"),("🎨 Творческий","l2"),("🏋️ Активный","l3"),("🌙 Размеренный","l4")],1))
    await state.set_state(Q.lifestyle)

# Q3
@router.callback_query(Q.lifestyle,F.data.startswith("l"))
async def q3(cb:CallbackQuery,state:FSMContext):
    v={"l1":"Деловой","l2":"Творческий","l3":"Активный","l4":"Размеренный"}[cb.data]
    await state.update_data(lifestyle=v);await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(4,"Где носите ароматы?","🎭")+"\n\n<i>Разные ситуации — разные ароматы</i>",
        reply_markup=K([("📆 Каждый день","o1"),("🌃 На выход","o2"),("🏢 На работу","o3"),("🔀 По-разному","o4")],1))
    await state.set_state(Q.occasions)

# Q4
@router.callback_query(Q.occasions,F.data.startswith("o"))
async def q4(cb:CallbackQuery,state:FSMContext):
    v={"o1":"Каждый день","o2":"На выход","o3":"На работу","o4":"По-разному"}[cb.data]
    await state.update_data(occasions=v);await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(5,"Интенсивность","💨")+"\n\n<i>Насколько «громким» должен быть?</i>",
        reply_markup=K([("🌬 Шёпот — близко к коже","i1"),("☁️ Разговор — для себя","i2"),("🔥 Заявление — мощный шлейф","i3"),("🎲 По настроению","i4")],1))
    await state.set_state(Q.intensity)

# Q5
@router.callback_query(Q.intensity,F.data.startswith("i"))
async def q5(cb:CallbackQuery,state:FSMContext):
    v={"i1":"Лёгкие","i2":"Умеренные","i3":"Мощные","i4":"По настроению"}[cb.data]
    await state.update_data(intensity=v);await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(6,"Парфюмерный опыт","🎓")+"\n\n<i>Влияет на сложность ароматов</i>",
        reply_markup=K([("🌱 Новичок","e1"),("🌿 Любитель","e2"),("🌳 Энтузиаст","e3"),("👑 Гуру","e4")],1))
    await state.set_state(Q.experience)

# Q6
@router.callback_query(Q.experience,F.data.startswith("e"))
async def q6(cb:CallbackQuery,state:FSMContext):
    v={"e1":"Новичок","e2":"Любитель","e3":"Энтузиаст","e4":"Гуру"}[cb.data]
    await state.update_data(experience=v);await cb.answer(f"✓ {v}")
    await state.update_data(_fav=[])
    await cb.message.edit_text(hdr(7,"Любимые ноты ❤️","🌸")+"\n\n<i>Выберите всё, что нравится\nНажмите «Готово» когда закончите</i>",
        reply_markup=_nkb("f",[]))
    await state.set_state(Q.fav_notes)

# Extended note map
NM={
    "citrus":"🍋 Цитрусовые","floral":"🌹 Цветочные","woody":"🌳 Древесные",
    "sweet":"🍦 Ванильные/сладкие","fresh":"🌊 Свежие/морские","spicy":"🌶 Пряные/восточные",
    "leather":"🧥 Кожаные","tobacco":"🚬 Табачные/дымные","coffee":"☕ Кофейные",
    "fruit":"🍑 Фруктовые","gourmand":"🍫 Гурманские/шоколадные","musk":"🤍 Мускусные/чистые",
    "oud":"🕌 Удовые","amber":"🐳 Амбровые","herbal":"🌿 Травяные/зелёные",
    "powder":"💄 Пудровые","aqua":"💧 Акватические","boozy":"🥃 Алкогольные/бальзамические",
}

def _nkb(pf,sel):
    btns=[]
    for k,lb in NM.items():
        ch=" ✓" if lb in sel else ""
        btns.append((f"{lb}{ch}",f"{pf}_{k}"))
    if sel:btns.append((f"✅ Готово ({len(sel)})",f"{pf}_done"))
    else:btns.append(("⏭ Пропустить",f"{pf}_done"))
    return K(btns,2)

# Q7 fav notes
@router.callback_query(Q.fav_notes,F.data.startswith("f_"))
async def q7(cb:CallbackQuery,state:FSMContext):
    d=await state.get_data();fav=d.get("_fav",[])
    k=cb.data[2:]
    if k=="done":
        await state.update_data(fav_notes=", ".join(fav) if fav else "Не выбрано",_dis=[])
        await cb.answer()
        await cb.message.edit_text(hdr(8,"Нелюбимые ноты 🚫","❌")+"\n\n<i>Что НЕ должно быть в боксе?</i>",reply_markup=_nkb("d",[]))
        await state.set_state(Q.disliked_notes);return
    lb=NM.get(k,k)
    if lb in fav:fav.remove(lb)
    else:fav.append(lb)
    await state.update_data(_fav=fav);await cb.answer(f"{'✓' if lb in fav else '✗'} {lb}")
    await cb.message.edit_reply_markup(reply_markup=_nkb("f",fav))

# Q8 disliked
@router.callback_query(Q.disliked_notes,F.data.startswith("d_"))
async def q8(cb:CallbackQuery,state:FSMContext):
    d=await state.get_data();dis=d.get("_dis",[])
    k=cb.data[2:]
    if k=="done":
        await state.update_data(disliked_notes=", ".join(dis) if dis else "Нет")
        await cb.answer()
        await cb.message.edit_text(hdr(9,"Ваши ароматы","👃")+"\n\n<i>Напишите что носите сейчас или нравилось раньше.\nЭто ключ к пониманию вашего вкуса.</i>\n\n<code>Sauvage, Baccarat Rouge 540, Lost Cherry</code>\n\nИли напишите «нет».")
        await state.set_state(Q.current_perfumes);return
    lb=NM.get(k,k)
    if lb in dis:dis.remove(lb)
    else:dis.append(lb)
    await state.update_data(_dis=dis);await cb.answer(f"{'✓' if lb in dis else '✗'} {lb}")
    await cb.message.edit_reply_markup(reply_markup=_nkb("d",dis))

# Q9
@router.message(Q.current_perfumes)
async def q9(msg:Message,state:FSMContext):
    await state.update_data(current_perfumes=msg.text.strip())
    await msg.answer(hdr(10,"Любимый сезон","🌤")+"\n\n<i>Когда чувствуете себя в своей стихии?</i>",
        reply_markup=K([("🌸 Весна","s1"),("☀️ Лето","s2"),("🍂 Осень","s3"),("❄️ Зима","s4"),("🔄 Все","s5")],2))
    await state.set_state(Q.season_pref)

# Q10
@router.callback_query(Q.season_pref,F.data.startswith("s"))
async def q10(cb:CallbackQuery,state:FSMContext):
    v={"s1":"Весна","s2":"Лето","s3":"Осень","s4":"Зима","s5":"Все"}[cb.data]
    await state.update_data(season_pref=v);await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(11,"Время суток","🕐")+"\n\n<i>Когда вам важнее пахнуть?</i>",
        reply_markup=K([("🌅 День","t1"),("🌙 Вечер","t2"),("🔄 Универсально","t3")],1))
    await state.set_state(Q.time_of_day)

# Q11
@router.callback_query(Q.time_of_day,F.data.startswith("t"))
async def q11(cb:CallbackQuery,state:FSMContext):
    v={"t1":"День","t2":"Вечер","t3":"Универсально"}[cb.data]
    await state.update_data(time_of_day=v);await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(12,"Настроение аромата","🎭")+"\n\n<i>Какую эмоцию хотите излучать?</i>",
        reply_markup=K([("❤️ Романтика","m1"),("💪 Уверенность","m2"),("🧘 Спокойствие","m3"),("⚡ Энергия","m4"),("🔮 Загадочность","m5"),("😏 Соблазн","m6")],2))
    await state.set_state(Q.mood)

# Q12
@router.callback_query(Q.mood,F.data.startswith("m"))
async def q12(cb:CallbackQuery,state:FSMContext):
    v={"m1":"Романтика","m2":"Уверенность","m3":"Спокойствие","m4":"Энергия","m5":"Загадочность","m6":"Соблазн"}[cb.data]
    await state.update_data(mood=v);await cb.answer(f"✓ {v}")
    await cb.message.edit_text(
        hdr(13,"Ассоциации","🌍")+"\n\n<i>Закройте глаза...\nГде вы чувствуете себя счастливым?</i>",
        reply_markup=K([
            ("🌲 Лес после дождя","z1"),("🌊 Морской берег","z2"),
            ("🏙 Ночной мегаполис","z3"),("🕌 Восточный базар","z4"),
            ("🍰 Кондитерская","z5"),("🏔 Горный воздух","z6"),
            ("📚 Старая библиотека","z7"),("🌾 Цветущий луг","z8"),
            ("🏖 Тропический остров","z9"),("🪵 Камин в шале","z10"),
            ("☕ Утро в кофейне","z11"),("🌃 Крыша небоскрёба","z12"),
        ],2))
    await state.set_state(Q.associations)

# Q13
ASSOC={"z1":"Лес после дождя","z2":"Морской берег","z3":"Ночной мегаполис","z4":"Восточный базар","z5":"Кондитерская","z6":"Горный воздух","z7":"Старая библиотека","z8":"Цветущий луг","z9":"Тропический остров","z10":"Камин в шале","z11":"Утро в кофейне","z12":"Крыша небоскрёба"}

@router.callback_query(Q.associations,F.data.startswith("z"))
async def q13(cb:CallbackQuery,state:FSMContext):
    v=ASSOC.get(cb.data,"?")
    await state.update_data(associations=v);await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(14,"Желаемая стойкость","⏱")+"\n\n<i>Сколько должен держаться?</i>",
        reply_markup=K([("🕐 2-4ч — лёгкий намёк","r1"),("🕕 6-8ч — рабочий день","r2"),("🕛 12+ч — с утра до ночи","r3")],1))
    await state.set_state(Q.longevity)

# Q14
@router.callback_query(Q.longevity,F.data.startswith("r"))
async def q14(cb:CallbackQuery,state:FSMContext):
    v={"r1":"2-4ч","r2":"6-8ч","r3":"12+ч"}[cb.data]
    await state.update_data(longevity=v);await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(15,"Эксперименты","🚀")+"\n\n<i>Готовы к неожиданным открытиям?</i>",
        reply_markup=K([("🚀 Удивляйте!","x1"),("😌 Классику","x2"),("⚖️ 50/50","x3")],1))
    await state.set_state(Q.discovery)

# Q15
@router.callback_query(Q.discovery,F.data.startswith("x"))
async def q15(cb:CallbackQuery,state:FSMContext):
    v={"x1":"Эксперименты","x2":"Классика","x3":"50/50"}[cb.data]
    await state.update_data(discovery=v);await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(16,"Ценовой сегмент","💎")+"\n\n<i>Какой уровень ароматов ближе?</i>",
        reply_markup=K([("🛒 Масс (Zara, H&M)","b1"),("⭐ Средний (Boss, Versace)","b2"),("💫 Ниша (Byredo, Le Labo)","b3"),("👑 Люкс (Tom Ford, Creed)","b4"),("🎲 Все","b5")],1))
    await state.set_state(Q.budget)

# Q16
@router.callback_query(Q.budget,F.data.startswith("b"))
async def q16(cb:CallbackQuery,state:FSMContext):
    v={"b1":"Масс","b2":"Средний","b3":"Ниша","b4":"Люкс","b5":"Все"}[cb.data]
    await state.update_data(budget=v);await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(17,"Гардероб","👔")+"\n\n<i>Стиль одежды подсказывает стиль аромата</i>",
        reply_markup=K([("👕 Casual","w1"),("👔 Классика","w2"),("🧢 Street","w3"),("👗 Элегантный","w4"),("🎨 Эклектика","w5")],2))
    await state.set_state(Q.wardrobe)

# Q17
@router.callback_query(Q.wardrobe,F.data.startswith("w"))
async def q17(cb:CallbackQuery,state:FSMContext):
    v={"w1":"Casual","w2":"Классика","w3":"Street","w4":"Элегантный","w5":"Эклектика"}[cb.data]
    await state.update_data(wardrobe=v);await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(18,"Аллергии","⚠️")+"\n\n<i>Есть ли аллергия на компоненты?\nНапишите или нажмите «Нет».</i>",
        reply_markup=K([("✅ Нет","al0")]))
    await state.set_state(Q.allergies)

# Q18
@router.callback_query(Q.allergies,F.data=="al0")
async def q18a(cb:CallbackQuery,state:FSMContext):
    await state.update_data(allergies="Нет");await cb.answer();await _q19(cb.message,state)
@router.message(Q.allergies)
async def q18b(msg:Message,state:FSMContext):
    await state.update_data(allergies=msg.text.strip());await _q19(msg,state)

async def _q19(msg,state):
    await msg.answer(hdr(19,"Цель подписки","🎯")+"\n\n<i>Зачем вам DARBOX?</i>",
        reply_markup=K([("🔍 Найти свой аромат","g1"),("🌍 Попробовать новое","g2"),("📚 Коллекция","g3"),("🎁 Подарок","g4")],1))
    await state.set_state(Q.goal)

# Q19
@router.callback_query(Q.goal,F.data.startswith("g"))
async def q19(cb:CallbackQuery,state:FSMContext):
    v={"g1":"Найти свой","g2":"Попробовать новое","g3":"Коллекция","g4":"Подарок"}[cb.data]
    await state.update_data(goal=v);await cb.answer(f"✓ {v}")
    await cb.message.edit_text(hdr(20,"Пожелания","💬")+"\n\n<i>Любые мысли, мечты об аромате.\nИли «Пропустить».</i>",
        reply_markup=K([("⏭ Пропустить","ew0")]))
    await state.set_state(Q.extra_wishes)

# Q20
@router.callback_query(Q.extra_wishes,F.data=="ew0")
async def q20a(cb:CallbackQuery,state:FSMContext):
    await state.update_data(extra_wishes="—");await cb.answer();await _box(cb.message,state)
@router.message(Q.extra_wishes)
async def q20b(msg:Message,state:FSMContext):
    await state.update_data(extra_wishes=msg.text.strip());await _box(msg,state)

# ═══════════════ BOX CHOICE ═══════════════
async def _box(msg,state):
    txt=f"🎉 <b>Анкета завершена!</b>\n\n{pbar(T,T)}\n\nТеперь выберите формат DARBOX:\n\n"
    for bk,b in BOXES.items():
        txt+=f"{b['em']} <b>{b['name']}</b>\n<i>{b['desc']}</i>\n<b>{b['price']:,} ₽</b>/мес\n\n"
    await msg.answer(txt,reply_markup=K([
        ("🧪 8×3мл — 1 980₽","bx_8x3"),("🧴 6×6мл — 2 380₽","bx_6x6"),("✨ 5×10мл — 3 580₽","bx_5x10")],1))
    await state.set_state(Q.box_type)

@router.callback_query(Q.box_type,F.data.startswith("bx_"))
async def pickbox(cb:CallbackQuery,state:FSMContext):
    bk=cb.data[3:];await state.update_data(box_type=bk);await cb.answer()
    bx=BOXES[bk];lines=[]
    for m,du in DURS.items():
        mo,tot=cprice(bk,m);lines.append(f"▸ <b>{du['l']}{du['b']}</b>\n   {mo:,} ₽/мес → итого <b>{tot:,} ₽</b>")
    await cb.message.edit_text(f"⏳ <b>Срок подписки</b>\n\nФормат: {bx['em']} {bx['name']}\n\n"+"\n\n".join(lines),
        reply_markup=K([("2 месяца","du2"),("4 мес (−5%)","du4"),("6 мес (−10%) 🔥","du6")],1))
    await state.set_state(Q.duration)

@router.callback_query(Q.duration,F.data.startswith("du"))
async def pickdur(cb:CallbackQuery,state:FSMContext):
    m=int(cb.data[2:]);d=await state.get_data();mo,tot=cprice(d["box_type"],m)
    await state.update_data(duration_months=m,monthly_price=mo,total_price=tot);await cb.answer()
    await cb.message.edit_text(
        "🚚 <b>Способ доставки</b>\n\n<i>Выберите удобный вариант:</i>",
        reply_markup=K([
            ("📦 Почта России — 280 ₽","dl_post"),
            ("🚚 СДЭК — 280 ₽","dl_cdek"),
            ("🏍 Курьер по Москве — 350 ₽","dl_courier"),
        ],1))
    await state.set_state(Q.delivery_type)

# ═══════════════ DELIVERY ═══════════════
@router.callback_query(Q.delivery_type,F.data.startswith("dl_"))
async def pickdel(cb:CallbackQuery,state:FSMContext):
    dt=cb.data[3:];dc=DEL_COST[dt]
    nm={"post":"Почта России","cdek":"СДЭК","courier":"Курьер по Москве"}[dt]
    await state.update_data(delivery_type=dt,delivery_cost=dc);await cb.answer(f"✓ {nm} +{dc}₽")
    await cb.message.edit_text("👤 <b>ФИО получателя</b>\n\nНапишите полное имя:")
    await state.set_state(Q.full_name)

@router.message(Q.full_name)
async def getname(msg:Message,state:FSMContext):
    await state.update_data(full_name=msg.text.strip())
    await msg.answer("📱 <b>Телефон</b>\n\nНомер для связи:");await state.set_state(Q.phone)

@router.message(Q.phone)
async def getphone(msg:Message,state:FSMContext):
    await state.update_data(phone=msg.text.strip())
    d=await state.get_data();dt=d.get("delivery_type","post")
    await msg.answer("🏙 <b>Город</b>\n\nВ какой город доставить?");await state.set_state(Q.city)

@router.message(Q.city)
async def getcity(msg:Message,state:FSMContext):
    await state.update_data(city=msg.text.strip())
    d=await state.get_data();dt=d.get("delivery_type","post")
    if dt=="courier":
        await msg.answer("🏠 <b>Адрес</b> (внутри МКАД)\n\n<i>Улица, дом, квартира</i>");await state.set_state(Q.address)
    elif dt=="cdek":
        await msg.answer("📍 <b>Адрес отделения СДЭК</b>\n\n<i>Улица и номер отделения</i>");await state.set_state(Q.address)
    else:
        await msg.answer("🏠 <b>Адрес</b>\n\n<i>Улица, дом, квартира</i>");await state.set_state(Q.address)

@router.message(Q.address)
async def getaddr(msg:Message,state:FSMContext):
    await state.update_data(address=msg.text.strip())
    d=await state.get_data()
    if d.get("delivery_type")=="post":
        await msg.answer("📮 <b>Индекс</b>\n\nПочтовый индекс:");await state.set_state(Q.postal_code)
    else:
        await state.update_data(postal_code="—");await _summary(msg,state)

@router.message(Q.postal_code)
async def getzip(msg:Message,state:FSMContext):
    await state.update_data(postal_code=msg.text.strip());await _summary(msg,state)

# ═══════════════ SUMMARY ═══════════════
async def _summary(msg,state):
    d=await state.get_data();bx=BOXES[d["box_type"]];du=DURS[d["duration_months"]]
    mo,tot=cprice(d["box_type"],d["duration_months"])
    dc=d.get("delivery_cost",0);grand=tot+dc
    dln={"post":"📦 Почта России","cdek":"🚚 СДЭК","courier":"🏍 Курьер"}[d.get("delivery_type","post")]

    txt=f"""{DIV}
📋 <b>ВАША ЗАЯВКА</b>
{DIV}

<b>Ольфакторный портрет:</b>
┊ 👤 {d.get('gender','—')} {('→ '+d.get('gift_gender','')) if d.get('gender')=='В подарок' else ''}· {d.get('age','—')}
┊ 🏃 {d.get('lifestyle','—')} · {d.get('occasions','—')}
┊ 💨 {d.get('intensity','—')} · 🎓 {d.get('experience','—')}
┊ ❤️ {d.get('fav_notes','—')}
┊ 🚫 {d.get('disliked_notes','—')}
┊ 👃 {d.get('current_perfumes','—')}
┊ 🌤 {d.get('season_pref','—')} · 🕐 {d.get('time_of_day','—')}
┊ 🎭 {d.get('mood','—')} · 🌍 {d.get('associations','—')}
┊ ⏱ {d.get('longevity','—')} · 🚀 {d.get('discovery','—')}
┊ 💎 {d.get('budget','—')} · 👔 {d.get('wardrobe','—')}
┊ ⚠️ {d.get('allergies','—')} · 🎯 {d.get('goal','—')}
┊ 💬 {d.get('extra_wishes','—')}

{div}
<b>Подписка:</b>
┊ {bx['em']} {bx['name']}
┊ ⏳ {du['l']}{du['b']}
┊ 💰 {mo:,} ₽/мес × {d['duration_months']} = <b>{tot:,} ₽</b>

<b>Доставка:</b>
┊ {dln} — {dc} ₽
┊ 👤 {d.get('full_name','—')} · 📱 {d.get('phone','—')}
┊ 🏙 {d.get('city','—')} · 🏠 {d.get('address','—')}
{('┊ 📮 '+d.get('postal_code','')) if d.get('postal_code','—')!='—' else ''}

{div}
<b>💳 ИТОГО: {grand:,} ₽</b>
<i>(подписка {tot:,} + доставка {dc})</i>
{DIV}"""
    await msg.answer(txt+"\n\n<b>Всё верно?</b>",reply_markup=K([("✅ Подтвердить","cf1"),("✏️ Заново","cf0")],1))
    await state.set_state(Q.confirm)

# ═══════════════ CONFIRM & PAY ═══════════════
@router.callback_query(Q.confirm,F.data=="cf1")
async def cfyes(cb:CallbackQuery,state:FSMContext):
    d=await state.get_data();await cb.answer("✅")
    savu(cb.from_user.id,{
        "username":cb.from_user.username or "","first_name":cb.from_user.first_name or "",
        **{k:d.get(k,"") for k in ["gender","gift_gender","age","lifestyle","occasions","intensity","experience",
        "fav_notes","disliked_notes","current_perfumes","season_pref","time_of_day","mood","associations",
        "longevity","discovery","budget","wardrobe","allergies","goal","extra_wishes",
        "box_type","full_name","phone","city","address","postal_code","delivery_type"]},
        "duration_months":d.get("duration_months",0),"monthly_price":d.get("monthly_price",0),
        "total_price":d.get("total_price",0),"delivery_cost":d.get("delivery_cost",0),"status":"pending",
    })
    bx=BOXES[d["box_type"]];mo,tot=cprice(d["box_type"],d["duration_months"])
    dc=d.get("delivery_cost",0);grand=tot+dc

    await cb.message.edit_text(f"🎉 <b>Заявка оформлена!</b>\n\nМы свяжемся с вами для оплаты.\n💬 {CONTACT} — если есть вопросы\n\nСпасибо за <b>DARBOX</b>! 🖤")
    await asyncio.sleep(1)
    await cb.message.answer(f"💰 <b>Оплата</b>\n\nСумма: <b>{grand:,} ₽</b>\n({tot:,} подписка + {dc} доставка)\n\n{PAYMENT_INFO}",
        reply_markup=K([("✅ Я оплатил(а)","pd"),("💬 Написать нам","cmsg")],1))

    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(ADMIN_CHAT_ID,
                f"🆕 <b>ЗАЯВКА DARBOX</b>\n\n👤 @{cb.from_user.username or '?'}\n🆔 <code>{cb.from_user.id}</code>\n\n"
                f"📦 {bx['name']} × {d['duration_months']}мес\n💰 {grand:,}₽ ({tot:,}+{dc})\n\n"
                f"❤️ {d.get('fav_notes','—')}\n🚫 {d.get('disliked_notes','—')}\n👃 {d.get('current_perfumes','—')}\n"
                f"🎭 {d.get('mood','—')} · 🌍 {d.get('associations','—')}\n🎓 {d.get('experience','—')} · 💎 {d.get('budget','—')}\n"
                f"📱 {d.get('phone','—')}\n🏙 {d.get('city','—')} · 🏠 {d.get('address','—')}",
                reply_markup=K([(f"💬 Написать","ac_{cb.from_user.id}"),(f"✅ Оплата OK","ap_{cb.from_user.id}"),(f"👤 Профиль","apr_{cb.from_user.id}")]))
        except:pass
    await state.clear()

@router.callback_query(Q.confirm,F.data=="cf0")
async def cfno(cb:CallbackQuery,state:FSMContext):
    await state.clear();await cb.answer();await cb.message.edit_text("🔄 Заново...");await cmd_start(cb.message,state)

# Payment done
@router.callback_query(F.data=="pd")
async def paydone(cb:CallbackQuery):
    await cb.answer("✅")
    await cb.message.edit_text("⏳ <b>Проверяем оплату...</b>\n\nОбычно до 30 мин. Напишем! 🖤",reply_markup=K([("💬 Написать","cmsg")]))
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        u=getu(cb.from_user.id)
        try:await bot.send_message(ADMIN_CHAT_ID,f"💳 <b>Оплата!</b> @{cb.from_user.username or '?'} <code>{cb.from_user.id}</code>\n💰 {u.get('total_price',0)+u.get('delivery_cost',0):,}₽",
            reply_markup=K([(f"✅ Подтвердить","ap_{cb.from_user.id}"),(f"💬 Написать","ac_{cb.from_user.id}")]))
        except:pass

@router.callback_query(F.data.startswith("ap_"))
async def adminpay(cb:CallbackQuery):
    if cb.from_user.username!=ADMIN_USERNAME:await cb.answer("⛔");return
    uid=int(cb.data[3:]);now=datetime.now()
    next_del=(now+timedelta(days=30)).strftime("%Y-%m-%d")
    savu(uid,{"status":"paid","paid_at":now.isoformat(),"next_delivery":next_del,"months_received":0})
    await cb.answer("✅");await cb.message.edit_text(cb.message.text+"\n\n✅ <b>ОПЛАТА OK</b>\n📅 Дата: "+now.strftime("%d.%m.%Y"))
    try:await bot.send_message(uid,"🎉 <b>Оплата подтверждена!</b>\n\nВаша подписка активна!\nМы начнём собирать ваш аромабокс 🖤\n\n💬 Пишите если что!",reply_markup=K([("💬 Написать","cmsg")]))
    except:pass

# ═══════════════ CHAT ═══════════════
@router.callback_query(F.data=="cmsg")
async def cmsg(cb:CallbackQuery):
    await cb.answer();await cb.message.answer("💬 Напишите — мы ответим!")

@router.callback_query(F.data.startswith("ac_"))
async def acstart(cb:CallbackQuery,state:FSMContext):
    if cb.from_user.username!=ADMIN_USERNAME:await cb.answer("⛔");return
    uid=int(cb.data[3:]);achat_with[cb.chat.id]=uid;u=getu(uid);await cb.answer()
    await cb.message.answer(f"💬 Чат с @{u.get('username','?')} (<code>{uid}</code>)\n/endchat — выход")
    await state.set_state(AChat.chatting)

@router.message(Command("chat"))
async def cchat(msg:Message,state:FSMContext):
    if msg.from_user.username!=ADMIN_USERNAME:return
    p=msg.text.split()
    if len(p)<2:await msg.answer("/chat <code>ID</code>");return
    uid=int(p[1]);achat_with[msg.chat.id]=uid
    await msg.answer(f"💬 Чат с <code>{uid}</code>. /endchat — выход");await state.set_state(AChat.chatting)

@router.message(Command("endchat"))
async def echat(msg:Message,state:FSMContext):
    achat_with.pop(msg.chat.id,None);await state.clear();await msg.answer("✅ Чат завершён.")

@router.message(AChat.chatting)
async def asend(msg:Message,state:FSMContext):
    uid=achat_with.get(msg.chat.id)
    if not uid:await state.clear();return
    try:
        await bot.send_message(uid,f"💬 <b>DAR Perfum:</b>\n\n{msg.text}",reply_markup=K([("💬 Ответить","cmsg")]))
        savmsg(uid,"admin→client",msg.text);await msg.answer(f"✅ → {uid}")
    except Exception as ex:await msg.answer(f"❌ {ex}")

# ═══════════════ MY SUB ═══════════════
@router.callback_query(F.data=="mysub")
async def mysub(cb:CallbackQuery):
    await cb.answer();u=getu(cb.from_user.id)
    if not u or not u.get("box_type"):await cb.message.answer("Нет подписок. /start 🌸");return
    bx=BOXES.get(u["box_type"],{})
    await cb.message.answer(f"📋 <b>Подписка:</b>\n\n{bx.get('em','')} {bx.get('name','?')}\n⏳ {u.get('duration_months','?')} мес\n💰 {u.get('monthly_price',0):,} ₽/мес\n📊 {u.get('status','new')}\n📅 След.доставка: {u.get('next_delivery','—')}")

# ═══════════════ FEEDBACK ═══════════════
@router.callback_query(F.data=="fbs")
async def fbs(cb:CallbackQuery,state:FSMContext):
    await cb.answer();await state.clear()
    await cb.message.answer("💬 <b>Отзыв</b>\n\nКакой месяц?",reply_markup=K([(f"{i}-й","fb_{i}") for i in range(1,7)]))
    await state.set_state(Fb.month)

@router.message(Command("feedback"))
async def fbcmd(msg:Message,state:FSMContext):
    await state.clear()
    await msg.answer("💬 <b>Отзыв</b>\n\nКакой месяц?",reply_markup=K([(f"{i}-й","fb_{i}") for i in range(1,7)]))
    await state.set_state(Fb.month)

@router.callback_query(Fb.month,F.data.startswith("fb_"))
async def fbm(cb:CallbackQuery,state:FSMContext):
    m=int(cb.data[3:]);await state.update_data(fm=m);await cb.answer()
    await cb.message.edit_text(f"📝 Месяц {m} — название аромата:");await state.set_state(Fb.aroma)

@router.message(Fb.aroma)
async def fba(msg:Message,state:FSMContext):
    await state.update_data(fa=msg.text.strip())
    await msg.answer(f"⭐ «{msg.text.strip()}»:",reply_markup=K([("😍","fr5"),("👍","fr4"),("😐","fr3"),("👎","fr2"),("🤢","fr1")],5))
    await state.set_state(Fb.rating)

@router.callback_query(Fb.rating,F.data.startswith("fr"))
async def fbr(cb:CallbackQuery,state:FSMContext):
    r=int(cb.data[2:]);await state.update_data(fr=r);await cb.answer()
    await cb.message.edit_text("💬 Комментарий?",reply_markup=K([("⏭ Пропустить","fcs")]))
    await state.set_state(Fb.comment)

@router.callback_query(Fb.comment,F.data=="fcs")
async def fcs(cb:CallbackQuery,state:FSMContext):
    await state.update_data(fc="—");await cb.answer();await _fbs(cb.message,state,cb.from_user.id)
@router.message(Fb.comment)
async def fct(msg:Message,state:FSMContext):
    await state.update_data(fc=msg.text.strip());await _fbs(msg,state,msg.from_user.id)

async def _fbs(msg,state,uid):
    d=await state.get_data();savfb(uid,d["fm"],d["fa"],d["fr"],d["fc"])
    await msg.answer(f"✅ {d['fa']} — {'⭐'*d['fr']}\n\nЕщё?",reply_markup=K([("🧴 Да","fby"),("✅ Всё","fbn")]))
    await state.set_state(Fb.more)
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        try:await bot.send_message(ADMIN_CHAT_ID,f"💬 Отзыв {uid}: {d['fa']} {'⭐'*d['fr']}\n{d['fc']}")
        except:pass

@router.callback_query(Fb.more,F.data=="fby")
async def fby(cb:CallbackQuery,state:FSMContext):
    d=await state.get_data();await cb.answer();await cb.message.edit_text(f"📝 Месяц {d['fm']} — аромат:");await state.set_state(Fb.aroma)
@router.callback_query(Fb.more,F.data=="fbn")
async def fbn(cb:CallbackQuery,state:FSMContext):
    await cb.answer();await state.clear();await cb.message.edit_text("🙏 Спасибо! Учтём 🖤\n/start — меню")

# ═══════════════ ADDRESS CONFIRM ═══════════════
@router.callback_query(F.data.startswith("addr_same_"))
async def addr_same(cb:CallbackQuery):
    uid=int(cb.data.replace("addr_same_",""))
    await cb.answer("✅");await cb.message.edit_text("✅ Адрес подтверждён! Ваш бокс скоро будет отправлен 🖤")
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        u=getu(uid)
        try:await bot.send_message(ADMIN_CHAT_ID,f"✅ @{u.get('username','?')} подтвердил адрес (без изменений)\n🏠 {u.get('city','?')}, {u.get('address','?')}")
        except:pass

@router.callback_query(F.data.startswith("addr_new_"))
async def addr_new(cb:CallbackQuery,state:FSMContext):
    uid=int(cb.data.replace("addr_new_",""));await cb.answer()
    await cb.message.edit_text("🏠 <b>Новый адрес</b>\n\nНапишите город, улицу, дом, квартиру:")
    await state.update_data(confirm_uid=uid);await state.set_state(Confirm.address)

@router.message(Confirm.address)
async def new_addr(msg:Message,state:FSMContext):
    d=await state.get_data();uid=d.get("confirm_uid",msg.from_user.id)
    savu(uid,{"address":msg.text.strip()})
    await msg.answer("✅ Адрес обновлён! Бокс будет отправлен по новому адресу 🖤")
    await state.clear()
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        try:await bot.send_message(ADMIN_CHAT_ID,f"📍 @{msg.from_user.username or '?'} изменил адрес:\n🏠 {msg.text.strip()}")
        except:pass

# ═══════════════ ADMIN ═══════════════
@router.message(Command("admin"))
async def cadmin(msg:Message):
    if msg.from_user.username!=ADMIN_USERNAME:await msg.answer("⛔");return
    global ADMIN_CHAT_ID;ADMIN_CHAT_ID=msg.chat.id
    s=get_subs();paid=[x for x in s if x.get("status")=="paid"]
    await msg.answer(f"🔐 <b>Админ DARBOX</b>\n\n📊 Заявок: {len(s)}\n💳 Оплачено: {len(paid)}\n🔔 Уведомления: ВКЛ\n\n"
        "/subs — список\n/profile ID\n/reviews ID\n/chat ID · /endchat\n/broadcast — рассылка\n/remind — отправить напоминания о доставке\n/due — кому отправлять на этой неделе")

@router.message(Command("subs"))
async def csubs(msg:Message):
    if msg.from_user.username!=ADMIN_USERNAME:return
    s=get_subs()
    if not s:await msg.answer("Пусто.");return
    lines=[f"• @{x['username'] or '?'} — {BOXES.get(x['box_type'],{}).get('short','?')} {x['duration_months']}мес ({x['status']}) {'💳'+x.get('paid_at','')[:10] if x.get('paid_at') else ''}" for x in s[:30]]
    await msg.answer(f"📋 <b>Подписчики ({len(s)}):</b>\n\n"+"\n".join(lines))

@router.message(Command("due"))
async def cdue(msg:Message):
    if msg.from_user.username!=ADMIN_USERNAME:return
    due=get_due_reminders(7)
    if not due:await msg.answer("На этой неделе отправок нет.");return
    lines=[f"• @{x['username'] or '?'} — {x.get('city','?')}, {x.get('address','?')}\n  📅 {x.get('next_delivery','?')} · {BOXES.get(x['box_type'],{}).get('short','?')}" for x in due]
    await msg.answer(f"📦 <b>Отправить на этой неделе ({len(due)}):</b>\n\n"+"\n\n".join(lines))

@router.message(Command("remind"))
async def cremind(msg:Message):
    if msg.from_user.username!=ADMIN_USERNAME:return
    due=get_due_reminders(3);sent=0
    for u in due:
        try:
            await bot.send_message(u["user_id"],
                f"📦 <b>Ваш DARBOX скоро будет отправлен!</b>\n\n"
                f"Текущий адрес доставки:\n🏙 {u.get('city','?')}\n🏠 {u.get('address','?')}\n\n"
                f"Всё верно?",
                reply_markup=K([
                    (f"✅ Да, всё ок","addr_same_{u['user_id']}"),
                    (f"📍 Изменить адрес","addr_new_{u['user_id']}"),
                ],1))
            sent+=1
        except:pass
        await asyncio.sleep(0.1)
    await msg.answer(f"✅ Напоминания: {sent}/{len(due)}")

@router.message(Command("profile"))
async def cprofile(msg:Message):
    if msg.from_user.username!=ADMIN_USERNAME:return
    p=msg.text.split()
    if len(p)<2:await msg.answer("/profile <code>ID</code>");return
    u=getu(int(p[1]))
    if not u:await msg.answer("?");return
    await msg.answer(
        f"👤 @{u.get('username','?')} | {u.get('full_name','?')}\n📱 {u.get('phone','?')} | 📊 {u.get('status','?')}\n"
        f"💳 Оплата: {u.get('paid_at','—')[:10] if u.get('paid_at') else '—'}\n📅 След: {u.get('next_delivery','—')}\n\n"
        f"Пол: {u.get('gender','?')}{' → '+u.get('gift_gender','') if u.get('gender')=='В подарок' else ''}\nВозраст: {u.get('age','?')}\n"
        f"Стиль: {u.get('lifestyle','?')} | Повод: {u.get('occasions','?')}\nИнтенс: {u.get('intensity','?')} | Опыт: {u.get('experience','?')}\n"
        f"❤️ {u.get('fav_notes','?')}\n🚫 {u.get('disliked_notes','?')}\n👃 {u.get('current_perfumes','?')}\n"
        f"Сезон: {u.get('season_pref','?')} | Время: {u.get('time_of_day','?')}\n"
        f"Настроение: {u.get('mood','?')} | Ассоц: {u.get('associations','?')}\n"
        f"Стойкость: {u.get('longevity','?')} | Открытия: {u.get('discovery','?')}\n"
        f"Бюджет: {u.get('budget','?')} | Гардероб: {u.get('wardrobe','?')}\n"
        f"Аллергии: {u.get('allergies','?')} | Цель: {u.get('goal','?')}\n💬 {u.get('extra_wishes','?')}\n\n"
        f"🏙 {u.get('city','?')} | 🏠 {u.get('address','?')} | 📮 {u.get('postal_code','?')}")

@router.callback_query(F.data.startswith("apr_"))
async def aqp(cb:CallbackQuery):
    if cb.from_user.username!=ADMIN_USERNAME:await cb.answer("⛔");return
    uid=int(cb.data[4:]);u=getu(uid);await cb.answer()
    if u:await cb.message.answer(f"👤 @{u.get('username','?')}\n❤️ {u.get('fav_notes','?')}\n🚫 {u.get('disliked_notes','?')}\n🎭 {u.get('mood','?')} · 🌍 {u.get('associations','?')}")

@router.message(Command("reviews"))
async def creviews(msg:Message):
    if msg.from_user.username!=ADMIN_USERNAME:return
    p=msg.text.split()
    if len(p)<2:await msg.answer("/reviews <code>ID</code>");return
    fs=getfb(int(p[1]))
    if not fs:await msg.answer("Нет отзывов.");return
    lines=[f"М{f['month_num']} | {f['aroma_name']} {'⭐'*f['rating']}\n   {f['comment']}" for f in fs]
    await msg.answer("💬 <b>Отзывы:</b>\n\n"+"\n\n".join(lines))

@router.message(Command("broadcast"))
async def cbcast(msg:Message,state:FSMContext):
    if msg.from_user.username!=ADMIN_USERNAME:return
    await msg.answer("📢 Текст:");await state.set_state(Bcast.text)

@router.message(Bcast.text)
async def dobcast(msg:Message,state:FSMContext):
    if msg.from_user.username!=ADMIN_USERNAME:return
    s=get_subs();sent=0
    for x in s:
        try:await bot.send_message(x["user_id"],msg.text);sent+=1
        except:pass
        await asyncio.sleep(0.1)
    await msg.answer(f"✅ {sent}/{len(s)}");await state.clear()

# ═══════════════ CLIENT → ADMIN ═══════════════
@router.message(F.text)
async def c2a(msg:Message,state:FSMContext):
    if msg.from_user.username==ADMIN_USERNAME:return
    cs=await state.get_state()
    if cs and (cs.startswith("Q:") or cs.startswith("Fb:") or cs.startswith("Confirm:")):return
    savmsg(msg.from_user.id,"client→admin",msg.text)
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        try:await bot.send_message(ADMIN_CHAT_ID,f"💬 @{msg.from_user.username or '?'} (<code>{msg.from_user.id}</code>):\n\n{msg.text}",
            reply_markup=K([(f"💬 Ответить","ac_{msg.from_user.id}"),(f"👤 Профиль","apr_{msg.from_user.id}")]))
        except:pass
    await msg.answer("✅ Отправлено! 🖤")

# ═══════════════ LAUNCH ═══════════════
async def main():
    init_db();print("🚀 DARBOX v3!");await dp.start_polling(bot)
if __name__=="__main__":asyncio.run(main())
