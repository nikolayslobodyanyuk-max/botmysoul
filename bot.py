import logging
import json
import math
import sqlalchemy
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ============= НАСТРОЙКА =============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '8753350871:AAGTNJVb9pb93fMP_Oe7cjRYb2g5wqPJ4jo'
WEBAPP_URL = 'https://nikolayslobodyanuk-max.github.io/botmysoul/webapp/'

# ============= БАЗА ДАННЫХ =============
Base = declarative_base()
engine = create_engine('sqlite:///soulmate.db', connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)

CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
    "Нижний Новгород", "Челябинск", "Самара", "Омск", "Ростов-на-Дону",
    "Уфа", "Красноярск", "Воронеж", "Пермь", "Волгоград",
    "Краснодар", "Саратов", "Тюмень", "Тольятти", "Ижевск",
    "Барнаул", "Ульяновск", "Иркутск", "Хабаровск", "Ярославль",
    "Владивосток", "Махачкала", "Томск", "Оренбург", "Кемерово",
    "Новокузнецк", "Рязань", "Астрахань", "Набережные Челны", "Пенза",
    "Киров", "Липецк", "Чебоксары", "Калининград", "Тула",
    "Курск", "Улан-Удэ", "Ставрополь", "Сочи", "Белгород",
    "Архангельск", "Владимир", "Смоленск", "Чита", "Севастополь"
]

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    interests = Column(String, nullable=True)
    city = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    last_active = Column(DateTime, default=datetime.now)
    
    def get_interests(self):
        if self.interests:
            return json.loads(self.interests)
        return []
    
    def set_interests(self, interests_list):
        self.interests = json.dumps(interests_list)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, nullable=False)
    sender_id = Column(Integer, nullable=False)
    receiver_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True)
    user1_id = Column(Integer, nullable=False)
    user2_id = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.now)
    ended_at = Column(DateTime, nullable=True)
    compatibility = Column(Float, nullable=True)

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    category = Column(String, nullable=True)

QUESTIONS = [
    {"text": "Какая твоя любимая книга и почему?", "category": "interests"},
    {"text": "Что для тебя настоящая любовь?", "category": "love"},
    {"text": "Как выглядит твой идеальный вечер?", "category": "life"},
    {"text": "Какая у тебя любимая цитата?", "category": "life"},
    {"text": "Что ты ценишь в людях больше всего?", "category": "values"},
    {"text": "Какой твой любимый фильм и почему?", "category": "interests"},
    {"text": "Что бы ты делал(а), если бы у тебя был неограниченный бюджет?", "category": "dreams"},
    {"text": "Какое твое любимое место на Земле?", "category": "life"},
    {"text": "Что для тебя счастье?", "category": "love"},
    {"text": "Какую песню ты бы посвятил(а) своей второй половинке?", "category": "love"},
]

def init_db():
    Base.metadata.create_all(engine)
    session = Session()
    if session.query(Question).count() == 0:
        for q in QUESTIONS:
            session.add(Question(text=q['text'], category=q['category']))
        session.commit()
    session.close()

def get_user(user_id):
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    session.close()
    return user

def create_or_update_user(user_id, username, first_name, gender=None, age=None, interests=None, city=None, lat=None, lon=None):
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if user:
        user.username = username
        user.first_name = first_name
        user.last_active = datetime.now()
        if gender: user.gender = gender
        if age: user.age = age
        if interests is not None: user.set_interests(interests)
        if city: user.city = city
        if lat and lon:
            user.latitude = lat
            user.longitude = lon
    else:
        user = User(
            user_id=user_id, username=username, first_name=first_name,
            gender=gender, age=age, city=city,
            interests=json.dumps(interests) if interests else None,
            latitude=lat, longitude=lon
        )
        session.add(user)
    session.commit()
    session.close()
    return user

def save_message(chat_id, sender_id, receiver_id, text):
    session = Session()
    session.add(Message(chat_id=chat_id, sender_id=sender_id, receiver_id=receiver_id, text=text))
    session.commit()
    session.close()

def save_chat(user1_id, user2_id):
    session = Session()
    chat = Chat(user1_id=user1_id, user2_id=user2_id)
    session.add(chat)
    session.commit()
    chat_id = chat.id
    session.close()
    return chat_id

def end_chat(chat_id):
    session = Session()
    chat = session.query(Chat).filter_by(id=chat_id).first()
    if chat:
        chat.ended_at = datetime.now()
        session.commit()
    session.close()

def calculate_compatibility(user1, user2):
    compatibility = 50
    interests1 = user1.get_interests() if user1 else []
    interests2 = user2.get_interests() if user2 else []
    if interests1 and interests2:
        common = len(set(interests1) & set(interests2))
        total = len(set(interests1) | set(interests2))
        if total > 0:
            compatibility += (common / total) * 30
    if user1.age and user2.age:
        age_diff = abs(user1.age - user2.age)
        if age_diff <= 3: compatibility += 20
        elif age_diff <= 5: compatibility += 10
        elif age_diff <= 10: compatibility += 5
    if user1.city and user2.city and user1.city == user2.city:
        compatibility += 10
    return min(100, compatibility)

def calculate_distance(lat1, lon1, lat2, lon2):
    if not lat1 or not lon1 or not lat2 or not lon2:
        return None
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def get_random_question():
    session = Session()
    q = session.query(Question).order_by(sqlalchemy.sql.func.random()).first()
    session.close()
    return q.text if q else "Расскажи что-то о себе:"

# ============= ХРАНИЛИЩЕ =============
chats = {}
waiting = {}

# ============= ОБРАБОТЧИКИ =============
async def start(update, context):
    user = update.effective_user
    db_user = get_user(user.id)
    
    if not db_user or not db_user.city:
        keyboard = [
            [InlineKeyboardButton("📝 Заполнить профиль", web_app=WebAppInfo(url=f"{WEBAPP_URL}register.html"))],
            [InlineKeyboardButton("📍 Отправить геолокацию", callback_data='location')]
        ]
        await update.message.reply_text(
            f"✨ Привет, {user.first_name}!\n\n"
            "💫 Чтобы найти свою родственную душу, нам нужно узнать тебя лучше.\n\n"
            "📝 Нажми «Заполнить профиль» или отправь свою геолокацию.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    keyboard = [
        [InlineKeyboardButton("💖 Найти свою половинку", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("📝 Вопросы для знакомства", callback_data='questions')],
        [InlineKeyboardButton("👤 Мой профиль", callback_data='profile')],
        [InlineKeyboardButton("❌ Закончить диалог", callback_data='stop')]
    ]
    await update.message.reply_text(
        f"✨ С возвращением, {user.first_name}!\n📍 Твой город: {db_user.city or 'Не указан'}\n\n💫 Готов найти свою родственную душу?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def location_handler(update, context):
    user = update.effective_user
    location = update.message.location
    if location:
        db_user = get_user(user.id)
        if db_user:
            db_user.latitude = location.latitude
            db_user.longitude = location.longitude
            db_user.last_active = datetime.now()
            session = Session()
            session.commit()
            session.close()
        await update.message.reply_text(
            "📍 Отлично! Теперь мы знаем твоё местоположение.\nТеперь заполни остальную информацию в профиле.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Заполнить профиль", web_app=WebAppInfo(url=f"{WEBAPP_URL}register.html"))]
            ])
        )

async def questions_handler(update, context):
    query = update.callback_query
    await query.answer()
    question = get_random_question()
    keyboard = [
        [InlineKeyboardButton("💬 Следующий вопрос", callback_data='questions')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back')]
    ]
    await query.edit_message_text(
        f"💭 Вопрос дня:\n\n{question}\n\nЗадай этот вопрос своему собеседнику!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def profile_handler(update, context):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    if not user:
        await query.edit_message_text("👤 Профиль не найден.")
        return
    interests = user.get_interests()
    keyboard = [
        [InlineKeyboardButton("✏️ Редактировать профиль", web_app=WebAppInfo(url=f"{WEBAPP_URL}register.html"))],
        [InlineKeyboardButton("📍 Обновить геолокацию", callback_data='location')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back')]
    ]
    await query.edit_message_text(
        f"👤 Твой профиль:\n\n📛 Имя: {user.first_name}\n⚤ Пол: {user.gender or 'Не указан'}\n📅 Возраст: {user.age or 'Не указан'}\n📍 Город: {user.city or 'Не указан'}\n🎯 Интересы: {', '.join(interests) if interests else 'Не указаны'}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def webapp_data(update, context):
    try:
        user_id = update.effective_user.id
        data = json.loads(update.message.web_app_data.data)
        action = data.get('action')
        
        if action == 'register':
            create_or_update_user(
                user_id, update.effective_user.username, update.effective_user.first_name,
                gender=data.get('gender'), age=int(data.get('age')) if data.get('age') else None,
                interests=data.get('interests', []), city=data.get('city')
            )
            await context.bot.send_message(user_id, json.dumps({'action': 'registered', 'text': '✅ Профиль сохранён!'}))
            
        elif action == 'find':
            user = get_user(user_id)
            if not user or not user.gender or not user.age or not user.city:
                await context.bot.send_message(user_id, json.dumps({'action': 'error', 'text': '📝 Сначала заполни профиль!'}))
                return
            
            partner = None
            for w in waiting:
                if w != user_id:
                    p = get_user(w)
                    if p and p.city and (not user.city or p.city == user.city or p.city in CITIES):
                        partner = p
                        break
            
            if partner is None:
                if user_id not in waiting:
                    waiting[user_id] = {'started_at': datetime.now()}
                await context.bot.send_message(user_id, json.dumps({'action': 'waiting', 'text': '✨ Ищем твою родственную душу...'}))
            else:
                chat_id = save_chat(user_id, partner.user_id)
                chats[user_id] = {'partner': partner.user_id, 'chat_id': chat_id}
                chats[partner.user_id] = {'partner': user_id, 'chat_id': chat_id}
                if user_id in waiting: del waiting[user_id]
                if partner.user_id in waiting: del waiting[partner.user_id]
                
                compatibility = calculate_compatibility(user, partner)
                city_info = f"\n📍 Вы из одного города — {user.city}! 🌟" if user.city and partner.city and user.city == partner.city else ""
                dist_info = ""
                if user.latitude and partner.latitude:
                    dist = calculate_distance(user.latitude, user.longitude, partner.latitude, partner.longitude)
                    if dist: dist_info = f"\n📏 Расстояние: ~{int(dist)} км"
                
                msg = f'💞 Ты нашёл(а) свою родственную душу! Совместимость: {compatibility}%{city_info}{dist_info}'
                await context.bot.send_message(user_id, json.dumps({'action': 'chat_started', 'compatibility': compatibility, 'message': msg}))
                await context.bot.send_message(partner.user_id, json.dumps({'action': 'chat_started', 'compatibility': compatibility, 'message': msg}))
                
        elif action == 'stop':
            if user_id in waiting:
                del waiting[user_id]
                await context.bot.send_message(user_id, json.dumps({'action': 'chat_ended', 'text': '🌅 Поиск отменён.'}))
            elif user_id in chats:
                partner_id = chats[user_id]['partner']
                end_chat(chats[user_id]['chat_id'])
                del chats[user_id]
                if partner_id in chats: del chats[partner_id]
                await context.bot.send_message(user_id, json.dumps({'action': 'chat_ended', 'text': '💔 Разговор завершён.'}))
                await context.bot.send_message(partner_id, json.dumps({'action': 'partner_left', 'text': '💫 Собеседник завершил диалог.'}))
                
        elif action == 'message':
            if user_id in chats:
                partner_id = chats[user_id]['partner']
                save_message(chats[user_id]['chat_id'], user_id, partner_id, data.get('text'))
                await context.bot.send_message(partner_id, json.dumps({'action': 'new_message', 'text': data.get('text')}))
                
        elif action == 'next':
            if user_id in chats:
                partner_id = chats[user_id]['partner']
                end_chat(chats[user_id]['chat_id'])
                del chats[user_id]
                if partner_id in chats: del chats[partner_id]
                await context.bot.send_message(partner_id, json.dumps({'action': 'partner_left', 'text': '🌊 Собеседник ищет нового.'}))
            
            user = get_user(user_id)
            partner = None
            for w in waiting:
                if w != user_id:
                    p = get_user(w)
                    if p and p.city:
                        partner = p
                        break
            
            if partner is None:
                if user_id not in waiting:
                    waiting[user_id] = {'started_at': datetime.now()}
                await context.bot.send_message(user_id, json.dumps({'action': 'waiting', 'text': '✨ Ищем новую родственную душу...'}))
            else:
                chat_id = save_chat(user_id, partner.user_id)
                chats[user_id] = {'partner': partner.user_id, 'chat_id': chat_id}
                chats[partner.user_id] = {'partner': user_id, 'chat_id': chat_id}
                if user_id in waiting: del waiting[user_id]
                if partner.user_id in waiting: del waiting[partner.user_id]
                compatibility = calculate_compatibility(user, partner)
                city_info = f"\n📍 {user.city} ↔ {partner.city}" if user.city and partner.city else ""
                await context.bot.send_message(user_id, json.dumps({'action': 'chat_started', 'compatibility': compatibility, 'message': f'💞 Новая встреча! Совместимость: {compatibility}%{city_info}'}))
                await context.bot.send_message(partner.user_id, json.dumps({'action': 'chat_started', 'compatibility': compatibility, 'message': f'💞 Новая встреча! Совместимость: {compatibility}%{city_info}'}))
                
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await context.bot.send_message(user_id, json.dumps({'action': 'error', 'text': '❌ Попробуй ещё раз.'}))

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == 'questions':
        await questions_handler(update, context)
    elif query.data == 'profile':
        await profile_handler(update, context)
    elif query.data == 'location':
        keyboard = ReplyKeyboardMarkup([[KeyboardButton("📍 Отправить геолокацию", request_location=True)]], resize_keyboard=True, one_time_keyboard=True)
        await query.message.reply_text("📍 Нажми кнопку, чтобы отправить своё местоположение:", reply_markup=keyboard)
    elif query.data == 'back':
        await start(update, context)
    elif query.data == 'stop':
        await webapp_data(update, context)

async def handle_message(update, context):
    user_id = update.effective_user.id
    if user_id in chats:
        partner_id = chats[user_id]['partner']
        save_message(chats[user_id]['chat_id'], user_id, partner_id, update.message.text)
        await context.bot.send_message(partner_id, f"💬 {update.message.text}")
        await update.message.reply_text("💌 Отправлено")
    else:
        await update.message.reply_text("ℹ️ Вы не в чате. Используйте /start")

async def stop_command(update, context):
    user_id = update.effective_user.id
    if user_id in waiting:
        del waiting[user_id]
        await update.message.reply_text("🌅 Поиск отменён.")
    elif user_id in chats:
        partner_id = chats[user_id]['partner']
        end_chat(chats[user_id]['chat_id'])
        del chats[user_id]
        if partner_id in chats: del chats[partner_id]
        await update.message.reply_text("💔 Диалог завершён.")
        await context.bot.send_message(partner_id, "👋 Собеседник завершил диалог.")
    else:
        await update.message.reply_text("ℹ️ Вы не в диалоге.")

# ============= ЗАПУСК =============
def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    
    print("💖 Бот для поиска родственной души запущен!")
    print("📱 @yourrandomsoulmatebot")
    app.run_polling()

if __name__ == '__main__':
    main()
