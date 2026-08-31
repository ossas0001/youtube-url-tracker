#!/usr/bin/env python3
"""依 YouTube 頻道與內容類型，將指定數量的網址輸出成 TXT。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import yt_dlp
except ImportError:  # pragma: no cover - 僅在未安裝相依套件時執行
    yt_dlp = None


TYPE_ALIASES = {
    "1": "shorts",
    "short": "shorts",
    "shorts": "shorts",
    "s": "shorts",
    "短片": "shorts",
    "短影音": "shorts",
    "2": "videos",
    "video": "videos",
    "videos": "videos",
    "v": "videos",
    "影片": "videos",
    "一般影片": "videos",
    "3": "streams",
    "live": "streams",
    "lives": "streams",
    "stream": "streams",
    "streams": "streams",
    "l": "streams",
    "直播": "streams",
}

TYPE_NAMES = {
    "shorts": "Shorts",
    "videos": "影片",
    "streams": "直播",
}

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
}


class TrackerError(RuntimeError):
    """可直接顯示給使用者的錯誤。"""


def normalize_content_type(value: str) -> str:
    key = value.strip().casefold()
    try:
        return TYPE_ALIASES[key]
    except KeyError as exc:
        raise TrackerError("內容類型請輸入 Shorts、影片或直播（也可輸入 1、2、3）。") from exc


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", "", value).lstrip("@").casefold()


def channel_base_from_input(channel: str) -> str | None:
    """若輸入已足以組成頻道網址就直接回傳，否則回傳 None。"""
    value = channel.strip()
    if not value:
        raise TrackerError("頻道名稱不能是空白。")

    if value.startswith("@") and len(value) > 1:
        return f"https://www.youtube.com/{value}"

    if re.fullmatch(r"UC[\w-]{20,}", value):
        return f"https://www.youtube.com/channel/{value}"

    candidate = value if "://" in value else f"https://{value}"
    parsed = urlparse(candidate)
    if parsed.hostname and parsed.hostname.casefold() in YOUTUBE_HOSTS:
        parts = [part for part in parsed.path.split("/") if part]
        if not parts:
            raise TrackerError("請輸入完整的 YouTube 頻道網址。")

        first = parts[0]
        if first.startswith("@"):
            return f"https://www.youtube.com/{first}"
        if first in {"channel", "c", "user"} and len(parts) >= 2:
            return f"https://www.youtube.com/{first}/{parts[1]}"
        raise TrackerError("這看起來不是 YouTube 頻道網址；請改貼頻道首頁網址。")

    return None


def ydl_options(limit: int | None = None) -> dict[str, Any]:
    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
    }
    if limit is not None:
        options["playlistend"] = limit
    return options


def resolve_channel(channel: str) -> tuple[str, str]:
    """將名稱、handle、ID 或網址解析成頻道首頁網址與顯示名稱。"""
    direct_url = channel_base_from_input(channel)
    if direct_url:
        return direct_url.rstrip("/"), channel.strip()

    query = channel.strip()
    with yt_dlp.YoutubeDL(ydl_options(limit=8)) as ydl:
        info = ydl.extract_info(f"ytsearch8:{query}", download=False)

    entries = [entry for entry in (info or {}).get("entries", []) if entry]
    if not entries:
        raise TrackerError(f"找不到頻道「{query}」，請改用 @handle 或完整頻道網址。")

    wanted = normalize_name(query)
    candidates: list[tuple[str, str]] = []
    for entry in entries:
        name = str(entry.get("channel") or entry.get("uploader") or "").strip()
        url = entry.get("channel_url") or entry.get("uploader_url")
        channel_id = entry.get("channel_id")
        if not url and channel_id:
            url = f"https://www.youtube.com/channel/{channel_id}"
        if url:
            candidates.append((str(url).rstrip("/"), name or query))

    if not candidates:
        raise TrackerError(f"搜尋到「{query}」的影片，但無法取得它的頻道網址。")

    for url, name in candidates:
        if normalize_name(name) == wanted:
            return url, name
    return candidates[0]


def video_id_from_entry(entry: dict[str, Any]) -> str | None:
    video_id = entry.get("id")
    if video_id and re.fullmatch(r"[\w-]{6,}", str(video_id)):
        return str(video_id)

    raw_url = str(entry.get("webpage_url") or entry.get("url") or "")
    match = re.search(r"(?:v=|/shorts/|/live/)([\w-]{6,})", raw_url)
    return match.group(1) if match else None


def collect_urls(channel_url: str, content_type: str, count: int) -> list[str]:
    tab_url = f"{channel_url.rstrip('/')}/{content_type}"
    # 多抓一些項目，避免置頂項目或無法解析的項目使最後數量不足。
    fetch_limit = max(count + 10, count * 2)
    with yt_dlp.YoutubeDL(ydl_options(limit=fetch_limit)) as ydl:
        info = ydl.extract_info(tab_url, download=False)

    if not info:
        raise TrackerError(f"無法讀取頻道的「{TYPE_NAMES[content_type]}」分頁。")

    urls: list[str] = []
    seen: set[str] = set()
    for entry in info.get("entries") or []:
        if not entry:
            continue
        video_id = video_id_from_entry(entry)
        if not video_id or video_id in seen:
            continue
        seen.add(video_id)
        if content_type == "shorts":
            urls.append(f"https://www.youtube.com/shorts/{video_id}")
        else:
            urls.append(f"https://www.youtube.com/watch?v={video_id}")
        if len(urls) >= count:
            break
    return urls


def output_path_from_name(filename: str) -> Path:
    value = filename.strip().strip('"')
    if not value:
        raise TrackerError("檔案名稱不能是空白。")
    path = Path(value).expanduser()
    if path.suffix.casefold() != ".txt":
        path = path.with_name(path.name + ".txt")
    return path


def write_urls(path: Path, urls: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(urls)
    if content:
        content += "\n"
    path.write_text(content, encoding="utf-8")


def ask_positive_integer(prompt: str) -> int:
    while True:
        value = input(prompt).strip()
        try:
            number = int(value)
            if number > 0:
                return number
        except ValueError:
            pass
        print("請輸入大於 0 的整數。")


def interactive_inputs() -> tuple[str, str, int, str]:
    print("YouTube 頻道網址整理工具")
    print("內容類型：1 = Shorts、2 = 影片、3 = 直播")
    channel = input("頻道名稱、@handle 或頻道網址：").strip()
    content_type = input("要追蹤的內容類型：").strip()
    count = ask_positive_integer("要輸出的網址數量：")
    filename = input("輸出檔案名稱：").strip()
    return channel, content_type, count, filename


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="將指定 YouTube 頻道的 Shorts、影片或直播網址整理成 TXT。"
    )
    parser.add_argument("--channel", help="頻道名稱、@handle、頻道 ID 或頻道網址")
    parser.add_argument("--type", dest="content_type", help="shorts、videos 或 live")
    parser.add_argument("--count", type=int, help="要輸出的網址數量")
    parser.add_argument("--output", help="輸出 TXT 檔名")
    return parser


def main() -> int:
    if yt_dlp is None:
        print("錯誤：尚未安裝 yt-dlp，請先執行：pip install -r requirements.txt", file=sys.stderr)
        return 1

    args = build_parser().parse_args()
    provided = [args.channel, args.content_type, args.count, args.output]
    if any(value is not None for value in provided):
        if not all(value is not None for value in provided):
            print("錯誤：命令列模式必須同時提供 --channel、--type、--count、--output。", file=sys.stderr)
            return 2
        channel, raw_type, count, filename = (
            args.channel,
            args.content_type,
            args.count,
            args.output,
        )
    else:
        channel, raw_type, count, filename = interactive_inputs()

    try:
        content_type = normalize_content_type(str(raw_type))
        if count is None or count <= 0:
            raise TrackerError("網址數量必須是大於 0 的整數。")
        output_path = output_path_from_name(str(filename))

        print("正在尋找頻道……")
        channel_url, channel_name = resolve_channel(str(channel))
        print(f"已找到：{channel_name}（{channel_url}）")
        print(f"正在讀取{TYPE_NAMES[content_type]}網址……")
        urls = collect_urls(channel_url, content_type, count)
        write_urls(output_path, urls)
    except TrackerError as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"錯誤：YouTube 資料讀取失敗：{exc}", file=sys.stderr)
        print("提示：可先執行 pip install -U yt-dlp 再重試。", file=sys.stderr)
        return 1

    resolved = output_path.resolve()
    print(f"完成：已將 {len(urls)} 個網址寫入 {resolved}")
    if len(urls) < count:
        print(f"注意：此分頁目前只取得 {len(urls)} 個可用網址，少於要求的 {count} 個。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
