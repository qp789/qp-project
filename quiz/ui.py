"""终端 UI：颜色、题目卡片、进度条与结果摘要。

非 TTY 环境（管道、CI）或设置了 NO_COLOR 时自动关闭颜色。
"""

from __future__ import annotations

import os
import shutil
import sys
import unicodedata
from typing import Sequence, TextIO

from .models import Answer, Question, SessionResult, label_for

RESET = "\033[0m"
STYLES = {
    "bold": "\033[1m", "dim": "\033[2m", "red": "\033[31m", "green": "\033[32m",
    "yellow": "\033[33m", "blue": "\033[34m", "magenta": "\033[35m", "cyan": "\033[36m",
}
DIFFICULTY_STARS = {1: "★☆☆", 2: "★★☆", 3: "★★★"}


def display_width(text: str) -> int:
    """按终端列宽计算宽度（中文/全角字符占两列）。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def pad(text: str, width: int) -> str:
    return text + " " * max(0, width - display_width(text))


def format_duration(seconds: float) -> str:
    total = int(round(max(0.0, seconds)))
    minutes, secs = divmod(total, 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class Console:
    """极简输出封装：统一处理颜色开关与缩进。"""

    def __init__(self, color: bool | None = None, stream: TextIO | None = None) -> None:
        self.stream = stream or sys.stdout
        if color is None:
            color = self._supports_color(self.stream)
        self.color = color

    @staticmethod
    def _supports_color(stream: TextIO) -> bool:
        if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
            return False
        isatty = getattr(stream, "isatty", None)
        return bool(isatty and isatty())

    def paint(self, text: str, *styles: str) -> str:
        if not self.color or not styles:
            return text
        return "".join(STYLES.get(style, "") for style in styles) + text + RESET

    def write(self, text: str = "") -> None:
        print(text, file=self.stream)

    def error(self, text: str) -> None:
        self.write(self.paint(f"错误：{text}", "red", "bold"))

    def info(self, text: str) -> None:
        self.write(self.paint(text, "dim"))

    def rule(self, title: str = "") -> None:
        width = max(24, min(72, shutil.get_terminal_size((72, 24)).columns))
        if not title:
            self.write(self.paint("─" * width, "dim"))
            return
        decorated = f" {title} "
        side = max(0, (width - len(decorated)) // 2)
        self.write(self.paint("─" * side + decorated + "─" * max(0, width - side - len(decorated)),
                              "cyan"))

    def progress_bar(self, done: int, total: int, width: int = 20) -> str:
        ratio = min(1.0, max(0.0, done / max(1, total)))
        filled = int(round(ratio * width))
        return f"{'█' * filled}{'░' * (width - filled)} {ratio * 100:3.0f}%"

    def question_card(self, question: Question, position: int, total: int,
                      elapsed: float | None = None) -> None:
        meta = (f"[{position}/{total}] {question.category} · "
                f"难度 {DIFFICULTY_STARS[question.difficulty]} · 分值 {question.points}")
        if elapsed is not None:
            meta += f" · 用时 {format_duration(elapsed)}"
        self.write()
        self.write(self.paint(meta, "dim"))
        self.write(self.paint(self.progress_bar(position - 1, total), "cyan"))
        self.write()
        for line in question.prompt.splitlines() or [""]:
            self.write(f"  {line}")
        self.write()
        for index, option in enumerate(question.options):
            self.write(f"  {self.paint(label_for(index) + '.', 'bold')} {option}")

    def feedback(self, question: Question, answer: Answer) -> None:
        if answer.correct:
            self.write(self.paint(f"✔ 回答正确（+{answer.points} 分）", "green", "bold"))
        elif answer.choice is None:
            self.write(self.paint("↷ 已跳过（本题 0 分）", "yellow"))
        else:
            self.write(self.paint(f"✘ 回答错误，你选了 {label_for(answer.choice)}", "red", "bold"))
        if not answer.correct:
            self.write(f"  正确答案：{question.answer_label}")
        self.write(self.paint(f"  解析：{question.explanation}", "dim"))

    def summary(self, result: SessionResult, best: int, new_record: bool = False) -> None:
        self.write()
        self.rule("结果")
        mode_name = "练习" if result.mode == "practice" else "考试"
        self.write(f"模式：{mode_name}    用时：{format_duration(result.duration)}    "
                   f"得分：{self.paint(f'{result.score}/{result.max_score}', 'bold')}")
        self.write(f"正确：{result.correct_count}/{result.total}    "
                   f"正确率：{result.accuracy * 100:.1f}%")
        self.write(self.paint(f"历史最佳：{best} 分" + ("（新纪录！）" if new_record else ""),
                              "green" if new_record else "dim"))
        breakdown = result.category_breakdown()
        if breakdown:
            self.write()
            self.write(self.paint("分类正确率：", "bold"))
            for name, (ok, total) in breakdown.items():
                self.write(f"  {name:<6} {ok}/{total}  {ok / total * 100:5.1f}%")

    def review(self, pairs: Sequence[tuple[Question, Answer]]) -> None:
        if not pairs:
            return
        self.write()
        self.rule("错题回顾")
        for question, answer in pairs:
            self.write()
            self.write(self.paint(f"[{question.id}] {question.prompt.splitlines()[0]}", "bold"))
            chosen = "跳过" if answer.choice is None else label_for(answer.choice)
            self.write(f"  你的选择：{chosen}")
            self.write(self.paint(f"  正确答案：{question.answer_label}", "green"))
            self.write(self.paint(f"  解析：{question.explanation}", "dim"))

    def table(self, headers: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
        widths = [display_width(str(h)) for h in headers]
        for row in rows:
            for index in range(len(headers)):
                widths[index] = max(widths[index], display_width(str(row[index])))
        self.write(self.paint("  ".join(pad(str(h), widths[i])
                                        for i, h in enumerate(headers)).rstrip(), "bold"))
        for row in rows:
            self.write("  ".join(pad(str(cell), widths[i]) for i, cell in enumerate(row)).rstrip())
