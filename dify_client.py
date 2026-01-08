import json
import time

import requests

from config import DIFY_API_KEY, DIFY_BASE_URL, MAX_RETRY
from log import log
from schema import DifyChatRequest


def stream_dify(user_text: str, user_id: str, conversation_id: str | None):
    payload = DifyChatRequest(
        query=user_text,
        user=user_id,
        response_mode="streaming",
        conversation_id=conversation_id,
    )
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }
    last_answer = ""
    received_any = False
    last_error = None
    for attempt in range(1, MAX_RETRY + 1):
        response = None
        try:
            log(f"Dify stream attempt {attempt} for user {user_id}", log_level="info")
            response = requests.post(
                f"{DIFY_BASE_URL}/chat-messages",
                headers=headers,
                json=payload.model_dump(exclude_none=True),
                stream=True,
                timeout=60,
            )
            response.raise_for_status()
            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    return
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    continue
                event_type = event.get("event")
                if event_type in ("message", "agent_message"):
                    answer = event.get("answer") or ""
                    if not answer:
                        continue
                    if answer.startswith(last_answer):
                        delta = answer[len(last_answer) :]
                    else:
                        delta = answer
                    last_answer = answer
                    if delta:
                        received_any = True
                        yield ("message", delta, None)
                elif event_type == "message_end":
                    conv_id = event.get("conversation_id")
                    yield ("end", "", conv_id)
                    return
                elif event_type == "error":
                    raise RuntimeError(event.get("message") or "Dify streaming error")
        except Exception as e:
            last_error = e
            log(f"Dify stream failed attempt {attempt}: {e}", log_level="error")
            if received_any:
                return
            if attempt < MAX_RETRY:
                time.sleep(0.5 * attempt)
                continue
            raise last_error
        finally:
            if response is not None:
                response.close()
