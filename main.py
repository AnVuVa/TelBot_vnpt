from schema import ChatRequest, State
state = State()

from config import API_KEY, BASE_URL, HELP_MESSAGE
from log import log
import telebot
import requests
import json

bot = telebot.TeleBot(API_KEY)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Xin chào bạn! Tôi là chatbot hỗ trợ cho phần mềm SmartIR. Gõ /help để xem thêm.")

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

    print(f"User {message.chat.id} said: {user_text}")
    # Call handle_chat directly with the extracted message
    handle_chat(message)

def handle_chat(message):
    state.history = state.history + [(message.text, "")]

    conversation = "\n".join([f"User: {msg[0]}\nBot: {msg[1]}" for msg in state.history])
    chat_req = ChatRequest(message=conversation, model="qwen3 14B")
    try:
        generator = requests.post(BASE_URL + "/api/chat", json=chat_req.dict(), stream=True)
        bot.reply_to(message, "Thinking...")
        bot_response = ""
        count = 1
        cur = 1
        for chunk in generator.iter_lines():
            if not chunk:
                continue
            try:
                line = chunk.decode("utf-8").strip()
                print(line)
                if line.startswith("data:"):
                    data = json.loads(line[len("data:"):].strip())
                    token = data.get("token", "")
                    if "Tool calling" not in token:
                        bot_response += token
                        bot_response = bot_response.replace("Bot:", "").replace("User:", "")
                        if token:
                            count += 1
                    if count % 32 == 0:
                        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + cur, text=bot_response.strip())
                    if count % 160 == 0:
                        bot_response = ""
                        bot.send_message(message.chat.id, bot_response.strip())
                        cur += 1
            except Exception as e:
                print("Error parsing chunk:", e)
                continue

        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id+cur, text=bot_response.strip())
        state.history[-1] = (message.text, bot_response)
        log(f"Conversation so far:\n{conversation}", log_level="info")
    except Exception as e:
        log(f"Error during chat handling: {e}", log_level="error")
        bot.reply_to(message, "An error occurred while processing your request.")

@bot.message_handler(commands=['reset'])
def new_chat(message):
    state.history = []
    bot.reply_to(message, "Lịch sử cuộc trò chuyện đã được xóa.")

bot.polling()