# Telegram Bot
This repo is a Telegram bot that forwards user messages to Dify and sends the answer back to Telegram.
It includes a queue with rate limiting and a single-instance lock to avoid Telegram polling conflicts.

## Pipeline
`tele_user_input -> dify_api -> answer_to_telegram`

## Key Features
- Dify API integration (blocking response mode).
- Queue + rate limiter (`RATE_PER_SECOND`) with parallel workers.
- Retry on Dify requests (`MAX_RETRY`).
- Single-instance lock via `logs/bot.lock`.
- Structured logging to `logs/`.

## Project Structure
```
TELBOT_VNPT/
|-- app_context.py     # shared bot/queue/rate limiter state
|-- dify_client.py     # Dify API client with retry
|-- handlers.py        # Telegram command handlers
|-- instance_lock.py   # single-instance lock
|-- log.py             # file logger
|-- main.py            # app entrypoint
|-- processor.py       # chat processing pipeline
|-- queue_worker.py    # worker pool and queue logic
|-- rate_limiter.py    # rate limiter helper
|-- schema.py          # request models
|-- config.py          # runtime config
|-- pyproject.toml
|-- README.md
|-- uv.lock
`-- logs/
```

## Activity Diagram
```
            +----------------------+
            |       main.py        |
            |  entrypoint/startup  |
            +----------+-----------+
                       |
                       v
            +----------------------+
            |  instance_lock.py    |
            |  single instance     |
            +----------+-----------+
                       |
                       v
            +----------------------+
            |   app_context.py     |
            |  bot/queue/limiter   |
            +----------+-----------+
                       |
                       v
            +----------------------+
            |     handlers.py      |
            | /start /help /chat   |
            +----------+-----------+
                       |
                       v
            +----------------------+
            |  queue_worker.py     |
            |  worker pool + rate  |
            +----------+-----------+
                       |
                       v
            +----------------------+
            |    processor.py      |
            |  chat -> dify call   |
            +----------+-----------+
                       |
                       v
            +----------------------+
            |    dify_client.py    |
            |   API + retry        |
            +----------+-----------+
                       |
                       v
            +----------------------+
            |    Telegram reply    |
            |   (via bot object)   |
            +----------------------+
```

## Getting Started
### With uv
Install uv:
```
pip install uv
```
Sync dependencies:
```
uv sync
```
Run the bot:
```
uv run main.py
```

## About
by [AnVuVa](https://github.com/AnVuVa)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Feel free to use and modify the code as per the terms of the license. Feedbacks are welcome!
