"""命令行入口：交互答题、题库浏览、统计、历史与导出。"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from . import __version__
from .bank import QUESTIONS
from .engine import QuizError, Session, select_questions
from .models import label_for
from .storage import Store
from .ui import Console, DIFFICULTY_STARS, format_duration

QUIT = object()
PROMPT = "你的答案（A-D / 1-4，s 跳过，q 退出）："
QUESTIONS_BY_ID = {question.id: question for question in QUESTIONS}


def parse_choice(raw: str, option_count: int) -> int | None | object | str:
    """解析输入：返回下标、None（跳过）、QUIT 或 ""（无效，需重输）。"""
    text = raw.strip().upper()
    if not text:
        return ""
    if text in ("Q", "QUIT", "EXIT"):
        return QUIT
    if text in ("S", "SKIP"):
        return None
    if text.isdigit():
        index = int(text) - 1
    elif len(text) == 1 and "A" <= text <= "Z":
        index = ord(text) - ord("A")
    else:
        return ""
    return index if 0 <= index < option_count else ""


def shorten(text: str, limit: int = 34) -> str:
    line = text.splitlines()[0] if text else ""
    return line if len(line) <= limit else line[: limit - 1] + "…"


def cmd_play(args: argparse.Namespace, console: Console) -> int:
    try:
        questions = select_questions(
            QUESTIONS, count=args.count, categories=args.category,
            difficulties=args.difficulty, seed=args.seed, shuffle=not args.no_shuffle,
        )
    except QuizError as exc:
        console.error(str(exc))
        return 2

    with Store(args.db) as store:
        session = Session(questions, mode=args.mode).start()
        mode_name = "练习（答完立即看解析）" if args.mode == "practice" else "考试（全部答完再看解析）"
        console.rule("Python 自测")
        console.write(f"题目：{len(questions)} 道    模式：{mode_name}")
        console.write(f"题库：{len(QUESTIONS)} 道内置题    记录：{store.path}")

        while not session.finished:
            question = session.current
            assert question is not None
            console.question_card(question, session.position, session.total)
            parsed: object = ""
            while parsed == "":
                try:
                    raw = input(console.paint(PROMPT, "bold"))
                except (EOFError, KeyboardInterrupt):
                    console.write()
                    console.info("输入已结束，本轮成绩未保存")
                    return 0
                parsed = parse_choice(raw, len(question.options))
                if parsed == "":
                    console.error("无效输入，请输入选项字母或序号")
            if parsed is QUIT:
                console.info("已退出本轮（成绩未保存）")
                return 0
            answer = session.submit(parsed)  # type: ignore[arg-type]
            if args.mode == "practice":
                console.feedback(question, answer)

        result = session.result()
        best_before = store.stats().best_score
        store.save(result)
        console.summary(result, max(best_before, result.score), new_record=result.score > best_before)
        if not args.no_review:
            wrong = [
                (QUESTIONS_BY_ID[item.question_id], item)
                for item in result.answers
                if not item.correct and item.question_id in QUESTIONS_BY_ID
            ]
            console.review(wrong)
        return 0


def cmd_list(args: argparse.Namespace, console: Console) -> int:
    pool = [q for q in QUESTIONS if not args.category or q.category in args.category]
    if not pool:
        console.error("没有符合分类的题目")
        return 2
    rows = [(q.id, q.category, DIFFICULTY_STARS[q.difficulty], str(q.points), shorten(q.prompt))
            for q in pool]
    console.rule(f"题库（{len(pool)} 道）")
    console.table(("ID", "分类", "难度", "分值", "题干"), rows)
    return 0


def cmd_stats(args: argparse.Namespace, console: Console) -> int:
    with Store(args.db) as store:
        stats = store.stats()
        per_category = store.category_stats()
    console.rule("统计")
    console.write(f"答题轮数：{stats.sessions}    累计题数：{stats.answers}    正确：{stats.correct}")
    console.write(f"总正确率：{stats.accuracy * 100:.1f}%    最佳单轮：{stats.best_score} 分"
                  f"    平均分：{stats.average_score:.1f}")
    console.write(f"最近一次：{stats.last_played or '暂无记录'}")
    if per_category:
        console.write()
        rows = [(i["category"], str(i["total"]), str(i["correct"]), f"{i['accuracy'] * 100:.1f}%")
                for i in per_category]
        console.table(("分类", "题数", "正确", "正确率"), rows)
    if not stats.sessions:
        console.info("还没有答题记录，运行 `python3 main.py play` 开始第一轮吧。")
    return 0


def cmd_history(args: argparse.Namespace, console: Console) -> int:
    with Store(args.db) as store:
        sessions = store.recent(limit=args.limit)
    if not sessions:
        console.info("暂无历史记录")
        return 0
    console.rule(f"最近 {len(sessions)} 轮")
    rows = [(str(s["id"]), s["started_at"].replace("T", " "),
             "练习" if s["mode"] == "practice" else "考试",
             f"{s['correct']}/{s['total']}", str(s["score"]), format_duration(s["duration"]))
            for s in sessions]
    console.table(("ID", "时间", "模式", "正确", "得分", "用时"), rows)
    return 0


def cmd_export(args: argparse.Namespace, console: Console) -> int:
    with Store(args.db) as store:
        sessions = store.all_sessions()
        payload = {
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "stats": asdict(store.stats()),
            "categories": store.category_stats(),
            "sessions": sessions,
        }
    target = Path(args.output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "json":
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        fields = ("id", "started_at", "mode", "total", "correct", "score", "duration")
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(sessions)
    console.info(f"已导出 {len(sessions)} 轮记录到 {target}")
    return 0


def cmd_reset(args: argparse.Namespace, console: Console) -> int:
    if not args.yes:
        try:
            reply = input("确认清空所有答题记录？[y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            console.write()
            return 1
        if reply not in ("y", "yes"):
            console.info("已取消")
            return 0
    with Store(args.db) as store:
        store.reset()
    console.info("记录已清空")
    return 0


def add_global_options(parser: argparse.ArgumentParser, *, suppress: bool = False) -> None:
    """--db / --no-color 挂在根命令和子命令上；子命令默认值用 SUPPRESS 避免覆盖。"""
    parser.add_argument("--db", metavar="PATH",
                        default=argparse.SUPPRESS if suppress else None,
                        help="历史记录数据库路径（默认 ~/.qpquiz/history.db）")
    parser.add_argument("--no-color", action="store_true",
                        default=argparse.SUPPRESS if suppress else False,
                        help="关闭彩色输出")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qpquiz",
        description="Python 自测题库：15 道内置单选题，支持练习/考试、统计与导出。",
    )
    add_global_options(parser)
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    play = sub.add_parser("play", help="开始一轮答题")
    add_global_options(play, suppress=True)
    play.add_argument("-n", "--count", type=int, default=10, help="题目数量（默认 10）")
    play.add_argument("-c", "--category", action="append", default=[], help="只抽指定分类，可重复")
    play.add_argument("-d", "--difficulty", action="append", type=int, choices=(1, 2, 3),
                      default=[], help="只抽指定难度，可重复")
    play.add_argument("--mode", choices=("practice", "exam"), default="exam", help="练习或考试模式")
    play.add_argument("--seed", type=int, help="随机种子，便于复现同一套题")
    play.add_argument("--no-shuffle", action="store_true", help="按题库顺序出题")
    play.add_argument("--no-review", action="store_true", help="结束后不展示错题回顾")
    play.set_defaults(func=cmd_play)

    listing = sub.add_parser("list", help="查看题库")
    add_global_options(listing, suppress=True)
    listing.add_argument("-c", "--category", action="append", default=[], help="按分类过滤")
    listing.set_defaults(func=cmd_list)

    stats = sub.add_parser("stats", help="查看统计")
    add_global_options(stats, suppress=True)
    stats.set_defaults(func=cmd_stats)

    history = sub.add_parser("history", help="查看历史记录")
    add_global_options(history, suppress=True)
    history.add_argument("-l", "--limit", type=int, default=20)
    history.set_defaults(func=cmd_history)

    export = sub.add_parser("export", help="导出历史记录")
    add_global_options(export, suppress=True)
    export.add_argument("-f", "--format", choices=("json", "csv"), default="json")
    export.add_argument("-o", "--output", default="qpquiz-export.json")
    export.set_defaults(func=cmd_export)

    reset = sub.add_parser("reset", help="清空历史记录")
    add_global_options(reset, suppress=True)
    reset.add_argument("--yes", action="store_true", help="跳过确认")
    reset.set_defaults(func=cmd_reset)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        args.func = cmd_play
        for name, value in (("count", 10), ("category", []), ("difficulty", []),
                            ("mode", "exam"), ("seed", None),
                            ("no_shuffle", False), ("no_review", False)):
            setattr(args, name, value)
    console = Console(color=False if getattr(args, "no_color", False) else None)
    try:
        return int(args.func(args, console))
    except QuizError as exc:
        console.error(str(exc))
        return 2
    except KeyboardInterrupt:
        console.write()
        console.info("已中断")
        return 130
