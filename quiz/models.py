"""数据模型：题目、作答记录与会话结果。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence

LABELS = ("A", "B", "C", "D", "E", "F")


def label_for(index: int) -> str:
    """选项下标转标签：0 -> "A"，超出 A-F 退回数字。"""
    return LABELS[index] if 0 <= index < len(LABELS) else str(index + 1)


@dataclass(frozen=True)
class Question:
    """单选题：options 为选项文本，answer 为正确选项下标（0 起）。"""

    id: str
    category: str
    difficulty: int
    prompt: str
    options: Sequence[str]
    answer: int
    explanation: str

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.category.strip() or not self.prompt.strip():
            raise ValueError(f"题目 {self.id or '?'} 缺少 id/分类/题干")
        if self.difficulty not in (1, 2, 3):
            raise ValueError(f"题目 {self.id} 的 difficulty 必须是 1/2/3")
        if len(self.options) < 2:
            raise ValueError(f"题目 {self.id} 至少需要两个选项")
        if not 0 <= self.answer < len(self.options):
            raise ValueError(f"题目 {self.id} 的 answer 下标越界")
        if not self.explanation.strip():
            raise ValueError(f"题目 {self.id} 缺少解析")

    @property
    def points(self) -> int:
        """答对得分：难度 1/2/3 对应 10/14/18 分。"""
        return 10 + 4 * (self.difficulty - 1)

    @property
    def answer_label(self) -> str:
        return label_for(self.answer)


@dataclass
class Answer:
    """一次作答：选择、对错、耗时与得分。"""

    question_id: str
    category: str
    difficulty: int
    choice: int | None
    correct: bool
    elapsed: float
    points: int

    @property
    def max_points(self) -> int:
        return 10 + 4 * (self.difficulty - 1)


@dataclass
class SessionResult:
    """一轮答题的完整结果，可直接交给 Store 持久化。"""

    mode: str
    started_at: datetime
    duration: float
    answers: list[Answer] = field(default_factory=list)
    session_id: int | None = None

    @property
    def total(self) -> int:
        return len(self.answers)

    @property
    def correct_count(self) -> int:
        return sum(1 for item in self.answers if item.correct)

    @property
    def score(self) -> int:
        return sum(item.points for item in self.answers)

    @property
    def max_score(self) -> int:
        return sum(item.max_points for item in self.answers)

    @property
    def accuracy(self) -> float:
        return self.correct_count / self.total if self.total else 0.0

    def category_breakdown(self) -> dict[str, tuple[int, int]]:
        """{分类: (答对数, 总数)}，按题量降序。"""
        buckets: dict[str, list[int]] = {}
        for item in self.answers:
            stat = buckets.setdefault(item.category, [0, 0])
            stat[0] += 1 if item.correct else 0
            stat[1] += 1
        ordered = sorted(buckets.items(), key=lambda kv: (-kv[1][1], kv[0]))
        return {name: (ok, total) for name, (ok, total) in ordered}
