# Nand2Tetris Hack Assembler (Project 6)

基於 Python 實作的 **Nand2Tetris — Hack 組譯器（Assembler）**。本工具能將 Hack 組合語言原始碼（`.asm`）組譯為 16 位元的二進位機器碼（`.hack`），支援完整的符號解析與兩階段掃描（Two-Pass Assembly）。

## 專案檔案結構

```text
.
├── assembler.py    # Hack 組譯器主程式
├── Add.asm         # 測試檔 1：計算 R0 = 2 + 3（無符號基本指令測試）
├── Max.asm         # 測試檔 2：計算 R2 = max(R0, R1)（含預定義符號與跳躍標籤測試）
├── Sum1ToN.asm     # 測試檔 3：計算 R1 = 1 + 2 + ... + R0（含自訂變數與迴圈標籤測試）
└── README.md       # 專案說明文件
```

---

## 功能特點

* **零外部相依性**：僅使用 Python 標準函式庫，無須額外安裝套件。
* **語法前處理**：自動清除單行註解（`//`）、行內註解、空白字元與空白行。
* **兩階段組譯（Two-Pass Assembly）**：
  * **First Pass**：解析所有標籤宣告 `(LABEL)` 並記錄對應的 ROM 指令位址，支援向前參照（Forward Reference）。
  * **Second Pass**：將 A 指令與 C 指令轉換為 16-bit 二進位機器碼，並自 `RAM[16]` 起自動配置自訂變數記憶體位址（如 `Sum1ToN.asm` 中的 `@n`、`@i`、`@sum`）。
* **完整符號表支援**：內建 `R0`–`R15`、`SP`、`LCL`、`ARG`、`THIS`、`THAT`、`SCREEN`、`KBD` 等預定義符號。

---

## 使用方式與測試

在終端機執行 `assembler.py` 並傳入欲組譯的 `.asm` 檔案路徑：

```bash
python assembler.py Add.asm
python assembler.py Max.asm
python assembler.py Sum1ToN.asm
```

### 執行輸出範例

```text
$ python assembler.py Add.asm
組譯完成：Add.hack（共 6 行機器碼）

$ python assembler.py Max.asm
組譯完成：Max.hack（共 16 行機器碼）

$ python assembler.py Sum1ToN.asm
組譯完成：Sum1ToN.hack（共 26 行機器碼）
```

---

## 核心運作流程

| 函式名稱 | 功能說明 |
| :--- | :--- |
| `create_symbol_table()` | 初始化並回傳包含所有 Hack 預定義符號的字典（Dictionary）。 |
| `clean_lines(raw_lines)` | 移除所有註解與空白，回傳純指令與標籤列表。 |
| `first_pass(lines, symbol_table)` | 掃描 `(LABEL)` 標籤並寫入對應的 ROM 位址，回傳不含標籤的純指令列表。 |
| `second_pass(instructions, symbol_table)` | 逐行呼叫 A/C 指令翻譯函式，並自 `RAM[16]` 起動態分配未知變數。 |
| `translate_a_instruction()` | 將 `@value` 或 `@symbol` 轉換為 `0vvvvvvvvvvvvvvv` 格式。 |
| `translate_c_instruction()` | 將 `dest=comp;jump` 拆解並查表轉換為 `111accccccdddjjj` 格式。 |

---

## Hack 指令編碼規格

### 1. A-Instruction（位址指令）
* **語法**：`@value`（非負整數或符號）
* **機器碼格式**：`0 vvv vvvv vvvv vvvv`（最高位元為 `0`，後 15 位元為二進位數值）

### 2. C-Instruction（計算指令）
* **語法**：`dest=comp;jump`（`dest=` 與 `;jump` 為選用）
* **機器碼格式**：`111 a cccccc ddd jjj`
  * `111`：C 指令固定標頭
  * `a` (1 bit) + `cccccc` (6 bits)：ALU 運算控制碼（`comp`）
  * `ddd` (3 bits)：儲存目標暫存器控制碼（`dest`）
  * `jjj` (3 bits)：條件跳躍控制碼（`jump`）