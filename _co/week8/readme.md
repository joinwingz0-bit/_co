# 認識 IC 設計的核心：EDA（電子設計自動化）與實作資源指南

> 本指南旨在介紹積體電路（IC）設計中不可或缺的核心工具——**EDA（Electronic Design Automation，電子設計自動化）**，並彙整從基礎邏輯閘、硬體描述語言（HDL）到完整晶片設計流程的開源專案、線上互動工具與頂尖大學課程資源。

---

## 📌 核心資源快速導覽

| 資源名稱 | 類型 | 內容簡介 | 相關連結 |
| :--- | :--- | :--- | :--- |
| **Veryl2Chip** | AI 自製 EDA 工具 | 將現代硬體描述語言（Veryl）一步步合成並視覺化為晶片版圖的輕量級 EDA 工具鏈 | [📦 GitHub 原始碼](https://github.com/ccc-eda/veryl2chip/) ｜ [🌐 線上使用](https://ccc-eda.github.io/veryl2chip/web/dist/index.html) |
| **Hack Computer** | Nand2tetris 網頁版 | 從最底層的 NAND 邏輯閘出發，親手用 HDL 打造出 ALU、記憶體與完整電腦架構 | [📦 GitHub 原始碼](https://github.com/ccc-js/hack-computer) ｜ [🌐 線上使用](https://ccc-js.github.io/hack-computer/dist/hdl.html) |
| **EDA 電子書** | 開源線上教材 | 深入淺出剖析 EDA 核心演算法、邏輯合成與實體設計原理的繁體中文電子書 | [📖 線上閱讀電子書](https://github.com/ccc-eda/eda-books/tree/main/book) |
| **Cornell ECE 5745** | 大學公開課程 | 康乃爾大學複雜數位 ASIC 設計課程，涵蓋工業界從 RTL 到 GDSII 的完整實務流程 | [🎓 課程講義 Handouts](https://www.csl.cornell.edu/courses/ece5745/handouts.html) |

---

## 💡 什麼是 IC 設計的 EDA？

**EDA（Electronic Design Automation，電子設計自動化）** 是指用來輔助設計、模擬、驗證與製造積體電路（IC）及印刷電路板（PCB）的軟體工具群。

由於現代高階晶片內部往往包含數十億甚至上百億個電晶體（例如超過 $10^{10}$ 個奈米級元件），人類已經不可能透過手工繪製電路圖來完成設計。從撰寫硬體程式碼、檢查邏輯錯誤、轉換為邏輯閘，到將數十億個元件擺放到矽晶圓上並拉好金屬導線，全都必須仰賴 EDA 軟體的自動化演算法來完成，因此 EDA 被譽為**「晶片之母」**。

### 🏢 建築比喻：把晶片設計想像成「蓋一棟摩天大樓」

* **IC 設計工程師（建築師）**：負責使用程式碼（硬體描述語言 HDL，如 Verilog、SystemVerilog、Veryl）寫出大樓的功能、房間配置與規格。
* **EDA 工具（全自動化建築工程軟體）**：
  1. **邏輯合成（Logic Synthesis）**：把文字描述自動轉換成數十億個邏輯閘與標準元件的連接網表（Gate-level Netlist）。
  2. **佈局與繞線（Place & Route, P&R）**：計算出每個元件在矽晶圓上的實際物理座標，並自動規劃金屬導線走法。
  3. **時序與物理驗證（Verification & Signoff）**：確保訊號能在極短時脈週期（例如 $T_{\text{clk}} \le 1\text{ ns}$，對應時脈頻率 $f \ge 1\text{ GHz}$）內準時送達、電力穩定且不過熱，並持續最佳化 **PPA（Power 功耗、Performance 效能、Area 面積）**。
  4. **輸出製造藍圖（Tape-out）**：最後輸出給晶圓代工廠（如台積電 TSMC）進行光罩製造的工程格式檔案（**GDSII** 或 **OASIS**）。

---

## 🔄 標準 IC 設計與 EDA 核心流程 (RTL to GDSII)

數位 IC 設計主要分為**前端設計（Front-End，邏輯與功能）**與**後端設計（Back-End，實體與物理實現）**兩大階段：

    [系統規格制定 (Specification)]
                 │
                 ▼
    [RTL 硬體描述語言設計 (Verilog / SystemVerilog / Veryl)]  ◄── 前端設計 (Front-End)
                 │
                 ▼
    [功能模擬與驗證 (Simulation & Verification)]
                 │
                 ▼
    [邏輯合成 (Logic Synthesis)] ── 將 RTL 轉換為標準邏輯閘網表 (Gate-level Netlist)
                 │
                 ▼
    [實體設計：佈局與繞線 (Place & Route: Floorplan / Placement / CTS / Routing)]  ◄── 後端設計 (Back-End)
                 │
                 ▼
    [靜態時序分析與實體簽核驗證 (STA / DRC / LVS Signoff)]
                 │
                 ▼
    [GDSII 光罩版圖輸出 (Tape-out 下線製造)]

### 各階段核心工作與 EDA 角色對照表

| 階段分類 | 設計步驟 | 工程目標 | EDA 工具扮演的角色 |
| :--- | :--- | :--- | :--- |
| **前端設計** | **1. RTL 設計** | 用 HDL 撰寫暫存器傳輸級（RTL）硬體邏輯 | 語法檢查、Linting 靜態分析 |
| **前端設計** | **2. 功能驗證** | 確認電路邏輯在各種輸入下皆正確無誤 | 數位邏輯模擬器（Simulator）、形式驗證（Formal Verification） |
| **前端轉後端** | **3. 邏輯合成** | 將抽象的程式碼映射為實際的標準邏輯閘（Standard Cells） | 合成器（Synthesizer）進行布林代數化簡、技術映射與時序最佳化 |
| **後端設計** | **4. 平面規劃與擺置** | 決定晶片長寬、I/O 位置並擺放數百萬至數十億個邏輯閘 | Floorplanner 與 Placer 演算法最小化繞線總長度與擁塞度 |
| **後端設計** | **5. 時脈樹合成與繞線** | 讓時脈訊號同步抵達所有暫存器，並用多層金屬線連通所有接腳 | CTS（Clock Tree Synthesis）降低時脈偏移（Skew），Router 自動完成全域與細部繞線 |
| **後端簽核** | **6. 驗證與下線** | 檢查時序是否違規、版圖是否符合晶圓廠物理製造規則 | **STA**（靜態時序分析）、**DRC**（設計規則檢查）、**LVS**（電路圖與版圖比對） |

---

## 🛠️ 精選開源專案、線上互動工具與課程詳解

商用的工業級 EDA 軟體（如 Synopsys、Cadence、Siemens EDA）通常價格高昂且架構龐大，初學者難以直接窺探其內部演算法。以下四個資源提供從底層邏輯閘、自製輕量級 EDA 工具鏈到大學工業標準課程的完整學習路徑：

### 1. AI 自製 EDA：`veryl2chip`
透過結合 AI 輔助開發與現代硬體描述語言 **Veryl**（一種語法更安全、現代化的 SystemVerilog 替代語言），此專案展示如何從零打造一個輕量級、可視覺化的教學用 EDA 工具鏈，讓你親眼看見程式碼如何一步步變成晶片版圖。
* **核心特色**：
  * 支援從硬體描述語言解析（Parsing）、邏輯合成（Synthesis）、元件擺置（Placement）到繞線（Routing）的完整微縮流程。
  * 提供直覺的網頁視覺化介面，無須在電腦安裝龐大軟體即可即時體驗「從程式碼到晶片版圖」的轉換過程。
* **相關連結**：
  * 📦 **GitHub 專案原始碼**：[https://github.com/ccc-eda/veryl2chip/](https://github.com/ccc-eda/veryl2chip/)
  * 🌐 **線上互動體驗版**：[https://ccc-eda.github.io/veryl2chip/web/dist/index.html](https://ccc-eda.github.io/veryl2chip/web/dist/index.html)

### 2. Nand2tetris 網頁專案：`hack-computer`
要理解 EDA 為什麼能把程式轉換成邏輯閘，最好的起點就是親手用基本邏輯閘拼出一台電腦。本專案將經典的《Nand to Tetris》（從 NAND 閘到俄羅斯方塊）硬體模擬器搬上瀏覽器。
* **核心特色**：
  * 從最基礎的單一 `NAND` 邏輯閘出發，透過撰寫簡單的 HDL，親手搭建出 `NOT`、`AND`、`OR`、`XOR`、加法器、算術邏輯單元（ALU）、記憶體（RAM），最終組裝出一顆完整的 16-bit Hack CPU 與電腦系統。
  * 純網頁前端執行，即時進行硬體邏輯模擬與測試腳本驗證。
* **相關連結**：
  * 📦 **GitHub 專案原始碼**：[https://github.com/ccc-js/hack-computer](https://github.com/ccc-js/hack-computer)
  * 🌐 **線上 HDL 模擬器**：[https://ccc-js.github.io/hack-computer/dist/hdl.html](https://ccc-js.github.io/hack-computer/dist/hdl.html)

### 3. 開源教材：EDA 電子書 (`eda-books`)
光會操作工具還不夠，若想理解 EDA 軟體背後究竟用了哪些資料結構與演算法，這本開源電子書提供了極佳的中文導讀。
* **核心特色**：
  * 涵蓋布林代數、二元決策圖（BDD）、邏輯合成演算法、圖論在電路分割（Partitioning）與繞線（如迷宮繞線 Lee's Algorithm、A* 演算法）上的應用。
  * 結合實作範例，幫助讀者從軟體工程與演算法的角度切入 EDA 領域。
* **相關連結**：
  * 📖 **線上閱讀電子書**：[https://github.com/ccc-eda/eda-books/tree/main/book](https://github.com/ccc-eda/eda-books/tree/main/book)

### 4. 頂尖大學課程：康乃爾大學 IC 設計課程 (Cornell ECE 5745)
**ECE 5745: Complex Digital ASIC Design** 是康乃爾大學極具代表性的高階數位積體電路設計課程，完整公開了全套教學講義（Handouts），展現真實學術界與工業界如何運用主流商用與開源 EDA 工具完成晶片設計。
* **核心特色**：
  * 詳細講解 CMOS 電晶體原理、標準元件庫（Standard Cell Library）、RTL 編碼規範、自動化邏輯合成、自動佈局繞線（Automated Place & Route）、靜態時序分析（STA）與功耗分析。
  * 講義圖文並茂，非常適合用來對照 `veryl2chip` 與 `eda-books` 的概念，理解真實流片（Tape-out）等級的工程細節。
* **相關連結**：
  * 🎓 **課程講義與教材 (Handouts)**：[https://www.csl.cornell.edu/courses/ece5745/handouts.html](https://www.csl.cornell.edu/courses/ece5745/handouts.html)

---

## 🗺️ 推薦自學路線 (Learning Path)

如果您是剛接觸 IC 設計或對 EDA 工具開發感興趣的學習者，建議按照以下四個步驟循序漸進：

1. **Step 1：建立數位邏輯與硬體思維（約 1～2 週）**
   * 打開 **[Hack Computer 線上 HDL 模擬器](https://ccc-js.github.io/hack-computer/dist/hdl.html)**，動手用 `NAND` 閘合成出基本邏輯閘與 ALU，體會「硬體電路是平行運作，而非像軟體逐行執行」的核心觀念。
2. **Step 2：親眼見證 RTL 到晶片版圖的自動化流程（約 1 週）**
   * 前往 **[Veryl2Chip 線上工具](https://ccc-eda.github.io/veryl2chip/web/dist/index.html)**，觀察一段硬體描述語言如何被自動拆解為邏輯網表，並進一步擺置與繞線成晶片版圖。
3. **Step 3：深入理解 EDA 核心演算法與原始碼（約 2～4 週）**
   * 搭配閱讀 **[EDA 電子書](https://github.com/ccc-eda/eda-books/tree/main/book)** 與 **[Veryl2Chip 原始碼](https://github.com/ccc-eda/veryl2chip/)**，了解合成器（Synthesizer）、擺置器（Placer）與繞線器（Router）背後的程式實作邏輯。
4. **Step 4：接軌工業級 ASIC 設計全流程（進階深造）**
   * 研讀 **[康乃爾大學 ECE 5745 課程講義](https://www.csl.cornell.edu/courses/ece5745/handouts.html)**，深入掌握時序收斂（Timing Closure）、功耗分析、CMOS 物理特性與完整的工業級 ASIC 設計方法學。
