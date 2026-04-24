# restaurant-line-bot

LINE Messaging API bot for collecting restaurant-related URLs and writing them to Google Sheets.

## Features

- FastAPI service with `GET /` health check and `POST /callback` LINE webhook.
- LINE webhook signature validation.
- URL extraction from text messages.
- Source detection for Facebook, Instagram, YouTube, Google Maps, and Other.
- Google Sheets append with Taipei timestamp and LINE source identifiers.
- Render deployment config.

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill in `.env`:

```env
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
LINE_ADMIN_USER_ID=
GOOGLE_SHEET_ID=1Slva6CqO2sJ4lyRjkR8U1RlS9oaF_dVbAS312rG9ffo
GOOGLE_SERVICE_ACCOUNT_JSON_PATH=service_account.json
APP_ENV=development
```

For local Google Sheets access, put the service account JSON at `service_account.json`.
For Render, set `GOOGLE_SERVICE_ACCOUNT_JSON` to the full service account JSON content.

## Google Sheets

Expected headers:

```text
id
created_at
group_id
room_id
user_id
source
original_url
status
restaurant_name
address
google_maps_url
note
```

Share the spreadsheet with the service account `client_email`.

## Run Locally

```bash
uvicorn app:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/
```

Expected response:

```json
{
  "status": "ok",
  "service": "restaurant-line-bot"
}
```

## LINE Webhook

Deploy the app and set the LINE webhook URL:

```text
https://<render-service-url>/callback
```

Example:

```text
https://restaurant-line-bot.onrender.com/callback
```

Disable LINE auto-reply and greeting messages, then enable webhook.

## Render

`render.yaml` uses:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

Required Render environment variables:

```text
LINE_CHANNEL_SECRET
LINE_CHANNEL_ACCESS_TOKEN
GOOGLE_SHEET_ID
GOOGLE_SERVICE_ACCOUNT_JSON
APP_ENV=production
```

## Test

```bash
pytest
```
