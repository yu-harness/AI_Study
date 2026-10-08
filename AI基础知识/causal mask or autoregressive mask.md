**Causal Mask**（因果掩码），在生成任务中也常被称为 **Autoregressive Mask**（自回归掩码），是所有自回归语言模型（如 GPT 系列、Llama 系列等 Decoder-only 架构）中最关键的结构约束。

其核心定义一句话概括：**在计算注意力分布时，强制让每一个 Token 只能关注自身及排在它之前的 Token，彻底屏蔽未来时间步的信息。**



在标准的自注意力机制中，注意力分数矩阵由 $S = \frac{QK^T}{\sqrt{d_k}}$ 计算得出，其形状为 $[L, L]$（其中 $L$ 为序列长度），矩阵元素 $S_{i, j}$ 表示第 $i$ 个 Token（Query）去关注第 $j$ 个 Token（Key）的未归一化打分。

为了保证因果性，必须对未来位置（即 $j > i$ 的位置）施加惩罚：
$$M_{i, j} = \begin{cases} 0, & j \le i \\ -\infty, & j > i \end{cases}$$
掩码后的注意力打分计算为：
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}} + M\right)V$$

#### 掩码矩阵的形状
掩码后送入 Softmax 的矩阵天然是一个**下三角矩阵**（包含对角线）：
$$\begin{bmatrix} S_{11} & -\infty & -\infty & \dots & -\infty \\ S_{21} & S_{22} & -\infty & \dots & -\infty \\ S_{31} & S_{32} & S_{33} & \dots & -\infty \\ \vdots & \vdots & \vdots & \ddots & \vdots \\ S_{L1} & S_{L2} & S_{L3} & \dots & S_{LL} \end{bmatrix}$$

由于 $e^{-\infty} = 0$，经过 Softmax 之后，所有原本填入 $-\infty$ 的位置权重全部严格变为 **0**，这意味着模型在计算表征时完全切断了与后续 Token 的信息传递路径。
### 2. 为什么必须引入 Causalx Mask？
1. **防止“信息穿越（Data Leakage）”**
    - 自回归模型（AR）的核心训练目标是最大化联合概率：
$$P(w_1, w_2, \dots, w_L) = \prod_{t=1}^L P(w_t \mid w_1, \dots, w_{t-1})$$
    - 如果不加掩码，在预测第 $t$ 个词时，第 $t$ 层甚至更高层网络可以直接通过全连接的 Attention 抄到第 $t$ 个词乃至之后词的 Embedding，网络会退化为恒等映射（抄答案），失去生成能力。
**训练并行与推理串行的统一桥梁**
- **训练时（Teacher Forcing）**：由于目标文本完整已知，借助 Causal Mask 的下三角性质，整段序列（长度 $L$）可以一次性送入 GPU 进行大矩阵乘法，**$L$ 个位置的损失同时并行计算**，完全不需要写 `for` 循环逐步预测。
- **推理时（自回归解码）**：在实际生成文本时，未来词尚未产生，自然无法看到未来；Causal Mask 确保了训练时的上下文视野与推理生成时的视野完全一致（保持同构）。
### 3. 工程实现与优化演进
在工程落地中，Causal Mask 的实现经历了从“纯张量相加”到“内核级融合”的演进：
- **朴素实现（Add Mask）**：
    分配一个形状为 $[L, L]$ 的下三角浮点张量，直接将其加在点积结果矩阵上。
    - _劣势_：需要将 $[L, L]$ 的中间矩阵显式写入显存（HBM），显存占用为 $O(L^2)$，长序列极易导致 OOM。
- **算子级融合（Fused Causal Mask）**：
    在 PyTorch 常见的 CUDA Kernel 中，将掩码逻辑融合进 Softmax 计算流中，若索引满足 `col > row`，直接跳过计算并置为 0，避免显式构建显存掩码矩阵。
- **FlashAttention 架构优化**：
    在 FlashAttention 中，利用 Causal Mask 的几何规则，甚至可以**直接跳过严格处于上三角的计算块（Tile/Block）**。这不仅节省了显存读写，还将 GEMM 的计算量直接减少了接近 **50%**。

