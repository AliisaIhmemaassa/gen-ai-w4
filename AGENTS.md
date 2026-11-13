# hakuchat

Python chat server (Flask) + single `index.html` UI. Model calls OpenRouter via the OpenAI library; when appropriate it calls a `web_search` tool and loops until a text answer.

## Target structure (per requirements)

- One Python server (Flask) serving `index.html` and `POST /api/chat`
- `index.html`: message list, text field, Send button, Enter sends; no frameworks; clickable links; shows when search was used and with what query
- Conversation history per browser session

## Setup

- No package manifest; install into the existing `.venv`: `.venv/bin/python3 -m pip install flask openai`
- Run: `OPENROUTER_API_KEY=<key> .venv/bin/python3 app.py` → `http://127.0.0.1:5000` (Flask)
- Legacy entrypoint: `.venv/bin/python3 server.py` → `http://127.0.0.1:8080` (stdlib `http.server`)
- `OPENROUTER_API_KEY` is validated at import time (`chat_core.py`/`server.py`) — the server won't start without it. Do **not** use `OPEN_ROUTER_UUS` (old `weather.py` demo). Key must not be in code or git history.
- **Gotcha**: `.venv/bin/python` is a 0-byte broken stub in this repo — always use `.venv/bin/python3`.

## Non-obvious commands / gotchas

- Model: `nvidia/nemotron-3.5-super-vl:free`, base URL `https://openrouter.ai/api/v1`
- Tool: `web_search` with `query` (string, required) and `max_results` (int, default 5)
- Search runs `curl` via `subprocess.run` against DuckDuckGo HTML; result parsed into `{title, url}` list, returned to model as JSON
- Tool-use loop: execute tool calls, recall model, repeat until text answer; max 5 rounds (`chat_core.chat`)
- `chat_core.chat(messages)` returns `{"answer", "search_used", "search_query"}` — not a plain string
- UI text is Finnish (`index.html` `lang="fi"`; placeholder/button labels in Finnish) — keep language consistent when editing.

## Repo scope

- `app.py` (Flask, port 5000), `search.py` (`web_search`), `chat_core.py` (tool-use loop), `index.html` (vanilla JS), `README.md`; `server.py` (stdlib `http.server`, port 8080) and `weather.py` are older demos.
- Server: `GET /` serves `index.html` (read from disk), `POST /api/chat` runs the tool-use loop.
- No tests, lint/typecheck config, CI, or git commits yet.
