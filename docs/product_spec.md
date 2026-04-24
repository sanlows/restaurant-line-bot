# Product Spec

## MVP Goal

Build a LINE bot that records restaurant-related URLs from chat messages into Google Sheets.

## User Flow

1. User sends one or more URLs to the bot.
2. Bot extracts URLs and detects their source.
3. Bot appends one row per URL to Google Sheets.
4. Bot replies with the created record id or ids.

## Supported Sources

| URL pattern | source |
|---|---|
| `facebook.com`, `fb.watch`, `fb.com` | Facebook |
| `instagram.com` | Instagram |
| `youtube.com`, `youtu.be` | YouTube |
| `maps.google.com`, `google.com/maps`, `goo.gl/maps` | Google Maps |
| Other URLs | Other |

## Replies

Single URL:

```text
已收到並記錄 #12
```

Multiple URLs:

```text
已收到 3 筆並記錄：#12, #13, #14
```

No URL:

```text
請傳送餐廳貼文或地圖網址，我會幫你記錄。
```
