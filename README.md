# qp-project · Python 自测题库（qpquiz）

一个零依赖的终端答题程序：内置 15 道 Python 单选题，支持练习/考试两种模式、
分类与难度筛选、SQLite 成绩记录、正确率统计、错题回顾与 JSON/CSV 导出。

```text
$ python3 main.py play -n 5
──────────────────────────── Python 自测 ────────────────────────────
题目：5 道    模式：考试（全部答完再看解析）
题库：15 道内置题    记录：/root/.qpquiz/history.db

[1/5] 函数 · 难度 ★★☆ · 分值 14
████░░░░░░░░░░░░░░░░  20%

  连续调用 add(1)、add(2)，返回值分别是？

  def add(x, bucket=[]):
      bucket.append(x)
      return bucket

  A. [1] 和 [2]
  B. [1] 和 [1, 2]
  C. 两次都返回 []
  D. 第二次调用抛出 TypeError
你的答案（A-D / 1-4，s 跳过，q 退出）：
```

## 功能

- **15 道内置题**：覆盖基础、数据结构、函数、面向对象、异常、迭代器六个分类，难度 1–3 级
- **两种模式**：`practice` 每题作答后立即给解析；`exam` 全部答完统一回顾
- **灵活抽题**：`--count` 题量、`--category` 分类、`--difficulty` 难度、`--seed` 复现同一套题
- **计分**：按难度加权（10/14/18 分），跳过记为答错
- **持久化**：每轮结果写入 SQLite（默认 `~/.qpquiz/history.db`），记录每道题的作答与耗时
- **统计**：总正确率、最佳单轮、平均分、分类正确率、历史记录列表
- **错题回顾**：结束后列出错题、你的选择、正确答案与解析
- **导出**：`export` 支持 JSON / CSV，方便二次分析
- **零第三方依赖**：只用标准库，Python 3.9+ 即可运行

## 快速开始

```bash
git clone https://github.com/qp789/qp-project.git
cd qp-project

python3 main.py                 # 默认：随机 10 题，考试模式
python3 main.py play -n 15      # 全部 15 题
python3 main.py play -c 函数 -c 迭代器 --mode practice
python3 main.py list            # 查看题库
python3 main.py stats           # 查看统计
python3 main.py history -l 10   # 最近 10 轮
python3 main.py export -f json -o report.json
python3 main.py reset --yes     # 清空记录
```

选项：`--db PATH` 指定数据库，`--no-color` 关闭颜色（管道下会自动关闭），
`-v/--version` 查看版本。全局选项放在子命令前后都可以。

## 命令一览

| 命令 | 说明 |
| --- | --- |
| `play` | 开始一轮答题：`-n/--count`、`-c/--category`、`-d/--difficulty`、`--mode`、`--seed`、`--no-shuffle`、`--no-review` |
| `list` | 列出题库（可按分类过滤） |
| `stats` | 全局统计 + 分类正确率 |
| `history` | 历史轮次（`-l/--limit`） |
| `export` | 导出历史：`-f json\|csv`、`-o 路径` |
| `reset` | 清空记录（`--yes` 跳过确认） |

## 题目

15 道题完整列表（含答案与解析）见 [questions.md](questions.md)，题源在
`quiz/bank.py`。分类与难度分布：

| 分类 | 题数 | 难度 |
| --- | --- | --- |
| 基础 | 4 | ★☆☆ / ★★☆ |
| 迭代器 | 4 | ★★☆ / ★★★ |
| 数据结构 | 2 | ★★☆ |
| 函数 | 2 | ★★☆ / ★★★ |
| 面向对象 | 2 | ★★☆ / ★★★ |
| 异常 | 1 | ★★★ |

## 项目结构

```text
.
├── main.py              # 入口：python3 main.py [command]
├── quiz/
│   ├── models.py        # Question / Answer / SessionResult 数据模型
│   ├── bank.py          # 15 道内置题
│   ├── engine.py        # 抽题与答题状态机、计分
│   ├── storage.py       # SQLite 持久化与统计查询
│   ├── ui.py            # 终端渲染：颜色、进度条、表格、错题回顾
│   └── cli.py           # argparse 子命令与交互循环
├── tests/test_quiz.py   # 13 个单元测试
└── questions.md         # 题目清单（含答案与解析）
```

## 数据与计分

- 数据库：`~/.qpquiz/history.db`（可用 `--db` 或环境变量 `QPQUIZ_DB` 覆盖），
  两张表：`sessions`（每轮汇总）、`answers`（每题作答明细）。
- 分值：难度 1/2/3 分别 10/14/18 分；跳过按 0 分计。
- 正确率与最佳成绩都由 SQL 聚合实时计算，不做冗余缓存。

## 新增题目

在 `quiz/bank.py` 的 `QUESTIONS` 里追加一条即可，`id` 需唯一：

```python
Question(
    id="q16", category="基础", difficulty=1,
    prompt="题干……",
    options=("选项 A", "选项 B", "选项 C", "选项 D"),
    answer=0,
    explanation="解析……",
)
```

`Question` 在构造时会校验难度、选项数量和答案下标，写错会直接抛 `ValueError`。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

覆盖题库完整性、抽题过滤与随机复现、计分与跳过、输入解析、SQLite 存取与统计。

## License

MIT，见 [LICENSE](LICENSE)。
