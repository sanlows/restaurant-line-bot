# 餐廳記錄群組 LINE Bot｜Windsurf 自動開發規格書

> 目的：讓 LINE 群組中的任何成員貼上 Facebook / Instagram / YouTube / Google Maps / 其他餐廳推薦連結時，Bot 自動偵測、記錄到 Google Sheets，並在群組中簡短回覆收藏結果。

---

## 0.1 目前 Render 部署狀態更新（2026-04-24）

目前 Render Web Service 已建立，但尚未成功部署。

Render 顯示訊息：

```text
Your service has not been deployed because the GitHub repository is empty. Make a commit before retrying.
```

這代表 Render 服務本身已建立，但 GitHub repository 目前沒有任何程式碼 commit，因此 Render 無法 build / deploy。

目前已取得的 Render Service URL：

```text
https://restaurant-line-bot-351d.onrender.com
```

正式給 LINE 使用的 Webhook URL 應為：

```text
https://restaurant-line-bot-351d.onrender.com/callback
```

但在 GitHub repo 有程式碼並成功部署前，請先不要在 LINE Developers Console 按 Verify；即使填入，也會因為後端尚未啟動而驗證失敗。

下一步必須先完成：

```text
Windsurf 建立專案程式碼
→ git commit
→ git push 到 GitHub repository：sanlows/restaurant-line-bot
→ 回 Render 執行 Manual Deploy
→ 確認 https://restaurant-line-bot-351d.onrender.com/ 可回傳健康檢查
→ 再填 LINE Webhook URL：https://restaurant-line-bot-351d.onrender.com/callback
```

Render 目前建議設定：

| 項目 | 值 |
|---|---|
| Runtime / Language | Python 3 |
| Branch | main |
| Root Directory | 空白，除非專案不是放在 repo 根目錄 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app:app --host 0.0.0.0 --port $PORT` |

Render Environment Variables 必須設定：

```env
LINE_CHANNEL_SECRET=請填在 Render，不要寫入程式碼
LINE_CHANNEL_ACCESS_TOKEN=請填在 Render，不要寫入程式碼
GOOGLE_SHEET_ID=1Slva6CqO2sJ4lyRjkR8U1RlS9oaF_dVbAS312rG9ffo
GOOGLE_SERVICE_ACCOUNT_JSON=請貼整份 service account JSON，不要寫入程式碼
APP_ENV=production
```

Google Service Account 的 `client_email` 也必須已加入 Google Sheet 共用權限，角色為「編輯者」。


## 0. 重要安全提醒

請勿將任何真實密鑰寫入 GitHub、README、測試檔或程式碼中。

使用者先前已提供過 LINE Channel Secret 與 Channel Access Token，這些都屬於敏感資訊。正式上線前建議重新產生新的 Token / Secret，並只放在 `.env` 或部署平台的 Environment Variables。

本專案所有敏感資訊都必須透過環境變數讀取。

---

## 1. 專案名稱

```text
restaurant-line-bot
```

LINE Bot 顯示名稱：

```text
餐廳記錄群組
```

Bot basic ID：

```text
@555hrtwa
```

---

## 2. 已知 LINE Channel 資訊

```env
LINE_CHANNEL_ID=2009889654
LINE_CHANNEL_SECRET=請放在 .env，不要寫入程式碼
LINE_CHANNEL_ACCESS_TOKEN=請放在 .env，不要寫入程式碼
LINE_ADMIN_USER_ID=U120a5191516accb8b3a36b80392e3331
```

LINE 官方帳號設定目前狀態：

| 項目 | 狀態 / 建議 |
|---|---|
| Channel type | Messaging API / Bot |
| Allow bot to join group chats | Enabled |
| Auto-reply messages | 建議 Disabled |
| Greeting messages | 建議 Disabled |
| Webhook | 後端部署完成後 Enabled |
| Webhook URL | 部署完成後填入 `https://<render-service-url>/callback` |

---

## 3. Google Sheet 資訊

Google Sheet URL：

```text
https://docs.google.com/spreadsheets/d/1Slva6CqO2sJ4lyRjkR8U1RlS9oaF_dVbAS312rG9ffo/edit?usp=sharing
```

Google Sheet ID：

```env
GOOGLE_SHEET_ID=1Slva6CqO2sJ4lyRjkR8U1RlS9oaF_dVbAS312rG9ffo
```

第一版工作表欄位固定如下：

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

第一版 MVP 寫入欄位：

```text
id
created_at
group_id
room_id
user_id
source
original_url
status
```

其餘欄位可先留空：

```text
restaurant_name
address
google_maps_url
note
```

---

## 4. 第一版 MVP 目標

完成以下最小可用流程：

```text
LINE 群組有人貼餐廳連結
→ LINE webhook 把訊息送到後端 `/callback`
→ 後端驗證 LINE signature
→ 偵測訊息中的 URL
→ 判斷來源平台
→ 寫入 Google Sheets
→ Bot 回覆群組「已收藏餐廳連結 #id」
```

### MVP 功能需求

1. 建立 Python FastAPI 專案。
2. 提供 `/callback` endpoint 給 LINE Webhook 使用。
3. 驗證 LINE webhook signature。
4. 使用 LINE Channel Access Token 回覆訊息。
5. 當收到 LINE 文字訊息時，偵測訊息中的 URL。
6. 支援一則訊息中出現一個或多個 URL。
7. 如果訊息沒有 URL，不要回覆。
8. 判斷 URL 來源平台。
9. 將資料寫入 Google Sheets。
10. `status` 預設為 `已收藏`。
11. 回覆 LINE：
    - 一個 URL：`已收藏餐廳連結 #id`
    - 多個 URL：`已收藏 N 筆餐廳連結：#id1, #id2`
12. 不要把真實 token、secret、Google key 寫死。
13. 建立 `.env.example`、`README.md`、`requirements.txt`。
14. 建立基本單元測試，至少測試 URL 抽取與來源平台判斷。

---

## 5. URL 來源判斷規則

| URL 網域 | source |
|---|---|
| `facebook.com` / `fb.watch` / `fb.com` | Facebook |
| `instagram.com` | Instagram |
| `youtube.com` / `youtu.be` | YouTube |
| `maps.google.com` / `google.com/maps` / `goo.gl/maps` | Google Maps |
| 其他 | Other |

---

## 6. 建議技術選型

```text
Python 3.11+
FastAPI
uvicorn
python-dotenv
line-bot-sdk
gspread
google-auth
pytest
```

---

## 7. 建議專案結構

```text
restaurant-line-bot/
├─ app.py
├─ requirements.txt
├─ .env.example
├─ .gitignore
├─ README.md
├─ AGENTS.md
├─ render.yaml
├─ services/
│  ├─ line_service.py
│  ├─ sheets_service.py
│  ├─ url_parser.py
│  └─ id_generator.py
├─ config/
│  └─ settings.py
├─ tests/
│  ├─ test_url_parser.py
│  └─ test_source_detector.py
└─ docs/
   ├─ product_spec.md
   ├─ google_sheets_schema.md
   └─ deployment_guide.md
```

---

## 8. `.env.example` 範例

```env
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
LINE_ADMIN_USER_ID=

GOOGLE_SHEET_ID=1Slva6CqO2sJ4lyRjkR8U1RlS9oaF_dVbAS312rG9ffo
GOOGLE_SERVICE_ACCOUNT_JSON_PATH=service_account.json

APP_ENV=development
```

第二階段若要接 Google Places，再加入：

```env
GOOGLE_PLACES_API_KEY=
```

---

## 9. Google Service Account 設定需求

1. 建立 Google Cloud Project。
2. 啟用 Google Sheets API。
3. 建立 Service Account。
4. 下載 JSON 憑證檔。
5. 檔名建議：

```text
service_account.json
```

6. 將 `service_account.json` 放在專案根目錄。
7. 將 `service_account.json` 中的 `client_email` 加入 Google Sheet 共用權限，角色設為「編輯者」。
8. `service_account.json` 必須加入 `.gitignore`，不得提交到 GitHub。

---

## 10. `.gitignore` 必須包含

```gitignore
.env
service_account.json
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
.env.*
```

---

## 11. FastAPI endpoint 需求

### `GET /`

健康檢查用，回傳：

```json
{
  "status": "ok",
  "service": "restaurant-line-bot"
}
```

### `POST /callback`

LINE webhook endpoint。

功能：

1. 讀取 request body。
2. 驗證 `X-Line-Signature`。
3. 處理 message event。
4. 如果是文字訊息，抽取 URL。
5. 如果沒有 URL，不回覆。
6. 如果有 URL，寫入 Google Sheets。
7. 回覆收藏結果。

---

## 12. Google Sheets 寫入規則

### id 產生方式

第一版可用簡單遞增 ID：

```text
目前 Sheet 已有資料列數 - 1 + 1
```

也就是第一筆資料為 `1`，第二筆為 `2`。

### created_at

使用台灣時間 `Asia/Taipei`。

建議格式：

```text
YYYY-MM-DD HH:mm:ss
```

### group_id / room_id / user_id

依 LINE event source 判斷：

- group message：寫入 `group_id`，`room_id` 留空。
- room message：寫入 `room_id`，`group_id` 留空。
- 1:1 message：`group_id` 與 `room_id` 皆可留空。
- `user_id` 若 event 有提供則寫入。

---

## 13. LINE 回覆規則

### 一個 URL

```text
已收藏餐廳連結 #12
```

### 多個 URL

```text
已收藏 3 筆餐廳連結：#12, #13, #14
```

### 沒有 URL

不回覆，避免群組太吵。

---

## 14. Render 部署需求

啟動指令建議：

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

若建立 `render.yaml`，可使用下列概念：

```yaml
services:
  - type: web
    name: restaurant-line-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: APP_ENV
        value: production
      - key: LINE_CHANNEL_SECRET
        sync: false
      - key: LINE_CHANNEL_ACCESS_TOKEN
        sync: false
      - key: GOOGLE_SHEET_ID
        value: 1Slva6CqO2sJ4lyRjkR8U1RlS9oaF_dVbAS312rG9ffo
      - key: GOOGLE_SERVICE_ACCOUNT_JSON
        sync: false
```

注意：Render 不一定適合用檔案路徑保存 `service_account.json`。建議支援兩種模式：

1. 本機開發：讀取 `GOOGLE_SERVICE_ACCOUNT_JSON_PATH=service_account.json`
2. Render 部署：讀取 `GOOGLE_SERVICE_ACCOUNT_JSON` 環境變數，內容是整份 service account JSON 字串

請 Windsurf 實作時優先支援這兩種模式。

---

## 15. Webhook URL 說明

Webhook URL 不是 LINE 自動產生的，也不是 Windsurf 本身自動產生的。

它會在你把後端部署到 Render / Railway / Cloud Run 之後，由部署平台提供公開網址。

如果 Render service name 是：

```text
restaurant-line-bot
```

常見網址可能是：

```text
https://restaurant-line-bot-351d.onrender.com
```

但是否真的能拿到這個網址，取決於 Render 上該 service name 是否可用。

LINE Webhook URL 應填：

```text
https://restaurant-line-bot-351d.onrender.com/callback
```

若 Render 實際產生的網址不同，請以 Render 顯示的實際網址為準，並加上 `/callback`。

---

## 16. 開發順序

### Step 1：建立專案骨架

建立 FastAPI 專案、services、config、tests、docs、README、AGENTS.md。

### Step 2：實作 URL 抽取與來源判斷

先不接 LINE，也不接 Google Sheets，單純完成：

```text
輸入文字 → 抽出 URL list → 判斷 source
```

並建立 pytest 測試。

### Step 3：實作 Google Sheets 寫入

完成 `sheets_service.py`：

- 連線 Google Sheets
- 確認表頭存在
- 取得下一個 id
- append row

### Step 4：實作 LINE webhook

完成 `/callback`：

- 驗證 LINE signature
- 處理 message event
- 抽 URL
- 寫入 Sheet
- 回覆 LINE

### Step 5：本機測試

用 pytest 測試：

```bash
pytest
```

啟動本機：

```bash
uvicorn app:app --reload
```

### Step 6：部署到 Render

設定環境變數：

```text
LINE_CHANNEL_SECRET
LINE_CHANNEL_ACCESS_TOKEN
GOOGLE_SHEET_ID
GOOGLE_SERVICE_ACCOUNT_JSON 或 GOOGLE_SERVICE_ACCOUNT_JSON_PATH
APP_ENV=production
```

### Step 7：取得 Render 公開 URL

例如：

```text
https://restaurant-line-bot-351d.onrender.com
```

### Step 8：回填 LINE Webhook URL

到 LINE Developers Console：

```text
Messaging API → Webhook settings → Webhook URL
```

填入：

```text
https://restaurant-line-bot-351d.onrender.com/callback
```

然後按：

```text
Update → Verify
```

### Step 9：開啟 Webhook

到 LINE Official Account Manager：

```text
Webhook = ON
```

### Step 10：加入群組測試

測試訊息：

```text
這間看起來不錯 https://www.facebook.com/share/r/xxxxx
```

預期 Bot 回覆：

```text
已收藏餐廳連結 #1
```

Google Sheet 應新增一列。

---

## 17. 第二階段功能：Google Places 自動補資料

第一版跑通後再做。

目標：

1. 如果是 Google Maps URL，嘗試解析或展開網址。
2. 如果可以取得店名或地點文字，使用 Google Places API 查詢。
3. 補上：
   - restaurant_name
   - address
   - google_maps_url
   - rating
   - price_level
4. Google Sheet 欄位可擴充。

---

## 18. 第三階段功能：查詢指令

未來可以支援：

```text
查 最近
查 板橋
查 燒肉
查 未整理
已吃過 #15
```

第一版請不要實作，避免範圍過大。

---

## 19. 給 Windsurf 的初始任務 Prompt

請直接將以下內容貼給 Windsurf Cascade：

```text
請依照本檔案規格，建立 restaurant-line-bot 專案。

優先完成第一版 MVP：
LINE 群組貼連結 → FastAPI webhook 收到 → 抽取 URL → 判斷來源 → 寫入 Google Sheets → LINE 回覆已收藏。

請注意：
1. 不要把任何真實 token、secret、service account JSON 寫入程式碼。
2. 所有設定都從 .env 或部署平台的 Environment Variables 讀取。
3. 請先建立完整專案骨架。
4. 請建立測試，至少包含 URL 抽取與來源平台判斷。
5. 請建立 README，說明本機啟動、Google Sheets 設定、Render 部署、LINE Webhook 設定。
6. 請讓 Render 可用 `uvicorn app:app --host 0.0.0.0 --port $PORT` 啟動。
7. 請支援本機使用 `GOOGLE_SERVICE_ACCOUNT_JSON_PATH`，部署時使用 `GOOGLE_SERVICE_ACCOUNT_JSON`。

完成後請回報：
- 建立了哪些檔案
- 如何設定 .env
- 如何本機測試
- 如何部署到 Render
- LINE Webhook URL 應該填什麼
```

---

## 20. 驗收標準

第一版完成後，必須符合：

1. `GET /` 回傳健康檢查 JSON。
2. URL 抽取測試通過。
3. 來源平台判斷測試通過。
4. LINE webhook 可通過 LINE Verify。
5. LINE 群組貼 URL 時，Google Sheet 新增資料。
6. Bot 在群組回覆收藏結果。
7. 沒有 URL 的一般聊天不回覆。
8. Git repo 中沒有任何真實 secret。

