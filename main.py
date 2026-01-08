import handlers  # register bot handlers
from app_context import bot
from config import RATE_PER_SECOND
from instance_lock import ensure_single_instance
from log import log
from queue_worker import start_worker_pool

if __name__ == "__main__":
    _lock_handle = ensure_single_instance()
    log("Bot is starting...", log_level="info")
    start_worker_pool(RATE_PER_SECOND)
    print("Bot is running 24/7...")
    bot.infinity_polling(timeout=None, long_polling_timeout=60)
