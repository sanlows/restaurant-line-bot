# restaurant-line-bot

LINE Messaging API bot for collecting restaurant-related URLs, enriching restaurant metadata when possible, and writing searchable records to Google Sheets.

## Features

- FastAPI service with `GET /` health check and `POST /callback` LINE webhook.
- LINE webhook signature validation.
- URL extraction from text messages.
- Source detection for Facebook, Instagram, YouTube, Google Maps, and Other.
- Google Sheets append with Taipei timestamp and LINE source identifiers.
- Group commands for recent records, keyword search, and manual record fixes.
- Best-effort metadata and Google Places enrichment.
- Render deployment config.

To save a link, start the LINE message with `存`:

```text
存 https://www.instagram.com/reel/xxxxx
```

Plain pasted links are ignored.

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
GOOGLE_PLACES_API_KEY=
```

For local Google Sheets access, put the service account JSON at `service_account.json`.
For Render, set `GOOGLE_SERVICE_ACCOUNT_JSON` to the full service account JSON content.
`GOOGLE_PLACES_API_KEY` is optional. If it is not set, the bot still collects links, stores metadata when available, supports search, and supports manual fixes.

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
category
city
district
address
google_maps_url
note
raw_title
raw_description
parse_confidence
```

Share the spreadsheet with the service account `client_email`.
If an older sheet exists, the app preserves existing headers and appends any missing v2 headers.

## LINE Commands

Recent records:

```text
list
查 最近
```

Keyword search:

```text
查 板橋
查 燒肉
查 火鍋
```

Manual fixes for records that could not be parsed automatically:

```text
命名 #3 阿城鵝肉
分類 #3 台式小吃
地區 #3 板橋
```

Queries are isolated by LINE context:

- Group messages only search the same `group_id`.
- Room messages only search the same `room_id`.
- 1:1 messages only search the same `user_id`.

Automatic parsing is best effort. Facebook and Instagram may block metadata access; when parsing fails, the original URL is still saved and the record is marked `待解析`.

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

Optional Render environment variable:

```text
GOOGLE_PLACES_API_KEY
```

## Deployment Check

After deployment:

1. Open `https://<render-service-url>/` and confirm the health check returns `{"status":"ok","service":"restaurant-line-bot"}`.
2. Set LINE webhook URL to `https://<render-service-url>/callback`.
3. Verify the webhook in LINE Developers.
4. In a LINE group, test a Facebook or Instagram URL.
5. Test `list`, `查 最近`, and a keyword search such as `查 板橋`.
6. Test manual fixes with `命名 #id`, `分類 #id`, and `地區 #id`.

## Test

```bash
pytest
```
