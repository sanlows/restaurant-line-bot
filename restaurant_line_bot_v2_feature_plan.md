# restaurant-line-bot v2 開發功能規劃

## 1. 目前狀態

目前 v1 MVP 已完成並驗證成功：

```text
LINE 群組貼餐廳連結
→ Bot 偵測 URL
→ 寫入 Google Sheets
→ Bot 回覆「已收藏餐廳連結 #id」
```

已確認可收藏：

- Facebook Reels 連結
- Instagram Reels 連結

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

## 2. v2 開發目標

v2 的核心目標是讓 Bot 從「連結收藏器」升級為「LINE 群組餐廳資料庫」。

v2 要新增兩大能力：

```text
1. 群組查詢指令
2. 自動解析餐廳資料
```

使用者希望流程是：

```text
群組成員貼餐廳連結
→ Bot 自動收藏
→ Bot 自動嘗試分析餐廳名稱、分類、地區、地址、Google Maps
→ 成功時回覆整理結果
→ 失敗時標記「待解析」
→ 必要時才用人工補救指令修正
```

人工輸入「命名」、「分類」、「地區」不應該是主要流程，而是自動解析失敗時的備援流程。

---

## 3. v2 功能範圍

### 3.1 群組查詢指令

需要支援以下指令：

```text
list
查 最近
查 板橋
查 燒肉
查 火鍋
查 台北
```

### 3.2 自動解析餐廳資料

收到 URL 後，Bot 應嘗試自動解析：

```text
restaurant_name
category
city
district
address
google_maps_url
raw_title
raw_description
parse_confidence
status
```

### 3.3 人工補救指令

自動解析失敗時，才使用：

```text
命名 #id 店名
分類 #id 分類
地區 #id 地區
```

---

## 4. Google Sheets 欄位規格

目前欄位建議調整為：

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

### 4.1 必須保留的既有欄位

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

### 4.2 v2 新增欄位

```text
category
city
district
raw_title
raw_description
parse_confidence
```

請 Windsurf 檢查目前 Google Sheet 是否已有這些欄位。若沒有，請在 README 或部署說明中提醒手動新增，或在程式中提供初始化欄位功能。

---

## 5. 狀態欄位 status 規格

`status` 建議使用以下值：

| status | 說明 |
|---|---|
| 已收藏 | 已成功保存原始連結，但尚未完成解析 |
| 已解析 | 已成功取得餐廳名稱或 Google Places 結果 |
| 待解析 | 自動解析失敗，需人工補資料 |
| 已吃過 | 後續版本使用 |
| 不考慮 | 後續版本使用 |

v2 主要使用：

```text
已收藏
已解析
待解析
```

---

## 6. 自動解析流程

### 6.1 通用流程

收到 URL 後：

```text
1. 先執行 v1 收藏流程
2. 寫入基本資料
3. 判斷 source
4. 根據 source 執行對應解析
5. 更新 Google Sheet 該筆資料
6. 回覆 LINE 群組整理結果
```

基本資料包括：

```text
id
created_at
group_id
room_id
user_id
source
original_url
status="已收藏"
```

---

## 7. 不同來源解析規格

### 7.1 Google Maps 連結

Google Maps 是最優先支援的來源。

流程：

```text
Google Maps URL
→ 嘗試解析 URL 或 metadata
→ 若有 GOOGLE_PLACES_API_KEY，呼叫 Google Places API
→ 補 restaurant_name / address / google_maps_url / category / city / district
→ status = 已解析
```

如果沒有 `GOOGLE_PLACES_API_KEY`：

```text
仍然要完成收藏
不要讓程式 crash
status 可維持「已收藏」或改為「待解析」
```

---

### 7.2 Facebook / Instagram / YouTube 連結

Facebook、Instagram、YouTube Reels / Shorts 不保證能抓到內容。

流程：

```text
URL
→ 嘗試抓 Open Graph metadata
→ 抓取 og:title / og:description / twitter:title / twitter:description / page title
→ 寫入 raw_title / raw_description
→ 使用 rule-based extractor 推測店名、地區、分類
→ 若可形成查詢關鍵字，呼叫 Google Places Text Search
→ 若結果可信，更新餐廳資料並 status = 已解析
→ 若失敗，status = 待解析
```

必須注意：

```text
1. Facebook / Instagram 可能需要登入，抓不到是正常情況
2. 抓不到 metadata 不可讓程式 crash
3. 外部 request 要設定 timeout，例如 5 秒
4. 即使解析失敗，也要保留原始連結
```

---

### 7.3 其他連結

流程：

```text
URL
→ 嘗試抓 title / description
→ 若疑似餐廳內容，嘗試 Google Places
→ 若無法判斷，status = 已收藏 或 待解析
```

---

## 8. Google Places API 規格

### 8.1 新增環境變數

```env
GOOGLE_PLACES_API_KEY=
```

此為選填。若未設定，程式仍需正常運作。

### 8.2 新增檔案

建議新增：

```text
services/places_service.py
```

### 8.3 functions

```python
def text_search(query: str) -> list[dict]:
    pass


def get_place_detail(place_id: str) -> dict:
    pass


def normalize_place_result(result: dict) -> dict:
    pass
```

### 8.4 normalize 後資料格式

```python
{
    "restaurant_name": "...",
    "category": "...",
    "city": "...",
    "district": "...",
    "address": "...",
    "google_maps_url": "...",
    "place_id": "...",
    "confidence": 0.8,
}
```

### 8.5 錯誤處理

```text
1. API key 不存在：跳過 Places 查詢
2. API timeout：記錄 log，status = 待解析
3. 查無結果：status = 待解析
4. API 回傳錯誤：不可中斷收藏流程
```

---

## 9. Rule-based 餐廳資訊抽取

v2 第一版先不一定要接 OpenAI / Gemini。先建立 rule-based extractor，之後再擴充 AI。

### 9.1 新增檔案

```text
services/restaurant_extractor.py
```

### 9.2 functions

```python
def extract_restaurant_hint(raw_title: str, raw_description: str) -> dict:
    pass


def detect_area(text: str) -> dict:
    pass


def detect_category(text: str) -> str | None:
    pass
```

### 9.3 地區關鍵字

第一版可先支援：

```text
台北
新北
板橋
新莊
中和
永和
三重
蘆洲
信義
松山
中山
大安
士林
桃園
新竹
台中
台南
高雄
```

### 9.4 分類關鍵字

第一版可先支援：

```text
燒肉
火鍋
牛肉麵
拉麵
咖啡
甜點
早午餐
居酒屋
韓式
日式
義大利麵
小吃
便當
Buffet
吃到飽
漢堡
披薩
壽司
鐵板燒
牛排
```

### 9.5 輸出格式

```python
{
    "possible_name": "...",
    "city": "...",
    "district": "...",
    "category": "...",
    "query": "...",
    "confidence": 0.4,
}
```

---

## 10. Metadata Parser 規格

### 10.1 新增檔案

```text
services/metadata_parser.py
```

### 10.2 functions

```python
def fetch_metadata(url: str, timeout: int = 5) -> dict:
    pass
```

### 10.3 擷取欄位

依序嘗試抓：

```text
og:title
og:description
twitter:title
twitter:description
<title>
meta description
```

### 10.4 回傳格式

```python
{
    "title": "...",
    "description": "...",
    "error": None,
}
```

若失敗：

```python
{
    "title": "",
    "description": "",
    "error": "timeout or blocked",
}
```

### 10.5 注意事項

```text
1. Facebook / Instagram 很可能抓不到
2. timeout 必須設定
3. 不可讓 exception 中斷主流程
4. user-agent 可設定為一般瀏覽器 UA
```

---

## 11. LINE 回覆格式

### 11.1 解析成功

```text
已收藏餐廳連結 #3

店名：阿城鵝肉
分類：台式小吃
地區：台北市中山區
狀態：已解析
```

若有 Google Maps：

```text
已收藏餐廳連結 #3

店名：阿城鵝肉
分類：台式小吃
地區：台北市中山區
地圖：https://...
狀態：已解析
```

### 11.2 只收藏成功但解析失敗

```text
已收藏餐廳連結 #3

目前無法自動判斷店名，已標記為待解析。
可之後輸入：
命名 #3 店名
分類 #3 類型
地區 #3 地區
```

### 11.3 多筆 URL

```text
已收藏 2 筆餐廳連結：#4, #5

#4：已解析｜阿城鵝肉
#5：待解析｜尚未命名
```

---

## 12. 群組查詢指令規格

### 12.1 list

使用者輸入：

```text
list
```

功能：

```text
顯示目前聊天情境最近收藏的 5 筆資料。
```

回覆格式：

```text
最近收藏餐廳

#5｜阿城鵝肉
台式小吃｜台北市中山區
https://...

#4｜尚未命名
Instagram｜待解析
https://...
```

---

### 12.2 查 最近

使用者輸入：

```text
查 最近
```

功能同 `list`。

---

### 12.3 查 關鍵字

使用者輸入：

```text
查 板橋
查 燒肉
查 火鍋
```

搜尋欄位：

```text
restaurant_name
category
city
district
address
note
original_url
source
raw_title
raw_description
```

回覆格式：

```text
找到 3 筆「板橋」相關收藏

#8｜尚未命名
Instagram｜待解析
https://...

#6｜板橋某某牛肉麵
牛肉麵｜新北市板橋區
https://...
```

若查不到：

```text
找不到「板橋」相關收藏。
```

---

## 13. 群組隔離規則

查詢時必須依照來源情境隔離：

```text
group message → 只查同 group_id
room message → 只查同 room_id
user message → 只查同 user_id
```

避免不同群組資料互相被查出。

---

## 14. Sheets Service 新增功能

建議更新：

```text
services/sheets_service.py
```

新增 functions：

```python
def get_recent_records(context_id: str, context_type: str, limit: int = 5) -> list[dict]:
    pass


def search_records(keyword: str, context_id: str, context_type: str, limit: int = 5) -> list[dict]:
    pass


def update_record(record_id: str, updates: dict) -> bool:
    pass
```

### 14.1 context_type

```text
group
room
user
```

### 14.2 search_records 比對方式

第一版可用大小寫不敏感的 substring search。

---

## 15. Command Parser 規格

### 15.1 新增檔案

```text
services/command_parser.py
```

### 15.2 functions

```python
def parse_command(text: str) -> dict:
    pass
```

### 15.3 輸出格式

```python
{"type": "list"}
{"type": "search", "keyword": "板橋"}
{"type": "rename", "id": "3", "value": "阿城鵝肉"}
{"type": "set_category", "id": "3", "value": "台式小吃"}
{"type": "set_area", "id": "3", "value": "板橋"}
{"type": "none"}
```

### 15.4 支援指令

```text
list
List
LIST
查 最近
查 <keyword>
命名 #id <name>
分類 #id <category>
地區 #id <area>
```

---

## 16. 手動補救指令

### 16.1 命名

```text
命名 #3 阿城鵝肉
```

效果：

```text
更新 id=3 的 restaurant_name
```

回覆：

```text
已更新 #3 店名：阿城鵝肉
```

### 16.2 分類

```text
分類 #3 台式小吃
```

效果：

```text
更新 id=3 的 category
```

回覆：

```text
已更新 #3 分類：台式小吃
```

### 16.3 地區

```text
地區 #3 板橋
```

效果：

```text
更新 id=3 的 district 或 note
```

回覆：

```text
已更新 #3 地區：板橋
```

---

## 17. LINE 訊息處理優先順序

收到文字訊息後：

```text
1. 如果包含 URL：
   執行收藏 + 自動解析流程

2. 如果是 list / 查 最近：
   執行最近收藏查詢

3. 如果是 查 關鍵字：
   執行關鍵字查詢

4. 如果是 命名 / 分類 / 地區：
   執行人工補救更新

5. 其他普通聊天：
   不回覆
```

---

## 18. 錯誤處理要求

必須符合：

```text
1. 收藏流程優先，不可因解析失敗導致收藏失敗
2. Facebook / Instagram 抓不到 metadata 不可 crash
3. Google Places API 查不到不可 crash
4. 沒有 GOOGLE_PLACES_API_KEY 不可 crash
5. Google Sheets 寫入失敗要 log error
6. LINE 回覆失敗要 log error
7. 外部 HTTP request timeout 建議 5 秒
8. 任何解析失敗都要保留 original_url
```

---

## 19. 測試需求

請新增或更新以下測試。

### 19.1 test_command_parser.py

測試：

```text
list
List
LIST
查 最近
查 板橋
查 燒肉
普通聊天不觸發
命名 #3 阿城鵝肉
分類 #3 台式小吃
地區 #3 板橋
```

### 19.2 test_metadata_parser.py

測試：

```text
可解析 title / description
timeout 不 crash
無 metadata 不 crash
```

### 19.3 test_restaurant_extractor.py

測試：

```text
從文字判斷地區
從文字判斷分類
無法判斷時回傳低 confidence
```

### 19.4 test_source_detector.py

測試：

```text
Facebook
Instagram
YouTube
Google Maps
Other
```

### 19.5 test_search_records.py

測試：

```text
查詢同 group_id 的資料
不回傳其他 group_id 資料
restaurant_name 空白時顯示尚未命名
最多回傳 5 筆
```

### 19.6 test_places_service.py

測試：

```text
沒有 GOOGLE_PLACES_API_KEY 不 crash
Places API 查不到結果不 crash
normalize_place_result 正常
```

---

## 20. Render Environment Variables

目前必填：

```env
APP_ENV=production
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
GOOGLE_SHEET_ID=1Slva6CqO2sJ4lyRjkR8U1RlS9oaF_dVbAS312rG9ffo
GOOGLE_SERVICE_ACCOUNT_JSON=
```

v2 選填新增：

```env
GOOGLE_PLACES_API_KEY=
```

若未設定 `GOOGLE_PLACES_API_KEY`，Bot 仍要可以：

```text
收藏連結
抓 metadata
查詢 list
查關鍵字
人工補救更新
```

---

## 21. README 更新要求

請更新 README，包含：

```text
1. v2 功能說明
2. 支援指令清單
3. Google Sheet 欄位說明
4. Render Environment Variables
5. GOOGLE_PLACES_API_KEY 為選填
6. 自動解析不是 100% 成功
7. 解析失敗時會標記待解析
8. 人工補救指令使用方式
9. 部署後測試流程
```

---

## 22. 部署後驗收流程

部署後，請在 LINE 群組測試以下流程。

### 22.1 收藏測試

```text
貼 Facebook Reels 連結
貼 Instagram Reels 連結
貼 Google Maps 連結
```

預期：

```text
Bot 回覆已收藏
Google Sheet 新增資料
若可解析，補上店名 / 分類 / 地區
若不可解析，status = 待解析
```

### 22.2 查詢測試

```text
list
查 最近
查 板橋
查 燒肉
```

預期：

```text
Bot 回覆最近或符合關鍵字的餐廳清單
每筆顯示 id、店名或尚未命名、分類或狀態、連結
```

### 22.3 補救指令測試

```text
命名 #1 測試餐廳
分類 #1 燒肉
地區 #1 板橋
```

預期：

```text
Google Sheet 對應欄位被更新
Bot 回覆更新成功
```

---

## 23. 給 Windsurf 的任務指令

請將以下內容貼給 Windsurf：

```text
請依照 restaurant_line_bot_v2_feature_plan.md 開發 v2 功能。

目前 v1 已完成：
- LINE 群組貼連結會收藏到 Google Sheets
- Bot 會回覆「已收藏餐廳連結 #id」
- Render 已部署成功

v2 目標：
1. 新增群組查詢指令：list、查 最近、查 關鍵字。
2. 新增自動解析餐廳資料流程。
3. Google Maps 連結優先嘗試用 Google Places API 補店名、地址、地圖。
4. Facebook / Instagram / YouTube 連結嘗試抓 metadata，並用 rule-based extractor 推測地區與分類。
5. 解析失敗不可影響收藏，需標記為「待解析」。
6. 新增人工補救指令：命名 #id、分類 #id、地區 #id。
7. 查詢功能必須依 group_id / room_id / user_id 隔離資料。
8. 不要把任何真實 token、secret、Google key 寫入程式碼。
9. GOOGLE_PLACES_API_KEY 是選填，沒有設定時程式也不能 crash。
10. 完成後新增或更新測試，並更新 README。

請先檢查目前專案結構，再逐步實作。完成後請 commit 並 push，讓 Render 自動部署。
```

---

## 24. 建議開發順序

請 Windsurf 依下列順序開發：

```text
1. command_parser.py
2. sheets_service.py 新增查詢與更新 functions
3. list / 查最近 / 查關鍵字
4. 人工補救指令：命名 / 分類 / 地區
5. metadata_parser.py
6. restaurant_extractor.py
7. places_service.py
8. 收藏流程整合自動解析
9. 更新 README
10. 新增測試
11. commit / push / Render deploy
```

---

## 25. v2 不做或延後功能

以下功能先延後：

```text
1. OpenAI / Gemini 真正 AI 解析
2. Google Maps 詳細評分與營業時間
3. LINE Flex Message 美化卡片
4. 分頁查詢
5. 已吃過 / 不考慮完整工作流
6. 週末自動推薦
7. 圖片辨識
8. 多人推薦統計
```

v2 先以「可查詢、可自動初步解析、可手動補救」為主要目標。
