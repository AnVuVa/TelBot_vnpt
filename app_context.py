import queue

import telebot

from config import BOT_TELE_API_KEY, RATE_PER_SECOND
from rate_limiter import RateLimiter

bot = telebot.TeleBot(BOT_TELE_API_KEY, threaded=True)
conversation_ids = {}
request_queue = queue.Queue()
rate_limiter = RateLimiter(RATE_PER_SECOND)
