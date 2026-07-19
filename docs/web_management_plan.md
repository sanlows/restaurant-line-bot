# 餐廳收藏 Web 管理介面規劃草案

狀態：討論中，尚未排入實作。

最後更新：2026-07-19

## 1. 產品定位

將目前的 LINE Bot 與未來的 Web 管理介面分工：

- LINE Bot：負責快速收藏餐廳相關網址，維持簡單、低學習成本。
- Web 管理介面：負責查看、補資料、修改、搜尋、篩選、分析與產生美食建議。
- Google Sheets：第一階段繼續作為 LINE Bot 與 Web 介面共用的資料來源。
- Render FastAPI：沿用現有服務，同時提供 LINE webhook 與 Web 管理頁面。

預計路由概念：

```text
/
├─ /callback       LINE webhook
├─ /login          使用者登入
├─ /restaurants    餐廳清單
├─ /pending        待補資料
└─ /recommend      美食建議
```

## 2. 核心 UX 原則

- LINE 收藏流程維持單一步驟，不把複雜的資料補全流程塞進聊天指令。
- Web 介面同時支援手機與電腦瀏覽器。
- 初階使用者應能透過按鈕、表單及勾選篩選完成操作。
- 不要求一般使用者理解 Google Sheets 欄位或 Bot 指令格式。
- 自動解析失敗時仍保留原始網址，之後可在 Web 介面補資料。
- 進階功能漸進出現，不在第一版一次呈現全部選項。

## 3. 第一階段候選範圍（MVP）

### 3.1 登入與權限

- 網站不得完全公開修改權限。
- 優先評估 Google 登入與 email 白名單。
- 保留最後修改者與修改時間，方便多人協作追蹤。
- 共用密碼只作為原型選項，不作為長期方案。

### 3.2 餐廳清單

- 顯示現有 Google Sheets 收藏紀錄。
- 支援店名、分類、地區、狀態及收藏日期篩選。
- 電腦版以表格為主，手機版以卡片為主。
- 可開啟原始連結與 Google Maps 連結。

### 3.3 待補資料

- 預設列出缺少店名、分類、地區或 Google Maps 的紀錄。
- 提供單頁編輯表單。
- 支援「儲存並下一筆」與「略過」。
- 不強迫每筆資料立即補齊。

### 3.4 基本推薦

- 依地區、分類、想去／去過狀態篩選。
- 支援隨機一家或推薦三家。
- 第一版使用透明的規則排序，不依賴 AI。

## 4. 後續階段候選功能

- Google Places 候選搜尋與一鍵補入資料。
- 相同餐廳的多個 Facebook、Instagram、YouTube 來源去重與合併。
- 想去／去過、評分及最近造訪日期。
- 聚餐候選清單與多人投票。
- 依收藏時間、資料完整度及造訪狀態產生推薦分數。
- 將推薦結果複製或分享回 LINE。
- LINE Login／LIFF 整合。
- AI 輔助摘要或推薦理由；不作為第一版必要功能。

## 5. 資料與技術方向

### 第一階段

- 後端：沿用 FastAPI。
- 主機：沿用目前 Render Web Service。
- 資料：沿用 Google Sheets。
- 前端：使用響應式 HTML、CSS、JavaScript；技術框架後續再決定。
- 機密資料：只保存在 Render 環境變數，不送到瀏覽器。

### 資料欄位候選

未來可能新增：

```text
place_id
completion_status
visited_status
rating
last_visited_at
confirmed_at
confirmed_by
updated_at
updated_by
duplicate_of
```

欄位正式加入前，需先確認既有 Google Sheet 相容性與 migration 方法。

### 長期資料儲存

第一階段不急著改資料庫。若未來出現多人同時修改、資料量增加、歷史追蹤或複雜查詢需求，再評估從 Google Sheets 移轉至正式資料庫。

Render 本機檔案系統不可作為永久資料來源，因此不應把正式資料只存在服務內的 SQLite 或本機檔案。

## 6. 上線可靠性前置工作

Web 管理功能開始前，需一起處理或確認：

- webhook event 去重，避免 LINE 重送造成重複收藏。
- Google Sheets 寫入錯誤應回報給使用者或管理者。
- ID 產生方式需避免並行寫入產生重複 ID。
- metadata URL 抓取需限制內網與不安全目的地。
- Web 修改操作需有輸入驗證、授權檢查與基本 audit log。
- Render Free instance 休眠會影響 LINE 即時性；測試階段可接受，正式使用前需重新評估方案。

## 7. 尚待討論與決策

後續討論依序確認：

1. 哪些人可以登入：固定 email 白名單、Google 群組，或其他方式。
2. 所有人是否都能修改，或需要檢視者／編輯者兩種角色。
3. 第一版最重要的是補資料、搜尋，還是推薦功能。
4. 是否需要記錄每次修改的歷史，而不只是最後修改者。
5. 是否保留 Google Sheets 作為人工備援操作介面。
6. 手機版與電腦版哪一個是主要使用情境。
7. Render Free 冷啟動在測試階段是否可以接受。
8. Google Places API 的預算、使用限制及自動配對策略。

## 8. 暫定階段拆分

```text
Phase 0 需求與權限確認
Phase 1 登入、餐廳清單與唯讀搜尋
Phase 2 待補資料與安全編輯
Phase 3 基本美食推薦
Phase 4 Google Places 配對與餐廳去重
Phase 5 分享、投票與進階分析
```

每一階段在開始實作前，都需重新確認範圍與驗收方式。
