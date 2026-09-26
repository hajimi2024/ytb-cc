<div align="center">

# 🎬 ytb-cc

**把 YouTube 已有字幕收成一份文本**

[先检查 Python](#-先检查-python) · [安装 Python](#-安装-python) · [拉取并设置文件夹](#-拉取并设置文件夹) · [使用](#-使用) · [清除](#-清除)

</div>

<div align="center">

<pre><code>
                                 ██╗   ██╗████████╗██████╗        ██████╗ ██████╗
                                 ╚██╗ ██╔╝╚══██╔══╝██╔══██╗      ██╔════╝██╔════╝
                                  ╚████╔╝    ██║   ██████╔╝█████╗██║     ██║     
                                   ╚██╔╝     ██║   ██╔══██╗╚════╝██║     ██║     
                                    ██║      ██║   ██████╔╝      ╚██████╗╚██████╗
                                    ╚═╝      ╚═╝   ╚═════╝        ╚═════╝ ╚═════╝
                                                

                                    ─────────●──────────●─────────●───────      
                                           PowerShell    WSL      macOS           
</code></pre>

<p>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white">
  <img alt="Platforms" src="https://img.shields.io/badge/Platforms-PowerShell_%E2%80%A2_WSL_%E2%80%A2_macOS-16a34a?style=flat-square">
  <img alt="One command" src="https://img.shields.io/badge/Command-ytb--cc-d97706?style=flat-square">
  <br>
  <img alt="YouTube captions" src="https://img.shields.io/badge/Source-Existing_captions-b91c1c?style=flat-square">
  <img alt="Output" src="https://img.shields.io/badge/Output-UTF--8_txt-0891b2?style=flat-square">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-4f46e5?style=flat-square">
</p>

</div>

---

## 🐍 先检查 Python

这一步只查版本，不安装，也不拉仓库。需要 **Python 3.10 或更高**。

WSL、Mac：

```bash
python3 --version
```

Windows PowerShell：

```powershell
python --version
```

显示出 `Python 3.10`、`3.11`、`3.12` 或更高，就跳到后面的「拉取并设置文件夹」。提示找不到命令，或者版本低于 3.10，先做下一节。

## 📦 安装 Python

没有安装时用安装命令。已经安装但版本过旧时用更新命令。做完再查一次版本。

WSL 安装：

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv
```

WSL 更新：

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv
python3 --version
```

Windows 安装：

```powershell
winget install Python.Python.3.12
```

Windows 更新：

```powershell
winget upgrade Python.Python.3.12
```

装完后关掉终端再开一个，然后重新查版本。

Mac（已安装 Homebrew）安装：

```bash
brew install python@3.12
```

Mac 更新：

```bash
brew upgrade python@3.12
python3 --version
```

## 📥 拉取并设置文件夹

版本合格后再执行。WSL、Mac：

```bash
git clone https://github.com/hajimi2024/ytb-cc.git
cd ytb-cc
python3 -m ytb_cc.setup && cd ~
```

Windows PowerShell：

```powershell
git clone https://github.com/hajimi2024/ytb-cc.git
cd ytb-cc
python -m ytb_cc.setup; if ($LASTEXITCODE -eq 0) { Set-Location ~ }
```

WSL 里的 Ubuntu 不允许把程序直接装进系统 Python。setup 会在仓库里建一个虚拟环境再安装，不用额外加参数。如果提示无法创建虚拟环境，先执行 `sudo apt install -y python3-venv`，然后重新运行 setup。

setup 装好命令后，只问一次字幕文件夹。

- 直接按回车：使用默认文件夹，并自动创建。WSL 和 Mac 在家目录下的 `YouTube字幕`，Windows 是 `C:\Users\当前用户\YouTube字幕`。
- 要自定义：输入绝对路径，例如 `/mnt/e/YouTube字幕` 或 `D:\YouTube字幕`。相对路径不会被接受。

成功后终端回到登录时的目录，提示符从 `~/ytb-cc #` 回到 `~ #`。这是家目录，不是硬盘最顶层的 `/`。安装失败时不会跳走。

Windows 会把 `ytb-cc` 放到 `%USERPROFILE%\.local\bin`，并写入用户 PATH。请新开一个 PowerShell 窗口再用。WSL 和 Mac 如果提示找不到命令，把 `~/.local/bin` 加入 PATH，然后新开一个终端。

用 zsh（WSL 或 Mac）时，在 `~/.zshrc` 加一行，否则链接里的 `?` 到不了程序：

```zsh
unsetopt nomatch
```

以后要换字幕文件夹，先进仓库再运行一次 setup，成功后同样回到家目录。WSL、Mac 用 `python3 -m ytb_cc.setup && cd ~`，Windows 用 `python -m ytb_cc.setup`，成功后再 `Set-Location ~`。

## 💬 使用

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

- 链接里有 `&` 时要加引号，否则 PowerShell 和 zsh 都会把后面截掉。
- 还没做过安装里的 setup 就运行 `ytb-cc`，程序只提示先完成上面的安装，不会开始拉字幕。
- `--lang` 会换成你给的语言顺序。`-o` 只影响这一次，不改已经保存的文件夹。

输出文件是 `{你设置的文件夹}/{频道全名}/{标题}.txt`。同名文件直接覆盖。

成功时会有一行文件夹路径。Windows Terminal 里按住 **Ctrl** 再单击，Mac 的终端里按住 **Cmd** 再单击，打开这个文件所在的文件夹。

## 🈶 字幕选择

1. 有中文人工字幕就用中文人工。简体优先于繁体。
2. 没有中文人工时，英语优先于其他语言。英语里先人工、后自动。
3. 两者都没有时，用列表里第一条其他人工字幕。
4. 完全没有人工字幕时，用列表第一条。

拉不到字幕时退出码是 `2`，不会写文件。终端会显示 `拉取失败:`，以及：

```text
常见原因: 作者关闭字幕 / 会员视频 / 地区限制 / 需要登录
```

## 🛡️ 不做的事

- 不读剪贴板。
- 不把视频简介全文写进文件。
- 不为没有字幕的视频做语音识别。

## 🧹 清除

以后如果想卸掉这个命令，在家目录执行。这只删除程序、配置和克隆下来的仓库，不删除已经生成的字幕文件夹。

WSL、Mac：

```bash
python3 -m pip uninstall -y ytb-cc
rm -rf ~/.config/ytb-cc ~/ytb-cc
```

Windows PowerShell：

```powershell
python -m pip uninstall -y ytb-cc
Remove-Item -Recurse -Force "$env:APPDATA\ytb-cc", "$env:USERPROFILE\ytb-cc", "$env:USERPROFILE\.local\bin\ytb-cc.cmd"
```

字幕如果也要删，再自己删除当时设置的那个文件夹。

## 📄 License

MIT License. 详情见 [LICENSE](LICENSE)。
