from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

import youtube_url_tracker as tracker


class FakeYoutubeDL:
    """以固定回應取代網路存取，讓測試可離線執行。"""

    response: dict = {}

    def __init__(self, _options: dict) -> None:
        pass

    def __enter__(self) -> "FakeYoutubeDL":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def extract_info(self, _target: str, download: bool = False) -> dict:
        assert not download
        return self.response


def install_fake_ydl(monkeypatch: pytest.MonkeyPatch, response: dict) -> None:
    FakeYoutubeDL.response = response
    monkeypatch.setattr(tracker, "yt_dlp", SimpleNamespace(YoutubeDL=FakeYoutubeDL))


@pytest.mark.parametrize(
    ("value", "expected"),
    [("短影音", "shorts"), ("影片", "videos"), ("直播", "streams"), ("  S  ", "shorts")],
)
def test_normalize_content_type(value: str, expected: str) -> None:
    assert tracker.normalize_content_type(value) == expected


def test_validate_count_rejects_outside_safe_range() -> None:
    assert tracker.validate_count(tracker.MAX_URL_COUNT) == tracker.MAX_URL_COUNT
    for invalid_count in (None, 0, -1, tracker.MAX_URL_COUNT + 1):
        with pytest.raises(tracker.TrackerError):
            tracker.validate_count(invalid_count)


def test_channel_base_from_input_normalizes_channel_url() -> None:
    assert tracker.channel_base_from_input("@OpenAI") == "https://www.youtube.com/@OpenAI"
    assert (
        tracker.channel_base_from_input("https://www.youtube.com/@OpenAI/videos")
        == "https://www.youtube.com/@OpenAI"
    )


def test_resolve_channel_uses_exact_name_match(monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_ydl(
        monkeypatch,
        {
            "entries": [
                {"channel": "OpenAI Clips", "channel_url": "https://youtube.com/@clips"},
                {"channel": "OpenAI", "channel_url": "https://youtube.com/@OpenAI"},
            ]
        },
    )

    assert tracker.resolve_channel("OpenAI") == ("https://youtube.com/@OpenAI", "OpenAI")


def test_resolve_channel_rejects_ambiguous_name(monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_ydl(
        monkeypatch,
        {"entries": [{"channel": "OpenAI Clips", "channel_url": "https://youtube.com/@clips"}]},
    )

    with pytest.raises(tracker.TrackerError, match="@handle"):
        tracker.resolve_channel("OpenAI")


def test_collect_urls_deduplicates_and_preserves_content_url_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_ydl(
        monkeypatch,
        {"entries": [{"id": "abc12345"}, {"id": "abc12345"}, {"id": "def67890"}]},
    )

    assert tracker.collect_urls("https://youtube.com/@example", "shorts", 2) == [
        "https://www.youtube.com/shorts/abc12345",
        "https://www.youtube.com/shorts/def67890",
    ]


def test_collect_urls_rejects_empty_result(monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_ydl(monkeypatch, {"entries": []})

    with pytest.raises(tracker.TrackerError, match="未建立輸出檔案"):
        tracker.collect_urls("https://youtube.com/@example", "videos", 1)


def test_write_urls_requires_explicit_overwrite(tmp_path) -> None:
    output = tmp_path / "urls.txt"
    output.write_text("original\n", encoding="utf-8")

    with pytest.raises(tracker.TrackerError, match="已存在"):
        tracker.write_urls(output, ["https://example.com/new"])
    assert output.read_text(encoding="utf-8") == "original\n"

    tracker.write_urls(output, ["https://example.com/new"], overwrite=True)
    assert output.read_text(encoding="utf-8") == "https://example.com/new\n"


def test_confirm_overwrite_accepts_yes_and_defaults_to_no(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    target = tmp_path / "urls.txt"
    monkeypatch.setattr("builtins.input", lambda _prompt: "yes")
    assert tracker.confirm_overwrite(target)

    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    assert not tracker.confirm_overwrite(target)


def test_main_rejects_existing_file_without_overwrite(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "urls.txt"
    output.write_text("original\n", encoding="utf-8")
    monkeypatch.setattr(tracker, "yt_dlp", object())
    monkeypatch.setattr(tracker, "resolve_channel", lambda _channel: ("https://youtube.com/@a", "A"))
    monkeypatch.setattr(tracker, "collect_urls", lambda *_args: ["https://example.com/new"])
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youtube_url_tracker.py",
            "--channel",
            "@a",
            "--type",
            "videos",
            "--count",
            "1",
            "--output",
            str(output),
        ],
    )

    assert tracker.main() == 1
    assert "已存在" in capsys.readouterr().err
    assert output.read_text(encoding="utf-8") == "original\n"


def test_main_allows_explicit_overwrite_and_rejects_empty_urls(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    output = tmp_path / "urls.txt"
    output.write_text("original\n", encoding="utf-8")
    monkeypatch.setattr(tracker, "yt_dlp", object())
    monkeypatch.setattr(tracker, "resolve_channel", lambda _channel: ("https://youtube.com/@a", "A"))
    monkeypatch.setattr(tracker, "collect_urls", lambda *_args: ["https://example.com/new"])
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youtube_url_tracker.py",
            "--channel",
            "@a",
            "--type",
            "videos",
            "--count",
            "1",
            "--output",
            str(output),
            "--overwrite",
        ],
    )

    assert tracker.main() == 0
    assert output.read_text(encoding="utf-8") == "https://example.com/new\n"

    empty_output = tmp_path / "empty.txt"
    monkeypatch.setattr(tracker, "collect_urls", lambda *_args: [])
    monkeypatch.setattr(sys, "argv", sys.argv[:-2] + [str(empty_output), "--overwrite"])
    assert tracker.main() == 1
    assert not empty_output.exists()
