import logging

import telebot
from django.conf import settings


logger = logging.getLogger(__name__)

bot = telebot.TeleBot(
    settings.TELEGRAM_BOT_TOKEN,
    parse_mode="HTML",
)


def send_telegram_message(text: str):
    """
    Send a message to the configured Telegram admin chat.
    Logs an error if sending fails.
    """
    try:
        bot.send_message(
            chat_id=settings.TELEGRAM_ADMIN_CHAT_ID,
            text=text,
        )
    except Exception as e:
        logger.error("Failed to send Telegram message: %s", e)
