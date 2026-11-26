---
title: "ViT"
topic: "多模型"
type: note
date: 2026-11-18
---

# ViT（Vision Transformer）

ViT 是把图像当作“一句话”交给 Transformer 处理，不做卷积

## 模型介绍

在计算机视觉领域中，多数算法都保持 CNN 整体结构不变，在 CNN 中增加 attention 模块，或用 attention 模块替换 CNN 的某些部分。有研究者提出，没必要总是依赖 CNN，于是提出 ViT：**仅使用 Transformer 结构也能在图像分类任务上表现很好**。

受 NLP 中 Transformer 成功应用的启发，ViT 尝试把标准 Transformer 直接用于图像，只对分类流程做最少的修改：把整幅图像拆成小图像块，把这些块的线性嵌入序列作为 Transformer 输入，再用监督学习做图像分类训练。

在中等规模（ImageNet）与大规模（ImageNet-21K、JFT-300M）数据上的实验结果：

- Transformer 相比 CNN 缺少一定的**平移不变性**与**局部感知性**，数据不充分时难以达到同等效果；用中等规模 ImageNet 训练时，精度比 ResNet 低几个百分点。
- 当训练样本足够多时结论反转：用大规模数据预训练后再迁移到其他数据集，可达到或超过当时 SOTA。

## 模型结构与实现

![[Pasted image 20261118115539.png|804]]

### 1. 图像分块嵌入

Transformer 的输入是二维矩阵，形状可表示为 $(N,D)$：$N$ 是序列长度，$D$ 是每个向量的维度。因此第一步要把 $H\times W\times C$ 的三维图像转成 $(N,D)$。

具体做法：把 $H\times W\times C$ 的图像变为 $N\times(P^2\cdot C)$ 的序列，即切成小块后展平。序列共含 $N=\frac{HW}{P^2}$ 个图像块，每块维度为 $P^2\cdot C$，其中 $P$ 是块大小，$C$ 是通道数。此时 $N$ 就可以当作序列长度。

但每块维度是 $P^2\cdot C$，而需要的向量维度是 $D$，所以还要做 Embedding：**对每个 $P^2\cdot C$ 的块做一次线性变换，压到 $D$ 维**。

> [图 2] 图像分块嵌入示意图

代码实现中，用一个大小等于 $P$、步长也等于 $P$ 的卷积核，代替原文的「展平 + 全连接」：

```python
# 图像分块、Embedding
class PatchEmbed(nn.Layer):
    def __init__(self, img_size=224, patch_size=16, in_chans=3, embed_dim=768):
        super().__init__()
        img_size = to_2tuple(img_size)     # 224 -> (224, 224)
        patch_size = to_2tuple(patch_size)
        num_patches = (img_size[1] // patch_size[1]) * \
            (img_size[0] // patch_size[0])       # 图像块个数
        self.img_size = img_size
        self.patch_size = patch_size
        self.num_patches = num_patches
        # kernel_size = 块大小：每个块输出一个值，等价于逐块展平后共用同一个全连接
        self.proj = nn.Conv2D(
            in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x):
        B, C, H, W = x.shape
        assert H == self.img_size[0] and W == self.img_size[1], \
            "Input image size ({H}*{W}) doesn't match model."
        # [B, C, H, W] -> [B, C, H*W] -> [B, H*W, C]
        x = self.proj(x).flatten(2).transpose((0, 2, 1))
        return x
```

### 2. 多头注意力

图像转成 $N\times(P^2\cdot C)$ 序列后，就可以送入 Transformer 提取特征（图 3）。

> [图 3] 多头注意力示意图

Multi-head Attention 是 Transformer 最核心的结构。以 2 个 head 为例（图 4）：输入 $a_i$ 经转移矩阵切分为 $q_{(i,1)},q_{(i,2)},k_{(i,1)},k_{(i,2)},v_{(i,1)},v_{(i,2)}$，然后 $q_{(i,1)}$ 与 $k_{(i,1)}$ 做 attention 得到权重 $\alpha$，再与 $v_{(i,1)}$ 加权求和得到 $b_{(i,1)}$（$i=1,2,\dots,N$）；同理得 $b_{(i,2)}$。最后拼接并过一层线性层。

> [图 4] 多头注意力

其中由 $q,k,v$ 计算 $b$ 的方式是**缩放点积注意力**（图 5）：用每个 $q_{(i,j)}$ 与所有 $k_{(i,j)}$ 做加权内积，得到匹配度 $\alpha_{1,i}=\frac{q_1\cdot k_i}{\sqrt{d}}$。$d$ 是 $q$ 与 $k$ 的维度。因为内积数值随维度增大而增大，除以 $\sqrt{d}$ 相当于归一化。接着对 $\alpha_{(i,j)}$ 做 softmax，再与 $v_{(i,j)}$ 相乘。

> [图 5] 缩放点积注意力

```python
# Multi-head Attention
class Attention(nn.Layer):
    def __init__(self, dim, num_heads=8, qkv_bias=False, qk_scale=None,
                 attn_drop=0., proj_drop=0.):
        super().__init__()
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = qk_scale or head_dim ** -0.5
        self.qkv = nn.Linear(dim, dim * 3, bias_attr=qkv_bias)  # q,k,v 转移矩阵
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)                          # 最终线性层
        self.proj_drop = nn.Dropout(proj_drop)

    def forward(self, x):
        N, C = x.shape[1:]
        qkv = self.qkv(x).reshape(
            (-1, N, 3, self.num_heads, C // self.num_heads)
        ).transpose((2, 0, 3, 1, 4))
        q, k, v = qkv[0], qkv[1], qkv[2]           # 分割 q/k/v
        attn = (q.matmul(k.transpose((0, 1, 3, 2)))) * self.scale   # Matmul + Scale
        attn = nn.functional.softmax(attn, axis=-1)                 # Softmax
        attn = self.attn_drop(attn)
        x = (attn.matmul(v)).transpose((0, 2, 1, 3)).reshape((-1, N, C))
        x = self.proj(x)
        x = self.proj_drop(x)
        return x
```

### 3. 多层感知机（MLP）

Transformer 另一个重要结构是 MLP（图 6、图 7）：由输入层、输出层和至少一层隐藏层构成，相邻层之间全连接，可以拟合复杂非线性函数，复杂度取决于隐藏层数目与每层神经元数。

> [图 6] MLP 结构

> [图 7] 多层感知机

```python
class Mlp(nn.Layer):
    def __init__(self, in_features, hidden_features=None, out_features=None,
                 act_layer=nn.GELU, drop=0.):
        super().__init__()
        out_features = out_features or in_features
        hidden_features = hidden_features or in_features
        self.fc1 = nn.Linear(in_features, hidden_features)
        self.act = act_layer()
        self.fc2 = nn.Linear(hidden_features, out_features)
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        x = self.fc1(x)     # 输入层
        x = self.act(x)     # 激活
        x = self.drop(x)
        x = self.fc2(x)     # 输出层
        x = self.drop(x)
        return x
```

### 4. DropPath

代码中还用了 DropPath（Stochastic Depth）替代传统 Dropout：训练时**随机丢弃整个子层**，预测时使用完整网络。

```python
def drop_path(x, drop_prob=0., training=False):
    if drop_prob == 0. or not training:
        return x
    keep_prob = paddle.to_tensor(1 - drop_prob)
    shape = (paddle.shape(x)[0],) + (1,) * (x.ndim - 1)
    random_tensor = keep_prob + paddle.rand(shape, dtype=x.dtype)
    random_tensor = paddle.floor(random_tensor)
    output = x.divide(keep_prob) * random_tensor
    return output

class DropPath(nn.Layer):
    def __init__(self, drop_prob=None):
        super(DropPath, self).__init__()
        self.drop_prob = drop_prob

    def forward(self, x):
        return drop_path(x, self.drop_prob, self.training)
```

### 5. 基础模块

把 Attention、MLP、DropPath 组合起来就是一个基础 Block（图 8），采用 Pre-LN 结构：先归一化再进子层，最后残差相加。

> [图 8] 基础模块示意图

```python
class Block(nn.Layer):
    def __init__(self, dim, num_heads, mlp_ratio=4., qkv_bias=False, qk_scale=None,
                 drop=0., attn_drop=0., drop_path=0., act_layer=nn.GELU,
                 norm_layer='nn.LayerNorm', epsilon=1e-5):
        super().__init__()
        self.norm1 = eval(norm_layer)(dim, epsilon=epsilon)
        self.attn = Attention(dim, num_heads=num_heads, qkv_bias=qkv_bias,
                              qk_scale=qk_scale, attn_drop=attn_drop, proj_drop=drop)
        self.drop_path = DropPath(drop_path) if drop_path > 0. else Identity()
        self.norm2 = eval(norm_layer)(dim, epsilon=epsilon)
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim,
                       act_layer=act_layer, drop=drop)

    def forward(self, x):
        x = x + self.drop_path(self.attn(self.norm1(x)))    # MHSA + Add
        x = x + self.drop_path(self.mlp(self.norm2(x)))     # FFN + Add
        return x
```

### 6. 定义 ViT 网络

构建完整网络前，先看三个模块。

**Class Token**：把图像切成 $3\times3$ 共 9 块，最终输入序列长度却是 10——多出来的那个可学习向量就是 Class Token。它的作用在于：如果只有 9 个编码向量，分类时该用哪一个？于是把 Class Token 与 9 个向量一起输入，输出 10 个编码向量，用 Class Token 对应的那个做分类。

换个角度理解：ViT 只用了 Transformer 的 Encoder，Class Token 的作用就是"汇总其他 9 个输入向量的类别信息"。

**Positional Encoding**：ViT 没有用原版 Transformer 的 sincos 编码，而是直接用**可学习**的位置编码。可视化后（图 9）可以看到位置越接近、编码越相似，并出现行列结构——同一行/列的 patch 编码接近。

> [图 9] Positional Encoding 可视化

**MLP Head**：输出后接一个由 LayerNorm + 两层全连接组成的分类头，激活函数为 GELU。

先准备基础工具：

```python
# 参数初始化
trunc_normal_ = nn.initializer.TruncatedNormal(std=.02)
zeros_ = nn.initializer.Constant(value=0.)
ones_ = nn.initializer.Constant(value=1.)

def to_2tuple(x):
    return tuple([x] * 2)

class Identity(nn.Layer):
    def __init__(self):
        super(Identity, self).__init__()

    def forward(self, input):
        return input
```

完整网络：

```python
class VisionTransformer(nn.Layer):
    def __init__(self, img_size=224, patch_size=16, in_chans=3, class_dim=1000,
                 embed_dim=768, depth=12, num_heads=12, mlp_ratio=4, qkv_bias=False,
                 qk_scale=None, drop_rate=0., attn_drop_rate=0., drop_path_rate=0.,
                 norm_layer='nn.LayerNorm', epsilon=1e-5, **args):
        super().__init__()
        self.class_dim = class_dim
        self.num_features = self.embed_dim = embed_dim
        # 分块 + 降维：块大小 patch_size，输出维度 embed_dim
        self.patch_embed = PatchEmbed(img_size=img_size, patch_size=patch_size,
                                      in_chans=in_chans, embed_dim=embed_dim)
        num_patches = self.patch_embed.num_patches
        # 可学习位置编码（长度 = 块数 + 1 个 class token）
        self.pos_embed = self.create_parameter(
            shape=(1, num_patches + 1, embed_dim), default_initializer=zeros_)
        self.add_parameter("pos_embed", self.pos_embed)
        # class token
        self.cls_token = self.create_parameter(
            shape=(1, 1, embed_dim), default_initializer=zeros_)
        self.add_parameter("cls_token", self.cls_token)
        self.pos_drop = nn.Dropout(p=drop_rate)

        dpr = np.linspace(0, drop_path_rate, depth)     # 各层 drop path 率递增
        self.blocks = nn.LayerList([
            Block(dim=embed_dim, num_heads=num_heads, mlp_ratio=mlp_ratio,
                  qkv_bias=qkv_bias, qk_scale=qk_scale, drop=drop_rate,
                  attn_drop=attn_drop_rate, drop_path=dpr[i],
                  norm_layer=norm_layer, epsilon=epsilon)
            for i in range(depth)
        ])

        self.norm = eval(norm_layer)(embed_dim, epsilon=epsilon)
        self.head = nn.Linear(embed_dim, class_dim) if class_dim > 0 else Identity()

        trunc_normal_(self.pos_embed)
        trunc_normal_(self.cls_token)
        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            trunc_normal_(m.weight)
            if m.bias is not None:
                zeros_(m.bias)
        elif isinstance(m, nn.LayerNorm):
            zeros_(m.bias)
            ones_(m.weight)

    def forward_features(self, x):
        B = paddle.shape(x)[0]
        x = self.patch_embed(x)                       # 分块 + 降维
        cls_tokens = self.cls_token.expand((B, -1, -1))
        x = paddle.concat((cls_tokens, x), axis=1)    # 拼上 class token
        x = x + self.pos_embed                        # 加位置编码
        x = self.pos_drop(x)
        for blk in self.blocks:                       # 堆叠 Transformer
            x = blk(x)
        x = self.norm(x)
        return x[:, 0]                                # 只取 class token 的输出

    def forward(self, x):
        x = self.forward_features(x)
        x = self.head(x)
        return x
```

## 模型指标

在常用数据集上做迁移学习：

| 数据集 | 最高指标 |
| --- | --- |
| ImageNet | 88.55% |
| ImageNet ReaL | 90.72% |
| CIFAR-100 | 94.55% |
| VTAB（19 tasks） | 88.55% |

> [图 10] ViT 网络指标

## 模型特点

- 与 CNN 不同，ViT 把标准 Transformer 直接用于图像，对分类流程做最少修改
- 为满足 Transformer 的输入要求，把图像拆成小块后线性嵌入成序列
- 用 Class Token 承担分类输出，避免"9 个向量里该挑哪个"的问题

## 参考文献

[1] An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale

## 相关笔记

- 多头注意力机制与形状推导：[[transformer#06 多头注意力：为什么分头（含手算与默写）]]
- 位置编码对比（可学习 vs RoPE）：[[位置编码]]
- ViT 与 CNN 的归纳偏置差异，见本文「模型介绍」第 1 条
