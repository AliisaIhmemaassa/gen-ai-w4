# hakuchat

Python chat server + single `index.html` UI. The model calls OpenRouter via the OpenAI library and can use a `web_search` tool, looping until it gives a text answer.

## Requirements

- Python 3
- `OPENROUTER_API_KEY` environment variable (not `OPEN_ROUTER_UUS`)
- Python package: `openai`

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install openai
```

## Run

```bash
export OPENROUTER_API_KEY=<your openrouter key>
.venv/bin/python server.py
```

Then open `http://127.0.0.1:8080`.

## Behavior

- `GET /` serves `index.html`
- `POST /api/chat` body: `{session_id, message}` → `{answer, search_used, search_query, session_id}`
- `web_search` tool runs `curl` via `subprocess.run` against DuckDuckGo HTML, parses `{title, url}` results
- Tool-use loop: max 5 rounds, then returns whatever text was produced
- Conversation history is kept per browser session (client generates a `session_id` stored in `localStorage`)
- UI shows when search was used and with what query; links in answers are clickable

## Notes

- No Flask: server uses the standard library `http.server`
- `server.py` reads `index.html` from disk, so keep both files together
- The API key must never be committed; `OPENROUTER_API_KEY` is read from the environment only
