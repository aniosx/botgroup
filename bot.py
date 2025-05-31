#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import threading

from flask import Flask
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler
)

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),  # Save logs to a file
        logging.StreamHandler()  # Print logs to console
    ]
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

# حالات المحادثة
REPLY = 1

# رسالة ترحيب عند /start
def start_command(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.id == OWNER_ID:
        return
    update.message.reply_text("مرحبًا بك! أرسل رسالتك أو أي نوع من الوسائط، وسأقوم بإرسالها إلى المشرف.")

# رسائل المشرف
def handle_owner_message(update: Update, context: CallbackContext):
    # Skip if the admin is in the REPLY state
    if context.user_data.get('reply_to'):
        return

    message = update.message
    chat_id = GROUP_CHAT_ID

    try:
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
    except Exception as e:
        logger.error(f"Error sending message to group: {e}")
        update.message.reply_text(f"حدث خطأ أثناء إرسال الرسالة إلى المجموعة: {e}")

# رسائل المستخدمين العاديين
def handle_user_message(update: Update, context: CallbackContext):
    user = update.effective_user
    message = update.message

    if user.id == OWNER_ID or user.id in blocked_users:
        return

    # إعداد اسم المستخدم مع رابط تليجرام
    user_name = user.first_name or user.username or f"User{user.id}"
    user_link = f"[{user_name}](tg://user?id={user.id})"
    caption = message.caption or ''
    user_info = f"رسالة من {user_link}:\n{message.text or caption}"

    # إعداد الأزرار
    keyboard = [
        [
            InlineKeyboardButton("الرد", callback_data=f"reply_{user.id}"),
            InlineKeyboardButton("حظر", callback_data=f"block_{user.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # إرسال للمشرف
    try:
        if message.text:
            context.bot.send_message(chat_id=OWNER_ID, text=user_info, reply_markup=reply_markup, parse_mode='Markdown')
        elif message.photo:
            context.bot.send_photo(chat_id=OWNER_ID, photo=message.photo[-1].file_id, caption=user_info, reply_markup=reply_markup, parse_mode='Markdown')
        elif message.video:
            context.bot.send_video(chat_id=OWNER_ID, video=message.video.file_id, caption=user_info, reply_markup=reply_markup, parse_mode='Markdown')
        elif message.document:
            context.bot.send_document(chat_id=OWNER_ID, document=message.document.file_id, caption=user_info, reply_markup=reply_markup, parse_mode='Markdown')
        elif message.audio:
            context.bot.send_audio(chat_id=OWNER_ID, audio=message.audio.file_id, caption=user_info, reply_markup=reply_markup, parse_mode='Markdown')
        elif message.voice:
            context.bot.send_voice(chat_id=OWNER_ID, voice=message.voice.file_id, caption=user_info, reply_markup=reply_markup, parse_mode='Markdown')
        elif message.sticker:
            context.bot.send_sticker(chat_id=OWNER_ID, sticker=message.sticker.file_id)
            context.bot.send_message(chat_id=OWNER_ID, text=user_info, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            update.message.reply_text("نوع الوسائط غير مدعوم.")
            return

        # تأكيد للمستخدم
        update.message.reply_text("✅ تم إرسال رسالتك/الوسائط إلى المشرف. شكرًا لتواصلك.")
    except Exception as e:
        logger.error(f"Error sending message to admin: {e}")
        update.message.reply_text("حدث خطأ أثناء إرسال الرسالة إلى المشرف.")

# معالجة الأزرار
def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id

    if user_id != OWNER_ID:
        query.answer("غير مصرح لك باستخدام هذه الأزرار.")
        return

    data = query.data
    if data.startswith("reply_"):
        target_user_id = int(data.split("_")[1])
        context.user_data['reply_to'] = target_user_id
        query.message.reply_text("أرسل الرد الآن:")
        query.answer()
        return REPLY
    elif data.startswith("block_"):
        target_user_id = int(data.split("_")[1])
        blocked_users.add(target_user_id)
        save_blocked_users(blocked_users)
        query.message.reply_text("تم حظر المستخدم.")
        query.answer()

# معالجة الرد
def handle_reply(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        return ConversationHandler.END

    target_user_id = context.user_data.get('reply_to')
    if not target_user_id:
        update.message.reply_text("حدث خطأ، لم يتم تحديد المستخدم.")
        return ConversationHandler.END

    message = update.message.text
    try:
        context.bot.send_message(chat_id=target_user_id, text=message)
        update.message.reply_text("تم إرسال الرد إلى المستخدم.")
        logger.info(f"Reply sent to user {target_user_id}: {message}")
    except Exception as e:
        logger.error(f"Error sending reply to user {target_user_id}: {e}")
        update.message.reply_text(f"حدث خطأ أثناء إرسال الرد: {e}")
    
    # تنظيف البيانات
    context.user_data.pop('reply_to', None)
    return ConversationHandler.END

# إلغاء الرد
def cancel_reply(update: Update, context: CallbackContext):
    update.message.reply_text("تم إلغاء الرد.")
    context.user_data.pop('reply_to', None)
    return ConversationHandler.END

# رد المشرف على مستخدم باستخدام الأمر
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
        logger.info(f"Reply sent via command to user {user_id}: {message}")
    except Exception as e:
        logger.error(f"Error in reply_command: {e}")
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
        logger.info(f"User {user_id} blocked.")
    except Exception as e:
        logger.error(f"Error in block_command: {e}")
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
        logger.info(f"User {user_id} unblocked.")
    except Exception as e:
        logger.error(f"Error in unblock_command: {e}")
        update.message.reply_text(f"حدث خطأ: {e}")

# تشغيل Flask
def run_flask():
    app.run(host='0.0.0.0', port=PORT)

def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # إعداد ConversationHandler للرد
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern='^reply_')],
        states={
            REPLY: [MessageHandler(Filters.text & ~Filters.command, handle_reply)]
        },
        fallbacks=[CommandHandler('cancel', cancel_reply)]
    )

    # أوامر المشرف
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("reply", reply_command))
    dispatcher.add_handler(CommandHandler("block", block_command))
    dispatcher.add_handler(CommandHandler("unblock", unblock_command))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

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

    # تشغيل Flask في الخلفية
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # بدء البوت
    try:
        updater.start_polling()
        logger.info("Bot started successfully.")
        updater.idle()
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

if __name__ == '__main__':
    main()
