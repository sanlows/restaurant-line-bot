# Deployment Guide

## Render

1. Create a new Render web service from this repository.
2. Use Python environment.
3. Build command:

```bash
pip install -r requirements.txt
```

4. Start command:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

5. Set environment variables:

```text
APP_ENV=production
LINE_CHANNEL_SECRET=<from LINE Developers>
LINE_CHANNEL_ACCESS_TOKEN=<from LINE Developers>
GOOGLE_SHEET_ID=1Slva6CqO2sJ4lyRjkR8U1RlS9oaF_dVbAS312rG9ffo
GOOGLE_SERVICE_ACCOUNT_JSON=<full service account JSON>
```

## LINE Developers

Set the Messaging API webhook URL:

```text
https://<render-service-url>/callback
```

Then:

- Enable webhook.
- Disable auto-reply messages.
- Disable greeting messages.
- Click Verify.

## Google Sheets

1. Enable Google Sheets API in Google Cloud.
2. Create a service account.
3. Share the spreadsheet with the service account `client_email`.
4. Keep local credentials in `service_account.json`, or use `GOOGLE_SERVICE_ACCOUNT_JSON` in Render.
