# YouTube 網址整理工具

輸入 YouTube 頻道名稱、`@handle`、頻道 ID 或頻道網址，即可把指定數量的 Shorts、一般影片或直播網址整理成 TXT 檔。程式使用 `yt-dlp` 讀取公開頁面，不需要申請 YouTube API 金鑰。

## 功能

- 支援 Shorts、一般影片與直播分頁
- 可指定輸出的網址數量與檔名
- 每行輸出一個網址，並自動排除重複項目
- 支援互動操作與命令列參數
- 輸出為 UTF-8 編碼 TXT

## 安裝

需要 Python 3.10 以上版本：

```powershell
python -m pip install -r requirements.txt
```

## 使用方法

### 互動模式

Windows 可以雙擊 `啟動工具.bat`，或在 PowerShell 執行：

```powershell
python youtube_url_tracker.py
```

依畫面提示輸入：

1. 頻道名稱、`@handle`、頻道 ID 或完整頻道網址
2. `1`（Shorts）、`2`（一般影片）或 `3`（直播）
3. 想取得的網址數量
4. 輸出檔名；若未包含 `.txt`，程式會自動補上

### 命令列模式

```powershell
python youtube_url_tracker.py --channel "@OpenAI" --type shorts --count 20 --output shorts清單.txt
```

`--type` 可使用 `shorts`、`videos`、`live`，也接受中文「短影音」、「影片」、「直播」。

## 頻道名稱搜尋

只輸入頻道名稱時，程式會優先選擇名稱完全相同的頻道；若沒有完全相同的結果，則採用 YouTube 的第一個搜尋結果。為避免同名頻道選錯，建議輸入 `@handle` 或完整頻道網址。

## 注意事項

YouTube 頁面結構可能變動。若讀取失敗，可先更新 `yt-dlp`：

```powershell
python -m pip install -U yt-dlp
```
