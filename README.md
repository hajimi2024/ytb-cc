# ytb-cc

把一条 YouTube 视频的**已有字幕**收成一份 UTF-8 文本。不下载视频，不做语音识别，不登录账号。

PowerShell、WSL、Mac 用的是同一个命令：

```text
ytb-cc <YouTube链接或11位视频ID>
```

## 拉到本地

需要 Python 3.10 或更高。三个系统都是这三行。第二步会问你把字幕放在哪个文件夹，只问这一次。

```text
git clone https://github.com/hajimi2024/ytb-cc.git
cd ytb-cc
python -m ytb_cc.setup
```

按提示自己输入路径，例如：

| 系统 | 路径样子 |
|---|---|
| WSL | `/mnt/e/YouTube字幕` |
| Windows PowerShell | `D:\YouTube字幕` |
| Mac | `/Users/你的用户名/YouTube字幕` |

目录还不存在时，会再问一次是否创建。回答 `y` 才会创建。

以后要换文件夹，再运行一次 `python -m ytb_cc.setup`。

如果装完提示找不到 `ytb-cc`：WSL 和 Mac 把 `~/.local/bin` 加入 PATH；Windows 确认 Python 的 `Scripts` 目录在 PATH 里。然后新开一个终端。

## 之后每次

```text
ytb-cc https://www.youtube.com/watch?v=VIDEO_ID
ytb-cc VIDEO_ID
ytb-cc --timestamps <链接>
ytb-cc --srt <链接>
ytb-cc --lang zh-Hans en <链接>
ytb-cc -o 某文件.txt <链接>
```

`--lang` 会换成你给的语言顺序。`-o` 只影响这一次，不改已保存的文件夹。

输出文件是 `{你设置的文件夹}/{频道全名}/{标题}.txt`。同名文件直接覆盖。

成功时会有一行文件夹路径。Windows Terminal 里按住 Ctrl 再单击，Mac 的终端里按住 Cmd 再单击，打开这个文件所在的文件夹。

## 终端上要注意的三件事

zsh（WSL 或 Mac）在 `~/.zshrc` 加一行，否则链接里的 `?` 进不了程序：

```zsh
unsetopt nomatch
```

PowerShell、zsh 都一样：链接里有 `&` 时加上引号，否则会被截断。

还没运行过 setup 就执行 `ytb-cc`，程序只提示你先 setup，不会开始下载字幕。

## 字幕怎么选

1. 有中文人工字幕就用中文人工。简体优先于繁体。
2. 没有中文人工时，英语优先于其他语言。英语里先人工、后自动。
3. 两者都没有时，用列表里第一条其他人工字幕。
4. 完全没有人工字幕时，用列表第一条。

拉不到字幕时退出码是 2，不会写文件。终端会显示 `拉取失败:`，以及 `常见原因: 作者关闭字幕 / 会员视频 / 地区限制 / 需要登录`。

## 不做什么

不读剪贴板，不把视频简介全文写进文件，不为没有字幕的视频做语音识别。
