import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '8753350871:AAGTNJVb9pb93fMP_Oe7cjRYb2g5wqPJ4jo'
WEBAPP_URL = 'https://nikolayslobodyanyuk-max.github.io/botmysoul/webapp/'

# Хранилище
waiting = []
chats = {}

async def start(update, context):
    keyboard = [[
        InlineKeyboardButton("📱 Открыть приложение", web_app=WebAppInfo(url=WEBAPP_URL))
    ]]
    await update.message.reply_text(
        "👋 Привет! Это бот для знакомств.\n\n"
        "🤝 Анонимное общение без фото и личных данных.\n"
        "Нажми кнопку, чтобы открыть приложение:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def webapp_data(update, context):
    try:
        user_id = update.effective_user.id
        data = json.loads(update.message.web_app_data.data)
        action = data.get('action')
        
        logger.info(f"Действие от {user_id}: {action}")
        
        if action == 'find':
            partner = None
            for w in waiting:
                if w != user_id:
                    partner = w
                    break
            
            if partner is None:
                if user_id not in waiting:
                    waiting.append(user_id)
                await context.bot.send_message(user_id, json.dumps({'action': 'waiting', 'text': 'Ищем собеседника...'}))
            else:
                chats[user_id] = partner
                chats[partner] = user_id
                if user_id in waiting: waiting.remove(user_id)
                if partner in waiting: waiting.remove(partner)
                await context.bot.send_message(user_id, json.dumps({'action': 'chat_started'}))
                await context.bot.send_message(partner, json.dumps({'action': 'chat_started'}))
                
        elif action == 'stop':
            if user_id in waiting:
                waiting.remove(user_id)
                await context.bot.send_message(user_id, json.dumps({'action': 'chat_ended'}))
            elif user_id in chats:
                partner = chats[user_id]
                del chats[user_id]
                if partner in chats: del chats[partner]
                await context.bot.send_message(user_id, json.dumps({'action': 'chat_ended'}))
                await context.bot.send_message(partner, json.dumps({'action': 'partner_left'}))
                
        elif action == 'message':
            if user_id in chats:
                partner = chats[user_id]
                await context.bot.send_message(partner, json.dumps({'action': 'new_message', 'text': data.get('text')}))
                
        elif action == 'next':
            if user_id in chats:
                partner = chats[user_id]
                del chats[user_id]
                if partner in chats: del chats[partner]
                await context.bot.send_message(partner, json.dumps({'action': 'partner_left'}))
            
            new_partner = None
            for w in waiting:
                if w != user_id:
                    new_partner = w
                    break
            
            if new_partner is None:
                if user_id not in waiting:
                    waiting.append(user_id)
                await context.bot.send_message(user_id, json.dumps({'action': 'waiting', 'text': 'Ищем нового собеседника...'}))
            else:
                chats[user_id] = new_partner
                chats[new_partner] = user_id
                if user_id in waiting: waiting.remove(user_id)
                if new_partner in waiting: waiting.remove(new_partner)
                await context.bot.send_message(user_id, json.dumps({'action': 'chat_started'}))
                await context.bot.send_message(new_partner, json.dumps({'action': 'chat_started'}))
                
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await context.bot.send_message(user_id, json.dumps({'action': 'error', 'text': str(e)}))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data))
    
    print("✅ Бот запущен!")
    print(f"🌐 WebApp URL: {WEBAPP_URL}")
    print("📱 Откройте Telegram и найдите @Gmbls_bot")
    app.run_polling()

if __name__ == '__main__':
    main()
