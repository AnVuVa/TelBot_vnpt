from app_context import bot, conversation_ids
from dify_client import call_dify
from log import log


def split_message(text: str, max_len: int = 4096):
    if not text:
        return [""]
    return [text[i : i + max_len] for i in range(0, len(text), max_len)]


def process_chat(message, user_text):
    thinking_msg = None
    try:
        thinking_msg = bot.reply_to(message, "Thinking...")
        conversation_id = conversation_ids.get(message.chat.id)
        answer, new_conversation_id = call_dify(
            user_text,
            str(message.chat.id),
            conversation_id,
        )
        if new_conversation_id:
            conversation_ids[message.chat.id] = new_conversation_id

        if not answer:
            answer = "No response from Dify."

        chunks = split_message(answer)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=thinking_msg.message_id,
            text=chunks[0] or "...",
        )
        for chunk in chunks[1:]:
            bot.send_message(message.chat.id, chunk)
        log(
            f"Sent Dify answer to user {message.chat.id} (chunks={len(chunks)})",
            log_level="info",
        )
    except Exception as e:
        log(f"Error during Dify request: {e}", log_level="error")
        error_text = "An error occurred while processing your request."
        if thinking_msg:
            try:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=thinking_msg.message_id,
                    text=error_text,
                )
            except Exception:
                bot.reply_to(message, error_text)
        else:
            bot.reply_to(message, error_text)
