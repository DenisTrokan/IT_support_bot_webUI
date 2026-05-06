from __future__ import annotations

import logging
import os
from functools import wraps
from typing import Any
from urllib.parse import urlencode
from uuid import uuid4

import requests
from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.flask_client import OAuth
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from requests import RequestException, Timeout

from config import Config

os.environ.setdefault("AUTHLIB_INSECURE_TRANSPORT", "true")

oauth = OAuth()


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


def _as_list(value: Any) -> list[Any]:
	if value is None:
		return []

	if isinstance(value, list):
		return value

	if isinstance(value, tuple):
		return list(value)

	return [value]


def _normalize_user_claims(claims: dict[str, Any]) -> dict[str, Any]:
	preferred_username = str(
		claims.get("preferred_username")
		or claims.get("upn")
		or claims.get("email")
		or ""
	).strip()
	name = str(claims.get("name") or preferred_username or claims.get("oid") or claims.get("sub") or "Microsoft user").strip()

	return {
		"name": name,
		"email": preferred_username,
		"oid": str(claims.get("oid") or claims.get("sub") or "").strip(),
		"tenantId": str(claims.get("tid") or "").strip(),
		"preferredUsername": preferred_username,
		"roles": _as_list(claims.get("roles")),
		"groups": _as_list(claims.get("groups")),
	}


def _require_login(api: bool = False):
	def decorator(view):
		@wraps(view)
		def wrapped(*args: Any, **kwargs: Any):
			if session.get("user"):
				return view(*args, **kwargs)

			if api:
				return jsonify({"error": "Please sign in with your company account.", "loginUrl": url_for("login")}), 401

			return redirect(url_for("login"))

		return wrapped

	return decorator


def _build_n8n_headers(app: Flask) -> dict[str, str]:
	header_name = app.config["N8N_INTERNAL_SECRET_HEADER"]
	secret = app.config["N8N_INTERNAL_SECRET"]

	if not secret:
		return {}

	return {header_name: secret}


def create_app() -> Flask:
	app = Flask(__name__)
	app.config.from_object(Config)

	logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

	tenant_id = app.config["AZURE_TENANT_ID"] or "common"
	oauth.register(
		name="microsoft",
		client_id=app.config["AZURE_CLIENT_ID"],
		client_secret=app.config["AZURE_CLIENT_SECRET"],
		server_metadata_url=f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration",
		client_kwargs={"scope": " ".join(app.config["AZURE_SCOPES"])},
	)
	oauth.init_app(app)

	app.config.update(
		SESSION_COOKIE_SECURE=False,
		SESSION_COOKIE_HTTPONLY=True,
		SESSION_COOKIE_SAMESITE="Lax",
	)

	if not all((app.config["AZURE_CLIENT_ID"], app.config["AZURE_CLIENT_SECRET"], app.config["AZURE_REDIRECT_URI"])):
		app.logger.warning("Microsoft auth is not fully configured; login routes will not work until the Azure values are set.")

	@app.get("/")
	@_require_login()
	def home() -> str:
		return render_template(
			"index.html",
			max_length=app.config["MAX_MESSAGE_LENGTH"],
			user=session.get("user"),
		)

	@app.get("/login")
	def login() -> Any:
		if session.get("user"):
			return redirect(url_for("home"))

		if not all((app.config["AZURE_CLIENT_ID"], app.config["AZURE_CLIENT_SECRET"], app.config["AZURE_REDIRECT_URI"])):
			return jsonify({"error": "Microsoft auth is not configured on the server."}), 500

		nonce = str(uuid4())
		session["nonce"] = nonce
		return oauth.microsoft.authorize_redirect(redirect_uri=app.config["AZURE_REDIRECT_URI"], nonce=nonce)

	@app.get("/auth/callback")
	def auth_callback() -> Any:
		if not all((app.config["AZURE_CLIENT_ID"], app.config["AZURE_CLIENT_SECRET"], app.config["AZURE_REDIRECT_URI"])):
			return jsonify({"error": "Microsoft auth is not configured on the server."}), 500

		try:
			token = oauth.microsoft.authorize_access_token()
			nonce = session.get("nonce")
			claims = dict(oauth.microsoft.parse_id_token(token, nonce=nonce))
		except OAuthError as error:
			app.logger.exception("Microsoft login failed")
			return jsonify({"error": f"Microsoft login failed: {error.error}"}), 401
		except Exception:
			app.logger.exception("Microsoft login failed")
			return jsonify({"error": "Microsoft login failed."}), 401

		session["user"] = _normalize_user_claims(claims)
		return redirect(url_for("home"))

	@app.get("/logout")
	def logout() -> Any:
		session.clear()

		try:
			server_metadata = oauth.microsoft.load_server_metadata()
			end_session_endpoint = server_metadata.get("end_session_endpoint")
		except Exception:
			end_session_endpoint = None

		if end_session_endpoint:
			params = {"post_logout_redirect_uri": app.config["AZURE_POST_LOGOUT_REDIRECT_URI"] or url_for("home", _external=True)}
			return redirect(f"{end_session_endpoint}?{urlencode(params)}")

		return redirect(url_for("home"))

	@app.post("/api/chat")
	@_require_login(api=True)
	def chat() -> tuple[Any, int]:
		current_user = session.get("user") or {}
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

		n8n_payload = {
			"chatInput": chat_input,
			"sessionId": session_id,
			"requestId": str(uuid4()),
			"user": current_user,
			"userName": current_user.get("name"),
			"userEmail": current_user.get("email"),
			"userOid": current_user.get("oid"),
			"tenantId": current_user.get("tenantId"),
			"userRoles": current_user.get("roles", []),
			"userGroups": current_user.get("groups", []),
		}

		try:
			response = requests.post(
				webhook_url,
				json=n8n_payload,
				headers=_build_n8n_headers(app),
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
	app.run(host="localhost", debug=app.config["FLASK_DEBUG"])
