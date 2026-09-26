"""第一次把仓库拿到本机时运行：python -m ytb_cc.setup"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ytb_cc import (
    clean_entered_path,
    example_output_dir,
    load_saved_dir,
    save_output_dir,
)


def repo_root() -> Path | None:
    root = Path(__file__).resolve().parents[1]
    toml = root / "pyproject.toml"
    if not toml.is_file():
        return None
    text = toml.read_text(encoding="utf-8")
    if 'name = "ytb-cc"' not in text:
        return None
    return root


def install_command(root: Path) -> int:
    print("正在安装 ytb-cc …")
    completed = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", str(root)],
        check=False,
    )
    if completed.returncode != 0:
        print("安装失败。请确认当前 Python 是 3.10 或更高，并且 pip 可用。", file=sys.stderr)
    return completed.returncode


def confirm(prompt: str, input_fn) -> bool:
    answer = input_fn(prompt).strip().lower()
    return answer in {"y", "yes", "是"}


def run_setup(input_fn=input, isatty: bool | None = None, install: bool | None = None) -> int:
    if isatty is None:
        isatty = sys.stdin.isatty()
    if not isatty:
        print("请在交互终端里运行：python -m ytb_cc.setup", file=sys.stderr)
        return 1

    if install is None:
        install = repo_root() is not None
    if install:
        root = repo_root()
        if root is None:
            print("找不到仓库里的 pyproject.toml，未安装命令。", file=sys.stderr)
            return 1
        code = install_command(root)
        if code != 0:
            return code

    current = load_saved_dir()
    if current is not None:
        print(f"当前字幕目录：{current}")
        if not confirm("要更换吗？输入 y 更换，其他键保持：", input_fn):
            print("保持不变。以后使用：ytb-cc <链接>")
            return 0

    print("请设置一个专门用来放字幕的文件夹。")
    print("设置好之后，每次只要运行 ytb-cc <链接>，不用再填路径。")
    print(f"示例：{example_output_dir()}")
    entered = clean_entered_path(input_fn("路径："))
    if not entered:
        print("没有输入路径，未保存。", file=sys.stderr)
        return 1

    directory = Path(entered).expanduser()
    if directory.exists() and not directory.is_dir():
        print("这不是文件夹，未保存。", file=sys.stderr)
        return 1
    if not directory.exists():
        if not confirm(f"目录不存在：{directory}\n是否创建？输入 y 创建：", input_fn):
            print("未创建，未保存。", file=sys.stderr)
            return 1
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(f"无法创建：{exc}", file=sys.stderr)
            return 1
    try:
        probe = directory / ".ytb-cc-write-test"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        print(f"不能写入这个文件夹：{exc}", file=sys.stderr)
        return 1

    save_output_dir(directory.resolve())
    print(f"已保存：{directory.resolve()}")
    print("以后使用：ytb-cc <链接>")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_setup())
