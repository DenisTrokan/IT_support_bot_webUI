from __future__ import annotations

import argparse
import json
import os
import sys
from uuid import uuid4

import requests


def build_payload(chat_input: str, session_id: str, name: str, email: str, oid: str, tenant_id: str) -> dict[str, object]:
	user = {
		"name": name,
		"email": email,
		"oid": oid,
		"tenantId": tenant_id,
	}

	return {
		"chatInput": chat_input,
		"sessionId": session_id,
		"requestId": str(uuid4()),
		"user": user,
		"userName": name,
		"userEmail": email,
		"userOid": oid,
		"tenantId": tenant_id,
	}


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Send a test payload to the n8n webhook.")
	parser.add_argument(
		"--url",
		default=os.getenv("N8N_WEBHOOK_URL", "").strip(),
		help="Webhook URL to test. Defaults to N8N_WEBHOOK_URL.",
	)
	parser.add_argument(
		"--secret",
		default=os.getenv("N8N_INTERNAL_SECRET", "").strip(),
		help="Optional shared secret header value. Defaults to N8N_INTERNAL_SECRET.",
	)
	parser.add_argument("--header-name", default=os.getenv("N8N_INTERNAL_SECRET_HEADER", "X-Webhook-Secret"), help="Header name for the shared secret.")
	parser.add_argument("--chat-input", default="test from script", help="Chat input to send.")
	parser.add_argument("--session-id", default="script-session", help="Session ID to send.")
	parser.add_argument("--name", default="Mario Rossi", help="User name to send.")
	parser.add_argument("--email", default="mario.rossi@example.com", help="User email to send.")
	parser.add_argument("--oid", default="oid-123", help="User OID to send.")
	parser.add_argument("--tenant-id", default="tenant-123", help="Tenant ID to send.")
	parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds.")
	return parser.parse_args()


def main() -> int:
	args = parse_args()

	if not args.url:
		print("Missing webhook URL. Pass --url or set N8N_WEBHOOK_URL.", file=sys.stderr)
		return 2

	payload = build_payload(
		chat_input=args.chat_input,
		session_id=args.session_id,
		name=args.name,
		email=args.email,
		oid=args.oid,
		tenant_id=args.tenant_id,
	)

	headers = {"Content-Type": "application/json"}
	if args.secret:
		headers[args.header_name] = args.secret

	print(f"POST {args.url}")
	print(json.dumps(payload, indent=2, ensure_ascii=False))

	response = requests.post(args.url, json=payload, headers=headers, timeout=args.timeout)
	print(f"\nStatus: {response.status_code}")
	print("Response headers:")
	for key, value in response.headers.items():
		print(f"  {key}: {value}")

	print("\nResponse body:")
	print(response.text)

	return 0 if response.ok else 1


if __name__ == "__main__":
	raise SystemExit(main())