#!/usr/bin/env python3
"""hakuchat Flask-palvelin: tarjoaa index.html:n ja POST /api/chat -rajapinnan.

Rajapinta nojaa chat_core.chat-funktioon (OpenAI + web_search tool use).
"""
import os
import uuid
from flask import Flask, request, jsonify, send_file

from chat_core import chat

app = Flask(__name__)

# Keskusteluhistoria muistissa avaimella session_id.
sessions = {}


def history_for(session_id):
    if session_id not in sessions:
        sessions[session_id] = []
    return sessions[session_id]


@app.get("/")
def index():
    return send_file("index.html")


@app.post("/api/chat")
def chat_endpoint():
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id") or str(uuid.uuid4())
    user_message = data.get("message", "")

    if not isinstance(user_message, str) or not user_message.strip():
        return jsonify({"error": "message required"}), 400

    history = history_for(session_id)
    history.append({"role": "user", "content": user_message})

    result = chat(history)

    # Tallenna mallin vastaus historiaan jatkokysymyksiä varten.
    assistant_msg = {"role": "assistant", "content": result["answer"]}
    history.append(assistant_msg)

    return jsonify({
        "session_id": session_id,
        "answer": result["answer"],
        "search_used": result["search_used"],
        "search_query": result["search_query"],
    })


def main():
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
