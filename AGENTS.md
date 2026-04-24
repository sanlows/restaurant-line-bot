# AGENTS

This project is a Python FastAPI LINE Messaging API bot for collecting restaurant-related URLs and saving them to Google Sheets.

## Local conventions

- Keep secrets in `.env` or hosting environment variables only.
- Do not commit `service_account.json`.
- Prefer small, testable services under `services/`.
- Keep webhook behavior in `app.py`; keep parsing and persistence logic outside it.

## Verification

Run:

```bash
pytest
```

Start locally:

```bash
uvicorn app:app --reload
```
