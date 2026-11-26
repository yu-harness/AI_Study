---
title: "python基础数据结构"
topic: "python基础"
type: note
date: 2026-10-31
---

# Python 基础数据结构

## 1 五种常用容器

- **list**：有序、可变、可重复，按位置存取。
- **tuple**：有序、不可变、可重复，用来装一组长度固定的值。
- **dict**：键值对，键唯一且可哈希，3.7 起保证按插入顺序迭代。
- **set**：只存键，自动去重，支持交并差。
- **str**：不可变的字符序列，本身也是一种序列容器。

选型可以按一句话判断：按**下标访问**用 list，按**名字取值**用 dict，**判重与集合运算**用 set，把一组值固定住用 tuple。

## 2 list 的底层

CPython 的 list 是一个**指针数组**，外面套一层结构体，里面记三件事：**数组首地址、已用长度、已分配容量**。

- **索引 $O(1)$**：第 $i$ 个元素的位置是 `start + i × 8`（64 位平台），一次乘加就到。
- **末尾追加均摊 $O(1)$**：容量用满时一次性多申请一些，增长公式是 `size + (size >> 3) + 6`，大约 1.125 倍。多申请的部分留给后面几次追加，不必每次扩容。
- **中间插入 $O(n)$**：`insert(0, x)` 要把后面所有元素整体后移一格，元素越多越慢。
- **成员检查 $O(n)$**：`x in lst` 是逐个比较，没有索引可用。

**常用操作**

```python
nums = [3, 1, 2]

nums.append(4)          # 末尾追加，均摊 O(1)
nums.extend([5, 6])     # 一次追加多个
nums.insert(0, 0)       # 头部插入，O(n)
nums.pop()              # 弹出末尾并返回
nums.pop(0)             # 弹出头部，O(n)
nums.remove(3)          # 按值删掉第一个匹配项，找不到抛 ValueError
nums.index(2)           # 找下标，找不到抛 ValueError
nums.count(2)           # 数出现次数，O(n)

nums.sort()                        # 原地排序，返回 None
top = sorted(nums, reverse=True)   # 返回新 list，原 list 不动

doubled = [x * 2 for x in nums if x > 2]    # 列表推导
matrix = [[0] * 3 for _ in range(2)]        # 二维初始化，每行独立
```

## 3 tuple 为什么省内存

tuple 不需要「已分配容量」这个字段，长度在创建时就定下来，也没有多留空位，所以同样内容的 tuple 比 list 占用更少。

- 创建后不能改，因此可以当 dict 的键，前提是里面每个元素都可哈希。
- 函数返回多个值，实际返回的是一个 tuple。

**常用操作**

```python
point = (3, 5)
x, y = point                    # 解包
first, *rest = (1, 2, 3)        # 星号收集剩下的，rest 是 [2, 3]
point[0]                        # 3，按下标读

# point[0] = 9                  # TypeError，创建后不能改
hash(point)                     # 元素都可哈希时，tuple 本身可哈希

def min_max(nums):
    return min(nums), max(nums) # 返回的其实是一个 tuple
```

## 4 dict 与 set 的哈希表

两者共用一套哈希表实现，区别只在存不存值。

- 3.6 起 CPython 换成紧凑结构：一张稀疏的索引数组记位置，一张紧凑的条目数组按插入顺序存 hash、key、value。
- 好处有两个：内存比旧实现省 20% 到 25%；遍历按条目数组的顺序走，插入有序于是成了自然结果。
- 查找分三步：算 `hash(key)` → 用 hash 的低几位定位索引数组 → 比对 hash 与 key。
- 冲突用开放寻址解决：目标位置被占就按固定规则往后探，直到找到空位。
- 负载因子到 $2/3$ 就扩容，新容量按 4 倍或 2 倍增长（看当前用量是否超过 50000）。

set 与 dict 的差别在条目里只存 key、不存 value，所以同样元素个数下更省内存。

**dict 常用操作**

```python
stock = {"apple": 3, "pear": 5}

stock["banana"] = 2              # 有则覆盖，无则新增
stock.get("orange", 0)           # 取不到给默认值，不抛异常
stock.setdefault("kiwi", 0)      # 键不存在时写入默认值，并返回它

for k, v in stock.items():       # 同时拿键和值
    print(k, v)

del stock["pear"]                # 删键，键不存在抛 KeyError
stock.pop("kiwi", None)          # 删键并返回，键不存在给默认值

cheap = {k: v for k, v in stock.items() if v < 3}   # 字典推导
```

**set 常用操作**

```python
a = {1, 2, 3}
b = {3, 4}

a | b            # 并集 {1, 2, 3, 4}
a & b            # 交集 {3}
a - b            # 差集 {1, 2}
a.add(5)         # 加元素
a.discard(5)     # 删元素，不存在也不报错
a.remove(5)      # 删元素，不存在抛 KeyError

list(set([1, 1, 2]))    # 去重，但顺序不保证
```

## 5 str 的拼接代价

str 不可变，每次 `+` 都要新开一块内存、把两边都拷进去。循环里拼 $n$ 次，总代价是 $O(n^2)$。

正确做法是先收集到 list，最后用 `"".join(parts)` 一次拼完：join 先算总长度，只分配一次。

CPython 对 `s += t` 有一个就地扩展的特例，只在 s 的引用计数为 1 时生效。可以靠它跑得快，不能靠它保证复杂度。

**常用操作**

```python
s = "  a,b,c  "

s.strip()               # 'a,b,c'，去掉两端空白
s.split(",")            # ['  a', 'b', 'c  ']，按分隔符切
"-".join(["a", "b"])    # 'a-b'，把 list 拼成一个 str
s.replace("a", "x")     # 返回新 str，原串不动
s.upper(), s.lower()
s.startswith("  a")

name, score = "tom", 91.5
f"{name}: {score:.1f}"  # 'tom: 91.5'，f-string 带格式

s[::-1]                 # 反转
```

## 6 复杂度速查

- **list**：索引 $O(1)$；末尾追加均摊 $O(1)$；中间插入删除 $O(n)$；成员检查 $O(n)$；切片 $O(k)$，$k$ 是切片长度。
- **dict**：增删改查均摊 $O(1)$，最坏 $O(n)$（所有键撞在同一段）；遍历 $O(n)$。
- **set**：增删查均摊 $O(1)$；交并差 $O(\text{两个集合长度之和})$。
- **str**：索引 $O(1)$；切片 $O(k)$；`in` 找子串最坏 $O(n \times m)$，$m$ 是子串长度。

## 7 四个常见坑

**可变对象做默认参数**

```python
def add(x, acc=[]):
    acc.append(x)
    return acc
```

默认值在函数定义时求值一次，所有调用共用同一个 list，第二次调用就带着上一次的结果。正确写法是默认值给 `None`，进函数再建。

**浅拷贝只复制第一层**

`lst[:]`、`lst.copy()`、`copy.copy(lst)` 都是浅拷贝：外层容器新建，里面的对象仍是同一批。嵌套 list 改内层，两份都会变。要连同内层一起复制，用 `copy.deepcopy`。

**`[[0] * 3] * 2` 造出的是别名**

外层两个元素指向同一个内层 list，改 `a[0][0]` 会连带 `a[1][0]`。要互不影响的几行，用列表推导 `[[0] * 3 for _ in range(2)]`。

**迭代时改 dict**

遍历过程中增删键会抛 `RuntimeError: dictionary changed size during iteration`。先把键取成 list 再遍历，或者先收集要删的键，循环结束后统一删。

## 来源

按 CPython 3.11 的实现整理，增长公式与负载因子取自源码。
