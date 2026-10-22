#!/usr/bin/env python3
"""qpquiz 命令行入口。

用法：
    python3 main.py                 # 直接开始默认的 10 题考试模式
    python3 main.py play -n 15      # 15 题
    python3 main.py list            # 看题库
    python3 main.py stats           # 看统计
"""

from quiz.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
