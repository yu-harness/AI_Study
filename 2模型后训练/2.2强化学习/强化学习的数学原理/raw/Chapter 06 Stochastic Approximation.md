---
title: "Chapter 06 Stochastic Approximation"
topic: "2模型后训练"
type: note
date: 2026-11-06
---

# Chapter 6 Stochastic Approximation

![](d0aeb8f0f99e3c2775c0cdf33d77dbf36b704121f1f8a9a35a0d18fc40b615f5.jpg)

*Figure 6.1: Where we are in this book.*

Chapter 5 introduced the first class of model-free reinforcement learning algorithms based on Monte Carlo estimation. In the next chapter (Chapter 7), we will introduce another class of model-free reinforcement learning algorithms: temporal-difference learning. However, before proceeding to the next chapter, we need to press the pause button to better prepare ourselves. This is because temporal-difference algorithms are very different from the algorithms that we have studied so far. Many readers who see the temporal difference algorithms for the first time often wonder how these algorithms were designed in the first place and why they can work effectively. In fact, there is a knowledge gap between the previous and subsequent chapters: the algorithms we have studied so far are non-incremental, but the algorithms that we will study in the subsequent chapters are incremental.

We use the present chapter to fill this knowledge gap by introducing the basics of stochastic approximation. Although this chapter does not introduce any specific reinforcement learning algorithms, it lays the necessary foundations for studying subsequent chapters. We will see in Chapter 7 that the temporal-difference algorithms can be viewed as special stochastic approximation algorithms. The well-known stochastic gradi ent descent algorithms widely used in machine learning are also introduced in the present chapter.

## 6.1 Motivating example: Mean estimation

We next demonstrate how to convert a non-incremental algorithm to an incremental one by examining the mean estimation problem.

Consider a random variable X that takes values from a finite set . Our goal is to estimate E[X]. Suppose that we have a sequence of i.i.d. samples $\{ x _ { i } \} _ { i = 1 } ^ { n }$ . The expected value of X can be approximated by

$$
\mathbb {E} [ X ] \approx \bar {x} \doteq \frac {1}{n} \sum_ {i = 1} ^ {n} x _ {i}.\tag{6.1}
$$

The approximation in (6.1) is the basic idea of Monte Carlo estimation, as introduced in Chapter 5. We know that $\bar { x } \to \mathbb { E } [ X ]$ as $n \to \infty$ according to the law of large numbers.

We next show that two methods can be used to calculate ¯x in (6.1). The first nonincremental method collects all the samples first and then calculates the average. The drawback of such a method is that, if the number of samples is large, we may have to wait for a long time until all of the samples are collected. The second method can avoid this drawback because it calculates the average in an incremental manner. Specifically, suppose that

$$
w _ {k + 1} \doteq \frac {1}{k} \sum_ {i = 1} ^ {k} x _ {i}, \quad k = 1, 2, \dots
$$

and hence

$$
w _ {k} = \frac {1}{k - 1} \sum_ {i = 1} ^ {k - 1} x _ {i}, \quad k = 2, 3, \dots
$$

Then, $w _ { k + 1 }$ can be expressed in terms of $w _ { k }$ as

$$
w _ {k + 1} = \frac {1}{k} \sum_ {i = 1} ^ {k} x _ {i} = \frac {1}{k} \left(\sum_ {i = 1} ^ {k - 1} x _ {i} + x _ {k}\right) = \frac {1}{k} ((k - 1) w _ {k} + x _ {k}) = w _ {k} - \frac {1}{k} (w _ {k} - x _ {k}).
$$

Therefore, we obtain the following incremental algorithm:

$$
w _ {k + 1} = w _ {k} - \frac {1}{k} (w _ {k} - x _ {k}).\tag{6.2}
$$

This algorithm can be used to calculate the mean ¯x in an incremental manner. It can be verified that

$$
\begin{array}{l} w _ {1} = x _ {1}, \\ w _ {2} = w _ {1} - \frac {1}{1} (w _ {1} - x _ {1}) = x _ {1}, \\ w _ {3} = w _ {2} - \frac {1}{2} (w _ {2} - x _ {2}) = x _ {1} - \frac {1}{2} (x _ {1} - x _ {2}) = \frac {1}{2} (x _ {1} + x _ {2}), \\ w _ {4} = w _ {3} - \frac {1}{3} (w _ {3} - x _ {3}) = \frac {1}{3} (x _ {1} + x _ {2} + x _ {3}), \\ \vdots \end{array}
$$

$$
w _ {k + 1} = \frac {1}{k} \sum_ {i = 1} ^ {k} x _ {i}.\tag{6.3}
$$

The advantage of (6.2) is that the average can be immediately calculated every time we receive a sample. This average can be used to approximate ¯x and hence $\mathbb { E } [ X ]$ . Notably, the approximation may not be accurate at the beginning due to insuficient samples. However, it is better than nothing. As more samples are obtained, the estimation accuracy can be gradually improved according to the law of large numbers. In addition, one can also define $\begin{array} { r } { w _ { k + 1 } = \frac { 1 } { 1 + k } \sum _ { i = 1 } ^ { k + 1 } x _ { i } } \end{array}$ and $\begin{array} { r } { \boldsymbol { w _ { k } } \ : = \ : \frac { 1 } { k } \sum _ { i = 1 } ^ { k } \boldsymbol { x _ { i } } } \end{array}$ . Doing so would not make any significant difference. In this case, the corresponding iterative algorithm is $w _ { k + 1 } =$ $\begin{array} { r } { w _ { k } - \frac { 1 } { 1 + k } ( w _ { k } - x _ { k + 1 } ) } \end{array}$

Furthermore, consider an algorithm with a more general expression:

$$
w _ {k + 1} = w _ {k} - \alpha_ {k} (w _ {k} - x _ {k}).\tag{6.4}
$$

This algorithm is important and frequently used in this chapter. It is the same as (6.2) except that the coefficient $1 / k$ is replaced by $\alpha _ { k } > 0$ . Since the expression of $\alpha _ { k }$ is not given, we are not able to obtain the explicit expression of $w _ { k }$ as in (6.3). However, we will show in the next section that, if $\left\{ \alpha _ { k } \right\}$ satisfies some mild conditions, $w _ { k } \to \mathbb { E } [ X ]$ as $k  \infty$ . In Chapter $^ { 7 , }$ we will see that temporal-difference algorithms have similar (but more complex) expressions.

## 6.2 Robbins-Monro algorithm

Stochastic approximation refers to a broad class of stochastic iterative algorithms for solving root-finding or optimization problems [24]. Compared to many other root-finding algorithms such as gradient-based ones, stochastic approximation is powerful in the sense that it does not require the expression of the objective function or its derivative.

The Robbins-Monro (RM) algorithm is a pioneering work in the field of stochastic approximation [24–27]. The famous stochastic gradient descent algorithm is a special form of the RM algorithm, as shown in Section 6.4. We next introduce the details of the RM algorithm.

Suppose that we would like to find the root of the equation

$$
g (w) = 0,
$$

where $w \in \mathbb { R }$ is the unknown variable and $g : \mathbb { R } $ R is a function. Many problems can be formulated as root-finding problems. For example, if $J ( w )$ is an objective function to be optimized, this optimization problem can be converted to solving $g ( w ) \doteq \nabla _ { w } J ( w ) = 0$ In addition, an equation such as $g ( w ) = c _ { : }$ , where c is a constant, can also be converted to the above equation by rewriting $g ( w ) - c$ as a new function.

If the expression of $g$ or its derivative is known, there are many numerical algorithms that can be used. However, the problem we are facing is that the expression of the function $g$ is unknown. For example, the function may be represented by an artificial neural network whose structure and parameters are unknown. Moreover, we can only obtain a noisy observation of $g ( w )$ :

$$
\tilde {g} (w, \eta) = g (w) + \eta ,
$$

where $\eta \in \mathbb { R }$ is the observation error, which may or may not be Gaussian. In summary, it is a black-box system where only the input w and the noisy output $\widetilde g ( w , \eta )$ are known (see Figure 6.2). Our aim is to solve $g ( w ) = 0$ using w and $\tilde { g }$

![](3714d0811b339da6a32d33127c2c643490bc61e252378350bd7350d7803965ff.jpg)

*Figure 6.2: An illustration of the problem of solvingFig. 1: xx $g ( w ) = 0$ from w and ${ \tilde { g } } .$*

The RM algorithm that can solve $g ( w ) = 0$ is

$$
w _ {k + 1} = w _ {k} - a _ {k} \tilde {g} (w _ {k}, \eta_ {k}), \qquad k = 1, 2, 3, \ldots\tag{6.5}
$$

where $w _ { k }$ is the kth estimate of the root, $\tilde { g } ( w _ { k } , \eta _ { k } )$ is the kth noisy observation, and $a _ { k }$ is a positive coefficient. As can be seen, the RM algorithm does not require any information about the function. It only requires the input and output.

![](10c0cdc927dced39f72dacfe461820cd960b8896708d3c59f55962bbe1dd8d7a.jpg)

![](3ec9ab464331d6bc970d9b475bbe677ad3aa36deecb25806736d702dd7365437.jpg)

*Figure 6.3: An illustrative example of the RM algorithm.*

To illustrate the RM algorithm, consider an example in which $g ( w ) = w ^ { 3 } - 5$ . The true root is $5 ^ { 1 / 3 } \approx 1 . 7 1$ . Now, suppose that we can only observe the input w and the output $\tilde { g } ( w ) = g ( w ) + \eta$ , where $\eta$ is i.i.d. and obeys a standard normal distribution with a zero mean and a standard deviation of 1. The initial guess is $w _ { 1 } = 0$ , and the coefficient is $a _ { k } = 1 / k$ . The evolution process of $w _ { k }$ is shown in Figure 6.3. Even though the observation is corrupted by noise $\eta _ { k }$ , the estimate $w _ { k }$ can still converge to the true root. Note that the initial guess $w _ { 1 }$ must be properly selected to ensure convergence for the specific function of $g ( w ) = w ^ { 3 } - 5$ . In the following subsection, we present the conditions under which the RM algorithm converges for any initial guesses.

### 6.2.1 Convergence properties

Why can the RM algorithm in (6.5) find the root of $g ( w ) = 0 ?$ We next illustrate the idea with an example and then provide a rigorous convergence analysis.

Consider the example shown in Figure 6.4. In this example, $g ( w ) = \operatorname { t a n h } ( w - 1 )$ . The true root of $g ( w ) = 0 { \mathrm { ~ i s ~ } } w ^ { * } = 1$ . We apply the RM algorithm with $w _ { 1 } = 3$ and $a _ { k } = 1 / k$ To better illustrate the reason for convergence, we simply set $\eta _ { k } \equiv 0$ , and consequently, $\tilde { g } ( w _ { k } , \eta _ { k } ) = g ( w _ { k } )$ . The RM algorithm in this case is $w _ { k + 1 } = w _ { k } - a _ { k } g ( w _ { k } )$ . The resulting $\{ w _ { k } \}$ generated by the RM algorithm is shown in Figure 6.4. It can be seen that $w _ { k }$ converges to the true root $w ^ { * } = 1$

This simple example can illustrate why the RM algorithm converges.

When $w _ { k } > w ^ { * }$ , we have $g ( w _ { k } ) > 0$ . Then, $w _ { k + 1 } = w _ { k } - a _ { k } g ( w _ { k } ) < w _ { k }$ . If $a _ { k } g ( w _ { k } )$ is suficiently small, we have $w ^ { \ast } < w _ { k + 1 } < w _ { k }$ . As a result, $w _ { k + 1 }$ is closer to $w ^ { * }$ than $w _ { k }$

When $w _ { k } < w ^ { * }$ , we have $g ( w _ { k } ) < 0$ . Then, $w _ { k + 1 } = w _ { k } - a _ { k } g ( w _ { k } ) > w _ { k } . { \mathrm { ~ I f ~ } } | a _ { k } g ( w _ { k } ) |$ is suficiently small, we have $w ^ { \ast } > w _ { k + 1 } > w _ { k }$ . As a result, $w _ { k + 1 }$ is closer to $w ^ { * }$ than $w _ { k }$

In either case, $w _ { k + 1 }$ is closer to $w ^ { * }$ than $w _ { k }$ . Therefore, it is intuitive that $w _ { k }$ converges to $w ^ { * }$

![](2b0542c55b2ad6d641d45b8d3149225ed40f82916cb5cc9bd820ef04b25b48f2.jpg)

*Figure 6.4: An example for illustrating the convergence of the RM algorithm.*

The above example is simple since the observation error is assumed to be zero. It would be nontrivial to analyze the convergence in the presence of stochastic observation errors. A rigorous convergence result is given below.

Theorem 6.1 (Robbins-Monro theorem). In the Robbins-Monro algorithm in (6.5), if

(a) $0 < c _ { 1 } \leq \nabla _ { w } g ( w ) \leq c _ { 2 }$ for all w;

(b) $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } = \infty$ and $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } ^ { 2 } < \infty ,$

(c) $\mathbb { E } [ \eta _ { k } | \mathcal { H } _ { k } ] = 0$ and $\mathbb { E } [ \eta _ { k } ^ { 2 } \vert \mathcal { H } _ { k } ] < \infty ,$ where $\mathcal { H } _ { k } = \{ w _ { k } , w _ { k - 1 } , . . . \}$ , then $w _ { k }$ almost surely converges to the root $w ^ { * }$ satisfying $g ( w ^ { * } ) = 0$

We postpone the proof of this theorem to Section 6.3.3. This theorem relies on the notion of almost sure convergence, which is introduced in Appendix B.

The three conditions in Theorem 6.1 are explained as follows.

In the first condition, $0 < c _ { 1 } \le \nabla _ { w } g ( w )$ indicates that $g ( w )$ is a monotonically increasing function. This condition ensures that the root of $g ( w ) = 0$ exists and is unique. If $g ( w )$ is monotonically decreasing, we can simply treat $- g ( w )$ as a new function that is monotonically increasing.

As an application, we can formulate an optimization problem in which the objective function is $J ( w )$ as a root-finding problem: $g ( w ) \doteq \nabla _ { w } J ( w ) = 0$ . In this case, the condition that $g ( w )$ is monotonically increasing indicates that $J ( w )$ is convex, which is a commonly adopted assumption in optimization problems.

The inequality $\nabla _ { w } g ( w ) \le c _ { 2 }$ indicates that the gradient of $g ( w )$ is bounded from above. For example, $g ( w ) = \operatorname { t a n h } ( w - 1 )$ satisfies this condition, but $g ( w ) = w ^ { 3 } - 5$ does not.

The second condition about $\{ a _ { k } \}$ is interesting. We often see conditions like this in reinforcement learning algorithms. In particular, the condition $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } ^ { 2 } < \infty$ means that li $\textstyle \operatorname* { m } _ { n \to \infty } \sum _ { k = 1 } ^ { n } a _ { k } ^ { 2 }$ is bounded from above. It requires that $a _ { k }$ converges to zero as $k  \infty$ . The condition $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } = \infty$ means that lim $\scriptstyle 1 _ { n \to \infty } \sum _ { k = 1 } ^ { n } a _ { k }$ is infinitely large. It requires that $a _ { k }$ should not converge to zero too fast. These conditions have interesting properties, which will be analyzed in detail shortly.

The third condition is mild. It does not require the observation error $\eta _ { k }$ to be Gaussian. An important special case is that $\{ \eta _ { k } \}$ is an i.i.d. stochastic sequence satisfying $\mathbb { E } [ \eta _ { k } ] = 0$ and $\mathbb { E } [ \eta _ { k } ^ { 2 } ] < \infty$ . In this case, the third condition is valid because $\eta _ { k }$ is independent of $\mathcal { H } _ { k }$ and hence we have $\mathbb { E } [ \eta _ { k } | \mathcal { H } _ { k } ] = \mathbb { E } [ \eta _ { k } ] = 0$ and $\mathbb { E } [ \eta _ { k } ^ { 2 } | \mathcal { H } _ { k } ] = \mathbb { E } [ \eta _ { k } ^ { 2 } ]$

We next examine the second condition about the coeficients $\{ a _ { k } \}$ more closely.

Why is the second condition important for the convergence of the RM algorithm? This question can naturally be answered when we present a rigorous proof of the above theorem later. Here, we would like to provide some insightful intuition.

First, $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } ^ { 2 } < \infty$ indicates that $a _ { k } \to 0$ as $k  \infty$ . Why is this condition important? Suppose that the observation $\tilde { g } ( w _ { k } , \eta _ { k } )$ is always bounded. Since

$$
w _ {k + 1} - w _ {k} = - a _ {k} \tilde {g} (w _ {k}, \eta_ {k}),
$$

if $a _ { k } \to 0$ , then $a _ { k } \tilde { g } ( w _ { k } , \eta _ { k } )  0$ and hence $w _ { k + 1 } - w _ { k } \to 0$ , indicating that $w _ { k + 1 }$ and $w _ { k }$ approach each other when $k  \infty$ . Otherwise, if $a _ { k }$ does not converge, then $w _ { k }$ may still fluctuate when $k  \infty$

Second, $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } = \infty$ indicates that $a _ { k }$ should not converge to zero too fast. Why is this condition important? Summarizing both sides of the equations of $w _ { 2 } - w _ { 1 } =$ $- a _ { 1 } \tilde { g } ( w _ { 1 } , \eta _ { 1 } ) , w _ { 3 } - w _ { 2 } = - a _ { 2 } \tilde { g } ( w _ { 2 } , \eta _ { 2 } ) , w _ { 4 } - w _ { 3 } = - a _ { 3 } \tilde { g } ( w _ { 3 } , \eta _ { 3 } ) , \dots \mathrm { ~ g i v e s }$

$$
w _ {1} - w _ {\infty} = \sum_ {k = 1} ^ {\infty} a _ {k} \tilde {g} (w _ {k}, \eta_ {k}).
$$

If $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } < \infty$ , then $\textstyle { \big | } \sum _ { k = 1 } ^ { \infty } a _ { k } { \tilde { g } } ( w _ { k } , \eta _ { k } ) { \big | }$ is also bounded. Let b denote the finite upper bound such that

$$
\left| w _ {1} - w _ {\infty} \right| = \left| \sum_ {k = 1} ^ {\infty} a _ {k} \tilde {g} (w _ {k}, \eta_ {k}) \right| \leq b.\tag{6.6}
$$

If the initial guess $w _ { 1 }$ is selected far away from $w ^ { * }$ so that $| w _ { 1 } - w ^ { * } | > b$ , then it is impossible to have $w _ { \infty } = w ^ { * }$ according to (6.6). This suggests that the RM algorithm cannot find the true solution $w ^ { * }$ in this case. Therefore, the condition $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } = \infty$ is necessary to ensure convergency given an arbitrary initial guess.

What kinds of sequences satisfy $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } = \infty$ and $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } ^ { 2 } < \infty !$

One typical sequence is

$$
a _ {k} = \frac {1}{k}.
$$

On the one hand, it holds that

$$
\lim _ {n \to \infty} \left(\sum_ {k = 1} ^ {n} \frac {1}{k} - \ln n\right) = \kappa ,
$$

where $\kappa \approx 0 . 5 7 7$ is called the Euler-Mascheroni constant (or Euler’s constant) [28]. Since ln $n \to \infty$ as $n \to \infty$ , we have

$$
\sum_ {k = 1} ^ {\infty} \frac {1}{k} = \infty .
$$

In fact, $\begin{array} { r } { H _ { n } = \sum _ { k = 1 } ^ { n } \frac { 1 } { k } } \end{array}$ is called the harmonic number in number theory [29]. On the other hand, it holds that

$$
\sum_ {k = 1} ^ {\infty} \frac {1}{k ^ {2}} = \frac {\pi^ {2}}{6} <   \infty .
$$

Finding the value of $\scriptstyle \sum _ { k = 1 } ^ { \infty } { \frac { 1 } { k ^ { 2 } } }$ is known as the Basel problem [30].

In summary, the sequence $\{ a _ { k } = 1 / k \}$ satisfies the second condition in Theorem 6.1. Notably, a slight modification, such as $a _ { k } \ = \ 1 / ( k + 1 )$ or $a _ { k } ~ = ~ c _ { k } / k$ where $c _ { k }$ is bounded, also preserves this condition.

In the RM algorithm, $a _ { k }$ is often selected as a suficiently small constant in many applications. Although the second condition is not satisfied anymore in this case because $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } ^ { 2 } = \infty$ rather than $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } ^ { 2 } < \infty$ , the algorithm can still converge in a certain sense [24, Section 1.5]. In addition, $g ( x ) = x ^ { 3 } - 5$ in the example shown in Figure 6.3 does not satisfy the first condition, but the RM algorithm can still find the root if the initial guess is adequately (not arbitrarily) selected.

### 6.2.2 Application to mean estimation

We next apply the Robbins-Monro theorem to analyze the mean estimation problem, which has been discussed in Section 6.1. Recall that

$$
w _ {k + 1} = w _ {k} + \alpha_ {k} (x _ {k} - w _ {k})
$$

is the mean estimation algorithm in (6.4). When $\alpha _ { k } = 1 / k$ , we can obtain the analytical expression of $w _ { k + 1 }$ as $w _ { k + 1 } = 1 / k \textstyle \sum _ { i = 1 } ^ { k } x _ { i }$ . However, we would not be able to obtain an analytical expression when given general values of $\alpha _ { k }$ . In this case, the convergence analysis is nontrivial. We can show that the algorithm in this case is a special RM algorithm and hence its convergence naturally follows.

In particular, define a function as

$$
g (w) \doteq w - \mathbb {E} [ X ].
$$

The original problem is to obtain the value of $\mathbb { E } [ X ]$ . This problem is formulated as a root-finding problem to solve $g ( w ) = 0$ . Given a value of $w .$ , the noisy observation that we can obtain is $\tilde { g } \doteq w - x$ , where x is a sample of $X$ . Note that $\tilde { g }$ can be written as

$$
\begin{array}{r l} \tilde {g} (w, \eta) & = w - x \\ & = w - x + \mathbb {E} [ X ] - \mathbb {E} [ X ] \\ & = (w - \mathbb {E} [ X ]) + (\mathbb {E} [ X ] - x) \doteq g (w) + \eta , \end{array}
$$

where $\eta \doteq \mathbb { E } [ X ] - x$

The RM algorithm for solving this problem is

$$
w _ {k + 1} = w _ {k} - \alpha_ {k} \tilde {g} (w _ {k}, \eta_ {k}) = w _ {k} - \alpha_ {k} (w _ {k} - x _ {k}),
$$

which is exactly the algorithm in (6.4). As a result, it is guaranteed by Theorem 6.1 that $w _ { k }$ converges to $\mathbb { E } [ X ]$ almost surely if $\begin{array} { r } { \sum _ { k = 1 } ^ { \infty } \alpha _ { k } = \infty , \sum _ { k = 1 } ^ { \infty } \alpha _ { k } ^ { 2 } < \infty } \end{array}$ , and $\{ x _ { k } \}$ is i.i.d. It is worth mentioning that the convergence property does not rely on any assumption regarding the distribution of $X$

## 6.3 Dvoretzky’s convergence theorem

Until now, the convergence of the RM algorithm has not yet been proven. To do that, we next introduce Dvoretzky’s theorem [31, 32], which is a classic result in the field of stochastic approximation. This theorem can be used to analyze the convergence of the RM algorithm and many reinforcement learning algorithms.

This section is slightly mathematically intensive. Readers who are interested in the convergence analyses of stochastic algorithms are recommended to study this section. Otherwise, this section can be skipped.

Theorem 6.2 (Dvoretzky’s theorem). Consider a stochastic process

$$
\Delta_ {k + 1} = (1 - \alpha_ {k}) \Delta_ {k} + \beta_ {k} \eta_ {k},
$$

where $\{ \alpha _ { k } \} _ { k = 1 } ^ { \infty } , \{ \beta _ { k } \} _ { k = 1 } ^ { \infty } , \{ \eta _ { k } \} _ { k = 1 } ^ { \infty }$ are stochastic sequences. Here $\alpha _ { k } \geq 0 , \beta _ { k } \geq 0$ for all k. Then, $\Delta _ { k }$ converges to zero almost surely if the following conditions are satisfied:

(a) $\begin{array} { r } { \sum _ { k = 1 } ^ { \infty } \alpha _ { k } = \infty , \sum _ { k = 1 } ^ { \infty } \alpha _ { k } ^ { 2 } < \infty } \end{array}$ , and $\textstyle \sum _ { k = 1 } ^ { \infty } \beta _ { k } ^ { 2 } <$ uniformly almost surely;

(b) $\mathbb { E } [ \eta _ { k } | \mathcal { H } _ { k } ] = 0$ and $\mathbb { E } [ \eta _ { k } ^ { 2 } \vert \mathcal { H } _ { k } ] \le C$ almost surely;

where $\mathcal { H } _ { k } = \{ \Delta _ { k } , \Delta _ { k - 1 } , \ldots , \eta _ { k - 1 } , \ldots , \alpha _ { k - 1 } , \ldots , \beta _ { k - 1 } , \ldots \} .$

Before presenting the proof of this theorem, we first clarify some issues.

◇ In the RM algorithm, the coefficient sequence $\left\{ \alpha _ { k } \right\}$ is deterministic. However, Dvoretzky’s theorem allows $\{ \alpha _ { k } \} , \{ \beta _ { k } \}$ to be random variables that depend on $\mathcal { H } _ { k }$ . Thus, it is more useful in cases where $\alpha _ { k }$ or $\beta _ { k }$ is a function of $\Delta _ { k }$

◇ In the first condition, it is stated as “uniformly almost surely”. This is because $\alpha _ { k }$ and $\beta _ { k }$ may be random variables and hence the definition of their limits must be in the stochastic sense. In the second condition, it is also stated as “almost surely”. This is because $\mathcal { H } _ { k }$ is a sequence of random variables rather than specific values. As a result, $\mathbb { E } [ \eta _ { k } \vert \mathcal { H } _ { k } ]$ and $\mathbb { E } [ \eta _ { k } ^ { 2 } | \mathcal { H } _ { k } ]$ are random variables. The definition of the conditional expectation in this case is in the “almost sure” sense (Appendix B).

◇ The statement of Theorem 6.2 is slightly different from [32] in the sense that Theorem 6.2 does not require $\textstyle \sum _ { k = 1 } ^ { \infty } \beta _ { k } = \infty$ in the first condition. When $\textstyle \sum _ { k = 1 } ^ { \infty } \beta _ { k } < \infty$ especially in the extreme case where $\beta _ { k } = 0$ for all $k ,$ , the sequence can still converge.

### 6.3.1 Proof of Dvoretzky’s theorem

The original proof of Dvoretzky’s theorem was given in 1956 [31]. There are also other proofs. We next present a proof based on quasimartingales. With the convergence results of quasimartingales, the proof of Dvoretzky’s theorem is straightforward. More information about quasimartingales can be found in Appendix C.

Proof of Dvoretzky’s theorem. Let $h _ { k } \doteq \Delta _ { k } ^ { 2 }$ . Then,

$$
\begin{array}{r l} & h _ {k + 1} - h _ {k} = \Delta_ {k + 1} ^ {2} - \Delta_ {k} ^ {2} \\ & \qquad = (\Delta_ {k + 1} - \Delta_ {k}) (\Delta_ {k + 1} + \Delta_ {k}) \\ & \qquad = (- \alpha_ {k} \Delta_ {k} + \beta_ {k} \eta_ {k}) [ (2 - \alpha_ {k}) \Delta_ {k} + \beta_ {k} \eta_ {k} ] \\ & \qquad = - \alpha_ {k} (2 - \alpha_ {k}) \Delta_ {k} ^ {2} + \beta_ {k} ^ {2} \eta_ {k} ^ {2} + 2 (1 - \alpha_ {k}) \beta_ {k} \eta_ {k} \Delta_ {k}. \end{array}
$$

Taking expectations on both sides of the above equation yields

$$
\mathbb {E} \left[ h _ {k + 1} - h _ {k} \mid \mathcal {H} _ {k} \right] = \mathbb {E} \left[ - \alpha_ {k} (2 - \alpha_ {k}) \Delta_ {k} ^ {2} \mid \mathcal {H} _ {k} \right] + \mathbb {E} \left[ \beta_ {k} ^ {2} \eta_ {k} ^ {2} \mid \mathcal {H} _ {k} \right] + \mathbb {E} \left[ 2 (1 - \alpha_ {k}) \beta_ {k} \eta_ {k} \Delta_ {k} \mid \mathcal {H} _ {k} \right].\tag{6.7}
$$

First, since $\Delta _ { k }$ is included and hence determined by $\mathcal { H } _ { k }$ , it can be taken out from the expectation (see property (e) in Lemma B.1). Second, consider the simple case where $\alpha _ { k } , \beta _ { k }$ is determined by $\mathcal { H } _ { k }$ This case is valid when, for example, $\left\{ \alpha _ { k } \right\}$ and $\{ \beta _ { k } \}$ are functions of $\Delta _ { k }$ or deterministic sequences. Then, they can also be taken out of the expectation. Therefore, (6.7) becomes

$$
\mathbb {E} [ h _ {k + 1} - h _ {k} | \mathcal {H} _ {k} ] = - \alpha_ {k} (2 - \alpha_ {k}) \Delta_ {k} ^ {2} + \beta_ {k} ^ {2} \mathbb {E} [ \eta_ {k} ^ {2} | \mathcal {H} _ {k} ] + 2 (1 - \alpha_ {k}) \beta_ {k} \Delta_ {k} \mathbb {E} [ \eta_ {k} | \mathcal {H} _ {k} ].\tag{6.8}
$$

For the first term, since $\textstyle \sum _ { k = 1 } ^ { \infty } \alpha _ { k } ^ { 2 } < \infty$ implies $\alpha _ { k }  0$ almost surely, there exists a finite n such that $\alpha _ { k } \leq 1$ almost surely for all $k \geq n$ Without loss of generality, we next merely consider the case of $\alpha _ { k } \leq 1$ Then, $- \alpha _ { k } ( 2 - \alpha _ { k } ) \Delta _ { k } ^ { 2 } \le 0$ . For the second term, we have $\beta _ { k } ^ { 2 } \mathbb { E } [ \eta _ { k } ^ { 2 } | \mathcal { H } _ { k } ] \le \beta _ { k } ^ { 2 } C$ as assumed. The third term equals zero because $\mathbb { E } [ \eta _ { k } | \mathcal { H } _ { k } ] = 0$ as assumed. Therefore, (6.8) becomes

$$
\mathbb {E} [ h _ {k + 1} - h _ {k} | \mathcal {H} _ {k} ] = - \alpha_ {k} (2 - \alpha_ {k}) \Delta_ {k} ^ {2} + \beta_ {k} ^ {2} \mathbb {E} [ \eta_ {k} ^ {2} | \mathcal {H} _ {k} ] \leq \beta_ {k} ^ {2} C,\tag{6.9}
$$

and hence

$$
\sum_ {k = 1} ^ {\infty} \mathbb {E} [ h _ {k + 1} - h _ {k} | \mathcal {H} _ {k} ] \leq \sum_ {k = 1} ^ {\infty} \beta_ {k} ^ {2} C <   \infty .
$$

The last inequality is due to the condition $\textstyle \sum _ { k = 1 } ^ { \infty } \beta _ { k } ^ { 2 } \ < \ \infty$ Then, based on the quasimartingale convergence theorem in Appendix C, we conclude that $h _ { k }$ converges almost surely.

We next determine what value $\Delta _ { k }$ converges to. It follows from (6.9) that

$$
\sum_ {k = 1} ^ {\infty} \alpha_ {k} (2 - \alpha_ {k}) \Delta_ {k} ^ {2} = \sum_ {k = 1} ^ {\infty} \beta_ {k} ^ {2} \mathbb {E} [ \eta_ {k} ^ {2} | \mathcal {H} _ {k} ] - \sum_ {k = 1} ^ {\infty} \mathbb {E} [ h _ {k + 1} - h _ {k} | \mathcal {H} _ {k} ].
$$

The first term on the right-hand side is bounded as assumed. The second term is also bounded because $h _ { k }$ converges and hence $h _ { k + 1 } \ : - \ : h _ { k }$ is summable. Thus, $\begin{array} { r } { \sum _ { k = 1 } ^ { \infty } \alpha _ { k } ( 2 - \alpha _ { k } ) \Delta _ { k } ^ { 2 } } \end{array}$ on the left-hand side is also bounded. Since we consider the case of $\alpha _ { k } \leq 1$ , we have

$$
\infty > \sum_ {k = 1} ^ {\infty} \alpha_ {k} (2 - \alpha_ {k}) \Delta_ {k} ^ {2} \geq \sum_ {k = 1} ^ {\infty} \alpha_ {k} \Delta_ {k} ^ {2} \geq 0.
$$

Therefore, $\scriptstyle \sum _ { k = 1 } ^ { \infty } \alpha _ { k } \Delta _ { k } ^ { 2 }$ is bounded. Since $\textstyle \sum _ { k = 1 } ^ { \infty } \alpha _ { k } = \infty$ we must have $\Delta _ { k } \  \ 0$ almost surely.

### 6.3.2 Application to mean estimation

While the mean estimation algorithm, $w _ { k + 1 } = w _ { k } + \alpha _ { k } ( x _ { k } - w _ { k } )$ , has been analyzed using the RM theorem, we next show that its convergence can also be directly proven by Dvoretzky’s theorem.

Proof. Let $\boldsymbol { w ^ { * } } = \mathbb { E } [ \boldsymbol { X } ]$ . The mean estimation algorithm $w _ { k + 1 } = w _ { k } + \alpha _ { k } \big ( x _ { k } - w _ { k } \big )$ can be rewritten as

$$
w _ {k + 1} - w ^ {*} = w _ {k} - w ^ {*} + \alpha_ {k} (x _ {k} - w ^ {*} + w ^ {*} - w _ {k}).
$$

Let $\Delta \doteq w - w ^ { * }$ . Then, we have

$$
\begin{array}{c} \Delta_ {k + 1} = \Delta_ {k} + \alpha_ {k} (x _ {k} - w ^ {*} - \Delta_ {k}) \\ = (1 - \alpha_ {k}) \Delta_ {k} + \alpha_ {k} \underbrace {(x _ {k} - w ^ {*})} _ {\eta_ {k}}. \end{array}
$$

Since $\{ x _ { k } \}$ is i.i.d., we have $\mathbb { E } [ x _ { k } | \mathcal { H } _ { k } ] = \mathbb { E } [ x _ { k } ] = w ^ { * }$ . As a result, $\mathbb { E } [ \eta _ { k } | \mathcal { H } _ { k } ] = \mathbb { E } [ x _ { k } -$ $w ^ { * } | \mathcal { H } _ { k } ] = 0$ and $\mathbb { E } [ \eta _ { k } ^ { 2 } | \mathcal { H } _ { k } ] = \mathbb { E } [ x _ { k } ^ { 2 } | \mathcal { H } _ { k } ] - ( w ^ { * } ) ^ { 2 } = \mathbb { E } [ x _ { k } ^ { 2 } ] - ( w ^ { * } ) ^ { 2 }$ are bounded if the variance of $x _ { k }$ is finite. Following Dvoretzky’s theorem, we conclude that $\Delta _ { k }$ converges to zero and hence $w _ { k }$ converges to $\boldsymbol { w ^ { * } } = \mathbb { E } [ \boldsymbol { X } ]$ almost surely. □

### 6.3.3 Application to the Robbins-Monro theorem

We are now ready to prove the Robbins-Monro theorem using Dvoretzky’s theorem.

Proof of the Robbins-Monro theorem. The RM algorithm aims to find the root of $g ( w ) = 0$ . Suppose that the root is $w ^ { * }$ such that $g ( w ^ { * } ) = 0$ . The RM algorithm is

$$
\begin{array}{r} w _ {k + 1} = w _ {k} - a _ {k} \tilde {g} (w _ {k}, \eta_ {k}) \\ = w _ {k} - a _ {k} [ g (w _ {k}) + \eta_ {k} ]. \end{array}
$$

Then, we have

$$
w _ {k + 1} - w ^ {*} = w _ {k} - w ^ {*} - a _ {k} [ g (w _ {k}) - g (w ^ {*}) + \eta_ {k} ].
$$

Due to the mean value theorem [7, 8], we have $g ( w _ { k } ) - g ( w ^ { * } ) = \nabla _ { w } g ( w _ { k } ^ { \prime } ) ( w _ { k } - w ^ { * } )$ where $w _ { k } ^ { \prime } \in [ w _ { k } , w ^ { * } ]$ . Let $\Delta _ { k } \doteq w _ { k } - w ^ { * }$ . The above equation becomes

$$
\begin{array}{r l} & {\Delta_ {k + 1} = \Delta_ {k} - a _ {k} [ \nabla_ {w} g (w _ {k} ^ {\prime}) (w _ {k} - w ^ {*}) + \eta_ {k} ]} \\ & {\quad = \Delta_ {k} - a _ {k} \nabla_ {w} g (w _ {k} ^ {\prime}) \Delta_ {k} + a _ {k} (- \eta_ {k})} \\ & {\quad = [ 1 - \underbrace {a _ {k} \nabla_ {w} g (w _ {k} ^ {\prime})} _ {\alpha_ {k}} ] \Delta_ {k} + a _ {k} (- \eta_ {k}).} \end{array}
$$

Note that $\nabla _ { w } g ( w )$ is bounded as $0 < c _ { 1 } \leq \nabla _ { w } g ( w ) \leq c _ { 2 }$ as assumed. Since $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } =$ and $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } ^ { 2 } < \infty$ as assumed, we know $\textstyle \sum _ { k = 1 } ^ { \infty } \alpha _ { k } = \infty$ and $\textstyle \sum _ { k = 1 } ^ { \infty } \alpha _ { k } ^ { 2 } < \infty$ Thus, all the conditions in Dvoretzky’s theorem are satisfied and hence $\Delta _ { k }$ converges to zero almost surely. □

The proof of the RM theorem demonstrates the power of Dvoretzky’s theorem. In particular, $\alpha _ { k }$ in the proof is a stochastic sequence depending on $w _ { k }$ rather than a deterministic sequence. In this case, Dvoretzky’s theorem is still applicable.

### 6.3.4 An extension of Dvoretzky’s theorem

We next extend Dvoretzky’s theorem to a more general theorem that can handle multiple variables. This general theorem, proposed by [32], can be used to analyze the convergence of stochastic iterative algorithms such as Q-learning.

Theorem 6.3. Consider a finite set  of real numbers. For the stochastic process

$$
\Delta_ {k + 1} (s) = (1 - \alpha_ {k} (s)) \Delta_ {k} (s) + \beta_ {k} (s) \eta_ {k} (s),
$$

it holds that $\Delta _ { k } ( s )$ converges to zero almost surely for every $s \in S$ if the following conditions are satisfied for $s \in S$ :

(a) $\begin{array} { r } { \sum _ { k } \alpha _ { k } ( s ) = \infty , \sum _ { k } \alpha _ { k } ^ { 2 } ( s ) < \infty , \sum _ { k } \beta _ { k } ^ { 2 } ( s ) < \infty , } \end{array}$ , and $\mathbb { E } [ \beta _ { k } ( s ) | \mathcal { H } _ { k } ] \le $ $\mathbb { E } [ \alpha _ { k } ( s ) | \mathcal { H } _ { k } ]$ uniformly almost surely;

(b) $\| \mathbb { E } [ \eta _ { k } ( s ) \vert \mathcal { H } _ { k } ] \| _ { \infty } \leq \gamma \| \Delta _ { k } \| _ { \infty } , \ w h e r e \ \gamma \in ( 0 , 1 ) .$ ;

(c) $\mathrm { v a r } [ \eta _ { k } ( s ) | \mathcal { H } _ { k } ] \leq C ( 1 + \| \Delta _ { k } ( s ) \| _ { \infty } ) ^ { 2 }$ , where C is a constant.

Here, $\mathcal { H } _ { k } = \{ \Delta _ { k } , \Delta _ { k - 1 } , \ldots , \eta _ { k - 1 } , \ldots , \alpha _ { k - 1 } , \ldots , \beta _ { k - 1 } , \ldots \}$ represents the historical information. The term $\| \cdot \| _ { \infty }$ refers to the maximum norm.

Proof. As an extension, this theorem can be proven based on Dvoretzky’s theorem. Details can be found in [32] and are omitted here. □

Some remarks about this theorem are given below.

◇ We first clarify some notations in the theorem. The variable s can be viewed as an index. In the context of reinforcement learning, it indicates a state or a state-action pair. The maximum norm $\| \cdot \| _ { \infty }$ is defined over a set. It is similar but different from the $L ^ { \infty }$ norm of vectors. In particular, $\| \mathbb { E } [ \eta _ { k } ( s ) \vert \mathcal { H } _ { k } ] \| _ { \infty } \doteq$ $\mathrm { m a x } _ { s \in \mathcal { S } } | \mathbb { E } [ \eta _ { k } ( s ) | \mathcal { H } _ { k } ] |$ and $\lVert \Delta _ { k } ( s ) \rVert _ { \infty } \doteq \operatorname* { m a x } _ { s \in \mathcal { S } } \left| \Delta _ { k } ( s ) \right|$

◇ This theorem is more general than Dvoretzky’s theorem. First, it can handle the case of multiple variables due to the maximum norm operations. This is important for a reinforcement learning problem where there are multiple states. Second, while Dvoretzky’s theorem requires $\mathbb { E } [ \eta _ { k } ( s ) | \mathcal { H } _ { k } ] = 0$ and $\mathrm { v a r } [ \eta _ { k } ( s ) | \mathcal { H } _ { k } ] \le C$ , this theorem only requires that the expectation and variance are bounded by the error $\Delta _ { k }$

It should be noted that the convergence of $\Delta ( s )$ for all $s \in S$ requires that the conditions are valid for every $s \in S$ Therefore, when applying this theorem to prove the convergence of reinforcement learning algorithms, we need to show that the conditions are valid for every state (or state-action pair).

## 6.4 Stochastic gradient descent

This section introduces stochastic gradient descent (SGD) algorithms, which are widely used in the field of machine learning. We will see that SGD is a special RM algorithm, and the mean estimation algorithm is a special SGD algorithm.

Consider the following optimization problem:

$$
\min _ {w} J (w) = \mathbb {E} [ f (w, X) ],\tag{6.10}
$$

where w is the parameter to be optimized, and X is a random variable. The expectation is calculated with respect to X. Here, w and X can be either scalars or vectors. The function $f ( \cdot )$ is a scalar.

A straightforward method for solving (6.10) is gradient descent. In particular, the gradient of $\mathbb { E } [ f ( w , X ) ]$ is $\nabla _ { w } \mathbb { E } [ f ( w , X ) ] = \mathbb { E } [ \nabla _ { w } f ( w , X ) ]$ . Then, the gradient descent algorithm is

$$
w _ {k + 1} = w _ {k} - \alpha_ {k} \nabla_ {w} J (w _ {k}) = w _ {k} - \alpha_ {k} \mathbb {E} [ \nabla_ {w} f (w _ {k}, X) ].\tag{6.11}
$$

This gradient descent algorithm can find the optimal solution $w ^ { * }$ under some mild conditions such as the convexity of $f .$ Preliminaries about gradient descent algorithms can be found in Appendix D.

The gradient descent algorithm requires the expected value $\mathbb { E } [ \nabla _ { w } f ( w _ { k } , X ) ]$ . One way to obtain the expected value is based on the probability distribution of X. The distribution is, however, often unknown in practice. Another way is to collect a large number of i.i.d. samples $\{ x _ { i } \} _ { i = 1 } ^ { n }$ of X so that the expected value can be approximated as

$$
\mathbb {E} [ \nabla_ {w} f (w _ {k}, X) ] \approx \frac {1}{n} \sum_ {i = 1} ^ {n} \nabla_ {w} f (w _ {k}, x _ {i}).
$$

Then, (6.11) becomes

$$
w _ {k + 1} = w _ {k} - \frac {\alpha_ {k}}{n} \sum_ {i = 1} ^ {n} \nabla_ {w} f (w _ {k}, x _ {i}).\tag{6.12}
$$

One problem of the algorithm in (6.12) is that it requires all the samples in each iteration. In practice, if the samples are collected one by one, then it is favorable to update w every time a sample is collected. To that end, we can use the following algorithm:

$$
w _ {k + 1} = w _ {k} - \alpha_ {k} \nabla_ {w} f (w _ {k}, x _ {k}),\tag{6.13}
$$

where $x _ { k }$ is the sample collected at time step k. This is the well-known stochastic gradient descent algorithm. This algorithm is called “stochastic” because it relies on stochastic samples $\{ x _ { k } \}$

Compared to the gradient descent algorithm in (6.11), SGD replaces the true gradient $\mathbb { E } [ \nabla _ { w } f ( w , X ) ]$ with the stochastic gradient $\nabla _ { w } f ( w _ { k } , x _ { k } )$ . Since $\nabla _ { w } f ( w _ { k } , x _ { k } ) \neq$ $\mathbb { E } [ \nabla _ { w } f ( w , X ) ]$ , can such a replacement still ensure $w _ { k } \to w ^ { * }$ as $k  \infty ?$ The answer is yes. We next present an intuitive explanation and postpone the rigorous proof of the convergence to Section 6.4.5.

In particular, since

$$
\begin{array}{r l} & {\nabla_ {w} f (w _ {k}, x _ {k}) = \mathbb {E} [ \nabla_ {w} f (w _ {k}, X) ] + \Big (\nabla_ {w} f (w _ {k}, x _ {k}) - \mathbb {E} [ \nabla_ {w} f (w _ {k}, X) ] \Big)} \\ & {\qquad \doteq \mathbb {E} [ \nabla_ {w} f (w _ {k}, X) ] + \eta_ {k},} \end{array}
$$

the SGD algorithm in (6.13) can be rewritten as

$$
w _ {k + 1} = w _ {k} - \alpha_ {k} \mathbb {E} [ \nabla_ {w} f (w _ {k}, X) ] - \alpha_ {k} \eta_ {k}.
$$

Therefore, the SGD algorithm is the same as the regular gradient descent algorithm except that it has a perturbation term $\alpha _ { k } \eta _ { k }$ . Since $\{ x _ { k } \}$ is i.i.d., we have $\mathbb { E } _ { x _ { k } } [ \nabla _ { w } f ( w _ { k } , x _ { k } ) ] =$ $\mathbb { E } _ { X } [ \nabla _ { w } f ( w _ { k } , X ) ]$ ]. As a result,

$$
\mathbb {E} [ \eta_ {k} ] = \mathbb {E} \Big [ \nabla_ {w} f (w _ {k}, x _ {k}) - \mathbb {E} [ \nabla_ {w} f (w _ {k}, X) ] \Big ] = \mathbb {E} _ {x _ {k}} [ \nabla_ {w} f (w _ {k}, x _ {k}) ] - \mathbb {E} _ {X} [ \nabla_ {w} f (w _ {k}, X) ] = 0.
$$

Therefore, the perturbation term $\eta _ { k }$ has a zero mean, which intuitively suggests that it may not jeopardize the convergence property. A rigorous proof of the convergence of

SGD is given in Section 6.4.5.

### 6.4.1 Application to mean estimation

We next apply SGD to analyze the mean estimation problem and show that the mean estimation algorithm in (6.4) is a special SGD algorithm. To that end, we formulate the mean estimation problem as an optimization problem:

$$
\min _ {w} J (w) = \mathbb {E} \left[ \frac {1}{2} \| w - X \| ^ {2} \right] \doteq \mathbb {E} [ f (w, X) ],\tag{6.14}
$$

where $f ( w , X ) = \| w - X \| ^ { 2 } / 2$ and the gradient is $\nabla _ { w } f ( w , X ) = w - X$ . It can be verified that the optimal solution is $\boldsymbol { w ^ { * } } = \mathbb { E } [ \boldsymbol { X } ]$ by solving $\nabla _ { w } J ( w ) = 0$ . Therefore, this optimization problem is equivalent to the mean estimation problem.

$\diamond$ The gradient descent algorithm for solving (6.14) is

$$
\begin{array}{r l} & w _ {k + 1} = w _ {k} - \alpha_ {k} \nabla_ {w} J (w _ {k}) \\ & \qquad = w _ {k} - \alpha_ {k} \mathbb {E} [ \nabla_ {w} f (w _ {k}, X) ] \\ & \qquad = w _ {k} - \alpha_ {k} \mathbb {E} [ w _ {k} - X ]. \end{array}
$$

This gradient descent algorithm is not applicable since $\mathbb { E } [ w _ { k } - X ]$ or $\mathbb { E } [ X ]$ on the right-hand side is unknown (in fact, it is what we need to solve).

The SGD algorithm for solving (6.14) is

$$
w _ {k + 1} = w _ {k} - \alpha_ {k} \nabla_ {w} f (w _ {k}, x _ {k}) = w _ {k} - \alpha_ {k} (w _ {k} - x _ {k}),
$$

where $x _ { k }$ is a sample obtained at time step k. Notably, this SGD algorithm is the same as the iterative mean estimation algorithm in (6.4). Therefore, (6.4) is an SGD algorithm designed specifically for solving the mean estimation problem.

### 6.4.2 Convergence pattern of SGD

The idea of the SGD algorithm is to replace the true gradient with a stochastic gradient. However, since the stochastic gradient is random, one may ask whether the convergence speed of SGD is slow or random. Fortunately, SGD can converge efficiently in general. An interesting convergence pattern is that it behaves similarly to the regular gradient descent algorithm when the estimate $w _ { k }$ is far from the optimal solution $w ^ { * }$ . Only when $w _ { k }$ is close to $w ^ { * }$ , does the convergence of SGD exhibit more randomness.

An analysis of this pattern and an illustrative example are given below.

Analysis: The relative error between the stochastic and true gradients is

$$
\delta_ {k} \doteq \frac {| \nabla_ {w} f (w _ {k} , x _ {k}) - \mathbb {E} [ \nabla_ {w} f (w _ {k} , X) ] |}{| \mathbb {E} [ \nabla_ {w} f (w _ {k} , X) ] |}.
$$

For the sake of simplicity, we consider the case where w and $\nabla _ { w } f ( w , x )$ are both scalars. Since $w ^ { * }$ is the optimal solution, it holds that $\mathbb { E } [ \nabla _ { w } f ( w ^ { * } , X ) ] = 0$ . Then, the relative error can be rewritten as

$$
\delta_ {k} = \frac {| \nabla_ {w} f (w _ {k} , x _ {k}) - \mathbb {E} [ \nabla_ {w} f (w _ {k} , X) ] |}{| \mathbb {E} [ \nabla_ {w} f (w _ {k} , X) ] - \mathbb {E} [ \nabla_ {w} f (w ^ {*} , X) ] |} = \frac {| \nabla_ {w} f (w _ {k} , x _ {k}) - \mathbb {E} [ \nabla_ {w} f (w _ {k} , X) ] |}{| \mathbb {E} [ \nabla_ {w} ^ {2} f (\tilde {w} _ {k} , X) (w _ {k} - w ^ {*}) ] |},\tag{6.15}
$$

where the last equality is due to the mean value theorem [7, 8] and $\tilde { w } _ { k } \in [ w _ { k } , w ^ { * } ]$ Suppose that f is strictly convex such that $\nabla _ { w } ^ { 2 } f \ge c > 0$ for all $w , X$ . Then, the denominator in (6.15) becomes

$$
\begin{array}{r l} & {\left| \mathbb {E} [ \nabla_ {w} ^ {2} f (\tilde {w} _ {k}, X) (w _ {k} - w ^ {*}) ] \right| = \left| \mathbb {E} [ \nabla_ {w} ^ {2} f (\tilde {w} _ {k}, X) ] \right| \big | (w _ {k} - w ^ {*}) \big |} \\ & {\qquad \geq c | w _ {k} - w ^ {*} |.} \end{array}
$$

Substituting the above inequality into (6.15) yields

$$
\delta_ {k} \leq \frac {\big | \overbrace {\nabla_ {w} f (w _ {k} , x _ {k})} ^ {\text { stochastic gradient }} - \overbrace {\mathbb {E} [ \nabla_ {w} f (w _ {k} , X) ]} ^ {\text { true gradient }} \big |}{\underbrace {c | w _ {k} - w ^ {*} |} _ {\text { distance   to   the   optimal   solution }}}.
$$

The above inequality suggests an interesting convergence pattern of SGD: the relative error $\delta _ { k }$ is inversely proportional to $| w _ { k } - w ^ { * } |$ . As a result, when $| w _ { k } - w ^ { * } |$ is large, $\delta _ { k }$ is small. In this case, the SGD algorithm behaves like the gradient descent algorithm and hence $w _ { k }$ quickly converges to $w ^ { * }$ . When $w _ { k }$ is close to $w ^ { * }$ , the relative error $\delta _ { k }$ may be large, and the convergence exhibits more randomness.

Example: A good example for demonstrating the above analysis is the mean estimation problem. Consider the mean estimation problem in (6.14). When w and X are both scalar, we have $f ( w , X ) = | w - X | ^ { 2 } / 2$ and hence

$$
\begin{array}{c} \nabla_ {w} f (w, x _ {k}) = w - x _ {k}, \\ \mathbb {E} [ \nabla_ {w} f (w, x _ {k}) ] = w - \mathbb {E} [ X ] = w - w ^ {*}. \end{array}
$$

Thus, the relative error is

$$
\delta_ {k} = \frac {| \nabla_ {w} f (w _ {k} , x _ {k}) - \mathbb {E} [ \nabla_ {w} f (w _ {k} , X) ] |}{| \mathbb {E} [ \nabla_ {w} f (w _ {k} , X) ] |} = \frac {| (w _ {k} - x _ {k}) - (w _ {k} - \mathbb {E} [ X ]) |}{| w _ {k} - w ^ {*} |} = \frac {| \mathbb {E} [ X ] - x _ {k} |}{| w _ {k} - w ^ {*} |}.
$$

The expression of the relative error clearly shows that $\delta _ { k }$ is inversely proportional to $| w _ { k } - w ^ { * } |$ . As a result, when $w _ { k }$ is far from $w ^ { * }$ , the relative error is small, and SGD behaves like gradient descent. In addition, since $\delta _ { k }$ is proportional to $| \mathbb { E } [ X ] - x _ { k } |$ , the mean of $\delta _ { k }$ is proportional to the variance of $X$

![](b6e9bf86bfa3275b2ce31c4c733153d88102a1ff5b716910207c670cc023eb29.jpg)

![](0477c124a4eb80e2ca7e40341c34f6626096d04e318b2f2a34ac9d46090cf97e.jpg)

*Figure 6.5: An example for demonstrating stochastic and mini-batch gradient descent algorithms. The distribution of $X \in \mathbb { R } ^ { 2 }$ is uniform in the square area centered at the origin with a side length as 20. The mean is $\mathbb { E } [ X ] = 0$ . The mean estimation is based on 100 i.i.d. samples.*

The simulation results are shown in Figure 6.5. Here, $X \in \mathbb { R } ^ { 2 }$ represents a random position in the plane. Its distribution is uniform in the square area centered at the origin and $\mathbb { E } [ X ] = 0$ . The mean estimation is based on 100 i.i.d. samples. Although the initial guess of the mean is far away from the true value, it can be seen that the SGD estimate quickly approaches the neighborhood of the origin. When the estimate is close to the origin, the convergence process exhibits certain randomness.

### 6.4.3 A deterministic formulation of SGD

The formulation of SGD in (6.13) involves random variables. One may often encounter a deterministic formulation of SGD without involving any random variables.

In particular, consider a set of real numbers $\{ x _ { i } \} _ { i = 1 } ^ { n }$ , where $x _ { i }$ does not have to be a sample of any random variable. The optimization problem to be solved is to minimize the average:

$$
\min _ {w} J (w) = \frac {1}{n} \sum_ {i = 1} ^ {n} f (w, x _ {i}),
$$

where $f ( w , x _ { i } )$ is a parameterized function, and w is the parameter to be optimized. The gradient descent algorithm for solving this problem is

$$
w _ {k + 1} = w _ {k} - \alpha_ {k} \nabla_ {w} J (w _ {k}) = w _ {k} - \alpha_ {k} \frac {1}{n} \sum_ {i = 1} ^ {n} \nabla_ {w} f (w _ {k}, x _ {i}).
$$

Suppose that the set $\{ x _ { i } \} _ { i = 1 } ^ { n }$ is large and we can only fetch a single number each time.

In this case, it is favorable to update $w _ { k }$ in an incremental manner:

$$
w _ {k + 1} = w _ {k} - \alpha_ {k} \nabla_ {w} f (w _ {k}, x _ {k}).\tag{6.16}
$$

It must be noted that $x _ { k }$ here is the number fetched at time step $k$ instead of the kth element in the set $\{ x _ { i } \} _ { i = 1 } ^ { n }$

The algorithm in (6.16) is very similar to SGD, but its problem formulation is subtly different because it does not involve any random variables or expected values. Then, many questions arise. For example, is this algorithm SGD? How should we use the finite set of numbers $\{ x _ { i } \} _ { i = 1 } ^ { n } ?$ Should we sort these numbers in a certain order and then use them one by one, or should we randomly sample a number from the set?

A quick answer to the above questions is that, although no random variables are involved in the above formulation, we can convert the deterministic formulation to the stochastic formulation by introducing a random variable. In particular, let X be a random variable defined on the set $\{ x _ { i } \} _ { i = 1 } ^ { n }$ . Suppose that its probability distribution is uniform such that $p ( X = x _ { i } ) = 1 / n$ . Then, the deterministic optimization problem becomes a stochastic one:

$$
\min _ {w} J (w) = \frac {1}{n} \sum_ {i = 1} ^ {n} f (w, x _ {i}) = \mathbb {E} [ f (w, X) ].
$$

The last equality in the above equation is strict instead of approximate. Therefore, the algorithm in (6.16) is SGD, and the estimate converges if $x _ { k }$ is uniformly and independently sampled from $\{ x _ { i } \} _ { i = 1 } ^ { n }$ . Note that $x _ { k }$ may repeatedly take the same number in $\{ x _ { i } \} _ { i = 1 } ^ { n }$ since it is sampled randomly.

### 6.4.4 BGD, SGD, and mini-batch GD

While SGD uses a single sample in every iteration, we next introduce mini-batch gradient descent (MBGD), which uses a few more samples in every iteration. When all samples are used in every iteration, the algorithm is called batch gradient descent (BGD).

In particular, suppose that we would like to find the optimal solution that can minimize $J ( w ) = \mathbb { E } [ f ( w , X ) ]$ given a set of random samples $\{ x _ { i } \} _ { i = 1 } ^ { n }$ of $X$ . The BGD, SGD, and MBGD algorithms for solving this problem are, respectively,

$$
\begin{array}{l l} w _ {k + 1} = w _ {k} - \alpha_ {k} \frac {1}{n} \sum_ {i = 1} ^ {n} \nabla_ {w} f (w _ {k}, x _ {i}), & \text {(BGD)} \\ w _ {k + 1} = w _ {k} - \alpha_ {k} \frac {1}{m} \sum_ {j \in \mathcal {I} _ {k}} \nabla_ {w} f (w _ {k}, x _ {j}), & \text {(MBGD)} \\ w _ {k + 1} = w _ {k} - \alpha_ {k} \nabla_ {w} f (w _ {k}, x _ {k}). & \text {(SGD)} \end{array}
$$

In the BGD algorithm, all the samples are used in every iteration. When n is large, $\textstyle ( 1 / n ) \sum _ { i = 1 } ^ { n } \nabla _ { w } f ( w _ { k } , x _ { i } )$ is close to the true gradient $\mathbb { E } [ \nabla _ { w } f ( w _ { k } , X ) ]$ . In the MBGD algorithm, $\mathcal { T } _ { k }$ is a subset of $\{ 1 , \ldots , n \}$ obtained at time k. The size of the set is $| \mathcal { T } _ { k } | = m$ The samples in $\mathcal { T } _ { k }$ are also assumed to be i.i.d. In the SGD algorithm, $x _ { k }$ is randomly sampled from $\{ x _ { i } \} _ { i = 1 } ^ { n }$ at time k.

MBGD can be viewed as an intermediate version between SGD and BGD. Compared to SGD, MBGD has less randomness because it uses more samples instead of just one as in SGD. Compared to BGD, MBGD does not require using all the samples in every iteration, making it more flexible. If $m = 1$ , then MBGD becomes SGD. However, if $m = n$ , MBGD may not become BGD. This is because MBGD uses n randomly fetched samples, whereas BGD uses all n numbers. These n randomly fetched samples may contain the same number multiple times and hence may not cover all n numbers in $\{ x _ { i } \} _ { i = 1 } ^ { n }$

The convergence speed of MBGD is faster than that of SGD in general. This is because SGD uses $\nabla _ { w } f ( w _ { k } , x _ { k } )$ to approximate the true gradient, whereas MBGD uses $\begin{array} { r } { ( 1 / m ) \sum _ { j \in \mathbb { Z } _ { k } } \nabla _ { w } f ( w _ { k } , x _ { j } ) } \end{array}$ , which is closer to the true gradient because the randomness is averaged out. The convergence of the MBGD algorithm can be proven similarly to the SGD case.

A good example for demonstrating the above analysis is the mean estimation problem. In particular, given some numbers $\{ x _ { i } \} _ { i = 1 } ^ { n }$ , our goal is to calculate the mean $\textstyle { \bar { x } } = \sum _ { i = 1 } ^ { n } x _ { i } / n$ . This problem can be equivalently stated as the following optimization problem:

$$
\min _ {w} J (w) = \frac {1}{2 n} \sum_ {i = 1} ^ {n} \| w - x _ {i} \| ^ {2},
$$

whose optimal solution is $w ^ { * } = \bar { x }$ . The three algorithms for solving this problem are, respectively,

$$
\begin{array}{l} w _ {k + 1} = w _ {k} - \alpha_ {k} \frac {1}{n} \sum_ {i = 1} ^ {n} (w _ {k} - x _ {i}) = w _ {k} - \alpha_ {k} (w _ {k} - \bar {x}), \\ w _ {k + 1} = w _ {k} - \alpha_ {k} \frac {1}{m} \sum_ {j \in \mathcal {I} _ {k}} (w _ {k} - x _ {j}) = w _ {k} - \alpha_ {k} \left(w _ {k} - \bar {x} _ {k} ^ {(m)}\right), \\ w _ {k + 1} = w _ {k} - \alpha_ {k} (w _ {k} - x _ {k}), \qquad (\text {SGD}) \end{array}\tag{BGD}
$$

(MBGD) where $\begin{array} { r } { \bar { x } _ { k } ^ { ( m ) } = \sum _ { j \in \mathcal { T } _ { k } } { x _ { j } / m } } \end{array}$ . Furthermore, if $\alpha _ { k } = 1 / k$ , the above equations can be solved as follows:

$$
w _ {k + 1} = \frac {1}{k} \sum_ {j = 1} ^ {k} \bar {x} = \bar {x},\tag{BGD}
$$

$$
w _ {k + 1} = \frac {1}{k} \sum_ {j = 1} ^ {k} \bar {x} _ {j} ^ {(m)},\tag{MBGD}
$$

$$
w _ {k + 1} = \frac {1}{k} \sum_ {j = 1} ^ {k} x _ {j}. \qquad (\mathrm{SGD})
$$

The derivation of the above equations is similar to that of (6.3) and is omitted here. It can be seen that the estimate given by BGD at each step is exactly the optimal solution $w ^ { * } = \bar { x }$ . MBGD converges to the mean faster than SGD because $\bar { x } _ { k } ^ { ( m ) }$ is already an average.

A simulation example is given in Figure 6.5 to demonstrate the convergence of MBGD. Let $\alpha _ { k } = 1 / k$ . It is shown that all MBGD algorithms with different mini-batch sizes can converge to the mean. The case with $m = 5 0$ converges the fastest, while SGD with $m = 1$ is the slowest. This is consistent with the above analysis. Nevertheless, the convergence rate of SGD is still fast, especially when $w _ { k }$ is far from $w ^ { * }$

### 6.4.5 Convergence of SGD

The rigorous proof of the convergence of SGD is given as follows.

Theorem 6.4 (Convergence of SGD). For the SGD algorithm in (6.13), if the following conditions are satisfied, then $w _ { k }$ converges to the root of $\nabla _ { \boldsymbol { w } } \mathbb { E } [ f ( \boldsymbol { w } , \boldsymbol { X } ) ] = 0$ almost surely.

(a) $0 < c _ { 1 } \leq \nabla _ { w } ^ { 2 } f ( w , X ) \leq c _ { 2 } ,$

(b) $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } = \infty$ and $\textstyle \sum _ { k = 1 } ^ { \infty } a _ { k } ^ { 2 } < \infty$ ;

(c) $\{ x _ { k } \} _ { k = 1 } ^ { \infty }$ are i.i.d.

The three conditions in Theorem 6.4 are discussed below.

◇ Condition (a) is about the convexity of f. It requires the curvature of f to be bounded from above and below. Here, w is a scalar, and so is $\nabla _ { w } ^ { 2 } f ( w , X )$ . This condition can be generalized to the vector case. When w is a vector, $\nabla _ { w } ^ { 2 } f ( w , X )$ is the well-known Hessian matrix.

Condition (b) is similar to that of the RM algorithm. In fact, the SGD algorithm is a special RM algorithm (as shown in the proof in Box 6.1). In practice, $a _ { k }$ is often selected as a suficiently small constant. Although condition (b) is not satisfied in this case, the algorithm can still converge in a certain sense [24, Section 1.5].

Condition (c) is a common requirement.

### Box 6.1: Proof of Theorem 6.4

We next show that the SGD algorithm is a special RM algorithm. Then, the convergence of SGD naturally follows from the RM theorem.

The problem to be solved by SGD is to minimize $J ( w ) = \mathbb { E } [ f ( w , X ) ]$ This problem can be converted to a root-finding problem. That is, finding the root of $\nabla _ { w } J ( w ) = \operatorname { \mathbb { E } } [ \nabla _ { w } f ( w , X ) ] = 0$ . Let

$$
g (w) = \nabla_ {w} J (w) = \mathbb {E} [ \nabla_ {w} f (w, X) ].
$$

Then, SGD aims to find the root of $g ( w ) = 0 .$ This is exactly the problem solved by the RM algorithm. The quantity that we can measure is $\tilde { g } = \nabla _ { w } f ( w , x )$ , where x is a sample of X. Note that $\tilde { g }$ can be rewritten as

$$
\begin{array}{l} \tilde {g} (w, \eta) = \nabla_ {w} f (w, x) \\ \qquad = \mathbb {E} [ \nabla_ {w} f (w, X) ] + \underbrace {\nabla_ {w} f (w , x) - \mathbb {E} [ \nabla_ {w} f (w , X) ]} _ {\eta}. \end{array}
$$

Then, the RM algorithm for solving $g ( w ) = 0$ is

$$
w _ {k + 1} = w _ {k} - a _ {k} \tilde {g} (w _ {k}, \eta_ {k}) = w _ {k} - a _ {k} \nabla_ {w} f (w _ {k}, x _ {k}),
$$

which is the same as the SGD algorithm in (6.13). As a result, the SGD algorithm is a special RM algorithm. We next show that the three conditions in Theorem 6.1 are satisfied. Then, the convergence of SGD naturally follows from Theorem 6.1.

Since $\nabla _ { w } g ( w ) ~ = ~ \nabla _ { w } \mathbb { E } [ \nabla _ { w } f ( w , X ) ] ~ = ~ \mathbb { E } [ \nabla _ { w } ^ { 2 } f ( w , X ) ]$ , it follows from $c _ { 1 } \leq$ $\nabla _ { w } ^ { 2 } f ( w , X ) \leq c _ { 2 }$ that $c _ { 1 } \leq \nabla _ { w } g ( w ) \leq c _ { 2 }$ Thus, the first condition in Theorem 6.1 is satisfied.

◇ The second condition in Theorem 6.1 is the same as the second condition in this theorem.

◇ The third condition in Theorem 6.1 requires $\mathbb { E } [ \eta _ { k } | \mathcal { H } _ { k } ] = 0$ and $\mathbb { E } [ \eta _ { k } ^ { 2 } \vert \mathcal { H } _ { k } ] < \infty$ Since $\{ x _ { k } \}$ is i.i.d., we have $\mathbb { E } _ { x _ { k } } [ \nabla _ { w } f ( w , x _ { k } ) ] = \mathbb { E } [ \nabla _ { w } f ( w , X ) ]$ for all k. Therefore,

$$
\mathbb {E} [ \eta_ {k} | \mathcal {H} _ {k} ] = \mathbb {E} [ \nabla_ {w} f (w _ {k}, x _ {k}) - \mathbb {E} [ \nabla_ {w} f (w _ {k}, X) ] | \mathcal {H} _ {k} ].
$$

Since $\mathcal { H } _ { k } = \{ w _ { k } , w _ { k - 1 } , . . . \}$ and $x _ { k }$ is independent of $\mathcal { H } _ { k }$ , the first term on the right-hand side becomes $\mathbb { E } [ \nabla _ { w } f ( w _ { k } , x _ { k } ) | \mathcal { H } _ { k } ] \ = \ \mathbb { E } _ { x _ { k } } [ \nabla _ { w } f ( w _ { k } , x _ { k } ) ]$ The second term becomes $\mathbb { E } [ \mathbb { E } [ \nabla _ { w } f ( w _ { k } , X ) ] | \mathcal { H } _ { k } ] = \mathbb { E } [ \nabla _ { w } f ( w _ { k } , X ) ]$ because $\mathbb { E } [ \nabla _ { w } f ( w _ { k } , X ) ]$ ] is a function of $w _ { k }$ . Therefore,

$$
\mathbb {E} [ \eta_ {k} | \mathcal {H} _ {k} ] = \mathbb {E} _ {x _ {k}} [ \nabla_ {w} f (w _ {k}, x _ {k}) ] - \mathbb {E} [ \nabla_ {w} f (w _ {k}, X) ] = 0.
$$

Similarly, it can be proven that $\mathbb { E } [ \eta _ { k } ^ { 2 } \vert \mathcal { H } _ { k } ] < \infty \mathrm { i f } \left. \nabla _ { w } f ( w , x ) \right. < \infty$ for all w given any x.

Since the three conditions in Theorem 6.1 are satisfied, the convergence of the SGD algorithm follows.

## 6.5 Summary

Instead of introducing new reinforcement learning algorithms, this chapter introduced the preliminaries of stochastic approximation such as the RM and SGD algorithms. Compared to many other root-finding algorithms, the RM algorithm does not require the expression of the objective function or its derivative. It has been shown that the SGD algorithm is a special RM algorithm. Moreover, an important problem frequently discussed throughout this chapter is mean estimation. The mean estimation algorithm (6.4) is the first stochastic iterative algorithm we have ever introduced in this book. We showed that it is a special SGD algorithm. We will see in Chapter 7 that temporal-difference learning algorithms have similar expressions. Finally, the name “stochastic approximation” was first used by Robbins and Monro in 1951 [25]. More information about stochastic approximation can be found in [24].

## 6.6 Q&A

◇ Q: What is stochastic approximation?

A: Stochastic approximation refers to a broad class of stochastic iterative algorithms for solving root-finding or optimization problems.

◇ Q: Why do we need to study stochastic approximation?

A: This is because the temporal-difference reinforcement learning algorithms that will be introduced in Chapter 7 can be viewed as stochastic approximation algorithms. With the knowledge introduced in this chapter, we can be better prepared, and it will not be abrupt for us to see these algorithms for the first time.

Q: Why do we frequently discuss the mean estimation problem in this chapter?

A: This is because the state and action values are defined as the means of random variables. The temporal-difference learning algorithms introduced in Chapter 7 are similar to stochastic approximation algorithms for mean estimation.

### Q: What is the advantage of the RM algorithm over other root-finding algorithms?

A: Compared to many other root-finding algorithms, the RM algorithm is powerful in the sense that it does not require the expression of the objective function or its derivative. As a result, it is a black-box technique that only requires the input and output of the objective function. The famous SGD algorithm is a special form of the RM algorithm.

### ◇ Q: What is the basic idea of SGD?

A: SGD aims to solve optimization problems involving random variables. When the probability distributions of the given random variables are not known, SGD can solve the optimization problems merely by using samples. Mathematically, the SGD algo rithm can be obtained by replacing the true gradient expressed as an expectation in the gradient descent algorithm with a stochastic gradient.

### Q: Can SGD converge quickly?

A: SGD has an interesting convergence pattern. That is, if the estimate is far from the optimal solution, then the convergence process is fast. When the estimate is close to the solution, the randomness of the stochastic gradient becomes influential, and the convergence rate decreases.

### Q: What is MBGD? What are its advantages over SGD and BGD?

A: MBGD can be viewed as an intermediate version between SGD and BGD. Compared to SGD, it has less randomness because it uses more samples instead of just one as in SGD. Compared to BGD, it does not require the use of all the samples, making it more flexible.
