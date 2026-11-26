---
title: "Proximal Policy Optimization Algorithms"
topic: "2模型后训练"
type: note
date: 2026-11-15
---

# PPO 论文精读：Proximal Policy Optimization Algorithms

| 项     | 内容                                                                            |
| ----- | ----------------------------------------------------------------------------- |
| 作者    | John Schulman、Filip Wolski、Prafulla Dhariwal、Alec Radford、Oleg Klimov（OpenAI） |
| 年份    | 2017，arXiv:1707.06347v2                                                       |
| 一句话贡献 | 用**一个 clip 的目标函数**替代 TRPO 的二阶约束优化，让「策略别一步改太狠」变得实现极简，又能多轮复用同一批数据               |
| 影响    | 成为 RLHF 里默认的策略优化算法（见 [[2.2.9 PPO]]）                                           |


## 0. 先记住这三个式子

**① 策略梯度（出发点）**

$$\hat g=\hat{\mathbb{E}}_t\left[\nabla_\theta\log\pi_\theta(a_t\mid s_t)\hat A_t\right]$$

**② TRPO 的替代目标 + 约束**

$$\max_\theta\ \hat{\mathbb{E}}_t\left[\frac{\pi_\theta(a_t\mid s_t)}{\pi_{\theta_{\text{old}}}(a_t\mid s_t)}\hat A_t\right]\quad \text{s.t.}\ \hat{\mathbb{E}}_t\left[D_{\text{KL}}\left(\pi_{\theta_{\text{old}}},\pi_\theta\right)\right]\le\delta$$

**③ PPO 的 clip 目标（全文核心）**

$$L^{\text{CLIP}}(\theta)=\hat{\mathbb{E}}_t\left[\min\left(r_t(\theta)\hat A_t,\ \text{clip}\left(r_t(\theta),1-\epsilon,1+\epsilon\right)\hat A_t\right)\right]$$

其中 $r_t(\theta)=\dfrac{\pi_\theta(a_t\mid s_t)}{\pi_{\theta_{\text{old}}}(a_t\mid s_t)}$ 是**新旧策略的概率比**，$r_t(\theta_{\text{old}})=1$。

## 1. Abstract：作者自己怎么概括

1. 提出一族策略梯度方法：采样与优化交替，但每次采样后可以对同一批数据做**多轮** minibatch 更新。
2. PPO 具备 TRPO 的稳定性，却实现简单得多、更通用、样本效率更好。
3. 在 MuJoCo 连续控制与 Atari 上优于同期在线策略梯度方法，在采样效率、实现难度、墙钟时间之间取得较好平衡。

关键在第一句：标准策略梯度每批数据只能更新一次，PPO 能更新多次——这是它样本效率高的直接原因。

## 2. Introduction：它想解决什么

当时三条主流路线各有短板：

| 路线 | 代表 | 短板 |
| --- | --- | --- |
| 深度 Q-learning | DQN | 离散动作、难处理随机策略 |
| 朴素策略梯度 | REINFORCE、A2C | 数据利用率低、步长难定 |
| 信赖域 / 自然梯度 | TRPO | 稳，但要算 Fisher 矩阵、用共轭梯度，实现复杂，也不适合参数共享架构 |

PPO 的目标很明确：**要 TRPO 的稳定，要一阶方法的简单**。为此必须解决一个矛盾——朴素策略梯度理论上不允许多轮复用数据，因为策略一改，旧数据的分布就对不上了。

## 3. Background：为什么不能一直用同一批数据

### 3.1 朴素策略梯度的困境

用 $L^{\text{PG}}(\theta)=\hat{\mathbb{E}}_t[\log\pi_\theta(a_t\mid s_t)\hat A_t]$ 做梯度上升，每一步都要求数据来自当前策略。对同一批轨迹连续更新多次，策略已经变了而数据还是老策略采的，梯度估计就失去意义——论文直接称其为「**破坏性的大步更新**」（destructively large policy updates）。

### 3.2 TRPO 的做法

TRPO 引入重要性采样比率，把目标改写成：

$$L^{\text{CPI}}(\theta)=\hat{\mathbb{E}}_t\left[r_t(\theta)\hat A_t\right]$$

只要策略没变太远，$r_t\approx1$，这个替代目标就近似真实目标，于是同一批数据可以多用几轮。

但要用得安全，必须限制走多远。TRPO 用硬约束 $\mathbb{E}[D_{\text{KL}}]\le\delta$，实践中靠共轭梯度 + 线搜索求解。

论文指出：理论上更该用**惩罚**而非约束（式 5），但固定惩罚系数 $\beta$ 在不同问题、甚至同一训练的不同阶段都调不好——这才是 TRPO 选择硬约束的原因，也是 PPO 想绕开的麻烦。

## 4. Clipped Surrogate Objective：核心创新

### 4.1 直接的想法与问题

最大化 $L^{\text{CPI}}$ 没有约束时，$r_t$ 会被推到极端（比如 10 倍），策略一步跨太远。TRPO 用 KL 约束挡住，PPO 换了更便宜的办法：**在目标函数里直接削掉"跑太远"的收益**。

### 4.2 公式与两条分支

$$L^{\text{CLIP}}=\hat{\mathbb{E}}_t\left[\min\left(r_t\hat A_t,\ \text{clip}(r_t,1-\epsilon,1+\epsilon)\hat A_t\right)\right]$$

关键在于**分两种情况看**（论文 Figure 1）：

| 情况 | 含义 | 取 min 后发生什么 |
| --- | --- | --- |
| $\hat A_t>0$（动作比平均好） | 想增大其概率 | $r_t$ 超过 $1+\epsilon$ 后，clip 项变成常数 $(1+\epsilon)\hat A_t$，再增大没有额外收益 → 被抑制 |
| $\hat A_t<0$（动作比平均差） | 想减小其概率 | $r_t$ 低于 $1-\epsilon$ 后，clip 项变成常数 $(1-\epsilon)\hat A_t$，再减小没有更多收益 → 被抑制 |

注意 **min 的方向**：整体是**最大化**目标，取 min 意味着「乐观的那一项不算数」，永远按更保守的估计走，所以 $L^{\text{CLIP}}$ 是 $L^{\text{CPI}}$ 的**下界**（pessimistic bound）。

同时它**只惩罚"往坏的方向跑太远"**：如果 $r_t$ 偏离反而让目标变差，那一项照常计入、不被 clip，梯度仍能把它拉回来。

### 4.3 两个容易忽略的细节

- **一阶等价**：在 $\theta=\theta_{\text{old}}$ 附近（$r=1$）有 $L^{\text{CLIP}}=L^{\text{CPI}}$，第一轮更新与普通策略梯度完全一致，只有偏离之后才出现裁剪。
- **$\epsilon=0.2$**：实验里 0.1 / 0.2 / 0.3 都试过，0.2 最好。

## 5. Adaptive KL Penalty：备选方案

PPO 还给了另一条路：不 clip，改成**带自适应系数的 KL 惩罚**。

$$L^{\text{KLPEN}}=\hat{\mathbb{E}}_t\left[r_t\hat A_t-\beta\,D_{\text{KL}}\left(\pi_{\theta_{\text{old}}},\pi_\theta\right)\right]$$

每次更新后测实际 KL 距离 $d$，按规则调 $\beta$：

| 情况 | 调整 |
| --- | --- |
| $d<d_{\text{targ}}/1.5$ | 惩罚太重 → $\beta\leftarrow\beta/2$ |
| $d>d_{\text{targ}}\times1.5$ | 惩罚太轻 → $\beta\leftarrow\beta\times2$ |

论文明确说 KL 惩罚在实验里不如 clip，保留它只为作为基线。原因也好理解：clip 是硬天花板，KL 惩罚是软约束，而 $\beta$ 的调整总滞后一步。

## 6. Algorithm：完整损失与训练循环

### 6.1 三项拼起来的损失

实际使用时策略网络与价值网络常共享参数，于是把三项合并最大化：

$$L^{\text{CLIP+VF+S}}=\hat{\mathbb{E}}_t\left[L_t^{\text{CLIP}}(\theta)-c_1L_t^{\text{VF}}(\theta)+c_2S[\pi_\theta](s_t)\right]$$

| 项 | 作用 |
| --- | --- |
| $L^{\text{CLIP}}$ | 策略目标 |
| $-c_1L^{\text{VF}}$ | 价值函数平方误差，$L^{\text{VF}}=(V_\theta(s_t)-V_t^{\text{targ}})^2$，负号因为整体在最大化 |
| $+c_2S[\pi_\theta]$ | 熵奖励，鼓励探索、防止过早收敛 |

论文实验里策略与价值不共享参数，所以 $c_1$ 不起作用，也没用熵奖励。

### 6.2 优势怎么估：截断的 GAE

只跑 $T$ 步就更新，优势估计不能看 $T$ 之后：

$$\hat A_t=\delta_t+(\gamma\lambda)\delta_{t+1}+\cdots+(\gamma\lambda)^{T-t+1}\delta_{T-1},\qquad \delta_t=r_t+\gamma V(s_{t+1})-V(s_t)$$

$\lambda=1$ 退化成蒙特卡洛减基线，$\lambda=0$ 退化成单步 TD，$\lambda=0.95$ 是常用折中。

### 6.3 伪代码（Algorithm 1）

```text
for iteration = 1, 2, ... :
    for actor = 1..N:                     # N 个并行环境
        用 π_old 跑 T 步，收集轨迹
        计算优势 Â_1..Â_T
    在这 N*T 条样本上，用 minibatch SGD（通常 Adam）优化 L，做 K 个 epoch
    θ_old ← θ
```

三个超参决定"一批数据用多少次"：$T$（每条轨迹长度）、$N$（并行环境数）、$K$（复用轮数）。

## 7. Experiments：作者拿什么证明

### 7.1 先比目标函数（Table 1）

7 个 MuJoCo 任务 × 3 个随机种子，归一化到「随机策略 0 分、最好结果 1 分」：

| 变体 | 归一化得分 |
| --- | --- |
| 不裁剪、不惩罚 | **-0.39**（比随机策略还差） |
| clip $\epsilon=0.1$ | 0.76 |
| **clip $\epsilon=0.2$** | **0.82** |
| clip $\epsilon=0.3$ | 0.70 |
| 自适应 KL，$d_{\text{targ}}=0.01$ | 0.74 |
| 固定 KL，$\beta=3$ | 0.72 |

第一行最值得注意：**没有约束时真的会崩**，某个环境上直接跑成负分，说明多轮复用数据必须配约束。

### 7.2 再比算法（Figure 3）

对比 TRPO、CEM、带自适应步长的朴素策略梯度、A2C、A2C+信赖域：PPO 在几乎全部 MuJoCo 环境上同等样本量下收敛更快、最终分数更高。

### 7.3 高维连续控制与人形机器人

RoboschoolHumanoid 系列（奔跑、按旗子转向、被方块砸还要爬起来）：PPO 能训出稳定策略；同期 Heess 等人的工作也用 PPO 的 KL 变体训练 3D 机器人行走。

### 7.4 Atari（Table 2）

49 个游戏上与 A2C、ACER 对比，按两种口径统计「赢了几局」：

| 口径 | A2C | ACER | **PPO** |
| --- | --- | --- | --- |
| 全训练期平均奖励（偏快） | 1 | 18 | **30** |
| 最后 100 局平均（偏最终性能） | 1 | 28 | 19 |

结论：PPO 学得快（全期口径大幅领先），最终性能略逊 ACER，但实现简单得多。

## 8. Conclusion：作者自己的总结

PPO 用多轮随机梯度上升完成一次策略更新，具备信赖域方法的稳定性，却只比朴素策略梯度多几行代码；可用于策略与价值共享参数的架构；整体性能更好。

## 9. 我的理解：clip 到底在干什么

一句话：**clip 把"这个动作的概率该调多少"变成只在区间内有效的线性函数。**

- 概率比 $r_t$ 从 1 出发；$\hat A_t>0$ 时越大越好，但到 $1+\epsilon$ 就封顶，收益不再增加 → 梯度变 0；
- $\hat A_t<0$ 时越小越好，到 $1-\epsilon$ 封底 → 梯度同样变 0。

效果是**在参数空间里划出一个安全区，一旦走出区外，该样本就不再推动策略继续往那个方向走**。这与 TRPO 的 KL 约束目标一致，但不需要二阶信息。

代价也要说清：clip 只保证**单次更新**不离得太远，不是全局保证；$\epsilon$ 太小学习慢，太大则退化成无约束（实验里 0.3 已明显变差）。

## 10. 与 RLHF-PPO 的关系

这篇论文是纯 RL 场景的 PPO：奖励由环境给，只有 Actor 和 Critic。

RLHF 把它搬到对话生成上时补了两件事：用 Reward 模型给整句打分，用 Reference 模型算 KL 防止 reward hacking。clip 目标本身完全一致，见 [[2.2.9 PPO]] 里「从传统 PPO 到 RLHF-PPO 的三个变化」。

## 11. 面试可能问到的六个点

1. **PPO 相比 TRPO 改了什么**：把 KL 硬约束换成一阶可导的 clip，省掉 Fisher 矩阵与共轭梯度。
2. **为什么要用概率比 $r_t$**：让同一批旧数据在新策略下仍可用（重要性采样），从而支持多轮更新。
3. **为什么要取 min**：取较小值构成下界，避免对乐观估计过度优化。
4. **$\epsilon$ 的作用与取值**：控制单次更新的信赖域宽度，0.2 为实验最佳。
5. **KL 惩罚为什么不如 clip**：软约束加系数滞后调整，得分 0.68~0.74，而 clip 达 0.82。
6. **PPO 为什么在 LLM 里流行**：实现简单、支持并行采样、对超参不敏感；缺点是四模型同时驻留显存，之后才有 DPO/GRPO 等替代。

## 12. 论文附录的超参（MuJoCo 100 万步设置）

| 超参 | 值 |
| --- | --- |
| 轨迹长度 $T$ | 2048 |
| Adam 学习率 | $3\times10^{-4}$ |
| 复用轮数 $K$ | 10 |
| minibatch | 64 |
| 折扣 $\gamma$ | 0.99 |
| GAE $\lambda$ | 0.95 |
| clip $\epsilon$ | 0.2 |
