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
    CallbackContext
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

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text & Filters.private, handle_owner_message))

    # تشغيل Flask في خلفية
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # بدء الاستماع
    updater.start_polling()
    logger.info("Group broadcast bot started.")
    updater.idle()

if __name__ == '__main__':
    main()
