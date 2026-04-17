# IT Support Bot Web UI

This project is a lightweight Flask web interface for an internal IT support chatbot.

The UI sends user messages to an n8n webhook and displays the returned answer in a chat layout.

## What it does

- Provides a simple chat interface for IT support requests
- Sends requests to n8n using `chatInput` and `sessionId`
- Shows bot responses in the same conversation
- Keeps local chat history per browser session

## Tech stack

- Python 3.10+
- Flask
- Requests
- python-dotenv

## Project structure

- `app.py`: Flask app, routes, webhook forwarding
- `config.py`: environment-based configuration
- `templates/`: HTML templates
- `static/`: CSS, JavaScript, and images

## Local setup

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a local `.env` file in the project root.
5. Start the app:

```bash
python app.py
```

Then open:

- `http://127.0.0.1:5000`

## Environment variables

Set these values in your local `.env` file:

```env
FLASK_DEBUG=0
SECRET_KEY=replace-with-local-secret
N8N_WEBHOOK_URL=https://your-n8n-host/webhook/your-path
N8N_TIMEOUT_SECONDS=120
MAX_MESSAGE_LENGTH=500
```

## Webhook payload

The app sends this JSON body to n8n:

```json
{
  "chatInput": "User message",
  "sessionId": "browser-session-id"
}
```

## Notes

- Do not commit `.env` files.
- Keep webhook URLs and secrets local.
- If n8n takes longer than the configured timeout, the UI will show a timeout message.

## License

See `LICENSE`.
