# LINE Bot Webhook 400 Bad Request Debug Guide

## 目前狀態

目前 Render 後端已經成功部署，首頁健康檢查可以正常回應：

```json
{"status":"ok","service":"restaurant-line-bot"}
```

這代表：

- Render Web Service 已建立成功
- FastAPI 應用程式可以正常啟動
- `/` health check endpoint 正常
- 問題不是 Render 主機完全無法啟動

但在 LINE Developers Console 按下 **Verify** 時，出現：

```text
The webhook returned an HTTP status code other than 200. (400 Bad Request)
```

這代表 LINE 有成功打到你的 webhook URL：

```text
https://restaurant-line-bot-351d.onrender.com/callback
```

但是 `/callback` endpoint 回傳了 `400 Bad Request`。

---

## 問題判斷

目前問題集中在：

```text
/callback endpoint 收到 LINE 的 POST request 後，程式主動回傳 400。
```

最常見原因有兩類：

1. `LINE_CHANNEL_SECRET` 與 LINE Developers Console 目前的 Channel secret 不一致。
2. `/callback` 程式邏輯太嚴格，把 LINE Verify request、非文字訊息、沒有 URL 的訊息誤判為錯誤，導致回傳 400。

---

## Webhook URL 檢查

LINE Developers Console 的 Webhook URL 應該是：

```text
https://restaurant-line-bot-351d.onrender.com/callback
```

不是：

```text
https://restaurant-line-bot-351d.onrender.com
```

目前已確認 Webhook URL 已經加上 `/callback`，這部分是正確的。

---

## Render 健康檢查

請在瀏覽器打開：

```text
https://restaurant-line-bot-351d.onrender.com/
```

預期應該看到：

```json
{"status":"ok","service":"restaurant-line-bot"}
```

若此頁正常，代表 Render 與 FastAPI 主程式基本可用。

---

## 優先排查項目一：LINE_CHANNEL_SECRET 是否正確

LINE webhook 會透過 `X-Line-Signature` 驗證 request 來源。

如果 Render 環境變數中的：

```env
LINE_CHANNEL_SECRET
```

和 LINE Developers Console → Basic settings 中目前顯示的 Channel secret 不一致，程式會回傳 400。

### 檢查位置

到 Render：

```text
restaurant-line-bot
→ Environment
```

確認以下變數：

```env
LINE_CHANNEL_SECRET=目前 LINE Developers Console 顯示的 Channel secret
LINE_CHANNEL_ACCESS_TOKEN=目前 Messaging API 顯示的 long-lived Channel access token
GOOGLE_SHEET_ID=1Slva6CqO2sJ4lyRjkR8U1RlS9oaF_dVbAS312rG9ffo
GOOGLE_SERVICE_ACCOUNT_JSON=整份 Google service account JSON
APP_ENV=production
```

若有修改任何環境變數，必須重新部署：

```text
Manual Deploy
→ Deploy latest commit
```

---

## 優先排查項目二：Render Logs

請到 Render 左側選單：

```text
Logs
```

然後回 LINE Developers Console 再按一次：

```text
Verify
```

觀察 Render Logs。

### 如果看到 InvalidSignatureError

例如：

```text
InvalidSignatureError
Invalid signature
```

代表：

```text
LINE_CHANNEL_SECRET 設錯或與目前 Channel 不一致。
```

解法：

1. 到 LINE Developers Console → Basic settings 複製最新 Channel secret。
2. 到 Render → Environment 更新 `LINE_CHANNEL_SECRET`。
3. 重新 Deploy。
4. 再按 LINE Verify。

---

### 如果看到 No handler / Bad request / Missing event

例如：

```text
BadRequest
No handler found
No message event
No text message
No URL found
```

代表 `/callback` 程式邏輯太嚴格。

正確邏輯應該是：

```text
只要 signature 正確，就應回傳 200 OK。
```

不應該因為以下情況回 400：

- event 不是 message event
- message 不是文字訊息
- 文字訊息沒有 URL
- 不是 group source
- LINE Verify request 沒有餐廳連結

---

## 正確的 `/callback` 行為

`/callback` endpoint 應該符合以下規則：

1. 接收 LINE webhook 的 POST request。
2. 讀取 request body。
3. 讀取 header：`X-Line-Signature`。
4. 使用 `LINE_CHANNEL_SECRET` 驗證 signature。
5. 只有 signature 驗證失敗時回傳 400。
6. 如果 signature 正確，無論 event 內容是否需要處理，都回傳 200。
7. 如果沒有文字訊息，忽略並回 200。
8. 如果文字訊息沒有 URL，忽略並回 200。
9. 如果有 URL，才進行：
   - URL 抽取
   - 來源平台判斷
   - Google Sheets 寫入
   - LINE 回覆

---

## 建議的 FastAPI callback 寫法概念

以下是概念範例，實際請 Windsurf 依目前專案結構整合：

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from linebot.exceptions import InvalidSignatureError

app = FastAPI()

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_text = body.decode("utf-8")

    try:
        handler.handle(body_text, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        # 視專案策略而定：
        # 若希望 LINE 不重送，可回 200 並記錄錯誤。
        # 若希望 LINE 知道處理失敗，可回 500。
        print(f"Callback processing error: {e}")
        return PlainTextResponse("OK", status_code=200)

    return PlainTextResponse("OK", status_code=200)
```

重點：

```text
signature 正確 → 回 200
signature 錯誤 → 回 400
```

---

## 請 Windsurf 修正的任務指令

請直接複製以下內容貼給 Windsurf：

```text
目前 Render 首頁健康檢查正常：
https://restaurant-line-bot-351d.onrender.com/
可以回傳：
{"status":"ok","service":"restaurant-line-bot"}

但 LINE Developers Console Verify Webhook 時，Webhook URL：
https://restaurant-line-bot-351d.onrender.com/callback
回傳 400 Bad Request。

請檢查並修正 /callback endpoint。

要求：
1. /callback 必須接受 LINE webhook 的 POST request。
2. 必須讀取 X-Line-Signature header。
3. 必須使用 LINE_CHANNEL_SECRET 驗證 webhook signature。
4. 只有 signature 驗證失敗時，才回傳 400。
5. 如果 signature 正確，不管 event 是否為 message event，都必須回傳 200 OK。
6. 如果 event 沒有文字訊息，不要回 400，直接忽略並回 200。
7. 如果文字訊息沒有 URL，不要回覆 LINE，但仍然回 200。
8. 如果文字訊息有 URL，才做 URL 抽取、來源判斷、Google Sheets 寫入、LINE 回覆。
9. 加入清楚 logs，至少包含：
   - callback received
   - signature valid / invalid
   - request body length
   - number of events
   - event type
   - source type
   - message text
   - extracted urls
   - Google Sheets write success / failure
10. 確認 LINE Developers Console 的 Verify 可以通過。
11. 修正後 commit 並 push 到 GitHub，讓 Render 自動重新部署。
12. 不要把任何真實 secret、token、Google private key 寫入程式碼或 README。
```

---

## Render 重新部署後的測試流程

Windsurf 修正並 push 後，Render 會自動部署。

請依序測試：

### 1. 測試首頁

打開：

```text
https://restaurant-line-bot-351d.onrender.com/
```

預期：

```json
{"status":"ok","service":"restaurant-line-bot"}
```

---

### 2. LINE Developers Verify

到 LINE Developers Console：

```text
Messaging API
→ Webhook settings
→ Verify
```

預期：

```text
Success
```

---

### 3. 確認 Use webhook 開啟

```text
Use webhook = ON
```

---

### 4. LINE 群組實測

把 Bot 加入 LINE 測試群組，貼上：

```text
https://www.facebook.com/share/r/1DqziX2Whg/?mibextid=wwXIfr
```

預期 LINE 回覆：

```text
已收藏餐廳連結 #1
```

Google Sheet 應新增一列。

---

## Google Sheets 權限確認

Google Sheet：

```text
https://docs.google.com/spreadsheets/d/1Slva6CqO2sJ4lyRjkR8U1RlS9oaF_dVbAS312rG9ffo/edit
```

必須分享給 service account email，權限設為「編輯者」。

目前 service account email：

```text
msafptogoogle@precise-tenure-227410.iam.gserviceaccount.com
```

---

## 安全提醒

目前以下資訊曾經在對話或測試過程中出現，正式上線後建議重新產生：

- LINE Channel secret
- LINE Channel access token
- Google service account JSON private key

建議正式確認系統可運作後：

1. 重新產生 LINE Channel access token。
2. 如有必要，重新產生 LINE Channel secret。
3. 在 Google Cloud Console 重新建立 service account JSON key。
4. 刪除舊的 Google service account key。
5. 更新 Render Environment Variables。
6. 重新部署 Render。

不要把任何 secret 放入：

- GitHub
- README
- Windsurf 文件
- LINE 群組
- 公開截圖

---

## 目前待辦清單

```text
1. 到 Render Logs 檢查 LINE Verify 時的錯誤訊息。
2. 確認是否為 InvalidSignatureError。
3. 若是，修正 Render 的 LINE_CHANNEL_SECRET。
4. 若不是，請 Windsurf 修正 /callback endpoint 邏輯。
5. 修正後 push 到 GitHub。
6. Render 自動重新部署。
7. 確認首頁健康檢查正常。
8. 回 LINE Developers Console 按 Verify。
9. Verify 成功後，確認 Use webhook = ON。
10. LINE 群組貼連結實測。
11. 確認 Google Sheet 是否新增資料。
```
