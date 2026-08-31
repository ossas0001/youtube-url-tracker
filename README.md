# YouTube 頻道網址整理工具

這是一個使用 Python 製作的 YouTube 網址匯出工具。輸入頻道、內容類型、數量與檔名後，程式會讀取該頻道最新的內容，並將網址逐行整理成 TXT 檔案。

程式透過 `yt-dlp` 讀取 YouTube 公開頁面，不需要申請 YouTube Data API 金鑰，適合建立影片清單、批次處理來源或整理追蹤名單。

## 功能

- 支援 Shorts、一般影片與直播分頁
- 可指定輸出的網址數量與檔名
- 每行輸出一個網址，並自動排除重複項目
- 支援互動操作與命令列參數
- 輸出為 UTF-8 編碼 TXT

Shorts 會輸出 `/shorts/影片ID` 網址；一般影片與直播會輸出 `/watch?v=影片ID` 網址。

## 安裝

需要 Python 3.10 以上版本：

```powershell
python -m pip install -r requirements.txt
```

## 完整操作流程

1. 安裝 Python 3.10 或更新版本。
2. 在專案資料夾執行 `python -m pip install -r requirements.txt`。
3. 雙擊 `啟動工具.bat`，或執行 `python youtube_url_tracker.py`。
4. 輸入頻道名稱、`@handle`、頻道 ID 或完整網址。
5. 選擇 Shorts、一般影片或直播。
6. 輸入需要的網址數量及輸出檔名。
7. 程式會顯示實際輸出數量與 TXT 儲存位置。

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

輸入範例：

```text
頻道：@OpenAI
類型：1
數量：20
檔名：OpenAI_shorts.txt
```

直播選項會讀取頻道的直播分頁，其中可能包含目前直播、預定直播及直播存檔。如果頻道內容不足，程式會輸出實際取得的數量並顯示提醒。

### 命令列模式

```powershell
python youtube_url_tracker.py --channel "@OpenAI" --type shorts --count 20 --output shorts清單.txt
```

`--type` 可使用 `shorts`、`videos`、`live`，也接受中文「短影音」、「影片」、「直播」。

命令列參數：

| 參數 | 用途 | 範例 |
| --- | --- | --- |
| `--channel` | 頻道名稱、handle、ID 或網址 | `@OpenAI` |
| `--type` | `shorts`、`videos`、`live` 或中文類型 | `shorts` |
| `--count` | 網址數量，必須大於 0 | `20` |
| `--output` | 輸出檔名或路徑 | `output/list.txt` |

四個參數必須同時提供。完全不提供參數時，程式會進入互動模式。

## 輸出格式

成功後 TXT 會以 UTF-8 編碼儲存，每行一個網址：

```text
https://www.youtube.com/shorts/VIDEO_ID_1
https://www.youtube.com/shorts/VIDEO_ID_2
https://www.youtube.com/shorts/VIDEO_ID_3
```

檔名未包含 `.txt` 時會自動補上；若檔名包含資料夾路徑，程式會自動建立所需資料夾。

## 頻道名稱搜尋

只輸入頻道名稱時，程式會優先選擇名稱完全相同的頻道；若沒有完全相同的結果，則採用 YouTube 的第一個搜尋結果。為避免同名頻道選錯，建議輸入 `@handle` 或完整頻道網址。

## 注意事項

- 若搜尋到錯誤頻道，請改用 `@handle` 或完整頻道首頁網址。
- 取得數量不足通常代表頻道內容不足，或部分內容無法公開讀取。
- 直播分頁可能同時包含目前直播、預定直播與直播存檔。

YouTube 頁面結構可能變動。若讀取失敗，可先更新 `yt-dlp`：

```powershell
python -m pip install -U yt-dlp
```
