from app_context import bot, conversation_ids, request_queue
from config import HELP_MESSAGE
from log import log


@bot.message_handler(commands=["start"])
def send_welcome(message):
    log(f"User {message.chat.id} sent /start", log_level="info")
    bot.reply_to(
        message,
        "Xin chào quý khách! Tôi là chatbot hỗ trợ cho phần mềm SmartIR, gõ /help để xem thêm.",
    )


@bot.message_handler(commands=["help"])
def send_help(message):
    log(f"User {message.chat.id} sent /help", log_level="info")
    bot.reply_to(message, HELP_MESSAGE)


@bot.message_handler(commands=["chat", "ch"])
def start_chat(message):
    # Extract the part after "/chat "
    user_text = message.text.replace("/chat", "", 1).replace("/ch", "", 1).strip()

    if not user_text:
        bot.send_message(message.chat.id, "Hãy gửi tin nhắn sau lệnh /chat")
        return

    log(f"User {message.chat.id} said: {user_text}")
    request_queue.put((message, user_text))
    log(
        f"Queued request for user {message.chat.id} (queue={request_queue.qsize()})",
        log_level="info",
    )


@bot.message_handler(commands=["reset"])
def new_chat(message):
    log(f"User {message.chat.id} sent /reset", log_level="info")
    conversation_ids.pop(message.chat.id, None)
    bot.reply_to(message, "Lịch sử cuộc trò chuyện đã được xóa.")
