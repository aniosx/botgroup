#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CallbackContext

# Configuration des logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Chargement des variables d’environnement
load_dotenv()

# Variables principales
TOKEN = os.getenv('TELEGRAM_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID'))
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID'))
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # ex: https://ton-bot.onrender.com

# Initialisation
bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4, use_context=True)

# Fonction pour gérer les messages privés
def handle_owner_message(update: Update, context: CallbackContext):
    user = update.effective_user
    text = update.message.text

    if user.id != OWNER_ID:
        update.message.reply_text("Ce bot est privé.")
        logger.warning(f"Utilisateur non autorisé : {user.id}")
        return

    if text:
        context.bot.send_message(chat_id=GROUP_CHAT_ID, text=text)
        update.message.reply_text("Message envoyé au groupe.")

# Ajout du handler
dispatcher.add_handler(MessageHandler(Filters.text & Filters.private, handle_owner_message))

# Page d’accueil
@app.route('/')
def index():
    return 'Bot en ligne via webhook.'

# Point d’entrée pour Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

# Initialisation du webhook
@app.before_first_request
def init_webhook():
    webhook_url = f"{WEBHOOK_URL}/webhook"
    bot.delete_webhook()
    bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook défini sur : {webhook_url}")

# Démarrage de Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
