import time

import requests

from config import DIFY_API_KEY, DIFY_BASE_URL, MAX_RETRY
from log import log
from schema import DifyChatRequest


def call_dify(user_text: str, user_id: str, conversation_id: str | None):
    payload = DifyChatRequest(
        query=user_text,
        user=user_id,
        response_mode="blocking",
        conversation_id=conversation_id,
    )
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }
    last_error = None
    for attempt in range(1, MAX_RETRY + 1):
        try:
            log(f"Dify request attempt {attempt} for user {user_id}", log_level="info")
            response = requests.post(
                f"{DIFY_BASE_URL}/chat-messages",
                headers=headers,
                json=payload.model_dump(exclude_none=True),
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            answer = (data.get("answer") or "").strip()
            log(
                f"Dify response received for user {user_id} (len={len(answer)})",
                log_level="info",
            )
            return answer, data.get("conversation_id")
        except Exception as e:
            last_error = e
            log(f"Dify request failed attempt {attempt}: {e}", log_level="error")
            if attempt < MAX_RETRY:
                time.sleep(0.5 * attempt)
                continue
            raise last_error
            return None, None
