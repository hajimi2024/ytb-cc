#!/usr/bin/env python3
"""
一条命令：拉取 YouTube 标题、频道、发布日期、章节、字幕，汇总成一份 txt。
不下载视频，不重新语音识别。

用法:
  ytb-cc <YouTube链接或11位视频ID>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


VIDEO_ID_RE = re.compile(
    r"(?:v=|/shorts/|/embed/|youtu\.be/)([A-Za-z0-9_-]{11})"
)
DESC_TS_RE = re.compile(
    r"(?m)^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+?)\s*$"
)


def extract_js_object(html: str, marker: str) -> dict | None:
    idx = html.find(marker)
    if idx < 0:
        return None
    brace = html.find("{", idx)
    if brace < 0:
        return None
    depth = 0
    in_str = False
    escape = False
    quote = ""
    for i in range(brace, len(html)):
        ch = html[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_str = False
            continue
        if ch in ('"', "'"):
            in_str = True
            quote = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html[brace : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def extract_video_id(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    match = VIDEO_ID_RE.search(value)
    if match:
        return match.group(1)
    raise ValueError(f"无法从输入里解析视频 ID: {value}")


def http_json(url: str) -> dict | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def http_text(url: str) -> str | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


WIN_BAD = re.compile(r'[<>:"/\\\\|?*]')


def safe_name(name: str, fallback: str, max_len: int = 80) -> str:
    name = WIN_BAD.sub(" ", name or "")
    name = re.sub(r"\s+", " ", name).strip(" .")
    if not name:
        return fallback
    return name[:max_len].rstrip(" .")


def output_file(root: Path, channel_dir: str, title_stem: str) -> Path:
    """输出为 根目录/频道全名/节目标题.txt。同名文件由调用方直接覆盖。"""
    return root / channel_dir / f"{title_stem}.txt"


def platform_kind() -> str:
    """wsl / windows / mac / linux。"""
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "mac"
    if os.environ.get("WSL_DISTRO_NAME"):
        return "wsl"
    try:
        version = Path("/proc/version").read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        version = ""
    if "microsoft" in version or "wsl" in version:
        return "wsl"
    return "linux"


def example_output_dir() -> str:
    """回车时使用的默认绝对路径：当前用户家目录下的 YouTube字幕。"""
    return str((Path.home() / "YouTube字幕").resolve())


def config_path() -> Path:
    override = os.environ.get("YTB_CC_CONFIG")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "ytb-cc" / "config.json"
    return Path.home() / ".config" / "ytb-cc" / "config.json"


def load_saved_dir() -> Path | None:
    path = config_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    raw = (data.get("output_dir") or "").strip()
    if not raw:
        return None
    return Path(raw).expanduser()


def save_output_dir(directory: Path) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"output_dir": str(directory)}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def configured_output_dir() -> Path | None:
    env = os.environ.get("YTB_CC_DIR", "").strip()
    if env:
        return Path(env).expanduser()
    return load_saved_dir()


def clean_entered_path(raw: str) -> str:
    text = (raw or "").strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    return text


def windows_display_path(path: Path) -> str | None:
    """WSL 的 /mnt/e/... 或 Windows 原生路径，转成资源管理器里的写法。"""
    if sys.platform == "win32":
        return str(path.resolve())
    text = path.resolve().as_posix()
    match = re.match(r"^/mnt/([a-zA-Z])(?:/(.*))?$", text)
    if not match:
        return None
    letter = match.group(1).upper()
    rest = (match.group(2) or "").replace("/", "\\")
    return f"{letter}:\\{rest}" if rest else f"{letter}:\\"


def explorer_folder_uri(windows_file: str) -> str:
    """Windows 资源管理器：中文原样放进 file URI，只编码空格等 ASCII。"""
    folder = windows_file.rsplit("\\", 1)[0].replace("\\", "/") + "/"
    encoded = []
    for ch in folder:
        if ord(ch) > 127:
            encoded.append(ch)
        else:
            encoded.append(urllib.parse.quote(ch, safe="/:"))
    return "file:///" + "".join(encoded)


def finder_folder_uri(file_path: str) -> str:
    """Mac 访达：file URI 使用百分号编码。"""
    folder = str(Path(file_path).expanduser().parent).replace("\\", "/")
    if not folder.startswith("/"):
        folder = "/" + folder
    if not folder.endswith("/"):
        folder += "/"
    return "file://" + urllib.parse.quote(folder, safe="/")


def format_terminal_link(uri: str, label: str, tty: bool | None = None) -> str:
    if tty is None:
        tty = sys.stdout.isatty()
    if not tty:
        return label
    return f"\033]8;;{uri}\033\\{label}\033]8;;\033\\"


def folder_link_target(path: Path) -> tuple[str, str, str] | None:
    """(标签, 显示路径, file URI)。无法对应到本机文件夹时返回 None。"""
    if sys.platform == "darwin":
        display = str(path.resolve())
        return ("访达", display, finder_folder_uri(display))
    windows = windows_display_path(path)
    if not windows:
        return None
    return ("资源管理器", windows, explorer_folder_uri(windows))


def folder_open_line(path: Path, tty: bool | None = None) -> str | None:
    target = folder_link_target(path)
    if target is None:
        return None
    label, display, uri = target
    return f"{label}: {format_terminal_link(uri, display, tty=tty)}"


def format_duration(seconds: int | None) -> str:
    if not seconds:
        return ""
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def ts_to_ms(stamp: str) -> int:
    parts = [int(p) for p in stamp.split(":")]
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0, parts[0], parts[1]
    else:
        return 0
    return ((h * 60 + m) * 60 + s) * 1000


def chapters_from_description(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    if not text:
        return found
    for stamp, title in DESC_TS_RE.findall(text.replace("\r", "")):
        title = title.strip(" -–—|")
        if title:
            found.append((ts_to_ms(stamp), title))
    return found


def format_ts_ms(ms: int) -> str:
    total = int(ms) // 1000
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def collect_chapters(node, found: list[tuple[int, str]] | None = None):
    if found is None:
        found = []
    if isinstance(node, dict):
        renderer = node.get("chapterRenderer")
        if isinstance(renderer, dict):
            title_obj = renderer.get("title") or {}
            title = title_obj.get("simpleText") or ""
            if not title:
                runs = title_obj.get("runs") or []
                title = "".join(r.get("text", "") for r in runs)
            start = renderer.get("timeRangeStartMillis", 0)
            if title:
                item = (int(start), title.strip())
                if item not in found:
                    found.append(item)
        for value in node.values():
            collect_chapters(value, found)
    elif isinstance(node, list):
        for item in node:
            collect_chapters(item, found)
    return found


def fetch_meta(video_id: str) -> dict:
    meta = {
        "title": "",
        "channel": "",
        "publish_date": "",
        "duration": "",
        "chapters": [],
    }
    oembed = http_json(
        "https://www.youtube.com/oembed?format=json&url="
        + urllib.parse.quote(f"https://www.youtube.com/watch?v={video_id}")
    )
    if oembed:
        meta["title"] = (oembed.get("title") or "").strip()
        meta["channel"] = (oembed.get("author_name") or "").strip()

    html = http_text(f"https://www.youtube.com/watch?v={video_id}")
    if not html:
        return meta

    player = extract_js_object(html, "ytInitialPlayerResponse") or {}
    data = extract_js_object(html, "ytInitialData") or {}

    details = player.get("videoDetails") or {}
    micro = (player.get("microformat") or {}).get("playerMicroformatRenderer") or {}

    meta["title"] = meta["title"] or (details.get("title") or micro.get("title", {}).get("simpleText") or "").strip()
    meta["channel"] = meta["channel"] or (
        details.get("author") or micro.get("ownerChannelName") or ""
    ).strip()
    meta["publish_date"] = (
        (micro.get("publishDate") or micro.get("uploadDate") or "")[:10]
    )
    length = details.get("lengthSeconds") or micro.get("lengthSeconds")
    if length:
        meta["duration"] = format_duration(int(length))

    chapters = collect_chapters(player)
    if not chapters:
        chapters = collect_chapters(data)
    if not chapters:
        desc = micro.get("description", {}).get("simpleText") or ""
        chapters = chapters_from_description(desc)
    chapters.sort(key=lambda x: x[0])
    meta["chapters"] = chapters
    return meta


_ZH_SIMPLIFIED = ("zh-hans", "zh-cn", "zh-sg")
_ZH_TRADITIONAL = ("zh-hant", "zh-tw", "zh-hk", "zh-mo")
_EN_ORDER = ("en", "en-us", "en-gb")


def _lang_code(track) -> str:
    return (getattr(track, "language_code", "") or "").lower().replace("_", "-")


def _is_chinese(track) -> bool:
    code = _lang_code(track)
    return code == "zh" or code.startswith("zh-")


def _is_english(track) -> bool:
    code = _lang_code(track)
    return code == "en" or code.startswith("en-")


def _listed_rank(code: str, order: tuple[str, ...]) -> int:
    if code in order:
        return order.index(code)
    return len(order)


def _chinese_manual_key(track, index: int) -> tuple[int, int, int]:
    code = _lang_code(track)
    if code in _ZH_SIMPLIFIED or code.startswith("zh-hans-"):
        tier = 0
        rank = _listed_rank(code, _ZH_SIMPLIFIED)
    elif code in _ZH_TRADITIONAL or code.startswith("zh-hant-"):
        tier = 1
        rank = _listed_rank(code, _ZH_TRADITIONAL)
    elif code == "zh":
        tier, rank = 2, 0
    else:
        tier, rank = 3, 0
    return (tier, rank, index)


def _english_key(track, index: int) -> tuple[int, int, int]:
    manual = 0 if not track.is_generated else 1
    return (manual, _listed_rank(_lang_code(track), _EN_ORDER), index)


def select_track(tracks):
    """默认优先级：中文人工 > 英语 > 其他人工 > 列表第一条。"""
    if not tracks:
        raise RuntimeError("这个视频没有可拉取的字幕轨")

    chinese_manual = [
        (i, t) for i, t in enumerate(tracks) if _is_chinese(t) and not t.is_generated
    ]
    if chinese_manual:
        return min(chinese_manual, key=lambda item: _chinese_manual_key(item[1], item[0]))[1]

    english = [(i, t) for i, t in enumerate(tracks) if _is_english(t)]
    if english:
        return min(english, key=lambda item: _english_key(item[1], item[0]))[1]

    for t in tracks:
        if not t.is_generated:
            return t
    return tracks[0]


def select_by_langs(tracks, langs: list[str]):
    """显式 --lang 时仍按给定名单从左到右：精确人工、精确自动、前缀。"""
    if not tracks:
        raise RuntimeError("这个视频没有可拉取的字幕轨")

    for lang in langs:
        for t in tracks:
            if t.language_code == lang and not t.is_generated:
                return t
        for t in tracks:
            if t.language_code == lang:
                return t
        for t in tracks:
            if t.language_code.startswith(lang):
                return t

    for t in tracks:
        if not t.is_generated:
            return t
    return tracks[0]


def pick_transcript(api, video_id: str, langs: list[str] | None):
    listing = api.list(video_id)
    print("可用字幕轨:")
    tracks = []
    for t in listing:
        kind = "自动" if t.is_generated else "人工"
        print(f"  - {t.language_code:10} {t.language:20} [{kind}]")
        tracks.append(t)

    if langs:
        return select_by_langs(tracks, langs)
    return select_track(tracks)


def snippets_to_plain(snippets) -> str:
    parts = []
    for s in snippets:
        text = " ".join(s.text.split())
        if text:
            parts.append(text)
    blob = " ".join(parts)
    blob = re.sub(r"\s+", " ", blob).strip()
    blob = re.sub(r"([.!?。！？])\s*", r"\1\n", blob)
    blob = re.sub(r"\n+", "\n", blob).strip()
    return blob


def snippets_to_timestamped(snippets) -> str:
    lines = []
    for s in snippets:
        total = int(s.start)
        m, sec = divmod(total, 60)
        h, m = divmod(m, 60)
        stamp = f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"
        text = " ".join(s.text.split())
        if text:
            lines.append(f"[{stamp}] {text}")
    return "\n".join(lines)


def build_header(video_id: str, meta: dict, track, kind: str) -> str:
    lines = [
        f"title: {meta.get('title') or '(未获取到标题)'}",
        f"channel: {meta.get('channel') or '(未获取到频道)'}",
        f"published: {meta.get('publish_date') or '(未获取到日期)'}",
        f"duration: {meta.get('duration') or '(未获取到时长)'}",
        f"video_id: {video_id}",
        f"language: {track.language_code} ({track.language})",
        f"source: {kind}",
        f"url: https://www.youtube.com/watch?v={video_id}",
    ]
    chapters = meta.get("chapters") or []
    if chapters:
        lines.append("")
        lines.append("chapters:")
        for start_ms, title in chapters:
            lines.append(f"{format_ts_ms(start_ms)} {title}")
    lines.append("")
    lines.append("----- transcript -----")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="拉取 YouTube 字幕与视频信息为纯文本")
    parser.add_argument("url", help="YouTube 链接或 11 位视频 ID")
    parser.add_argument(
        "--lang",
        nargs="+",
        default=None,
        help="改用这份语言名单，从左到右尝试；不传则中文人工优先，其次英语",
    )
    parser.add_argument("--timestamps", action="store_true", help="保留时间轴")
    parser.add_argument("--srt", action="store_true", help="额外输出 .srt")
    parser.add_argument("-o", "--output", help="输出 txt 路径")
    args = parser.parse_args()

    if not args.output:
        root = configured_output_dir()
        if root is None:
            print(f"还没有字幕输出文件夹。请先在仓库目录运行：{Path(sys.executable).name} -m ytb_cc.setup", file=sys.stderr)
            return 1
        if not root.is_dir():
            print(f"字幕目录不存在：{root}", file=sys.stderr)
            print(f"请重新运行：{Path(sys.executable).name} -m ytb_cc.setup", file=sys.stderr)
            return 1
    else:
        root = None

    try:
        video_id = extract_video_id(args.url)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    print("拉取标题 / 日期 / 章节...")
    meta = fetch_meta(video_id)
    if meta.get("title"):
        print(f"标题: {meta['title']}")

    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()
    try:
        track = pick_transcript(api, video_id, args.lang)
        fetched = track.fetch()
    except Exception as exc:
        print(f"拉取失败: {exc}", file=sys.stderr)
        print("常见原因: 作者关闭字幕 / 会员视频 / 地区限制 / 需要登录", file=sys.stderr)
        return 2

    kind = "自动字幕" if track.is_generated else "人工字幕"
    header = build_header(video_id, meta, track, kind)
    body = snippets_to_timestamped(fetched) if args.timestamps else snippets_to_plain(fetched)
    text = header + body + "\n"

    channel_dir = safe_name(meta.get("channel") or "", f"channel_{video_id}")
    title_stem = safe_name(meta.get("title") or "", video_id)
    if args.output:
        out = Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
    else:
        out = output_file(root, channel_dir, title_stem)
        out.parent.mkdir(exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"\n已写入: {out.resolve()}")
    line = folder_open_line(out)
    if line:
        print(line)
    print(f"字幕轨: {track.language_code} / {kind} / {len(fetched)} 段")
    if meta.get("chapters"):
        print(f"章节: {len(meta['chapters'])} 个")

    if args.srt:
        from youtube_transcript_api.formatters import SRTFormatter

        srt_path = out.with_suffix(".srt")
        srt_path.write_text(SRTFormatter().format_transcript(fetched), encoding="utf-8")
        target = folder_link_target(srt_path)
        if target:
            _, display, uri = target
            print(f"SRT: {format_terminal_link(uri, display)}")
        else:
            print(f"SRT: {srt_path.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
