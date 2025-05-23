#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import threading

from flask import Flask
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext,
    CommandHandler
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

# إعداد Flask
app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot is active.'

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

def handle_owner_message(update: Update, context: CallbackContext):
    user = update.effective_user
    text = update.message.text

    if user.id != OWNER_ID:
        update.message.reply_text("هذا البوت خاص.")
        logger.warning(f"Unauthorized user tried to send: {user.id}")
        return

    if text:
        context.bot.send_message(chat_id=GROUP_CHAT_ID, text=text)
        update.message.reply_text("تم إرسال الرسالة إلى المجموعة.")

def handle_user_message(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.id == OWNER_ID:
        return  # Admin messages handled elsewhere

    if user.id in blocked_users:
        return

    msg = update.message.text or ''
    context.bot.send_message(
        chat_id=OWNER_ID,
        text=f"رسالة من المستخدم #{user.id}:\n{msg}"
    )

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

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # أوامر المسؤول
    dispatcher.add_handler(CommandHandler("reply", reply_command))
    dispatcher.add_handler(CommandHandler("block", block_command))
    dispatcher.add_handler(CommandHandler("unblock", unblock_command))

    # رسائل النصية الخاصة
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.private, handle_owner_message))
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.private, handle_user_message))

    # تشغيل Flask
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    updater.start_polling()
    logger.info("Bot started.")
    updater.idle()

if __name__ == '__main__':
    main()
