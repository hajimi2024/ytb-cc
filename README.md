# ytb-cc

把一条 YouTube 视频的已有字幕收成一份 UTF-8 文本。不下载视频，不做语音识别，不登录账号。

PowerShell、WSL、Mac 装完之后都用同一个命令。

## 安装

先安装 Python 3.10 或更高，并确认终端里能运行 `python`。没有 Python 时，下面的安装命令不会进入本项目，系统只会提示找不到 `python`。有些系统里的命令是 `python3`，那就把下面的 `python` 换成 `python3`。

三个系统都执行：

```text
git clone https://github.com/hajimi2024/ytb-cc.git
cd ytb-cc
python -m ytb_cc.setup
```

`python -m ytb_cc.setup` 会安装 `ytb-cc`，并只问一次字幕放在哪个文件夹。请自己输入完整路径，例如：

| 系统 | 路径样子 |
|---|---|
| WSL | `/mnt/e/YouTube字幕` |
| Windows PowerShell | `D:\YouTube字幕` |
| Mac | `/Users/你的用户名/YouTube字幕` |

目录还不存在时，会再问一次是否创建。输入 `y` 才会创建。

如果装完提示找不到 `ytb-cc`：WSL 和 Mac 把 `~/.local/bin` 加入 PATH；Windows 确认 Python 的 `Scripts` 目录在 PATH 里。然后新开一个终端。

用 zsh（WSL 或 Mac）时，在 `~/.zshrc` 加一行，否则链接里的 `?` 到不了程序：

```zsh
unsetopt nomatch
```

以后要换字幕文件夹，再运行一次：

```text
python -m ytb_cc.setup
```

## 使用

```text
ytb-cc <YouTube链接或11位视频ID>
```

例如：

```text
ytb-cc https://www.youtube.com/watch?v=VIDEO_ID
ytb-cc VIDEO_ID
ytb-cc --timestamps <链接>
ytb-cc --srt <链接>
ytb-cc --lang zh-Hans en <链接>
ytb-cc -o 某文件.txt <链接>
```

链接里有 `&` 时要加引号，否则 PowerShell 和 zsh 都会把后面截掉。

还没做过安装里的 setup 就运行 `ytb-cc`，程序只提示先运行 `python -m ytb_cc.setup`，不会开始拉字幕。

`--lang` 会换成你给的语言顺序。`-o` 只影响这一次，不改已经保存的文件夹。

输出文件是 `{你设置的文件夹}/{频道全名}/{标题}.txt`。同名文件直接覆盖。

成功时会有一行文件夹路径。Windows Terminal 里按住 Ctrl 再单击，Mac 的终端里按住 Cmd 再单击，打开这个文件所在的文件夹。

字幕按这个顺序选：

1. 有中文人工字幕就用中文人工。简体优先于繁体。
2. 没有中文人工时，英语优先于其他语言。英语里先人工、后自动。
3. 两者都没有时，用列表里第一条其他人工字幕。
4. 完全没有人工字幕时，用列表第一条。

拉不到字幕时退出码是 2，不会写文件。终端会显示 `拉取失败:`，以及 `常见原因: 作者关闭字幕 / 会员视频 / 地区限制 / 需要登录`。

不读剪贴板，不把视频简介全文写进文件，不为没有字幕的视频做语音识别。
