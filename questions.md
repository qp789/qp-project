# Python 自测题库（15 题）

> 题源：`quiz/bank.py`。运行 `python3 main.py play -n 15` 可一次答完这 15 道题。

**分类与难度**

| 分类 | 题号 | 难度 |
| --- | --- | --- |
| 基础 | 1、2、5、12 | ★☆☆ / ★★☆ |
| 数据结构 | 3、11 | ★★☆ |
| 函数 | 4、13 | ★★☆ / ★★★ |
| 迭代器 | 6、7、8、15 | ★★☆ / ★★★ |
| 面向对象 | 10、14 | ★★☆ / ★★★ |
| 异常 | 9 | ★★★ |

---

## 1. 基础 · ★☆☆

表达式 `[1, 2, 3] + [4]` 的结果是？

- A. `[1, 2, 3, 4]`
- B. `[1, 2, 3, [4]]`
- C. 抛出 `TypeError`
- D. `[5]`

<details>
<summary>答案与解析</summary>

**A** — 列表的 `+` 是拼接运算，返回一个新列表，不会把 `[4]` 当成一个元素；追加单个元素应该用 `append` 或 `extend`。

</details>

---

## 2. 基础 · ★☆☆

下面哪个表达式的求值结果是 `False`？

- A. `bool("0")`
- B. `bool([])`
- C. `bool([0])`
- D. `bool({0})`

<details>
<summary>答案与解析</summary>

**B** — 空容器为假，非空容器恒为真，即使里面装的是 `0`；所以 `bool("0")`、`bool([0])`、`bool({0})` 都是 `True`。

</details>

---

## 3. 数据结构 · ★★☆

已知 `d = {"a": 1}`，哪种写法在访问不存在的键 `"b"` 时会抛出 `KeyError`？

- A. `d.get("b")`
- B. `d["b"]`
- C. `d.get("b", 0)`
- D. `"b" in d`

<details>
<summary>答案与解析</summary>

**B** — `d["b"]` 走 `__getitem__`，键不存在直接抛 `KeyError`；`get` 返回 `None` 或默认值，`in` 只返回布尔值。

</details>

---

## 4. 函数 · ★★☆

连续调用 `add(1)`、`add(2)`，返回值分别是？

```python
def add(x, bucket=[]):
    bucket.append(x)
    return bucket
```

- A. `[1]` 和 `[2]`
- B. `[1]` 和 `[1, 2]`
- C. 两次都返回 `[]`
- D. 第二次调用抛出 `TypeError`

<details>
<summary>答案与解析</summary>

**B** — 默认参数在函数定义时只求值一次，`bucket` 始终指向同一个列表对象，两次调用会持续追加；正确写法是默认值用 `None`，函数内部再创建列表。

</details>

---

## 5. 基础 · ★★☆

`a = [1, 2, 3]`，`b = a`，执行 `b.append(4)` 后 `a` 的值是？

- A. `[1, 2, 3]`
- B. `[1, 2, 3, 4]`
- C. `[4]`
- D. 抛出 `AttributeError`

<details>
<summary>答案与解析</summary>

**B** — `b = a` 只复制引用，两者指向同一个列表对象，通过 `b` 修改会同时反映到 `a`。需要独立副本时用 `a.copy()` 或 `list(a)`。

</details>

---

## 6. 迭代器 · ★★★

执行下面的代码，输出是什么？

```python
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])
```

- A. `[0, 1, 2]`
- B. `[2, 2, 2]`
- C. `[0, 0, 0]`
- D. 抛出 `NameError`

<details>
<summary>答案与解析</summary>

**B** — `lambda` 里的 `i` 是闭包变量，按引用捕获；推导结束后 `i` 为 `2`，三个 `lambda` 读到的都是同一个 `i`。用 `lambda i=i: i` 可以固定当前值。

</details>

---

## 7. 迭代器 · ★★☆

`sorted([3, 1, 2], key=lambda x: -x)` 的结果是？

- A. `[1, 2, 3]`
- B. `[3, 2, 1]`
- C. `[3, 1, 2]`
- D. 抛出 `TypeError`

<details>
<summary>答案与解析</summary>

**B** — `sorted` 默认升序，`key` 把元素映射成相反数再比较，等价于按原值降序，结果为 `[3, 2, 1]`。

</details>

---

## 8. 迭代器 · ★★★

`g = (x * x for x in range(4))`，先 `sum(g)`，再 `sum(g)`，两次结果分别是？

- A. `14` 和 `14`
- B. `14` 和 `0`
- C. `0` 和 `14`
- D. 第二次抛出 `RuntimeError`

<details>
<summary>答案与解析</summary>

**B** — 生成器是一次性迭代器，第一次 `sum` 已把元素耗尽，第二次遍历拿不到元素，结果为 `0`。

</details>

---

## 9. 异常 · ★★★

函数 `f()` 返回什么？

```python
def f():
    try:
        return 1
    finally:
        return 2
```

- A. `1`
- B. `2`
- C. `None`
- D. 抛出 `ValueError`

<details>
<summary>答案与解析</summary>

**B** — `finally` 一定会执行；如果 `finally` 里也有 `return`，它会覆盖 `try` 中尚未返回的值，因此 `f()` 返回 `2`。

</details>

---

## 10. 面向对象 · ★★☆

关于 `@staticmethod` 和 `@classmethod`，下面说法正确的是？

- A. `staticmethod` 的第一个参数是 `cls`
- B. `staticmethod` 不接收隐式第一参数，`classmethod` 接收类对象
- C. 两者都必须先实例化才能调用
- D. `classmethod` 不能被子类调用

<details>
<summary>答案与解析</summary>

**B** — `staticmethod` 等价于普通函数，不自动传入 `self` 或 `cls`；`classmethod` 会把类对象作为第一个参数，通过子类调用时拿到的是子类。

</details>

---

## 11. 数据结构 · ★★☆

`a = [[1], [2]]`，`b = copy.copy(a)`，再执行 `b[0].append(9)`，结果是？

- A. 只有 `b` 改变，`a` 不受影响
- B. `a` 和 `b` 的内层列表是同一个对象，`a` 也变成 `[[1, 9], [2]]`
- C. `copy.copy` 会自动深拷贝，两者互不影响
- D. 抛出 `RecursionError`

<details>
<summary>答案与解析</summary>

**B** — `copy.copy` 是浅拷贝：只复制外层列表，内层元素仍是原对象；要彻底隔离嵌套结构需要 `copy.deepcopy`。

</details>

---

## 12. 基础 · ★☆☆

循环里反复 `result += s` 与先收集片段再 `"".join(parts)`，后者的主要优势是？

- A. `join` 通常更快，且避免产生大量临时字符串
- B. `+=` 会修改原字符串对象
- C. `join` 会自动把内容转成小写
- D. 两者完全等价，没有性能差异

<details>
<summary>答案与解析</summary>

**A** — 字符串不可变，每次 `+=` 都新建字符串并复制旧内容，循环多时是 O(n²)；`join` 只分配一次结果，效率高得多。

</details>

---

## 13. 函数 · ★★★

定义 `def f(a, *args, b=1, **kw)`，调用 `f(1, 2, 3, 4)` 时 `args` 的值是？

- A. `(2, 3, 4)`
- B. `(1, 2, 3, 4)`
- C. `(4,)`
- D. 调用直接报错

<details>
<summary>答案与解析</summary>

**A** — 第一个位置参数绑定给 `a`，其余位置参数全部收进 `args`，所以 `args` 是 `(2, 3, 4)`。

</details>

---

## 14. 面向对象 · ★★★

下面的代码输出什么？

```python
class A:
    x = 1

class B(A):
    pass

b = B()
b.x = 2
del b.x
print(b.x)
```

- A. `1`
- B. `2`
- C. 抛出 `AttributeError`
- D. `None`

<details>
<summary>答案与解析</summary>

**A** — `b.x = 2` 只创建了实例属性；`del b.x` 删除后，属性查找回退到类，读到继承来的 `A.x = 1`。

</details>

---

## 15. 迭代器 · ★★☆

`list(range(10))[1:8:2]` 的结果是？

- A. `[1, 3, 5, 7]`
- B. `[1, 3, 5, 7, 9]`
- C. `[2, 4, 6, 8]`
- D. `[1, 2, 3, 4, 5, 6, 7]`

<details>
<summary>答案与解析</summary>

**A** — 切片 `[start:stop:step]` 从下标 1 开始、到下标 8 之前结束、步长 2，取到 `1、3、5、7`。

</details>

---

## 答案速查

| 题号 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 答案 | A | B | B | B | B | B | B | B | B | B | B | A | A | A | A |
