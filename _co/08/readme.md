# Nand2Tetris Chapter 08：Virtual Machine II（Program Flow & Function Calls）

本目錄完成 **Nand2Tetris Chapter 08** 的全部 6 組虛擬機（VM）程式流程控制與函式呼叫題目，透過 `../week11/VMTranslator.py` 將 `.vm` 中間碼翻譯為 Hack 組合語言（`.asm`），並通過官方 `CPUEmulator` 的測試腳本（`.tst`）比對驗證。

---

## 一、題目清單與測試結果

| 類別 | 題目目錄 | 輸入檔案 | 輸出組語 | Bootstrap 引導碼 | 測試結果 |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **ProgramFlow** | `ProgramFlow/BasicLoop` | `BasicLoop.vm` | `BasicLoop.asm` | 無 | `Comparison ended successfully` |
| **ProgramFlow** | `ProgramFlow/FibonacciSeries` | `FibonacciSeries.vm` | `FibonacciSeries.asm` | 無 | `Comparison ended successfully` |
| **FunctionCalls** | `FunctionCalls/SimpleFunction` | `SimpleFunction.vm` | `SimpleFunction.asm` | 無 | `Comparison ended successfully` |
| **FunctionCalls** | `FunctionCalls/NestedCall` | `Sys.vm` | `NestedCall.asm` | 啟用 | `Comparison ended successfully` |
| **FunctionCalls** | `FunctionCalls/FibonacciElement` | `Main.vm`、`Sys.vm` | `FibonacciElement.asm` | 啟用 | `Comparison ended successfully` |
| **FunctionCalls** | `FunctionCalls/StaticsTest` | `Class1.vm`、`Class2.vm`、`Sys.vm` | `StaticsTest.asm` | 啟用 | `Comparison ended successfully` |

---

## 二、執行與驗證指令

於 `_co/08` 目錄下依序執行翻譯與模擬器測試：

### 1. 產生 Hack 組合語言（`.asm`）

```powershell
# 單檔測試（由 .tst 初始化指標，不加入 Bootstrap）
python ..\week11\VMTranslator.py ProgramFlow\BasicLoop\BasicLoop.vm
python ..\week11\VMTranslator.py ProgramFlow\FibonacciSeries\FibonacciSeries.vm
python ..\week11\VMTranslator.py FunctionCalls\SimpleFunction\SimpleFunction.vm

# 完整專案資料夾（自動寫入 SP=256 與 call Sys.init 0）
python ..\week11\VMTranslator.py FunctionCalls\NestedCall
python ..\week11\VMTranslator.py FunctionCalls\FibonacciElement
python ..\week11\VMTranslator.py FunctionCalls\StaticsTest
```

### 2. 執行 CPU Emulator 腳本驗證

```powershell
..\..\nand2tetris\tools\CPUEmulator.bat ProgramFlow\BasicLoop\BasicLoop.tst
..\..\nand2tetris\tools\CPUEmulator.bat ProgramFlow\FibonacciSeries\FibonacciSeries.tst
..\..\nand2tetris\tools\CPUEmulator.bat FunctionCalls\SimpleFunction\SimpleFunction.tst
..\..\nand2tetris\tools\CPUEmulator.bat FunctionCalls\NestedCall\NestedCall.tst
..\..\nand2tetris\tools\CPUEmulator.bat FunctionCalls\FibonacciElement\FibonacciElement.tst
..\..\nand2tetris\tools\CPUEmulator.bat FunctionCalls\StaticsTest\StaticsTest.tst
```

---

## 三、實作重點說明

1. **函式標籤作用域（Label Scoping）**：函式內部宣告的 `label`、`goto` 與 `if-goto` 皆轉換為 `functionName$label`，避免不同函式使用相同標籤名稱時產生符號衝突。
2. **開機引導碼（Bootstrap Code）自動判斷**：偵測輸入來源是否包含 `function Sys.init`；若包含（如 `NestedCall`、`FibonacciElement`、`StaticsTest`），自動於組語開頭初始化 `SP = 256` 並執行 `call Sys.init 0`。
3. **無參數函式返回位址保護（`return`）**：在執行 `*ARG = pop()` 之前先將 `retAddr = *(endFrame - 5)` 暫存至 `R14`，避免 `nArgs == 0` 時回傳值覆寫堆疊上的返回位址。
4. **跨檔案靜態變數隔離（`static`）**：各 `.vm` 檔案的 `static i` 依檔名映射為 `@FileName.i`（例如 `Class1.0` 與 `Class2.0`），確保多檔合併編譯時各自獨立配置於 `RAM[16..255]`。