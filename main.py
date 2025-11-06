from schema import ChatRequest, State
global state
state = State()

from config import API_KEY, BASE_URL, HELP_MESSAGE, MAX_HISTORY_LENGTH
from log import log
import telebot
import requests
import json, time

bot = telebot.TeleBot(API_KEY, threaded=True)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Xin chào quý khách! Tôi là chatbot hỗ trợ cho phần mềm SmartIR. Gõ /help để xem thêm.")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, HELP_MESSAGE)

@bot.message_handler(commands=['chat', 'ch'])
def start_chat(message):
    # Extract the part after "/chat "
    user_text = message.text.replace('/chat', '', 1).replace('/ch', '', 1).strip()

    if not user_text:
        bot.send_message(message.chat.id, "Please enter a message after /chat")
        return

    log(f"User {message.chat.id} said: {user_text}")
    # Call handle_chat directly with the extracted message
    handle_chat(message, user_text)

def handle_chat(message, user_text):
    state.history = state.history + [(user_text, "")]
    conversation = "\n".join([f"User: {msg[0]}\nBot: </think>Yêu cầu (câu hỏi) của User có liên quan đến sản phẩm SmartIR không? Nếu có, dùng tool 'knowledge_retriever'.</think> {msg[1]}" for msg in state.history])
    chat_req = ChatRequest(message=conversation, model="qwen3 14B")
    log(f"Chat History Length: {len(state.history)}", log_level="info")

    try:
        thinking_msg = bot.reply_to(message, "🤔 Thinking...")
        generator = requests.post(BASE_URL + "/api/chat", json=chat_req.dict(), stream=True)
        bot_response = ""
        count = 1
        last_edit = time.time()
        last_msg = thinking_msg  # store the current editable message

        for chunk in generator.iter_lines():
            if not chunk:
                continue
            try:
                line = chunk.decode("utf-8").strip()
                log(line, log_level="debug")
                if not line.startswith("data:"):
                    continue

                data = json.loads(line[len("data:"):].strip())
                token = data.get("token", "")
                if "Tool calling" in token:
                    log(str(token), log_level="info")
                    continue

                bot_response += token.replace("Bot:", "").replace("User:", "")
                if token:
                    count += 1

                # edit every 32 tokens (throttled)
                if count % 96 == 0 and time.time() - last_edit > 0.5:
                    try:
                        time.sleep(0.3)
                        bot.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=last_msg.message_id,
                            text=bot_response.strip() or "..."
                        )
                        last_edit = time.time()
                    except Exception as e:
                        if "message is not modified" not in str(e):
                            print("Edit error:", e)

                if count % (96*10+48) == 0:
                    last_msg = bot.send_message(message.chat.id, "...")
                    bot_response = ""
            except Exception as e:
                print("Error parsing chunk:", e)
                continue

        # Final update
        if bot_response.strip():
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=last_msg.message_id,
                text=bot_response.strip()
            )

        state.history[-1] = (user_text, bot_response)
        state.history = state.history[-MAX_HISTORY_LENGTH:]
        
        log(f"Conversation so far:\n{conversation}", log_level="info")

    except Exception as e:
        log(f"Error during chat handling: {e}", log_level="error")
        bot.reply_to(message, "⚠️ An error occurred while processing your request.")

@bot.message_handler(commands=['reset'])
def new_chat(message):
    global state
    state.history = []
    bot.reply_to(message, "Lịch sử cuộc trò chuyện đã được xóa.")

if __name__ == "__main__":
    print("Bot is running 24/7...")
    bot.infinity_polling(timeout=None, long_polling_timeout=60)