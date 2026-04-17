from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

import requests
from flask import Flask, jsonify, render_template, request
from requests import RequestException, Timeout

from config import Config


def _extract_reply(value: Any) -> str | None:
	if isinstance(value, str):
		text = value.strip()
		return text or None

	if isinstance(value, dict):
		for key in ("reply", "message", "text", "output", "response", "answer"):
			if key in value:
				extracted = _extract_reply(value[key])
				if extracted:
					return extracted

		for nested_value in value.values():
			extracted = _extract_reply(nested_value)
			if extracted:
				return extracted

	if isinstance(value, list):
		for item in value:
			extracted = _extract_reply(item)
			if extracted:
				return extracted

	return None


def create_app() -> Flask:
	app = Flask(__name__)
	app.config.from_object(Config)

	logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

	@app.get("/")
	def home() -> str:
		return render_template("index.html", max_length=app.config["MAX_MESSAGE_LENGTH"])

	@app.post("/api/chat")
	def chat() -> tuple[Any, int]:
		payload = request.get_json(silent=True) or {}
		chat_input = str(payload.get("chatInput", payload.get("message", ""))).strip()
		session_id = str(payload.get("sessionId", "")).strip() or str(uuid4())
		max_length = app.config["MAX_MESSAGE_LENGTH"]

		if not chat_input:
			return jsonify({"error": "Write a message before sending."}), 400

		if len(chat_input) > max_length:
			return jsonify({"error": f"Message is too long. Limit: {max_length} characters."}), 400

		webhook_url = app.config["N8N_WEBHOOK_URL"]
		if not webhook_url:
			return jsonify({"error": "n8n webhook is not configured on the server."}), 500

		try:
			response = requests.post(
				webhook_url,
				json={"chatInput": chat_input, "sessionId": session_id},
				timeout=app.config["N8N_TIMEOUT_SECONDS"],
			)
			response.raise_for_status()

			response_payload: Any
			if "application/json" in response.headers.get("Content-Type", ""):
				response_payload = response.json()
			else:
				response_payload = response.text

			reply = _extract_reply(response_payload) or "Risposta ricevuta, ma senza testo leggibile."
			if reply == "Risposta ricevuta, ma senza testo leggibile.":
				reply = "Response received, but no readable text was returned."
			return jsonify({"reply": reply}), 200
		except Timeout:
			app.logger.warning("n8n webhook timed out after %s seconds", app.config["N8N_TIMEOUT_SECONDS"])
			return jsonify({"error": "The request is taking longer than expected. The bot may still be working in n8n; please try again in a moment."}), 504
		except RequestException:
			app.logger.exception("Errore durante la chiamata al webhook n8n")
			return jsonify({"error": "The bot is not reachable right now. Please try again shortly."}), 502

	return app


app = create_app()


if __name__ == "__main__":
	app.run(debug=app.config["FLASK_DEBUG"])
