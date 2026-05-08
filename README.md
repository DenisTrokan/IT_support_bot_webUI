# IT Support Bot Web UI

This project is a lightweight Flask web interface for an internal IT support chatbot.

The UI uses Microsoft Entra ID for sign-in, then sends user messages to the new n8n webhook through Flask and displays the returned answer in a chat layout.

## What it does

- Provides a simple chat interface for IT support requests
- Sends requests to n8n using `chatInput` and `sessionId`
- Uses Flask as the only browser-facing chat entry point (`/api/chat`)
- Forwards verified Microsoft claims and a shared secret header to the n8n webhook
- Shows bot responses in the same conversation
- Keeps local chat history per browser session

## Tech stack

- Python 3.10+
- Flask
- Authlib
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
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-app-client-id
AZURE_CLIENT_SECRET=your-app-client-secret
AZURE_REDIRECT_URI=https://your-app-domain/auth/callback
AZURE_POST_LOGOUT_REDIRECT_URI=https://your-app-domain/
AZURE_SCOPES=openid profile email
N8N_WEBHOOK_URL=https://your-n8n-host/webhook/your-path
N8N_INTERNAL_SECRET=replace-with-a-shared-secret
N8N_INTERNAL_SECRET_HEADER=X-Webhook-Secret
N8N_TIMEOUT_SECONDS=120
MAX_MESSAGE_LENGTH=500
```

## Webhook payload

The app sends this JSON body to the n8n chat webhook:

```json
{
  "chatInput": "User message",
  "sessionId": "browser-session-id",
  "requestId": "backend-generated-request-id",
  "user": {
    "name": "Signed-in user",
    "email": "user@company.com",
    "oid": "azure-object-id",
    "tenantId": "azure-tenant-id",
    "preferredUsername": "user@company.com",
    "roles": [],
    "groups": []
  },
  "userName": "Signed-in user",
  "userEmail": "user@company.com",
  "userOid": "azure-object-id",
  "tenantId": "azure-tenant-id",
  "userRoles": [],
  "userGroups": []
}
```

The webhook response can be plain text or JSON. When JSON is used, Flask will try to extract a readable reply from common fields such as `reply`, `message`, `text`, `output`, `response`, or `answer`.

## Notes

- Do not commit `.env` files.
- Keep Azure credentials, webhook URLs, and shared secrets local.
- Protect the n8n webhook with a shared secret or private network path.
- If n8n takes longer than the configured timeout, the UI will show a timeout message.

## License

See `LICENSE`.
