# restaurant-line-bot 目前開發進度

> 最後更新：2026-04-27
>
> 本文件用來記錄目前已實測完成的功能、已知問題，以及下一階段開發方向。若與較早期的規格文件衝突，請以本文件與 `restaurant_line_bot_v2_feature_plan.md` 的最新版為準。

---

## 1. 目前整體狀態

目前專案已從 v1 MVP 進入 v2 功能擴充階段。

已確認：

```text
LINE 群組 / 聊天室
→ 使用者輸入「存 URL」或查詢指令
→ Bot 可回覆結果
→ Google Sheets 可保存資料
→ Render 服務已可正常運作
```

目前 Render 服務：

```text
https://restaurant-line-bot-351d.onrender.com
```

LINE Webhook URL：

```text
https://restaurant-line-bot-351d.onrender.com/callback
```

Google Sheet：

```text
https://docs.google.com/spreadsheets/d/1Slva6CqO2sJ4lyRjkR8U1RlS9oaF_dVbAS312rG9ffo/edit?usp=sharing
```

---

## 2. 已完成並實測成功的功能

### 2.1 連結收藏功能

已可使用以下格式收藏餐廳連結：

```text
存 https://www.instagram.com/p/DXYLjwgDG6q/?igsh=NmFwcDhzc3JiMnpl
```

實測回覆：

```text
已收藏餐廳連結 #4

目前無法自動判斷店名，已標記為待解析。
可之後輸入：
命名 #4 店名
分類 #4 類型
地區 #4 地區
```

目前確認：

- 可成功建立資料列。
- 可給予流水編號，例如 `#4`。
- Instagram 連結即使無法解析，也會保留原始 URL。
- 解析失敗時會標記為 `待解析`。
- 回覆會提示人工補救指令。

---

### 2.2 查詢最近收藏：`list`

已可輸入：

```text
list
```

實測回覆：

```text
最近收藏餐廳

#4｜Instagram
Instagram｜待解析
https://www.instagram.com/p/DXYLjwgDG6q/?igsh=NmFwcDhzc3JiMnpl
```

目前確認：

- `list` 指令已可觸發。
- 可顯示最近收藏紀錄。
- 可顯示 id、來源、狀態與原始連結。

待改善：

- 若 `restaurant_name` 空白，建議顯示 `尚未命名`，不要只顯示 `Instagram`。
- 回覆格式應統一為：店名 / 分類 / 地區 / 狀態 / 連結。

---

### 2.3 關鍵字查詢：`查 <keyword>`

已可輸入：

```text
查 定食
```

實測回覆：

```text
找到 1 筆「定食」相關收藏

#2｜よる-Yoru by Dennis Wang
定食｜ok
https://www.facebook.com/share/r/1DqziX2Whg/?mibextid=wwXIfr
```

目前確認：

- `查 關鍵字` 指令已可觸發。
- 可依關鍵字搜尋資料。
- 可回傳符合關鍵字的收藏。
- 已能顯示部分自動解析結果，例如店名與分類。

待改善：

- `ok` 不應出現在地區欄位。
- 若地區無法判斷，應顯示 `尚未判斷地區`。
- 搜尋欄位應確認包含：`restaurant_name`、`category`、`city`、`district`、`address`、`note`、`original_url`、`source`、`raw_title`、`raw_description`。

---

### 2.4 自動解析失敗 fallback

目前已確認：

```text
Instagram / Facebook 類連結若無法自動判斷店名
→ 不會中斷收藏
→ 原始 URL 仍保存
→ status 會變成「待解析」
→ Bot 會提示人工補救指令
```

這符合 v2 規劃中的核心要求：收藏流程優先，不可因解析失敗導致收藏失敗。

---

## 3. 目前已知問題與需修正項目

### 3.1 地區欄位顯示 `ok`

目前查詢結果出現：

```text
定食｜ok
```

這代表程式可能把 metadata parser 狀態、解析結果狀態、或其他欄位誤當作地區顯示。

修正要求：

```text
若 city / district / address 無法判斷，請顯示：尚未判斷地區
```

不應顯示：

```text
ok
None
null
unknown
true
false
空字串
```

---

### 3.2 `list` 顯示名稱需改善

目前：

```text
#4｜Instagram
Instagram｜待解析
URL
```

建議改為：

```text
#4｜尚未命名
分類：未分類
地區：尚未判斷地區
狀態：待解析
https://www.instagram.com/...
```

---

### 3.3 收藏觸發規則需確認

目前已確認 `存 URL` 可收藏。

需確認或新增：

```text
直接貼 URL → 也可自動收藏
存 URL → 也可自動收藏
普通聊天沒有 URL → 不回覆
```

這樣群組成員使用時會最直覺。

---

### 3.4 Google Places API 整合狀態需確認

目前查詢結果已出現店名與分類，代表已有部分解析能力。

但仍需確認：

```text
GOOGLE_PLACES_API_KEY 是否已接上
Google Maps URL 是否能自動補店名 / 地址 / 地圖
Facebook / Instagram metadata 是否有進一步送到 Places 查詢
```

---

## 4. 建議下一階段開發優先順序

### P0：穩定現有 v2 功能

1. 修正地區欄位顯示 `ok` 問題。
2. 統一 `list` 與 `查 關鍵字` 的回覆格式。
3. 確認 `直接貼 URL` 與 `存 URL` 都可收藏。
4. 確認沒有 URL 的普通聊天不回覆。
5. 加入測試，避免格式與欄位錯位再發生。

---

### P1：補強查詢體驗

支援並確認：

```text
list
查 最近
查 定食
查 板橋
查 燒肉
查 火鍋
```

查詢結果建議統一格式：

```text
#id｜餐廳名稱或尚未命名
分類：分類或未分類
地區：地區或尚未判斷地區
狀態：已解析 / 待解析 / 已收藏
https://...
```

---

### P2：補強自動解析能力

1. 強化 metadata parser。
2. 強化 rule-based restaurant extractor。
3. 確認 Google Places API optional integration。
4. Google Maps 連結優先自動補正式店名、地址、地圖。
5. Facebook / Instagram 若抓不到 metadata，仍保持 `待解析`。

---

### P3：人工補救指令驗收

需實測：

```text
命名 #4 店名
分類 #4 類型
地區 #4 地區
```

預期：

```text
Google Sheet 對應欄位被更新
Bot 回覆更新成功
list / 查詢結果立即顯示更新後資料
```

---

## 5. 給 Windsurf 的下一步任務

請將以下內容交給 Windsurf：

```text
目前 restaurant-line-bot 已經完成部分 v2 功能，請根據 docs/current_progress.md 進行修正與補強。

已實測成功：
1. 存 URL 可收藏連結。
2. 解析失敗時會標記待解析。
3. list 可顯示最近收藏。
4. 查 關鍵字 可搜尋資料。
5. 部分資料可顯示餐廳名稱與分類。

目前需優先修正：
1. 查詢結果中的地區欄位不應顯示 ok。
2. 若地區無法判斷，統一顯示「尚未判斷地區」。
3. 若 restaurant_name 空白，統一顯示「尚未命名」。
4. 若 category 空白，統一顯示「未分類」。
5. 統一 list / 查詢結果格式。
6. 確認「直接貼 URL」與「存 URL」都會觸發收藏。
7. 普通聊天沒有 URL 時不要回覆。
8. 補上測試，避免欄位錯位。

請不要把任何 token、secret、service account JSON 寫入程式碼或文件。
完成後請 commit 並 push，讓 Render 自動部署。
```

---

## 6. 目前驗收紀錄

### 6.1 `查 定食`

輸入：

```text
查 定食
```

實際回覆：

```text
找到 1 筆「定食」相關收藏

#2｜よる-Yoru by Dennis Wang
定食｜ok
https://www.facebook.com/share/r/1DqziX2Whg/?mibextid=wwXIfr
```

判定：

```text
查詢成功，但地區欄位顯示 ok 需修正。
```

---

### 6.2 `存 Instagram URL`

輸入：

```text
存 https://www.instagram.com/p/DXYLjwgDG6q/?igsh=NmFwcDhzc3JiMnpl
```

實際回覆：

```text
已收藏餐廳連結 #4

目前無法自動判斷店名，已標記為待解析。
可之後輸入：
命名 #4 店名
分類 #4 類型
地區 #4 地區
```

判定：

```text
收藏成功，解析失敗 fallback 正常。
```

---

### 6.3 `list`

輸入：

```text
list
```

實際回覆：

```text
最近收藏餐廳

#4｜Instagram
Instagram｜待解析
https://www.instagram.com/p/DXYLjwgDG6q/?igsh=NmFwcDhzc3JiMnpl
```

判定：

```text
list 成功，但顯示格式需優化：restaurant_name 空白時應顯示尚未命名。
```
