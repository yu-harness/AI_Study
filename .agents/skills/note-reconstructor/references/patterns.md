
# 笔记重构——可复用模式速查

## 图表类型选择决策树

**选 Mermaid flowchart / graph：**
- 架构关系、组件依赖
- 流程步骤、时序推进
- 决策分支、状态转换
- 方案对比（左右 subgraph）

**选 HTML 卡片 + 表格：**
- 数字逐层累加（A + B + C = 总和）
- 账单拆解、费用构成
- 层级包含（外层框包内层卡片）

**选 Mermaid 饼图：**
- 比例/占比对比（75% vs 25%）
- 各组件占总体的百分比

**组合使用：**
- 左侧 HTML 表格列明细 + 右侧 Mermaid 饼图看占比
- 最外层 HTML 框做"总账本"，内部嵌套各层

## 深色模式兼容规范（所有 HTML 必须遵守）

**绝对禁止：** 硬编码颜色值 `#fff`、`#fafafa`、`#eef7ff`、`#888`、`#999`、`#2c3e50` 等。

**安全可用的 Obsidian CSS 变量（阅读模式下确定存在）：**

| 用途 | 变量 |
|---|---|
| 正文文字 | `var(--text-normal)` |
| 次要文字 | `var(--text-muted)` |
| 强调色 | `var(--text-accent)` |
| 卡片/面板背景 | `var(--background-secondary)` |
| 页面背景 | `var(--background-primary)` |

**禁止使用的变量：** `var(--text-warning)`、`var(--text-error)`、`var(--text-success)`、`var(--background-modifier-border)`——这些在阅读模式下未定义。

**色彩区分靠 rgba 透明度：** `rgba(100,180,255,0.5)` 做边框，`rgba(100,180,255,0.08)` 做背景。RGB 固定，透明度变化。

**优先用纯 Markdown 表格做累加展示**——最可靠，零风险。只在确实需要叠层视觉效果时才用 HTML 卡片。

## HTML 卡片模板

### 垂直叠层卡片（总分结构 — 最常用）
```html
<div style="border:2px solid var(--text-accent); border-radius:12px; padding:16px; background:var(--background-secondary); text-align:center; margin:16px 0;">

<div style="font-size:1.15em; font-weight:bold; margin-bottom:4px; color:var(--text-normal);">📦 总标题</div>
<div style="font-size:0.9em; color:var(--text-muted); margin-bottom:10px;">简要说明</div>

<div style="border:2px solid rgba(255,180,100,0.5); border-radius:8px; padding:10px; background:rgba(255,180,100,0.08); margin-bottom:12px;">
  <strong style="color:var(--text-normal);">📋 顶层 = XX 字节</strong><br>
  <span style="font-size:0.85em; color:var(--text-muted);">构成细节</span>
</div>

<div style="display:flex; gap:10px; justify-content:center; align-items:stretch;">

<div style="flex:1; border:2px solid rgba(100,180,255,0.5); border-radius:8px; padding:12px; background:rgba(100,180,255,0.08);">
  <div style="font-weight:bold; margin-bottom:6px; color:var(--text-normal);">🔑 组件 A</div>
  <div style="font-size:1.5em; font-weight:bold; color:var(--text-accent);">数值</div>
  <div style="font-size:0.8em; color:var(--text-muted);">构成说明</div>
</div>

<div style="display:flex; align-items:center; font-size:1.3em; font-weight:bold; color:var(--text-muted);">+</div>

<div style="flex:1; border:2px solid rgba(100,180,255,0.5); border-radius:8px; padding:12px; background:rgba(100,180,255,0.08);">
  <div style="font-weight:bold; margin-bottom:6px; color:var(--text-normal);">💾 组件 B</div>
  <div style="font-size:1.5em; font-weight:bold; color:var(--text-accent);">数值</div>
  <div style="font-size:0.8em; color:var(--text-muted);">构成说明</div>
</div>

</div>

<div style="margin-top:14px; padding-top:12px; border-top:2px dashed var(--text-accent);">
  <span style="font-size:1.1em; font-weight:bold; color:var(--text-normal);">🔺 合计 = </span>
  <span style="font-size:1.6em; font-weight:bold; color:var(--text-accent);">总和</span><br>
  <span style="font-size:0.85em; color:var(--text-muted);">备注信息</span>
</div>

</div>
```

### 横向累加表格（A + B + C = 总和）

**首选方案：纯 Markdown 表格。** 最可靠，零渲染风险。

```
逐层累加：

| 步骤 | 组件 | 字节 | 构成 |
|---|---|---|---|
| ① | 组件 A | **XX B** | 构成说明 |
| ② | 组件 B | **XX B** | 构成说明 |
| ③ | 组件 C | **XX B** | 构成说明 |
| **=** | **🔺 合计** | **XX B** | 一句话概括 |
```

### 表格明细 + 饼图（拆账专用）

**铁律：HTML div 必须自闭合，Markdown 表格和 Mermaid 放在 div 之外。**

````markdown
<!-- 上半：可选用 HTML 卡片展示关键数据（仅在需要视觉效果时） -->
... 垂直叠层卡片 HTML（自闭合）...

<!-- 下半：纯 Markdown，一定不在 HTML 块内 -->

**拆账明细**

| 开销项 | 数值 | 说明 |
|---|---|---|
| ... | ... | ... |

```mermaid
pie showData
    title 占比标题
    "项目 A" : 数值
    "项目 B" : 数值
```
````

## 类比域选择指南
|---|---|---|
| 键值数据库架构 | 图书馆管理系统 | 书架→存储、索书号→索引、借还书→操作、入口柜台→访问框架 |
| 数据结构与操作复杂度 | 仓库管理系统 | 仓库→全局哈希表、货架号冲突→哈希冲突、扩建→rehash、渐进式搬迁→渐进式rehash |
| IO 多路复用 | 医院分诊台 | 医生→单线程、分诊台→内核 epoll、病人→客户端请求 |
| AOF 持久化 | 航行日志 | 日志→AOF 文件、誊抄→重写、叫人誊抄→fork 子进程 |
| RDB 快照 | 拍照 | 全量快照→大合影、COW→要改就复制一份再改、连拍→频繁快照不行 |
| 主从同步 | 出版社发行体系 | 原稿→主库、批量印刷→全量复制、寄送→命令传播、补发→增量复制、分印厂→级联 |
| 哨兵机制 | 自动化消防系统 | 烟雾探测器→监控、交叉验证→客观下线、备用水源→选主、切换通知→通知 |
| 哨兵集群 | 对讲机群组 | 同一频道→pub/sub 频道、举手→先到先投 |

## 常用 Mermaid 图表模板

### 架构总览图（多组件拆分）
```
flowchart TD
    Main["核心概念"] --> Comp1["组件 1<br/>简述"]
    Main --> Comp2["组件 2<br/>简述"]
    Comp1 --> Detail1["细节 A"]
    Comp2 --> Detail2["细节 B"]
    style Main fill:#d1ecf1
    style Comp1 fill:#d4edda
    style Comp2 fill:#fff3cd
```

### 流程步骤图（时序推进）
```
flowchart LR
    Step1["① 第一步<br/>说明"] --> Step2["② 第二步<br/>⚠️ 阻塞点"]
    Step2 --> Step3["③ 第三步<br/>✅ 解法"]
```

### 双方案对比图（左右并排）
```
flowchart LR
    subgraph "方案 A"
        A1[...] --> A2[...]
    end
    subgraph "方案 B（推荐）"
        B1[...] --> B2[...]
    end
```

### 决策树
```
flowchart TD
    Q{"核心问题？"} -->|"条件 1"| Choice1["选择 A"]
    Q -->|"条件 2"| Choice2["选择 B"]
    Choice1 --> Next{"继续判断？"}
```

### 时间线推演
```
flowchart LR
    T0["T0: 初始状态"] --> T1["T1: 事件 1"]
    T1 --> T2["T2: 事件 2"]
    T2 --> T3["T3: 最终状态 ✅"]
```

## 过渡衔接模板

### 节间过渡（从一节引出下一节）
```
---

**但光解决 X 还不够**——Y 的问题仍然存在。[一句话解释 Y 为什么重要]。这就引出了下一节的内容。

## 下一节标题
```

### 跨篇衔接——末尾（预告下一篇）
```
> **🧭 接下来看什么？** [本节解决了什么]，但[什么还没回答/什么新问题产生了]。下一节将[下篇的主题和核心卖点]。
```

### 跨篇衔接——开头（回顾上一篇）
```
> 💡 **从哪里来？** [上篇做了什么]，[建立了什么基础]。本节在此基础上[本篇的核心任务]。
```

## 一句话总结模板

```
> 核心概念 = 简洁解释 + 关键机制1（具体数据）+ 关键机制2（具体数据/公式）+ 核心结论。最大短板/工程底线/最佳实践。
```

## Mermaid 故障排除速查

| 症状 | 原因 | 修复 |
|---|---|---|
| 图表不渲染 | `graph` 模式 + `end` 关键字冲突 | `graph TD` → `flowchart TD` |
| 图表不渲染 | 节点标签含 `<br/>` | 改用中文逗号或短句 |
| subgraph 报错 | 中文标题未加引号 | `subgraph "中文标题"` |
| 编辑提示"已匹配 2 处" | style 字符串在多处出现 | 增加上下文限定到唯一匹配 |

## 表格常用格式

### 对比表（两类对比）
```
| 维度 | 方案 A | 方案 B |
|---|---|---|
| ... | ... | ... |
```

### 参数/特性表
```
| 参数/特性 | 含义 | 示例 |
|---|---|---|
| ... | ... | ... |
```

### 复杂度/选型表
```
| 场景 | 推荐方案 | 理由 |
|---|---|---|
| ... | ... | ... |
```
