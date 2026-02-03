# Shadow Worker (Discord-Self-Bot)

[[English](README.md)] | [繁體中文]

這是一個基於 Python 開發的 Discord 個人自動化助手。本專案結合了非同步事件處理與背景定時任務，旨在模擬真實用戶行為，達成自動化頻道維護與擬人化互動模擬。

> [!WARNING]
> **免責聲明**： 本專案僅供教育與研究用途。使用自動化腳本 (Self-bot) 違反 Discord 服務條款 (ToS)，可能導致帳號被封鎖。請自行承擔使用風險。

## ✨ 核心功能

- 🤖 擬人化自動回覆：監控特定伺服器中的提及 (Mention)，並在隨機的「思考」延遲與打字模擬後進行回覆。
- 📅 背景定時任務：在指定時間範圍內（週一至週五，07:50 - 07:58）隨機挑選時間點，自動發送 todo.txt 內容。
- ⌨️ 動態打字模擬：根據訊息長度實現精確的「正在輸入...」狀態，並區分短回覆與長篇內容兩種模式。
- 🛠️ 環境自動化：包含 Makefile (Linux/macOS) 與 .bat (Windows) 腳本，支援一鍵配置虛擬環境與部署。

## 🚀 快速開始

### Linux / macOS 用戶：
```bash
make setup  # Create venv and install dependencies
make run    # Start the assistant
```
### Windows 用戶：
```bash
./run_bot.bat
```

## ⚙️ 配置說明
環境變數：在根目錄建立 .env 檔案並填入以下資訊：
```
# Discord 帳號授權 Token
# 獲取方式：瀏覽器 F12 -> Network -> 找 /messages 請求 -> Headers -> authorization
DISCORD_TOKEN=

# 監控的目標伺服器 ID
# 獲取方式：Discord -> 設定 -> 進階 開啟「開發者模式」 -> 右鍵點擊伺服器圖示 -> 複製伺服器 ID
TARGET_GUILD_ID=

# 定時發送 todo.txt 的目標頻道 ID
# 獲取方式：右鍵點擊特定頻道 -> 複製頻道 ID
# (可以跟 TARGET_GUILD_ID 裡的頻道一樣，也可以是不同伺服器的頻道)
TODO_CHANNEL_ID=


# 觸發時段設定 (24小時制)
TODO_TIME=07:50
TODO_END_TIME=07:59

# 工作日設定 (0=週一, 1=週二, ..., 4=週五, 5=週六, 6=週日)
# 預設週一至週五：0,1,2,3,4
TODO_WORKDAYS=0,1,2,3,4

# 自動回覆語句
REPLY_RESPONSES=收到,了解,OK，收到,好的,我看一下,了解，處理中
```

## 內容準備
在根目錄建立 todo.txt 檔案，並輸入你想要定時發送的內容。
