# dsh-multi-lang-ui

**語言：** [English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md)

將 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) Web UI 一鍵切換為多種語言的插件（**繁體中文 / 日本語 / 한국어 / Français / Deutsch / Español**）。

> A DSH plugin that adds **multiple languages** to the Web UI language options — 繁體中文, 日本語, 한국어, Français, Deutsch, Español. Known UI strings use hand-polished translations (each language translated from the English baseline); any *new / updated / third-party* strings fall back to English (or, for 繁體中文, a runtime Simplified→Traditional converter) — so upstream UI updates and other plugins are covered **without re-translating every language**.

## 功能特性

- 在「設定 → 通用 → 語言」選單中新增 **6 種語言**（繁體中文 / 日本語 / 한국어 / Français / Deutsch / Español，與原有 中文 / English 並列）。
- **各語言逐條精譯**：官方全部 locale namespace 的 UI 字串，以**英文為基準**翻譯成各語言（各語言 700+ 條）。
- **缺字串兜底**：官方新增/改動字串、第三方插件未翻譯的字串——繁體中文以內置簡→繁字元表（720+ 字）即時轉繁；其他語言 fallback 英文（en 字典官方齊備），不會出現亂碼或殘缺。
- **DOM 層備援轉換（僅繁中）**：插件市場描述等非字典內容，繁中模式下以 MutationObserver 將渲染出的簡體即時轉繁（輸入框、代碼塊等用戶內容一律排除）。
- **持久化**：語言選擇存於瀏覽器 `localStorage`，重新載入或重開網頁後仍保持。
- **零侵入**：純 client 插件，不改動任何上游套件；locale 服務缺失時靜默降級，不影響其他插件。

## 安裝方式

**推薦：GitHub 安裝（可直接把此連結交給 agent 或自行執行）**

```bash
dsh plugin --profile web add https://github.com/asd13006/dsh-multi-lang-ui
```

或直接讓 agent 安裝：把本倉庫連結貼給 DSH 的 agent，指示其執行上述命令即可。

安裝後重啟 `dsh web`，在「設定 → 通用 → 語言」中選擇想要的語言即可。

**移除（重要）**：請使用 `dsh plugin remove`，它會同步清理 profile 的 bundle 清單；手動刪除套件可能導致殘留引用令 DSH 無法啟動：

```bash
dsh plugin --profile web remove dsh-multi-lang-ui
```

**npm 安裝（發佈至 npm 後可用）**：

```bash
dsh plugin --profile web add dsh-multi-lang-ui
```

## 運作原理

```
locale translate(ns, key)
        │
        ├─ active 是我們的語言？
        │     ├─ 存在精譯字典（DICTS）？  → 直接返回精譯
        │     └─ 不存在（新字串 / 第三方插件）
        │           ├─ zh-TW  → 取 zh 值 → 字元表逐字簡→繁 → 返回
        │           └─ 其他語言 → fallback 英文（en 值）
        └─ 其他語言 → 原樣交由 dsh-client-locale 處理
```

插件啟動時：

1. 註冊各語言的精譯字典至全部 namespace；
2. 包裝 `locale.translate`（精譯 → 兜底）與 `locale.setLocale`（接受我們的語言 id、寫入 localStorage）；
3. 將全部語言加入語言選項列表（patch locale snapshot 並觸發 `locale/change` 刷新語言行）；
4. 包裝 `locale.adopt`——內建 locale 的 host 偏好為異步載入，載入後會以 `locale.preference ?? 瀏覽器語言` 重置 active；若用戶偏好是我們的語言則重新斷言；
5. 啟動 DOM 層備援轉換（MutationObserver），在繁中模式下將非字典內容（如插件市場描述）即時轉為繁體，切換回其他語言時還原。

## 官方更新後是否需要重新翻譯？

**無需。** 三層防護：

1. 官方新增的字串 → 由運行時兜底機制直接覆蓋；
2. 官方改動的字串 → 精譯字典保留舊值，但第三方或新增字串同樣自動兜底；如需更新精譯可重新生成（見下文）；
3. 如需完全同步精譯：執行一次重新生成流程即可，無需逐條手工翻譯。

### 重新生成精譯字典（可選）

```bash
node scripts/extract.mjs <node_modules/@deepseek-ai 路徑>   # 1. 抽取官方最新 zh/en 字典至 src/zh-src/ 與 src/en/
# 2. 翻譯 src/en/*.json → src/<lang>/*.json（可用 LLM 批量處理，key/佔位符必須一致）
node scripts/assemble.mjs                                   # 3. 重新生成 lib/client.js
```

### 檢查未收錄簡體字（官方或第三方更新後執行）

```bash
node scripts/collect-chars.mjs [第三方client.js...]   # 收集所有出現的簡體字
node scripts/check-missing-chars.mjs                  # 列出字元表未收錄的簡體專用字
```

若檢測到未收錄字，請在 `src/zh-tw-parts/chars.json` 中補上「簡體字: 繁體字」映射，再執行 `node scripts/assemble.mjs`。

## 目錄結構

```
dsh-multi-lang-ui/
├── package.json              # 插件清單（dsh.client.inject / bundle.patch）
├── index.mjs                 # Host 側：no-op 入口（純 client 插件）
├── cordis.patch.yml          # Host 插件入口
├── lib/client.js             # 生成的 browser bundle（請勿手動修改）
├── src/
│   ├── zh-src/               # 抽取自官方的 zh 簡中字典（生成數據）
│   ├── en/                   # 抽取自官方的 en 字典（各語言翻譯基準）
│   ├── zh-tw/ ja/ ko/ fr/ de/ es/   # 各語言精譯字典（人工/LLM 翻譯，質量基準）
│   ├── zh-tw-parts/
│   │   ├── chars.json        # 簡→繁單字表（繁中運行時備援轉換用）
│   │   ├── simplified-only.txt  # 簡體專用字檢查表（維護用）
│   │   └── collected-chars.txt  # collect-chars 輸出
│   └── TERMINOLOGY.md        # 術語對照表（精譯時參考）
├── scripts/                  # extract / assemble / verify / collect / check
└── verify/                   # Playwright 端到端驗證腳本
```

## 已知限制

- 一對多簡體字（如「复」在 复制/恢复/复杂 中對應不同繁體）僅做單字映射（復），精譯字典已覆蓋主要字串；極少數新增字串可能出現不完全的轉換。
- 語言偏好存於瀏覽器 `localStorage`（各瀏覽器相互獨立）；內建 locale 對遠端瀏覽器本就不持久，此為一致的設計。
- 字元表未收錄的簡體字會原樣透傳——請以 `check-missing-chars.mjs` 定期檢查並補表。

## 安全性與隱私

- **無網路通訊**：插件不會發起任何網路請求（無 fetch / WebSocket / 上報）；唯一的對外 URL 僅為 README 中的文件連結。
- **不收集資料**：無 telemetry、無 analytics、無錯誤上報；唯一持久化的資料是瀏覽器 `localStorage["dsh-multi-lang-ui.preference"]`（值僅為語言 id，如 `"ja"`）。
- **不觸及敏感資料**：不讀寫 credentials / tokens / 會話記錄 / 檔案系統；Host 側（`index.mjs`）為 no-op，一無所動。
- **DOM 轉換為唯讀**：僅修改 DOM 文字節點（text node），無 innerHTML、無注入；輸入框、textarea、contenteditable、代碼塊（pre/code）一律排除，不影響用戶輸入或程式碼。顯示層的會話訊息會被轉換（僅為唯讀顯示效果，底層資料不變），切換回其他語言時自動還原。
- **零供應鏈風險**：`dependencies` 為空，安裝時不會下載任何新套件；client bundle 完全自包含（零 `require`）；peer 依賴均為 DSH 本機已有的官方套件。

## 常見問題（FAQ）

**Q：插件市場（dshmarket）點解冇顯示我個插件的介紹？**
A：市場的介紹與分類來自「awesome-dsh-plugin」策展 registry（`data/plugins/<owner>__<repo>.yml`），並非讀取本地 package.json。提交 `registry-entry.yml` 到該 registry（需 repo 建立滿 1 日且 ≥ 10 個 commit）後即會顯示。

**Q：版本號一定要發佈 npm 先有？**
A：唔使。已安裝插件的版本號由本地 `node_modules` 的 package.json 讀取（GitHub 安裝版同樣顯示 `v0.1.0`）。npm 發佈只影響「npm 搜尋」與「純 npm 安裝」體驗，與市場顯示無關。

**Q：官方更新 UI 或加了新字串，插件要更新嗎？**
A：無需等待插件更新——運行時兜底會即時覆蓋任何新字串（繁中即時簡轉繁、其他語言回退英文）；第三方插件的字串亦自動兜底。精譯字典可用 `scripts/` 重新生成以保持最佳品質。

**Q：移除插件後 DSH 無法啟動？**
A：請務必使用 `dsh plugin --profile web remove dsh-multi-lang-ui` 移除（會同步清理 profile 的 bundle 清單）。手動刪除套件可能留下殘留引用令 DSH 啟動失敗。

**Q：DSH 更新後語言選項消失了，或者頁面顯示「authentication required」？**
A：DSH 0.1.1+ 加咗瀏覽器認證——請用終端 `dsh web` 印出嘅帶 token URL 開啟（例如 `http://127.0.0.1:3080/?token=…`），冇 token 會回 401。若語言仍然冇出現，請更新插件（先 `dsh plugin --profile web remove dsh-multi-lang-ui`，再重新 add）——插件 0.1.1+ 已宣告 `inject: ["locale"]`，唔再依賴插件載入次序。

## License

MIT
