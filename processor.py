import json
import os
import time
from datetime import datetime, timezone

from app_context import bot, conversation_ids
from config import (
    ACCUMULATE_TOKEN,
    CONVERSATION_LOG_DIR,
    MAX_HISTORY,
    MAX_MESSAGE_LENGTH,
    MAX_RETRY,
)
from dify_client import stream_dify
from log import log


def _get_history_path(user_id: str) -> str:
    return os.path.join(CONVERSATION_LOG_DIR, f"{user_id}.log")


def _read_history_turns(user_id: str) -> list[dict[str, str]]:
    path = _get_history_path(user_id)
    if not os.path.exists(path):
        return []
    turns: list[dict[str, str]] = []
    legacy_lines: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                legacy_lines.append(line)
                continue
            user_text = item.get("user")
            bot_text = item.get("bot")
            if user_text is None or bot_text is None:
                continue
            turns.append({"user": str(user_text), "bot": str(bot_text)})

    if legacy_lines:
        i = 0
        while i < len(legacy_lines) - 1:
            if legacy_lines[i].startswith("U: ") and legacy_lines[i + 1].startswith("B: "):
                turns.append(
                    {
                        "user": legacy_lines[i][3:],
                        "bot": legacy_lines[i + 1][3:],
                    }
                )
                i += 2
            else:
                i += 1
    return turns


def _append_history(user_id: str, user_text: str, bot_text: str):
    os.makedirs(CONVERSATION_LOG_DIR, exist_ok=True)
    path = _get_history_path(user_id)
    with open(path, "a", encoding="utf-8") as f:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "user": user_text,
            "bot": bot_text,
        }
        f.write(json.dumps(entry, ensure_ascii=True) + "\n")


def _build_prompt(user_id: str, user_text: str) -> str:
    history_turns = _read_history_turns(user_id)
    if not history_turns:
        return user_text
    context = history_turns[-MAX_HISTORY:]
    blocks = []
    for idx, turn in enumerate(context, start=1):
        blocks.append(f"{idx}. User: {turn['user']}\n   Bot: {turn['bot']}")
    history_text = "\n".join(blocks)
    return f"Conversation history:\n{history_text}\nUser: {user_text}"


def _count_tokens(text: str) -> int:
    return len(text.split())


def _split_text(text: str) -> list[str]:
    if not text:
        return [""]
    return [text[i : i + MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]


def process_chat(message, user_text):
    thinking_msg = None
    try:
        thinking_msg = bot.reply_to(message, "Thinking...")
        conversation_id = conversation_ids.get(message.chat.id)
        chat_id = message.chat.id
        user_id = str(chat_id)
        prompt_text = _build_prompt(user_id, user_text)
        message_ids = [thinking_msg.message_id]

        def apply_updates(total_answer: str):
            if not total_answer:
                return
            chunks = _split_text(total_answer)
            last_index = len(message_ids) - 1
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_ids[last_index],
                text=chunks[last_index] or "...",
            )
            for chunk in chunks[len(message_ids) :]:
                msg = bot.send_message(chat_id, chunk)
                message_ids.append(msg.message_id)

        total_answer = ""
        new_conversation_id = None
        for attempt in range(1, MAX_RETRY + 1):
            try:
                accumulated_tokens = 0
                for event, chunk, conv_id in stream_dify(
                    prompt_text,
                    user_id,
                    conversation_id,
                ):
                    if event == "end":
                        new_conversation_id = conv_id
                        continue
                    if not chunk:
                        continue
                    total_answer += chunk
                    accumulated_tokens += _count_tokens(chunk)

                    if accumulated_tokens >= ACCUMULATE_TOKEN:
                        apply_updates(total_answer)
                        accumulated_tokens = 0
                break
            except Exception as e:
                log(f"Streaming attempt {attempt} failed: {e}", log_level="error")
                if attempt >= MAX_RETRY:
                    raise
                time.sleep(0.5 * attempt)

        if new_conversation_id:
            conversation_ids[chat_id] = new_conversation_id

        if not total_answer:
            total_answer = "No response from Dify."
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_ids[0],
                text=total_answer,
            )
        else:
            apply_updates(total_answer)

        _append_history(user_id, user_text, total_answer)
        log(
            f"Sent Dify answer to user {chat_id} (messages={len(message_ids)})",
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
