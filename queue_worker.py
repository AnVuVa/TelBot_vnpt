import threading

from app_context import rate_limiter, request_queue
from log import log
from processor import process_chat


def worker():
    while True:
        item = request_queue.get()
        if item is None:
            request_queue.task_done()
            break
        message, user_text = item
        try:
            rate_limiter.wait_for_slot()
            log(
                f"Processing queued request for user {message.chat.id}",
                log_level="info",
            )
            process_chat(message, user_text)
        except Exception as e:
            log(f"Worker error: {e}", log_level="error")
        finally:
            request_queue.task_done()


def start_worker_pool(worker_count: int):
    count = max(1, int(worker_count))
    for i in range(count):
        thread = threading.Thread(
            target=worker,
            name=f"worker-{i + 1}",
            daemon=True,
        )
        thread.start()
    log(
        f"Worker pool started (count={count}, rate={rate_limiter.rate_per_second}/s)",
        log_level="info",
    )
