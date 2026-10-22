"""单元测试：python3 -m unittest discover -s tests -v"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from quiz.bank import QUESTIONS, by_id
from quiz.cli import QUIT, parse_choice
from quiz.engine import QuizError, Session, select_questions
from quiz.models import Question
from quiz.storage import Store
from quiz.ui import Console, format_duration


def make_session(count: int = 3, mode: str = "exam") -> Session:
    return Session(select_questions(QUESTIONS, count=count, seed=42), mode=mode).start()


class BankTests(unittest.TestCase):
    def test_bank_integrity(self) -> None:
        self.assertEqual(len(QUESTIONS), 15)
        self.assertEqual(len({q.id for q in QUESTIONS}), 15)
        for question in QUESTIONS:
            self.assertIn(question.difficulty, (1, 2, 3))
            self.assertTrue(0 <= question.answer < len(question.options))
            self.assertTrue(question.explanation.strip())

    def test_lookup(self) -> None:
        self.assertEqual(by_id("q01").id, "q01")
        with self.assertRaises(KeyError):
            by_id("nope")

    def test_invalid_question_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Question(id="x", category="基础", difficulty=1, prompt="p",
                     options=("a", "b"), answer=5, explanation="e")


class SelectionTests(unittest.TestCase):
    def test_filter_and_cap(self) -> None:
        picked = select_questions(QUESTIONS, count=99, categories=["函数"])
        self.assertTrue(picked)
        self.assertTrue(all(q.category == "函数" for q in picked))
        self.assertEqual(len(select_questions(QUESTIONS, count=100)), len(QUESTIONS))

    def test_seed_reproducible(self) -> None:
        first = [q.id for q in select_questions(QUESTIONS, count=5, seed=7)]
        self.assertEqual(first, [q.id for q in select_questions(QUESTIONS, count=5, seed=7)])

    def test_errors(self) -> None:
        with self.assertRaises(QuizError):
            select_questions(QUESTIONS, count=3, categories=["不存在"])
        with self.assertRaises(QuizError):
            select_questions(QUESTIONS, count=0)


class SessionTests(unittest.TestCase):
    def test_all_correct_full_score(self) -> None:
        session = make_session()
        while not session.finished:
            question = session.current
            assert question is not None
            session.submit(question.answer)
        result = session.result()
        self.assertEqual(result.score, result.max_score)
        self.assertAlmostEqual(result.accuracy, 1.0)

    def test_wrong_and_skip_score_zero(self) -> None:
        session = make_session()
        question = session.current
        assert question is not None
        wrong = (question.answer + 1) % len(question.options)
        self.assertFalse(session.submit(wrong).correct)
        self.assertIsNone(session.submit(None).choice)

    def test_cannot_answer_after_finish(self) -> None:
        session = make_session(count=2)
        session.submit(0)
        session.submit(0)
        self.assertTrue(session.finished)
        self.assertIsNone(session.current)
        with self.assertRaises(QuizError):
            session.submit(0)


class ParseChoiceTests(unittest.TestCase):
    def test_parse(self) -> None:
        self.assertEqual(parse_choice("b", 4), 1)
        self.assertEqual(parse_choice("3", 4), 2)
        self.assertIsNone(parse_choice("s", 4))
        self.assertIs(parse_choice("q", 4), QUIT)
        for bad in ("", "z", "9"):
            self.assertEqual(parse_choice(bad, 4), "")


class StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "history.db")

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def test_roundtrip(self) -> None:
        self.assertEqual(self.store.stats().sessions, 0)
        session = make_session(3)
        while not session.finished:
            session.submit(0)
        result = session.result()
        self.assertGreater(self.store.save(result), 0)
        stats = self.store.stats()
        self.assertEqual((stats.sessions, stats.answers), (1, 3))
        self.assertEqual(stats.best_score, result.score)
        self.assertEqual(self.store.recent(5)[0]["total"], 3)
        self.assertEqual(sum(i["total"] for i in self.store.category_stats()), 3)
        self.store.reset()
        self.assertEqual(self.store.stats().sessions, 0)


class UiTests(unittest.TestCase):
    def test_format_duration(self) -> None:
        self.assertEqual(format_duration(0), "00:00")
        self.assertEqual(format_duration(65), "01:05")
        self.assertEqual(format_duration(3725), "01:02:05")

    def test_plain_output(self) -> None:
        console = Console(color=False)
        self.assertEqual(console.paint("x", "red"), "x")
        bar = console.progress_bar(1, 2)
        self.assertIn("█", bar)
        self.assertIn("50%", bar)


if __name__ == "__main__":
    unittest.main()
