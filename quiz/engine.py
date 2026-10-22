"""答题引擎：抽题、逐题作答、计分（不涉及任何输入输出）。"""

from __future__ import annotations

import random
import time
from datetime import datetime
from typing import Callable, Iterable, Sequence

from .models import Answer, Question, SessionResult


class QuizError(Exception):
    """抽题或作答流程中的可预期错误。"""


def select_questions(
    bank: Sequence[Question],
    count: int = 10,
    categories: Iterable[str] | None = None,
    difficulties: Iterable[int] | None = None,
    seed: int | None = None,
    shuffle: bool = True,
) -> list[Question]:
    """按分类/难度筛题并抽取 count 道；seed 相同则结果可复现。"""
    if count <= 0:
        raise QuizError("题目数量必须大于 0")
    pool = list(bank)
    if categories:
        wanted = {item.strip().lower() for item in categories if item.strip()}
        if wanted:
            pool = [q for q in pool if q.category.lower() in wanted]
    if difficulties:
        levels = set(difficulties)
        pool = [q for q in pool if q.difficulty in levels]
    if not pool:
        raise QuizError("没有符合筛选条件的题目")
    picked = min(count, len(pool))
    if shuffle:
        return random.Random(seed).sample(pool, picked)
    return pool[:picked]


class Session:
    """一轮答题的状态机；clock 可注入，便于测试用假时间。"""

    def __init__(
        self,
        questions: Sequence[Question],
        mode: str = "exam",
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not questions:
            raise QuizError("至少需要一道题目才能开始")
        if mode not in ("practice", "exam"):
            raise QuizError(f"未知模式：{mode}")
        self._questions = list(questions)
        self.mode = mode
        self._clock = clock
        self._index = 0
        self._finished = False
        self._started_at: datetime | None = None
        self._started_clock = 0.0
        self._question_started = 0.0
        self.answers: list[Answer] = []

    def start(self) -> "Session":
        self._started_at = datetime.now()
        self._started_clock = self._clock()
        self._question_started = self._started_clock
        return self

    @property
    def started_at(self) -> datetime:
        return self._started_at or datetime.now()

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def questions(self) -> list[Question]:
        return list(self._questions)

    @property
    def current(self) -> Question | None:
        return None if self.finished else self._questions[self._index]

    @property
    def position(self) -> int:
        """当前第几题（从 1 开始），结束后等于总题数。"""
        return min(self._index + 1, len(self._questions))

    @property
    def total(self) -> int:
        return len(self._questions)

    @property
    def correct_count(self) -> int:
        return sum(1 for item in self.answers if item.correct)

    @property
    def score(self) -> int:
        return sum(item.points for item in self.answers)

    def submit(self, choice: int | None) -> Answer:
        """提交当前题答案；choice 为 None 表示跳过（记为答错、0 分）。"""
        if self.finished:
            raise QuizError("本轮答题已经结束")
        question = self._questions[self._index]
        if choice is not None and not 0 <= choice < len(question.options):
            raise QuizError(f"选项下标越界：{choice}")
        now = self._clock()
        correct = choice is not None and choice == question.answer
        answer = Answer(
            question_id=question.id,
            category=question.category,
            difficulty=question.difficulty,
            choice=choice,
            correct=correct,
            elapsed=round(max(0.0, now - self._question_started), 3),
            points=question.points if correct else 0,
        )
        self.answers.append(answer)
        self._index += 1
        self._question_started = now
        self._finished = self._index >= len(self._questions)
        return answer

    def result(self) -> SessionResult:
        """生成结果快照（未答完也可取，用于中途退出时展示）。"""
        elapsed = max(0.0, self._clock() - self._started_clock)
        return SessionResult(
            mode=self.mode,
            started_at=self.started_at,
            duration=round(elapsed, 3),
            answers=list(self.answers),
        )
