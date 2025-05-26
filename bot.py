#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import threading

from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext,
    CommandHandler,
    Dispatcher
)

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تحميل المتغيرات من .env
load_dotenv()

# المتغيرات الأساسية
TOKEN = os.getenv('TELEGRAM_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID'))
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID'))
PORT = int(os.environ.get('PORT', 8080))
APP_URL = os.getenv('APP_URL')  # مثال: https://your-app-name.onrender.com

# إعداد Flask
app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot is active.'

# مسار Webhook لاستقبال التحديثات من Telegram
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), updater.bot)
    dispatcher.process_update(update)
    return 'OK'

# مسار المستخدمين المحظورين
BLOCKED_USERS_FILE = 'blocked_users.txt'

def load_blocked_users():
    if not os.path.exists(BLOCKED_USERS_FILE):
        return set()
    with open(BLOCKED_USERS_FILE, 'r') as f:
        return set(int(line.strip()) for line in f if line.strip().isdigit())

def save_blocked_users(users):
    with open(BLOCKED_USERS_FILE, 'w') as f:
        for uid in users:
            f.write(str(uid) + '\n')

blocked_users = load_blocked_users()

# رسالة ترحيب عند /start
def start_command(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.id == OWNER_ID:
        return
    update.message.reply_text("مرحبًا بك! أرسل رسالتك أو أي نوع من الوسائط، وسأقوم بإرسالها إلى المجموعة.")

# رسائل المشرف
def handle_owner_message(update: Update, context: CallbackContext):
    message = update.message
    chat_id = GROUP_CHAT_ID

    if message.text:
        context.bot.send_message(chat_id=chat_id, text=message.text)
    elif message.photo:
        context.bot.send_photo(chat_id=chat_id, photo=message.photo[-1].file_id, caption=message.caption or '')
    elif message.video:
        context.bot.send_video(chat_id=chat_id, video=message.video.file_id, caption=message.caption or '')
    elif message.document:
        context.bot.send_document(chat_id=chat_id, document=message.document.file_id, caption=message.caption or '')
    elif message.audio:
        context.bot.send_audio(chat_id=chat_id, audio=message.audio.file_id, caption=message.caption or '')
    elif message.voice:
        context.bot.send_voice(chat_id=chat_id, voice=message.voice.file_id, caption=message.caption or '')
    elif message.sticker:
        context.bot.send_sticker(chat_id=chat_id, sticker=message.sticker.file_id)
    else:
        update.message.reply_text("نوع الوسائط غير مدعوم.")
        return

    update.message.reply_text("تم إرسال الرسالة/الوسائط إلى المجموعة.")

# رسائل المستخدمين العاديين
def handle_user_message(update: Update, context: CallbackContext):
    user = update.effective_user
    message = update.message

    if user.id == OWNER_ID or user.id in blocked_users:
        return

    caption = message.caption or ''
    user_info = f"رسالة من المستخدم #{user.id}:\n{caption}"

    # إرسال إلى المجموعة بدلاً من المشرف
    if message.text:
        context.bot.send_message(chat_id=GROUP_CHAT_ID, text=user_info + f"\n{message.text}")
    elif message.photo:
        context.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=message.photo[-1].file_id, caption=user_info)
    elif message.video:
        context.bot.send_video(chat_id=GROUP_CHAT_ID, video=message.video.file_id, caption=user_info)
    elif message.document:
        context.bot.send_document(chat_id=GROUP_CHAT_ID, document=message.document.file_id, caption=user_info)
    elif message.audio:
        context.bot.send_audio(chat_id=GROUP_CHAT_ID, audio=message.audio.file_id, caption=user_info)
    elif message.voice:
        context.bot.send_voice(chat_id=GROUP_CHAT_ID, voice=message.voice.file_id, caption=user_info)
    elif message.sticker:
        context.bot.send_sticker(chat_id=GROUP_CHAT_ID, sticker=message.sticker.file_id)
        context.bot.send_message(chat_id=GROUP_CHAT_ID, text=user_info)
    else:
        update.message.reply_text("نوع الوسائط غير مدعوم.")
        return

    # تأكيد للمستخدم
    update.message.reply_text("✅ تم إرسال رسالتك/الوسائط إلى المجموعة. شكرًا لتواصلك.")

# رد المشرف على مستخدم
def reply_command(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        return

    args = context.args
    if len(args) < 2:
        update.message.reply_text("الاستخدام: /reply <user_id> <message>")
        return

    try:
        user_id = int(args[0])
        message = ' '.join(args[1:])
        context.bot.send_message(chat_id=user_id, text=message)
        update.message.reply_text("تم إرسال الرد.")
    except Exception as e:
        update.message.reply_text(f"حدث خطأ: {e}")

# حظر مستخدم
def block_command(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        return

    args = context.args
    if len(args) != 1:
        update.message.reply_text("الاستخدام: /block <user_id>")
        return

    try:
        user_id = int(args[0])
        blocked_users.add(user_id)
        save_blocked_users(blocked_users)
        update.message.reply_text("تم الحظر.")
    except Exception as e:
        update.message.reply_text(f"حدث خطأ: {e}")

# إلغاء الحظر
def unblock_command(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        return

    args = context.args
    if len(args) != 1:
        update.message.reply_text("الاستخدام: /unblock <user_id>")
        return

    try:
        user_id = int(args[0])
        blocked_users.discard(user_id)
        save_blocked_users(blocked_users)
        update.message.reply_text("تم إلغاء الحظر.")
    except Exception as e:
        update.message.reply_text(f"حدث خطأ: {e}")

# تشغيل Flask
def run_flask():
    app.run(host='0.0.0.0', port=PORT)

def main():
    global updater, dispatcher
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # أوامر المشرف
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("reply", reply_command))
    dispatcher.add_handler(CommandHandler("block", block_command))
    dispatcher.add_handler(CommandHandler("unblock", unblock_command))

    # رسائل المشرف
    dispatcher.add_handler(MessageHandler(
        (Filters.text | Filters.photo | Filters.video | Filters.document | Filters.audio | Filters.voice | Filters.sticker) 
        & Filters.private & Filters.user(user_id=OWNER_ID),
        handle_owner_message
    ))

    # رسائل المستخدمين
    dispatcher.add_handler(MessageHandler(
        (Filters.text | Filters.photo | Filters.video | Filters.document | Filters.audio | Filters.voice | Filters.sticker) 
        & Filters.private,
        handle_user_message
    ))

    # إيقاف أي Webhook سابق
    updater.bot.delete_webhook()

    # إعداد Webhook
    updater.bot.set_webhook(f'{APP_URL}/{TOKEN}')

    # تشغيل Flask في الخلفية
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    logger.info("Bot started with webhook.")

if __name__ == '__main__':
    main()
