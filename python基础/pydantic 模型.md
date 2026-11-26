---
title: "pydantic 模型"
topic: "python基础"
type: note
date: 2026-11-15
---

# pydantic 模型

用一个 Python 类描述一份数据长什么形状，创建对象的那一刻就把类型检查做完。核心是 `pydantic.BaseModel`。

## 1 最小示例

```python
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: str
    content: str
    tokens: int = 0
    tags: list[str] = Field(default_factory=list)

m = Message(role="user", content="hi")
m.tokens = "12"                    # 赋值时先校验再转成 int
print(m.model_dump())              # {'role': 'user', 'content': 'hi', 'tokens': 12, 'tags': []}
print(m.model_dump_json())         # 转成 JSON 字符串
```

类体里只写字段名和类型注解，不用写 `__init__`，不用写 `self.x = x`。构造函数、类型检查、转字典、转 JSON 全部由基类提供。

## 2 它做的四件事

| 能力 | 表现 |
| --- | --- |
| 校验 | `Message(role="user")` 缺少 `content`，立刻抛出 `ValidationError`，并指出字段名、错误类型、输入值 |
| 类型转换 | `"12"` 按注解转成 `12`；`"abc"` 转不了就报错 |
| 序列化 | `model_dump()` 得到 dict，`model_dump_json()` 得到 JSON 字符串 |
| 约束 | `Field(gt=0, max_length=100, pattern=...)` 限制取值范围、长度、格式 |

默认行为是忽略多余的键，传入模型没有定义的字段不会报错。要拦住这类输入就配置：

```python
from pydantic import BaseModel, ConfigDict

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)
    name: str
```

`extra="forbid"` 让多余字段报错，`validate_assignment=True` 让属性赋值也走校验。

## 3 嵌套与默认值

```python
from pydantic import BaseModel, Field, ValidationError

class ToolCall(BaseModel):
    name: str
    arguments: dict[str, str]

class Reply(BaseModel):
    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)   # 可变默认值必须用工厂函数

reply = Reply(content="查天气", tool_calls=[{"name": "get_weather", "arguments": {"city": "成都"}}])
print(type(reply.tool_calls[0]))    # <class '__main__.ToolCall'>，字典自动转成子模型

try:
    Reply(content="x", tool_calls=[{"name": "get_weather"}])
except ValidationError as exc:
    print(exc.errors())            # 列表形式，每项含 loc、msg、type、input
```

三点要记住：

- 嵌套的 dict 会自动转成对应的子模型，多层递归检查。
- 可变默认值（list、dict、子模型）用 `Field(default_factory=...)`，直接写 `= []` 会让所有实例共用同一个列表。
- 捕获之后看 `exc.errors()`，`loc` 指出出错位置，做错误提示时按它拼路径。

## 4 从 JSON 到模型，从模型到 JSON

```python
text = '{"content": "你好", "tool_calls": []}'

reply = Reply.model_validate_json(text)     # 解析字符串并校验
reply2 = Reply.model_validate({"content": "你好"})   # 从 dict 校验
schema = Reply.model_json_schema()           # 得到 JSON Schema
```

`model_json_schema()` 是和大模型对接的接口：把这份 schema 交给模型，要求它按 schema 输出 JSON，拿回来用 `model_validate_json()` 解析。解析成功就得到类型确定的 Python 对象，失败就说明模型没守格式，可以重试一次或换提示词。

默认情况下字符串类型的字段不会自动把数字转成字符串，这是 v2 的行为。

## 5 自定义校验

```python
from pydantic import BaseModel, field_validator, model_validator

class Query(BaseModel):
    city: str
    days: int

    @field_validator("city")
    @classmethod
    def city_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("城市不能为空")
        return value.strip()

    @model_validator(mode="after")
    def days_in_range(self):
        if not 1 <= self.days <= 30:
            raise ValueError("天数超出范围")
        return self
```

`field_validator` 管单个字段，`model_validator(mode="after")` 在全部字段检查完之后做跨字段判断。抛 `ValueError` 会被包装成 `ValidationError` 的一个条目。

## 6 和 dataclass、TypedDict 的分界

| 写法 | 运行时检查 | 适用场景 |
| --- | --- | --- |
| `@dataclass` | 不做，类型注解只给静态检查工具看 | 程序内部传递数据，数据来源可信 |
| `TypedDict` | 不做，本质仍是普通 dict | 描述字典的形状，给类型检查用 |
| `BaseModel` | 做，创建时立刻检查并转换 | 数据来自外部：HTTP 请求、配置文件、模型输出 |

判断标准只有一条：这份数据是别人给的还是自己造的。别人给的就要检查。

## 7 v1 与 v2 的方法对照

v1 的方法在 v2 里还留着，调用时给出弃用提示，新代码一律用 v2 的写法。

| 用途 | v1 | v2 |
| --- | --- | --- |
| 转字典 | `dict()` | `model_dump()` |
| 转 JSON | `json()` | `model_dump_json()` |
| 从字典校验 | `parse_obj()` | `model_validate()` |
| 从 JSON 校验 | `parse_raw()` | `model_validate_json()` |
| 配置 | 类内 `class Config` | `model_config = ConfigDict(...)` |
| 字段校验器 | `@validator` | `@field_validator` |
| 对象校验器 | `@root_validator` | `@model_validator` |

v2 的校验核心用 Rust 重写，同样的模型处理大列表时速度比 v1 快数倍。

## 8 和大模型应用的关系

- **结构化输出**：把 `model_json_schema()` 交给模型，模型返回 JSON，`model_validate_json()` 解析成对象。LangChain 的 `with_structured_output()`、OpenAI 的 structured outputs、MCP 的工具参数定义，走的都是这条路。
- **工具调用参数**：函数签名上的类型注解经 pydantic 转成 JSON Schema，模型按 schema 生成参数，服务端再用同一个模型校验参数是否合法。
- **FastAPI**：请求体和响应体的声明与校验都基于 pydantic，声明一个模型就等于同时拿到了数据检查、自动文档和类型提示。

面试里被问到，一句话就够：pydantic 用类型注解声明数据结构，创建对象时校验并转换类型，把外部来的不可信数据变成程序可以直接使用的对象；大模型输出结构化数据时，它承担格式定义与结果检查这两步。
