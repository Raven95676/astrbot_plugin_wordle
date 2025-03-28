# astrbot_plugin_wordle

> [!important]
> 正在准备对插件进行重构以支持会话控制功能。

Astrbot wordle游戏，支持指定位数

命令：
- wordle start [位数] - 开始一局游戏，位数可选，例如 wordle start 5
- wordle stop - 终止游戏
- wordle hint - 获取第一个字母
- wordle octordle - 开始一局octordle游戏（同时猜8个wordle）

如需替换词表，请替换插件根目录下的wordlist.txt

内置词表classic部分来自KyleBing的[english-vocabulary](https://github.com/KyleBing/english-vocabulary)
内置词表all来自dwyl的[english-words](https://github.com/dwyl/english-words)