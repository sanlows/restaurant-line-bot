# Google Sheets Schema

| Column | Required | Notes |
|---|---:|---|
| `id` | Yes | Sequential id based on current sheet row count. |
| `created_at` | Yes | `Asia/Taipei`, format `YYYY-MM-DD HH:mm:ss`. |
| `group_id` | Yes | LINE group id for group messages, otherwise empty. |
| `room_id` | Yes | LINE room id for room messages, otherwise empty. |
| `user_id` | Yes | LINE user id when available. |
| `source` | Yes | Facebook, Instagram, YouTube, Google Maps, or Other. |
| `original_url` | Yes | URL as sent by the user, after punctuation cleanup. |
| `status` | Yes | Defaults to `received`. |
| `restaurant_name` | No | Reserved for future enrichment. |
| `address` | No | Reserved for future enrichment. |
| `google_maps_url` | No | Reserved for future enrichment. |
| `note` | No | Reserved for manual notes or future commands. |
