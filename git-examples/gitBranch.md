# git branch怎麼用

`git branch` 主要用來**建立**、**查看**、**重新命名**與**刪除**分支。

### 1. 查看分支

```bash
git branch             # 查看所有本地分支（前面有 * 號代表當前所在分支）
git branch -r          # 查看所有遠端分支
git branch -a          # 查看本地與遠端所有分支
git branch -v          # 查看分支並顯示最新一次 commit 訊息

```

---

### 2. 建立分支

```bash
# 僅建立分支（不會自動切換過去）
git branch <branch-name>

# 建立並同時切換過去（推薦）
git switch -c <branch-name>     # 較新的 Git 語法（推薦）
git checkout -b <branch-name>   # 傳統語法

```

---

### 3. 重新命名分支

```bash
# 修改「當前所在」的分支名稱
git branch -m <new-name>

# 指定修改特定分支名稱
git branch -m <old-name> <new-name>

```

---

### 4. 刪除分支

```bash
# 安全刪除（已合併到當前分支才會允許刪除）
git branch -d <branch-name>

# 強制刪除（未合併的變更也會直接被丟棄）
git branch -D <branch-name>

# 刪除遠端分支
git push origin --delete <branch-name>

```

---

### 典型開發流程範例

1. 從主分支建立功能分支：
```bash
git switch -c feature/login

```


2. 完成修改並提交 commit：
```bash
git add .
git commit -m "feat: add user login function"

```


3. 切回主分支並合併：
```bash
git switch main
git merge feature/login

```


4. 合併完成後刪除功能分支：
```bash
git branch -d feature/login

```

`git checkout -b <branch-name>` 實際上就是 **「建立分支（`git branch`）+ 切換分支（`git checkout`）」的二合一指令**。

---

### 指令等效關係

下面這行複合指令：

```bash
git checkout -b feature

```

完全等同於依序執行這兩行：

```bash
git branch feature      # 1. 建立名為 feature 的新分支
git checkout feature    # 2. 將 HEAD（當前工作目錄）切換到 feature 分支

```

---

### 兩者核心行為差異

| 指令 | 作用 | 執行後 HEAD 所在位置 | 典型使用時機 |
| --- | --- | --- | --- |
| `git branch <name>` | **僅建立**新分支指針 | 留在**原本分支** | 想先開好分支備用，暫不切換 |
| `git checkout -b <name>` | **建立並立刻切換** | 移至**新建立的分支** | 準備立刻開始在新分支寫代碼 |

---

### 現代 Git 的推薦寫法

由於早期的 `git checkout` 同時負責「切換分支」和「還原檔案（discard changes）」，語意容易混淆，Git 自 **2.23 版本**起將功能拆分為兩個專門指令：

* `git switch`：專門用來處理**分支切換**
* `git restore`：專門用來處理**檔案還原**

因此，現代開發更推薦使用：

```bash
git switch -c <branch-name>   # -c 代表 --create，等同於 git checkout -b

```