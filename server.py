#!/usr/bin/env python3
"""hakuchat server: single-file Python HTTP server serving index.html and POST /api/chat.

Model calls OpenRouter via the OpenAI library with a web_search tool.
Tool-use loop runs until a text answer, max 5 rounds.
Conversation history per browser session (session_id sent by client).
"""
import json
import os
import re
import subprocess
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import quote, unquote, urlparse, parse_qs

from openai import OpenAI

API_KEY = os.environ.get("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "nvidia/nemotron-3.5-super-vl:free"
HOST = "127.0.0.1"
PORT = 8080

if not API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY environment variable is not set")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for information. Use this when the user asks about current events, facts, or anything you are not certain about. Returns a list of results, each with a title and a url.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}

# In-memory conversation history per session_id.
sessions = {}


def history_for(session_id):
    if session_id not in sessions:
        sessions[session_id] = []
    return sessions[session_id]


def web_search(query, max_results=5):
    """Run a DuckDuckGo HTML search via curl and return [{title, url}]."""
    url = "https://html.duckduckgo.com/html/?q=" + quote(query)
    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-L",
                "--max-time", "15",
                "-A", "Mozilla/5.0 (X11; Linux x86_64)",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        html = result.stdout
    except Exception as exc:  # curl/network failure
        return [{"title": "Haku epäonnistui", "url": "", "error": str(exc)}]

    results = []
    pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        re.DOTALL,
    )
    for match in pattern.finditer(html):
        href = match.group(1)
        title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        if href.startswith("//"):
            href = "https:" + href
        # Unwrap DuckDuckGo redirect (uddg param)
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            href = unquote(qs["uddg"][0])
        if title and href:
            results.append({"title": title, "url": href})
        if len(results) >= max_results:
            break
    if not results:
        results = [{"title": "Ei tuloksia", "url": ""}]
    return results


def run_chat(session_id, user_message):
    """Tool-use loop: call model, execute web_search if requested, repeat until text."""
    history = history_for(session_id)
    history.append({"role": "user", "content": user_message})

    search_used = False
    search_query = None
    last_text = ""

    for _ in range(5):
        response = client.chat.completions.create(
            model=MODEL,
            messages=history,
            tools=[WEB_SEARCH_TOOL],
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            history.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                if tc.function.name == "web_search":
                    args = json.loads(tc.function.arguments or "{}")
                    query = args.get("query", "")
                    max_results = int(args.get("max_results", 5) or 5)
                    search_used = True
                    search_query = query
                    results = web_search(query, max_results)
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(results, ensure_ascii=False),
                    })
            continue  # recall model with tool results

        # Plain text answer.
        last_text = msg.content or ""
        history.append({"role": "assistant", "content": last_text})
        return {
            "answer": last_text,
            "search_used": search_used,
            "search_query": search_query,
        }

    # Max rounds reached without a text answer.
    return {
        "answer": last_text,
        "search_used": search_used,
        "search_query": search_query,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return  # silence default request logging

    def _send_json(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            try:
                with open("index.html", "rb") as f:
                    body = f.read()
            except FileNotFoundError:
                self._send_json(404, {"error": "index.html not found"})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/chat":
            self._send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid json"})
            return

        session_id = data.get("session_id") or str(uuid.uuid4())
        user_message = data.get("message", "")
        if not isinstance(user_message, str) or not user_message.strip():
            self._send_json(400, {"error": "message required"})
            return

        result = run_chat(session_id, user_message)
        result["session_id"] = session_id
        self._send_json(200, result)


def main():
    server = HTTPServer((HOST, PORT), Handler)
    print(f"hakuchat server listening on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()


if __name__ == "__main__":
    main()
