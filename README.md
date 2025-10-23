# Telegram Bot
This work is a part of project VNPT-AI-Agent.

The target is to deploy the chatbot into Telegram

Also, this repo can be reuse for others type of API, as long as it return *Generator class*.

## Project Tree
```
TELBOT_VNPT/
├── __pycache__/
├── .venv/
├── logs/
│   ├── .gitignore
│   ├── .python-version
│   ├── config.py
│   ├── log.py
│   ├── main.py
│   ├── pyproject.toml
│   ├── README.md
│   ├── schema.py
│   └── uv.lock

```
## Getting start
### With uv
Install uv if you don't install it yet
```
pip install uv
```
Move to the folder and sync (install the required libraries)
```
uv sync
```
Run the script
```
uv run main.py
```

# About
This is a work of [AnVuVa](https://github.com/AnVuVa)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Feel free to use and modify the code as per the terms of the license. Feedbacks are welcome!