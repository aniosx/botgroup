import os
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import asyncio

# استدعاء المتغيرات البيئية
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

print("=== Starting Bot (Polling Only) ===")
print(f"BOT_TOKEN exists: {'Yes' if BOT_TOKEN else 'No'}")
print(f"OWNER_ID = {OWNER_ID}")
print(f"GROUP_CHAT_ID = {GROUP_CHAT_ID}")

# التأكد من وجود المتغيرات
if not BOT_TOKEN or not OWNER_ID or not GROUP_CHAT_ID:
    print("Error: One or more environment variables are missing!")
    exit(1)

OWNER_ID = int(OWNER_ID)
GROUP_CHAT_ID = int(GROUP_CHAT_ID)

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = update.message.text

    print(f"[RECEIVED] chat_id = {chat_id}, user_id = {user_id}, text = {text}")

    if user_id != OWNER_ID:
        await update.message.reply_text("هذا البوت خاص.")
        print("Unauthorized user tried to use the bot.")
        return

    if text:
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=text)
        print(f"[SENT] Message sent to group {GROUP_CHAT_ID}")

async def main():
    try:
        telegram_app = Application.builder().token(BOT_TOKEN).build()
        telegram_app.add_handler(MessageHandler(filters.TEXT, handle_private_message))
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        print("Bot is polling for updates... (waiting for messages)")
        await telegram_app.updater.idle()
    except Exception as e:
        print(f"Error while starting bot: {e}")

if __name__ == '__main__':
    asyncio.run(main())
