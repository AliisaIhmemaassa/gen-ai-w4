#!/usr/bin/env python3
"""chat_core: OpenAI tool-use loop with web_search tool.

chat(messages) -> str
"""
import json
import os
import sys

from openai import OpenAI

from search import web_search

MODEL = "nvidia/nemotron-3.5-super-vl:free"
BASE_URL = "https://openrouter.ai/api/v1"
MAX_ROUNDS = 5

API_KEY = os.environ.get("OPENROUTER_API_KEY")
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
                "query": {"type": "string", "description": "Search query"},
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


def chat(messages):
    """Run tool-use loop until text answer (max 5 rounds).

    Returns {"answer": str, "search_used": bool, "search_query": str|None}.
    """
    history = list(messages)
    search_used = False
    search_query = None

    for _ in range(MAX_ROUNDS):
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
                    print(f"Työkalukutsu: web_search(query={query!r}, max_results={max_results})")
                    search_used = True
                    search_query = query
                    results = web_search(query, max_results)
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(results, ensure_ascii=False),
                    })
            continue

        return {
            "answer": msg.content or "",
            "search_used": search_used,
            "search_query": search_query,
        }

    return {
        "answer": "",
        "search_used": search_used,
        "search_query": search_query,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Käyttö: python chat_core.py <viesti>")
        sys.exit(1)

    user_message = sys.argv[1]
    messages = [{"role": "user", "content": user_message}]
    result = chat(messages)
    print("\nVastaus:")
    print(result["answer"])
    if result["search_used"]:
        print(f"(Hakua käytetty: {result['search_query']})")
