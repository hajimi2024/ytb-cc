#!/bin/sh
# 服务器上可能没有 Python。这个脚本先补上 Python 3.10+，再进入 setup。
set -eu

cd "$(dirname "$0")"

say() {
  printf '%s\n' "$1"
}

if ! command -v python3 >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1 && [ "$(id -u)" -eq 0 ]; then
    say "没有找到 Python，正在安装 python3、pip 和 venv …"
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
  else
    say "没有找到 Python 3.10 或更高。"
    say "Debian / Ubuntu 请用 root 运行本脚本，或先执行："
    say "  apt update && apt install -y python3 python3-pip python3-venv"
    say "Mac 请先安装 Python 3.10+，再运行：python3 -m ytb_cc.setup"
    exit 1
  fi
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
  say "当前 python3 低于 3.10，无法安装 ytb-cc。"
  python3 --version || true
  exit 1
fi

# Debian / Ubuntu 会拒绝直接往系统 Python 里 pip install。装进仓库内的虚拟环境。
if [ ! -x .venv/bin/python ]; then
  say "正在创建虚拟环境 …"
  python3 -m venv .venv
fi

say "正在安装 ytb-cc …"
.venv/bin/python -m pip install -e .

if [ "$(id -u)" -eq 0 ]; then
  link=/usr/local/bin/ytb-cc
else
  mkdir -p "$HOME/.local/bin"
  link="$HOME/.local/bin/ytb-cc"
fi
ln -sfn "$(pwd)/.venv/bin/ytb-cc" "$link"

if ! command -v ytb-cc >/dev/null 2>&1; then
  say "命令已装到 $link"
  say "如果接下来提示找不到 ytb-cc，请把该目录加入 PATH，然后新开一个终端。"
fi

exec .venv/bin/python -m ytb_cc.setup
