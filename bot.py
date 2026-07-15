import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '8753350871:AAGTNJVb9pb93fMP_Oe7cjRYb2g5wqPJ4jo'
WEBAPP_URL = 'https://nikolayslobodyanuk-max.github.io/botmysoul/webapp/'

# Хранилище
waiting = []
chats = {}

async def start(update, context):
    keyboard = [[
        InlineKeyboardButton("💖 Найти свою половинку", web_app=WebAppInfo(url=WEBAPP_URL))
    ]]
    await update.message.reply_text(
        "✨ Привет, искатель родственной души!\n\n"
        "💫 Ты чувствуешь, что где-то есть человек, который поймёт тебя с полуслова?\n"
        "🌟 Тот, с кем можно разделить радость и грусть, мечты и мысли?\n\n"
        "🌙 Мы поможем тебе найти ЕГО или ЕЁ.\n"
        "Нажми на кнопку ниже и открой своё сердце для встречи:\n\n"
        "💝 Каждое знакомство — это шаг к судьбе.",
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
                await context.bot.send_message(user_id, json.dumps({'action': 'waiting', 'text': '✨ Ищем твою родственную душу...'}))
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
                await context.bot.send_message(user_id, json.dumps({'action': 'chat_ended', 'text': '🌅 Поиск отменён. Возможно, судьба ждёт тебя в другой раз.'}))
            elif user_id in chats:
                partner = chats[user_id]
                del chats[user_id]
                if partner in chats: del chats[partner]
                await context.bot.send_message(user_id, json.dumps({'action': 'chat_ended', 'text': '💔 Разговор завершён. Но может быть, вы встретитесь снова?'}))
                await context.bot.send_message(partner, json.dumps({'action': 'partner_left', 'text': '💫 Твой собеседник завершил диалог. Значит, это был не твой человек. Продолжай искать!'}))
                
        elif action == 'message':
            if user_id in chats:
                partner = chats[user_id]
                await context.bot.send_message(partner, json.dumps({'action': 'new_message', 'text': data.get('text')}))
                
        elif action == 'next':
            if user_id in chats:
                partner = chats[user_id]
                del chats[user_id]
                if partner in chats: del chats[partner]
                await context.bot.send_message(partner, json.dumps({'action': 'partner_left', 'text': '🌊 Твой собеседник продолжает поиск. Возможно, ваши пути пересекутся снова.'}))
            
            new_partner = None
            for w in waiting:
                if w != user_id:
                    new_partner = w
                    break
            
            if new_partner is None:
                if user_id not in waiting:
                    waiting.append(user_id)
                await context.bot.send_message(user_id, json.dumps({'action': 'waiting', 'text': '✨ Ищем новую родственную душу...'}))
            else:
                chats[user_id] = new_partner
                chats[new_partner] = user_id
                if user_id in waiting: waiting.remove(user_id)
                if new_partner in waiting: waiting.remove(new_partner)
                await context.bot.send_message(user_id, json.dumps({'action': 'chat_started'}))
                await context.bot.send_message(new_partner, json.dumps({'action': 'chat_started'}))
                
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await context.bot.send_message(user_id, json.dumps({'action': 'error', 'text': '❌ Что-то пошло не так. Просто попробуй ещё раз.'}))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data))
    
    print("💖 Бот для поиска родственной души запущен!")
    print(f"🌐 WebApp URL: {WEBAPP_URL}")
    print("📱 Откройте Telegram и найдите @Gmbls_bot")
    print("✨ Пусть судьба найдёт тебя!")
    app.run_polling()

if __name__ == '__main__':
    main()
