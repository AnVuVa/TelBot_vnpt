from config import LOG_DIR
import os

def log(message: str, log_level: str = "info", log_dir: str = LOG_DIR):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "bot.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{log_level.upper()}] {message}\n")