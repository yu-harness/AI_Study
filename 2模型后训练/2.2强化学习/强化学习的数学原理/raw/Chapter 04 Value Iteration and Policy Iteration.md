---
title: "Chapter 04 Value Iteration and Policy Iteration"
topic: "2模型后训练"
type: note
date: 2026-11-06
---

# Chapter 4 Value Iteration and Policy Iteration

![](21bf35d68f72ed8d9ec4b9ff84449f91ab40036ea0d11a53831500a36010c373.jpg)

*Figure 4.1: Where we are in this book.*

With the preparation in the previous chapters, we are now ready to present the first algorithms that can find optimal policies. This chapter introduces three algorithms that are closely related to each other. The first is the value iteration algorithm, which is exactly the algorithm suggested by the contraction mapping theorem for solving the Bellman optimality equation as discussed in the last chapter. We focus more on the implementation details of this algorithm in the present chapter. The second is the policy iteration algorithm, whose idea is widely used in reinforcement learning algorithms. The third is the truncated policy iteration algorithm, which is a unified algorithm that includes the value iteration and policy iteration algorithms as special cases.

The algorithms introduced in this chapter are called dynamic programming algorithms [10, 11], which require the system model. These algorithms are important foundations of the model-free reinforcement learning algorithms introduced in the subsequent chapters. For example, the Monte Carlo algorithms introduced in Chapter 5 can be immediately obtained by extending the policy iteration algorithm introduced in this chapter.

## 4.1 Value iteration

This section introduces the value iteration algorithm. It is exactly the algorithm suggested by the contraction mapping theorem for solving the Bellman optimality equation, as introduced in the last chapter (Theorem 3.3). In particular, the algorithm is

$$
v _ {k + 1} = \max _ {\pi \in \Pi} (r _ {\pi} + \gamma P _ {\pi} v _ {k}), \quad k = 0, 1, 2, \ldots
$$

It is guaranteed by Theorem 3.3 that $v _ { k }$ and $\pi _ { k }$ converge to the optimal state value and an optimal policy as $k  \infty .$ , respectively.

This algorithm is iterative and has two steps in every iteration.

The first step in every iteration is a policy update step. Mathematically, it aims to find a policy that can solve the following optimization problem:

$$
\pi_ {k + 1} = \arg \max _ {\pi} (r _ {\pi} + \gamma P _ {\pi} v _ {k}),
$$

where $v _ { k }$ is obtained in the previous iteration.

The second step is called a value update step. Mathematically, it calculates a new value $v _ { k + 1 }$ by

$$
v _ {k + 1} = r _ {\pi_ {k + 1}} + \gamma P _ {\pi_ {k + 1}} v _ {k},\tag{4.1}
$$

where $v _ { k + 1 }$ will be used in the next iteration.

The value iteration algorithm introduced above is in a matrix-vector form. To im plement this algorithm, we need to further examine its elementwise form. While the matrix-vector form is useful for understanding the core idea of the algorithm, the ele mentwise form is necessary for explaining the implementation details.

### 4.1.1 Elementwise form and implementation

Consider the time step k and a state s.

First, the elementwise form of the policy update step $\pi _ { k + 1 } = \arg \operatorname* { m a x } _ { \pi } ( r _ { \pi } + \gamma P _ { \pi } v _ { k } )$ i

$$
\pi_ {k + 1} (s) = \arg \max _ {\pi} \sum_ {a} \pi (a | s) \underbrace {\left(\sum_ {r} p (r | s , a) r + \gamma \sum_ {s ^ {\prime}} p (s ^ {\prime} | s , a) v _ {k} (s ^ {\prime})\right)} _ {q _ {k} (s, a)}, \quad s \in \mathcal {S}.
$$

We showed in Section 3.3.1 that the optimal policy that can solve the above optimization problem is

$$
\pi_ {k + 1} (a | s) = \left\{ \begin{array}{l l} 1, & a = a _ {k} ^ {*} (s), \\ 0, & a \neq a _ {k} ^ {*} (s), \end{array} \right.\tag{4.2}
$$

where $a _ { k } ^ { * } ( s ) = \arg \operatorname* { m a x } _ { a } q _ { k } ( s , a )$ . If $a _ { k } ^ { * } ( s ) = \arg \operatorname* { m a x } _ { a } q _ { k } ( s , a )$ has multiple solutions, we can select any of them without afecting the convergence of the algorithm. Since the new policy $\pi _ { k + 1 }$ selects the action with the greatest $q _ { k } ( s , a )$ , such a policy is called greedy.

Second, the elementwise form of the value update step $v _ { k + 1 } = r _ { \pi _ { k + 1 } } + \gamma P _ { \pi _ { k + 1 } } v _ { k }$ is

$$
v _ {k + 1} (s) = \sum_ {a} \pi_ {k + 1} (a | s) \underbrace {\left(\sum_ {r} p (r | s , a) r + \gamma \sum_ {s ^ {\prime}} p (s ^ {\prime} | s , a) v _ {k} (s ^ {\prime})\right)} _ {q _ {k} (s, a)}, \quad s \in \mathcal {S}.
$$

Substituting (4.2) into the above equation gives

$$
v _ {k + 1} (s) = \max _ {a} q _ {k} (s, a).
$$

In summary, the above steps can be illustrated as

$$
v _ {k} (s) \to q _ {k} (s, a) \to \text {new greedy policy} \pi_ {k + 1} (s) \to \text {new value} v _ {k + 1} (s) = \max _ {a} q _ {k} (s, a)
$$

The implementation details are summarized in Algorithm 4.1.

One problem that may be confusing is whether $v _ { k }$ in (4.1) is a state value. The answer is no. Although $v _ { k }$ eventually converges to the optimal state value, it is not ensured to satisfy the Bellman equation of any policy. For example, it does not satisfy $v _ { k } = r _ { \pi _ { k + 1 } } + \gamma P _ { \pi _ { k + 1 } } v _ { k } { \mathrm { ~ o r ~ } } v _ { k } = r _ { \pi _ { k } } + \gamma P _ { \pi _ { k } } v _ { k }$ in general. It is merely an intermediate value generated by the algorithm. In addition, since $v _ { k }$ is not a state value, $q _ { k }$ is not an action value.

### 4.1.2 Illustrative examples

We next present an example to illustrate the step-by-step implementation of the value iteration algorithm. This example is a two-by-two grid with one forbidden area (Figure 4.2). The target area is s<sub>4</sub>. The reward settings are r<sub>boundary</sub> $s _ { 4 }$ $= r _ { \mathrm { f o r b i d d e n } } = - 1$ and $r _ { \mathrm { t a r g e t } } = 1$ . The discount rate is $\gamma = 0 . 9$

### Algorithm 4.1: Value iteration algorithm

- **Initialization:** The probability models $p(r|s,a)$ and $p(s'|s,a)$ for all $(s,a)$ are known. Initial guess $v_{0}$ .
- **Goal:** Search for the optimal state value and an optimal policy for solving the Bellman optimality equation.
- While $v_{k}$ has not converged in the sense that $\|v_{k}-v_{k-1}\|$ is greater than a predefined small threshold, for the kth iteration, do
- For every state $s\in S$ , do
- For every action $a\in\mathcal{A}(s)$ , do
- **q-value:** $q_{k}(s,a)=\sum_{r}p(r|s,a)r+\gamma\sum_{s'}p(s'|s,a)v_{k}(s')$
- **Maximum action value:** $a_{k}^{*}(s)=\arg\max_{a}q_{k}(s,a)$
- **Policy update:** $\pi_{k+1}(a|s)=1$ if $a=a_{k}^{*}$ , and $\pi_{k+1}(a|s)=0$ otherwise
- **Value update:** $v_{k+1}(s)=\max_{a}q_{k}(s,a)$

| q-table | $a_1$ | $a_2$ | $a_3$ | $a_4$ | $a_5$ |
| --- | --- | --- | --- | --- | --- |
| $s_1$ | $-1 + \gamma v(s_1)$ | $-1 + \gamma v(s_2)$ | $0 + \gamma v(s_3)$ | $-1 + \gamma v(s_1)$ | $0 + \gamma v(s_1)$ |
| $s_2$ | $-1 + \gamma v(s_2)$ | $-1 + \gamma v(s_2)$ | $1 + \gamma v(s_4)$ | $0 + \gamma v(s_1)$ | $-1 + \gamma v(s_2)$ |
| $s_3$ | $0 + \gamma v(s_1)$ | $1 + \gamma v(s_4)$ | $-1 + \gamma v(s_3)$ | $-1 + \gamma v(s_3)$ | $0 + \gamma v(s_3)$ |
| $s_4$ | $-1 + \gamma v(s_2)$ | $-1 + \gamma v(s_4)$ | $-1 + \gamma v(s_4)$ | $0 + \gamma v(s_3)$ | $1 + \gamma v(s_4)$ |

*Table 4.1: The expression of $q ( s , a )$ for the example as shown in Figure 4.2.*

![](f71b9761520e484a230e68cd453345251fb62d00d2fb49c7dfacd18b6d7a1e81.jpg)

*Figure 4.2: An example for demonstrating the implementation of the value iteration algorithm.*

The expression of the q-value for each state-action pair is shown in Table 4.1.

$k = 0 \colon$

Without loss of generality, select the initial values as $v _ { 0 } ( s _ { 1 } ) = v _ { 0 } ( s _ { 2 } ) = v _ { 0 } ( s _ { 3 } ) =$ $v _ { 0 } ( s _ { 4 } ) = 0$ q-value calculation: Substituting $v _ { 0 } ( s _ { i } )$ into Table 4.1 gives the q-values shown in Table 4.2.

| q-table | $a_{1}$ | $a_{2}$ | $a_{3}$ | $a_{4}$ | $a_{5}$ |
| --- | --- | --- | --- | --- | --- |
| $s_{1}$ | -1 | -1 | 0 | -1 | 0 |
| $s_{2}$ | -1 | -1 | 1 | 0 | -1 |
| $s_{3}$ | 0 | 1 | -1 | -1 | 0 |
| $s_{4}$ | -1 | -1 | -1 | 0 | 1 |

*Table 4.2: The value of $\boldsymbol { q } ( s , a )$ at $k = 0$*

| q-table | $a_1$ | $a_2$ | $a_3$ | $a_4$ | $a_5$ |
| --- | --- | --- | --- | --- | --- |
| $s_1$ | $-1 + \gamma 0$ | $-1 + \gamma 1$ | $0 + \gamma 1$ | $-1 + \gamma 0$ | $0 + \gamma 0$ |
| $s_2$ | $-1 + \gamma 1$ | $-1 + \gamma 1$ | $1 + \gamma 1$ | $0 + \gamma 0$ | $-1 + \gamma 1$ |
| $s_3$ | $0 + \gamma 0$ | $1 + \gamma 1$ | $-1 + \gamma 1$ | $-1 + \gamma 1$ | $0 + \gamma 1$ |
| $s_4$ | $-1 + \gamma 1$ | $-1 + \gamma 1$ | $-1 + \gamma 1$ | $0 + \gamma 1$ | $1 + \gamma 1$ |

*Table 4.3: The value of $\boldsymbol { q } ( s , a )$ at $k = 1$*

Policy update: $\pi _ { 1 }$ is obtained by selecting the actions with the greatest q-values for every state:

$$
\pi_ {1} (a _ {5} | s _ {1}) = 1, \quad \pi_ {1} (a _ {3} | s _ {2}) = 1, \quad \pi_ {1} (a _ {2} | s _ {3}) = 1, \quad \pi_ {1} (a _ {5} | s _ {4}) = 1.
$$

This policy is visualized in Figure 4.2 (the middle subfigure). It is clear that this policy is not optimal because it selects to stay still at $s _ { 1 }$ . Notably, the q-values for $( s _ { 1 } , a _ { 5 } )$ and $( s _ { 1 } , a _ { 3 } )$ are actually the same, and we can randomly select either action.

Value update: $v _ { 1 }$ is obtained by updating the v-value to the greatest q-value for each state:

$$
v _ {1} (s _ {1}) = 0, \quad v _ {1} (s _ {2}) = 1, \quad v _ {1} (s _ {3}) = 1, \quad v _ {1} (s _ {4}) = 1.
$$

$k = 1 \colon$ q-value calculation: Substituting $v _ { 1 } ( s _ { i } )$ into Table 4.1 yields the q-values shown in Table 4.3.

Policy update: $\pi _ { 2 }$ is obtained by selecting the greatest q-values:

$$
\pi_ {2} (a _ {3} | s _ {1}) = 1, \quad \pi_ {2} (a _ {3} | s _ {2}) = 1, \quad \pi_ {2} (a _ {2} | s _ {3}) = 1, \quad \pi_ {2} (a _ {5} | s _ {4}) = 1.
$$

This policy is visualized in Figure 4.2 (the right subfigure).

Value update: $v _ { 2 }$ is obtained by updating the v-value to the greatest q-value for each state:

$$
v _ {2} (s _ {1}) = \gamma 1, v _ {2} (s _ {2}) = 1 + \gamma 1, v _ {2} (s _ {3}) = 1 + \gamma 1, v _ {2} (s _ {4}) = 1 + \gamma 1.
$$

k = 2, 3, 4, . . .

It is notable that policy $\pi _ { 2 } .$ , as illustrated in Figure 4.2, is already optimal. Therefore, we only need to run two iterations to obtain an optimal policy in this simple example. For more complex examples, we need to run more iterations until the value of $v _ { k }$ converges (e.g., until $\| v _ { k + 1 } - v _ { k } \|$ is smaller than a pre-specified threshold).

## 4.2 Policy iteration

This section presents another important algorithm: policy iteration. Unlike value itera tion, policy iteration is not for directly solving the Bellman optimality equation. However, it has an intimate relationship with value iteration, as shown later. Moreover, the idea of policy iteration is very important since it is widely utilized in reinforcement learning algorithms.

### 4.2.1 Algorithm analysis

Policy iteration is an iterative algorithm. Each iteration has two steps.

The first is a policy evaluation step. As its name suggests, this step evaluates a given policy by calculating the corresponding state value. That is to solve the following Bellman equation:

$$
v _ {\pi_ {k}} = r _ {\pi_ {k}} + \gamma P _ {\pi_ {k}} v _ {\pi_ {k}},\tag{4.3}
$$

where $\pi _ { k }$ is the policy obtained in the last iteration and $v _ { \pi _ { k } }$ is the state value to be calculated. The values of $r _ { \pi _ { k } }$ and $P _ { \pi _ { k } }$ can be obtained from the system model.

The second is a policy improvement step. As its name suggests, this step is used to improve the policy. In particular, once $v _ { \pi _ { k } }$ has been calculated in the first step, a new policy $\pi _ { k + 1 }$ can be obtained as

$$
\pi_ {k + 1} = \arg \max _ {\pi} (r _ {\pi} + \gamma P _ {\pi} v _ {\pi_ {k}}).
$$

Three questions naturally follow the above description of the algorithm.

In the policy evaluation step, how to solve the state value ${ v _ { \pi } } _ { k } ?$

In the policy improvement step, why is the new policy $\pi _ { k + 1 }$ better than $\pi _ { k } ?$

Why can this algorithm finally converge to an optimal policy?

We next answer these questions one by one.

### In the policy evaluation step, how to calculate ${ v _ { \pi } } _ { k } ?$

We introduced two methods in Chapter 2 for solving the Bellman equation in (4.3). We next revisit the two methods briefly. The first method is a closed-form solution:

$v _ { \pi _ { k } } = ( I - \gamma P _ { \pi _ { k } } ) ^ { - 1 } r _ { \pi _ { k } }$ . This closed-form solution is useful for theoretical analysis purposes, but it is ineficient to implement since it requires other numerical algorithms to compute the matrix inverse. The second method is an iterative algorithm that can be easily implemented:

$$
v _ {\pi_ {k}} ^ {(j + 1)} = r _ {\pi_ {k}} + \gamma P _ {\pi_ {k}} v _ {\pi_ {k}} ^ {(j)}, \quad j = 0, 1, 2, \dots\tag{4.4}
$$

where $v _ { \pi _ { k } } ^ { ( j ) }$ denotes the jth estimate of $v _ { \pi _ { k } }$ . Starting from any initial guess $v _ { \pi _ { k } } ^ { ( 0 ) }$ , it is ensured that $v _ { \pi _ { k } } ^ { ( j ) } \to v _ { \pi _ { k } }$ as $j \to \infty$ . Details can be found in Section 2.7.

Interestingly, policy iteration is an iterative algorithm with another iterative algorithm (4.4) embedded in the policy evaluation step. In theory, this embedded iterative algorithm requires an infinite number of steps (that is, $j \to \infty )$ to converge to the true state value $v _ { \pi _ { k } }$ . This is, however, impossible to realize. In practice, the iterative process terminates when a certain criterion is satisfied. For example, the termination criterion can be that $\| v _ { \pi _ { k } } ^ { ( j + 1 ) } - v _ { \pi _ { k } } ^ { ( j ) } \|$ is less than a prespecified threshold or that $j$ exceeds a prespecified value. If we do not run an infinite number of iterations, we can only obtain an imprecise value of $v _ { \pi _ { k } }$ , which will be used in the subsequent policy improvement step. Would this cause problems? The answer is no. The reason will become clear when we introduce the truncated policy iteration algorithm later in Section 4.3.

In the policy improvement step, why is $\pi _ { k + 1 }$ better than $\pi _ { k } ?$

The policy improvement step can improve the given policy, as shown below.

Lemma 4.1 (Policy improvement). $I f \pi _ { k + 1 } = \arg \operatorname* { m a x } _ { \pi } ( r _ { \pi } + \gamma P _ { \pi } v _ { \pi _ { k } } )$ , then $v _ { \pi _ { k + 1 } } \geq v _ { \pi _ { k } }$

Here, $v _ { \pi _ { k + 1 } } \geq v _ { \pi _ { k } }$ means that $v _ { \pi _ { k + 1 } } ( s ) \geq v _ { \pi _ { k } } ( s )$ for all s. The proof of this lemma is given in Box 4.1.

### Box 4.1: Proof of Lemma 4.1

Since $v _ { \pi _ { k + 1 } }$ and $v _ { \pi _ { k } }$ are state values, they satisfy the Bellman equations:

$$
\begin{array}{c} {v _ {\pi_ {k + 1}} = r _ {\pi_ {k + 1}} + \gamma P _ {\pi_ {k + 1}} v _ {\pi_ {k + 1}},} \\ {v _ {\pi_ {k}} = r _ {\pi_ {k}} + \gamma P _ {\pi_ {k}} v _ {\pi_ {k}}.} \end{array}
$$

Since $\pi _ { k + 1 } = \arg \operatorname* { m a x } _ { \pi } ( r _ { \pi } + \gamma P _ { \pi } v _ { \pi _ { k } } )$ , we know that

$$
r _ {\pi_ {k + 1}} + \gamma P _ {\pi_ {k + 1}} v _ {\pi_ {k}} \geq r _ {\pi_ {k}} + \gamma P _ {\pi_ {k}} v _ {\pi_ {k}}.
$$

It then follows that

$$
\begin{array}{r l} & v _ {\pi_ {k}} - v _ {\pi_ {k + 1}} = (r _ {\pi_ {k}} + \gamma P _ {\pi_ {k}} v _ {\pi_ {k}}) - (r _ {\pi_ {k + 1}} + \gamma P _ {\pi_ {k + 1}} v _ {\pi_ {k + 1}}) \\ & \qquad \leq (r _ {\pi_ {k + 1}} + \gamma P _ {\pi_ {k + 1}} v _ {\pi_ {k}}) - (r _ {\pi_ {k + 1}} + \gamma P _ {\pi_ {k + 1}} v _ {\pi_ {k + 1}}) \\ & \qquad \leq \gamma P _ {\pi_ {k + 1}} (v _ {\pi_ {k}} - v _ {\pi_ {k + 1}}). \end{array}
$$

Therefore,

$$
\begin{array}{r l} & v _ {\pi_ {k}} - v _ {\pi_ {k + 1}} \leq \gamma^ {2} P _ {\pi_ {k + 1}} ^ {2} (v _ {\pi_ {k}} - v _ {\pi_ {k + 1}}) \leq \ldots \leq \gamma^ {n} P _ {\pi_ {k + 1}} ^ {n} (v _ {\pi_ {k}} - v _ {\pi_ {k + 1}}) \\ & \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \qquad \leq \lim _ {n \to \infty} \gamma^ {n} P _ {\pi_ {k + 1}} ^ {n} (v _ {\pi_ {k}} - v _ {\pi_ {k + 1}}) = 0. \end{array}
$$

The limit is due to the facts that $\gamma ^ { n } \to 0 { \mathrm { ~ a s ~ } } n \to \infty$ and $P _ { \pi _ { k + 1 } } ^ { n }$ is a nonnegative stochastic matrix for any n. Here, a stochastic matrix refers to a nonnegative matrix whose row sums are equal to one for all rows.

Why can the policy iteration algorithm eventually find an optimal policy?

The policy iteration algorithm generates two sequences. The first is a sequence of policies: $\left\{ \pi _ { 0 } , \pi _ { 1 } , \ldots , \pi _ { k } , \ldots \right\}$ . The second is a sequence of state values: $\{ v _ { \pi _ { 0 } } , v _ { \pi _ { 1 } } , \ldots , v _ { \pi _ { k } } , \ldots \}$ Suppose that $v ^ { * }$ is the optimal state value. Then, $v _ { \pi _ { k } } \le v ^ { * }$ for all k. Since the policies are continuously improved according to Lemma 4.1, we know that

$$
v _ {\pi_ {0}} \leq v _ {\pi_ {1}} \leq v _ {\pi_ {2}} \leq \dots \leq v _ {\pi_ {k}} \leq \dots \leq v ^ {*}.
$$

Since $v _ { \pi _ { k } }$ is nondecreasing and always bounded from above by $v ^ { * }$ , it follows from the monotone convergence theorem [12] (Appendix C) that $v _ { \pi _ { k } }$ converges to a constant value, denoted as $v _ { \infty }$ , when $k  \infty$ . The following analysis shows that $v _ { \infty } = v ^ { * }$

Theorem 4.1 (Convergence of policy iteration). The state value sequence $\{ v _ { \pi _ { k } } \} _ { k = 0 } ^ { \infty }$ generated by the policy iteration algorithm converges to the optimal state value $v ^ { * }$ . As a result, the policy sequence $\{ \pi _ { k } \} _ { k = 0 } ^ { \infty }$ converges to an optimal policy.

The proof of this theorem is given in Box 4.2. The proof not only shows the convergence of the policy iteration algorithm but also reveals the relationship between the policy iteration and value iteration algorithms. Loosely speaking, if both algorithms start from the same initial guess, policy iteration will converge faster than value iteration due to the additional iterations embedded in the policy evaluation step. This point will become clearer when we introduce the truncated policy iteration algorithm in Section 4.3.

### Box 4.2: Proof of Theorem 4.1

The idea of the proof is to show that the policy iteration algorithm converges faster than the value iteration algorithm.

In particular, to prove the convergence of $\{ v _ { \pi _ { k } } \} _ { k = 0 } ^ { \infty } .$ , we introduce another sequence $\{ v _ { k } \} _ { k = 0 } ^ { \infty }$ generated by

$$
v _ {k + 1} = f (v _ {k}) = \max _ {\pi} (r _ {\pi} + \gamma P _ {\pi} v _ {k}).
$$

This iterative algorithm is exactly the value iteration algorithm. We already know that $v _ { k }$ converges to $v ^ { * }$ when given any initial value $v _ { 0 }$

For $k = 0$ , we can always find a $v _ { 0 }$ such that $v _ { \pi _ { 0 } } \geq v _ { 0 }$ for any $\pi _ { 0 }$

We next show that $v _ { k } \le v _ { \pi _ { k } } \le v ^ { * }$ for all k by induction.

For $k \geq 0$ , suppose that $v _ { \pi _ { k } } \geq v _ { k }$

For $k + 1$ , we have

$$
\begin{array}{r l} & v _ {\pi_ {k + 1}} - v _ {k + 1} = (r _ {\pi_ {k + 1}} + \gamma P _ {\pi_ {k + 1}} v _ {\pi_ {k + 1}}) - \underset {\pi} {\max} (r _ {\pi} + \gamma P _ {\pi} v _ {k}) \\ & \qquad \geq (r _ {\pi_ {k + 1}} + \gamma P _ {\pi_ {k + 1}} v _ {\pi_ {k}}) - \underset {\pi} {\max} (r _ {\pi} + \gamma P _ {\pi} v _ {k}) \\ & \qquad \quad \big (\text {because} v _ {\pi_ {k + 1}} \geq v _ {\pi_ {k}} \text {by Lemma 4.1 and} P _ {\pi_ {k + 1}} \geq 0 \big) \\ & \qquad = (r _ {\pi_ {k + 1}} + \gamma P _ {\pi_ {k + 1}} v _ {\pi_ {k}}) - (r _ {\pi_ {k} ^ {\prime}} + \gamma P _ {\pi_ {k} ^ {\prime}} v _ {k}) \\ & \qquad \quad \big (\text {suppose} \pi_ {k} ^ {\prime} = \arg \underset {\pi} {\max} (r _ {\pi} + \gamma P _ {\pi} v _ {k}) \big) \\ & \qquad \geq (r _ {\pi_ {k} ^ {\prime}} + \gamma P _ {\pi_ {k} ^ {\prime}} v _ {\pi_ {k}}) - (r _ {\pi_ {k} ^ {\prime}} + \gamma P _ {\pi_ {k} ^ {\prime}} v _ {k}) \\ & \qquad \quad \big (\text {because} \pi_ {k + 1} = \arg \underset {\pi} {\max} (r _ {\pi} + \gamma P _ {\pi} v _ {\pi_ {k}}) \big) \\ & \qquad = \gamma P _ {\pi_ {k} ^ {\prime}} (v _ {\pi_ {k}} - v _ {k}). \end{array}
$$

Since $v _ { \pi _ { k } } \mathrm { ~ - ~ } v _ { k } \geq 0$ and $P _ { \pi _ { k } ^ { \prime } }$ is nonnegative, we have $P _ { \pi _ { k } ^ { \prime } } ( v _ { \pi _ { k } } - v _ { k } ) \ge 0$ and hence $v _ { \pi _ { k + 1 } } - v _ { k + 1 } \geq 0$

Therefore, we can show by induction that $v _ { k } \le v _ { \pi _ { k } } \le v ^ { * }$ for any $k \geq 0$ . Since $v _ { k }$ converges to $v ^ { \ast } , v _ { \pi _ { k } }$ also converges to $v ^ { * }$

### 4.2.2 Elementwise form and implementation

To implement the policy iteration algorithm, we need to study its elementwise form.

First, the policy evaluation step solves $v _ { \pi _ { k } }$ from $v _ { \pi _ { k } } = r _ { \pi _ { k } } + \gamma P _ { \pi _ { k } } v _ { \pi _ { k } }$ by using the

### Algorithm 4.2: Policy iteration algorithm

- **Initialization:** The system model, $p(r|s,a)$ and $p(s'|s,a)$ for all $(s,a)$ , is known. Initial guess $\pi_{0}$ .
- **Goal:** Search for the optimal state value and an optimal policy.
- While $v_{\pi_{k}}$ has not converged, for the kth iteration, do

Policy evaluation:

Initialization: an arbitrary initial guess $v_{\pi_{k}}^{(0)}$ While $v_{\pi_{k}}^{(j)}$ has not converged, for the jth iteration, do

For every state $s \in S$ , do $v_{\pi_{k}}^{(j+1)}(s) = \sum_{a} \pi_{k}(a|s) \left[ \sum_{r} p(r|s,a)r + \gamma \sum_{s'} p(s'|s,a)v_{\pi_{k}}^{(j)}(s') \right]$ Policy improvement:

For every state $s \in S$ , do

For every action $a \in A$ , do $q_{\pi_{k}}(s,a) = \sum_{r} p(r|s,a)r + \gamma \sum_{s'} p(s'|s,a)v_{\pi_{k}}(s')$ $a_{k}^{*}(s) = \arg \max_{a} q_{\pi_{k}}(s,a)$ $\pi_{k+1}(a|s) = 1$ if $a = a_{k}^{*}$ , and $\pi_{k+1}(a|s) = 0$ otherwise iterative algorithm in (4.4). The elementwise form of this algorithm is

$$
v _ {\pi_ {k}} ^ {(j + 1)} (s) = \sum_ {a} \pi_ {k} (a | s) \left(\sum_ {r} p (r | s, a) r + \gamma \sum_ {s ^ {\prime}} p (s ^ {\prime} | s, a) v _ {\pi_ {k}} ^ {(j)} (s ^ {\prime})\right), \quad s \in \mathcal {S},
$$

where $j = 0 , 1 , 2 , . . .$

Second, the policy improvement step solves $\pi _ { k + 1 } = \arg \operatorname* { m a x } _ { \pi } ( r _ { \pi } + \gamma P _ { \pi } v _ { \pi _ { k } } )$ . The elementwise form of this equation is

$$
\pi_ {k + 1} (s) = \arg \max _ {\pi} \sum_ {a} \pi (a | s) \underbrace {\left(\sum_ {r} p (r | s , a) r + \gamma \sum_ {s ^ {\prime}} p (s ^ {\prime} | s , a) v _ {\pi_ {k}} (s ^ {\prime})\right)} _ {q _ {\pi_ {k}} (s, a)}, \quad s \in \mathcal {S},
$$

where $q _ { \pi _ { k } } ( s , a )$ is the action value under policy $\pi _ { k }$ . Let $a _ { k } ^ { * } ( s ) = \arg \operatorname* { m a x } _ { a } q _ { \pi _ { k } } ( s , a )$ Then, the greedy optimal policy is

$$
\pi_ {k + 1} (a | s) = \left\{ \begin{array}{l l} 1, & a = a _ {k} ^ {*} (s), \\ 0, & a \neq a _ {k} ^ {*} (s). \end{array} \right.
$$

The implementation details are summarized in Algorithm 4.2.

### 4.2.3 Illustrative examples

### A simple example

Consider a simple example shown in Figure 4.3. There are two states with three possible actions: $\mathcal { A } = \{ a _ { \ell } , a _ { 0 } , a _ { r } \}$ . The three actions represent moving leftward, staying unchanged, and moving rightward. The reward settings are $r _ { \mathrm { b o u n d a r y } } = - 1$ and $r _ { \mathrm { t a r g e t } } = 1$ The discount rate is $\gamma = 0 . 9$

![](0be5b3709d80fcc97f6fa28a02940668d3cd3cd64ea92e9b407e6a93fb149cc2.jpg)

![](ab8e3c0a42620294bc91fa4d19d461671efe1c52f211daa51bebb88cb4e2566e.jpg)

*Figure 4.3: An example for illustrating the implementation of the policy iteration algorithm.*

We next present the implementation of the policy iteration algorithm in a step-by-step manner. When $k = 0$ , we start with the initial policy shown in Figure $4 . 3 ( \mathrm { a } )$ . This policy is not good because it does not move toward the target area. We next show how to apply the policy iteration algorithm to obtain an optimal policy.

First, in the policy evaluation step, we need to solve the Bellman equation:

$$
\begin{array}{r l} & v _ {\pi_ {0}} (s _ {1}) = - 1 + \gamma v _ {\pi_ {0}} (s _ {1}), \\ & v _ {\pi_ {0}} (s _ {2}) = 0 + \gamma v _ {\pi_ {0}} (s _ {1}). \end{array}
$$

Since the equation is simple, it can be manually solved that

$$
v _ {\pi_ {0}} (s _ {1}) = - 1 0, v _ {\pi_ {0}} (s _ {2}) = - 9.
$$

In practice, the equation can be solved by the iterative algorithm in (4.4). For example, select the initial state values as $v _ { \pi _ { 0 } } ^ { ( 0 ) } ( s _ { 1 } ) = v _ { \pi _ { 0 } } ^ { ( 0 ) } ( s _ { 2 } ) = 0$ . It follows from (4.4) that

$$
\left\{ \begin{array}{l} v _ {\pi_ {0}} ^ {(1)} (s _ {1}) = - 1 + \gamma v _ {\pi_ {0}} ^ {(0)} (s _ {1}) = - 1, \\ v _ {\pi_ {0}} ^ {(1)} (s _ {2}) = 0 + \gamma v _ {\pi_ {0}} ^ {(0)} (s _ {1}) = 0, \\ \left\{ \begin{array}{l} v _ {\pi_ {0}} ^ {(2)} (s _ {1}) = - 1 + \gamma v _ {\pi_ {0}} ^ {(1)} (s _ {1}) = - 1. 9, \\ v _ {\pi_ {0}} ^ {(2)} (s _ {2}) = 0 + \gamma v _ {\pi_ {0}} ^ {(1)} (s _ {1}) = - 0. 9, \end{array} \right. \\ \left\{ \begin{array}{l} v _ {\pi_ {0}} ^ {(3)} (s _ {1}) = - 1 + \gamma v _ {\pi_ {0}} ^ {(2)} (s _ {1}) = - 2. 7 1, \\ v _ {\pi_ {0}} ^ {(3)} (s _ {2}) = 0 + \gamma v _ {\pi_ {0}} ^ {(2)} (s _ {1}) = - 1. 7 1, \end{array} \right. \\ \vdots \end{array} \right.
$$

With more iterations, we can see the trend: $v _ { \pi _ { 0 } } ^ { ( j ) } ( s _ { 1 } )  v _ { \pi _ { 0 } } ( s _ { 1 } ) = - 1 0 \mathrm { ~ a n d ~ } v _ { \pi _ { 0 } } ^ { ( j ) } ( s _ { 2 } ) $ $v _ { \pi _ { 0 } } ( s _ { 2 } ) = - 9$ as j increases.

Second, in the policy improvement step, the key is to calculate $q _ { \pi _ { 0 } } ( s , a )$ for each state-action pair. The following q-table can be used to demonstrate such a process:

| $q_{\pi_k}(s,a)$ | $a_\ell$ | $a_0$ | $a_r$ |
| --- | --- | --- | --- |
| $s_1$ | $-1 + \gamma v_{\pi_k}(s_1)$ | $0 + \gamma v_{\pi_k}(s_1)$ | $1 + \gamma v_{\pi_k}(s_2)$ |
| $s_2$ | $0 + \gamma v_{\pi_k}(s_1)$ | $1 + \gamma v_{\pi_k}(s_2)$ | $-1 + \gamma v_{\pi_k}(s_2)$ |

*Table 4.4: The expression of $q _ { \pi _ { k } } ( s , a )$ for the example in Figure 4.3.*

Substituting $v _ { \pi _ { 0 } } ( s _ { 1 } ) = - 1 0 , v _ { \pi _ { 0 } } ( s _ { 2 } ) = - 9$ obtained in the previous policy evaluation step into Table 4.4 yields Table 4.5.

| $q_{\pi_0}(s,a)$ | $a_\ell$ | $a_0$ | $a_r$ |
| --- | --- | --- | --- |
| $s_1$ | -10 | -9 | -7.1 |
| $s_2$ | -9 | -7.1 | -9.1 |

*Table 4.5: The value of $q _ { \pi _ { k } } ( s , a )$ when $k = 0$*

By seeking the greatest value of $q _ { \pi _ { 0 } } .$ , the improved policy $\pi _ { 1 }$ can be obtained as

$$
\pi_ {1} (a _ {r} | s _ {1}) = 1, \quad \pi_ {1} (a _ {0} | s _ {2}) = 1.
$$

This policy is illustrated in Figure 4.3(b). It is clear that this policy is optimal.

The above process shows that a single iteration is sufficient for finding the optimal policy in this simple example. More iterations are required for more complex examples.

### A more complicated example

We next demonstrate the policy iteration algorithm using a more complicated example shown in Figure 4.4. The reward settings are $r _ { \mathrm { b o u n d a r y } } = - 1 , r _ { \mathrm { f o r b i d d e n } } = - 1 0$ , and $r _ { \mathrm { t a r g e t } } =$ 1. The discount rate is $\gamma = 0 . 9$ . The policy iteration algorithm can converge to the optimal policy (Figure 4.4(h)) when starting from a random initial policy (Figure $4 . 4 ( \mathrm { a } ) )$ .

Two interesting phenomena are observed during the iteration process.

First, if we observe how the policy evolves, an interesting pattern is that the states that are close to the target area find the optimal policies earlier than those far away. Only if the close states can find trajectories to the target first, can the farther states find trajectories passing through the close states to reach the target.

Second, the spatial distribution of the state values exhibits an interesting pattern: the states that are located closer to the target have greater state values. The reason for this pattern is that an agent starting from a farther state must travel for many steps to obtain a positive reward. Such rewards would be severely discounted and hence relatively small.

![](3566cd0d41d6673c260c8efd5b2035ea75b98277416ba588f864f7947ace8722.jpg)

![](d5ec39e35c23fa496eb36e7359f845b43ddc95c2f64c20dadfdf491753770fca.jpg)

(a) $\pi _ { 0 }$ and $v _ { \pi _ { 0 } }$

![](41d617af673a32f28fcc5cbc1869313f6eeabbe0067d3aadaf11535028654a6b.jpg)

![](4ddc071a0964345d2ef7dd17f051b43636729dad2b3cb0706a469b6552ffeda9.jpg)

(b) $\pi _ { 1 }$ and $v _ { \pi _ { 1 } }$

![](277d5118312b9292de28a3f5e2e42f5c5862a950d763212de52693a89033d396.jpg)

![](524ad4870bdb83862c06a0457acfc91ff762517fb60229294dfdbda86691cbc7.jpg)

![](61eafbf9d24e1dacbc38def11e4332c8ef61693a3f35cca8054541754ec8078d.jpg)

![](3da7f09110cdb51887c676018cb8fef56636760ee572dcdcc5f7207551bf6b48.jpg)

(c) $\pi _ { 2 }$ and $v _ { \pi _ { 2 } }$

(d) $\pi _ { 3 }$ and $v _ { \pi _ { 3 } }$

![](f12049a677090fe40a2d635550a6f27fc609428a1a2e2df8f6c6b836498e2924.jpg)

![](43ca7a1e60a751d3bd3bc297e22809c3f4f2dcd5a22fdb76f5653628be086e4a.jpg)

(e) $\pi _ { 4 }$ and $v _ { \pi _ { 4 } }$

![](408530f36bb21bf4a3897411e46ec5ba1ed4cf9ca55db7afb245293f9d98eda7.jpg)

![](26374c5b544dd67b5fe2afc75a0696d385dc301ff78e8404ac28f9b21d67b854.jpg)

(f) $\pi _ { 5 }$ and $v _ { \pi _ { 5 } }$

![](b05bd14ec9f89ae1a35645dc3261a98e3a123e3bf2709bf610452147c6ae950e.jpg)

![](f6fda727a1b456851576233e0031a751ce69961b61d1d759ac415ab3b00e8b64.jpg)

(g) π<sub>9</sub> and $v _ { \pi _ { 9 } }$

![](cb7b09115461cf86a028a1a1c0c3b8dcda6d7d60e534381c71695a2dc41d21f2.jpg)

![](2f3a2d65ab77d4a91e983131835143d88c19a7f4419da2ed77d6b9cdacae6514.jpg)

(h) π<sub>10</sub> and $v _ { \pi _ { 1 0 } }$

*Figure 4.4: The evolution processes of the policies generated by the policy iteration algorithm.*

## 4.3 Truncated policy iteration

We next introduce a more general algorithm called truncated policy iteration. We will see that the value iteration and policy iteration algorithms are two special cases of the truncated policy iteration algorithm.

### 4.3.1 Comparing value iteration and policy iteration

First of all, we compare the value iteration and policy iteration algorithms by listing their steps as follows.

Policy iteration: Select an arbitrary initial policy $\pi _ { 0 }$ . In the kth iteration, do the following two steps.

- Step 1: Policy evaluation (PE). Given $\pi _ { k } .$ , solve $v _ { \pi _ { k } }$ from

$$
v _ {\pi_ {k}} = r _ {\pi_ {k}} + \gamma P _ {\pi_ {k}} v _ {\pi_ {k}}.
$$

- Step 2: Policy improvement (PI). Given $v _ { \pi _ { k } }$ , solve $\pi _ { k + 1 }$ from

$$
\pi_ {k + 1} = \arg \max _ {\pi} (r _ {\pi} + \gamma P _ {\pi} v _ {\pi_ {k}}).
$$

Value iteration: Select an arbitrary initial value $v _ { 0 }$ . In the kth iteration, do the following two steps.

- Step 1: Policy update (PU). Given $v _ { k }$ , solve $\pi _ { k + 1 }$ from

$$
\pi_ {k + 1} = \arg \max _ {\pi} (r _ {\pi} + \gamma P _ {\pi} v _ {k}).
$$

- Step 2: Value update (VU). Given $\pi _ { k + 1 }$ , solve $v _ { k + 1 }$ from

$$
v _ {k + 1} = r _ {\pi_ {k + 1}} + \gamma P _ {\pi_ {k + 1}} v _ {k}.
$$

The above steps of the two algorithms can be illustrated as

Policy iteration:

$$
\pi_ {0} \xrightarrow {P E} v _ {\pi_ {0}} \xrightarrow {P I} \pi_ {1} \xrightarrow {P E} v _ {\pi_ {1}} \xrightarrow {P I} \pi_ {2} \xrightarrow {P E} v _ {\pi_ {2}} \xrightarrow {P I} \dots
$$

Value iteration:

$$
v _ {0} \xrightarrow {P U} \pi_ {1} ^ {\prime} \xrightarrow {V U} v _ {1} \xrightarrow {P U} \pi_ {2} ^ {\prime} \xrightarrow {V U} v _ {2} \xrightarrow {P U} \dots
$$

It can be seen that the procedures of the two algorithms are very similar.

We examine their value steps more closely to see the difference between the two algorithms. In particular, let both algorithms start from the same initial condition: $v _ { 0 } ~ = ~ v _ { \pi _ { 0 } }$ . The procedures of the two algorithms are listed in Table 4.6. In the first three steps, the two algorithms generate the same results since $v _ { 0 } = v _ { \pi _ { 0 } }$ . They become

|  | Policy iteration algorithm | Value iteration algorithm | Comments |
| --- | --- | --- | --- |
| 1) Policy: | $\pi_0$ | N/A |  |
| 2) Value: | $v_{\pi_0} = r_{\pi_0} + \gamma P_{\pi_0} v_{\pi_0}$ | $v_0 \doteq v_{\pi_0}$ |  |
| 3) Policy: | $\pi_1 = \arg \max_\pi(r_\pi + \gamma P_\pi v_{\pi_0})$ | $\pi_1 = \arg \max_\pi(r_\pi + \gamma P_\pi v_0)$ | The two policies are the same |
| 4) Value: | $v_{\pi_1} = r_{\pi_1} + \gamma P_{\pi_1} v_{\pi_1}$ | $v_1 = r_{\pi_1} + \gamma P_{\pi_1} v_0$ | $v_{\pi_1} \geq v_1 \text{ since } v_{\pi_1} \geq v_{\pi_0}$ |
| 5) Policy: | $\pi_2 = \arg \max_\pi(r_\pi + \gamma P_\pi v_{\pi_1})$ | $\pi_2&#x27; = \arg \max_\pi(r_\pi + \gamma P_\pi v_1)$ |  |
| ⋮ | ⋮ | ⋮ | ⋮ |

*Table 4.6: A comparison between the implementation steps of policy iteration and value iteration. different in the fourth step. During the fourth step, the value iteration algorithm executes $v _ { 1 } = r _ { \pi _ { 1 } } + \gamma P _ { \pi _ { 1 } } v _ { 0 }$ , which is a one-step calculation, whereas the policy iteration algorithm solves $v _ { \pi _ { 1 } } = r _ { \pi _ { 1 } } + \gamma P _ { \pi _ { 1 } } v _ { \pi _ { 1 } }$ , which requires an infinite number of iterations. If we explicitly write out the iterative process for solving $v _ { \pi _ { 1 } } = r _ { \pi _ { 1 } } + \gamma P _ { \pi _ { 1 } } v _ { \pi _ { 1 } }$ in the fourth step, everything becomes clear. By letting $v _ { \pi _ { 1 } } ^ { ( 0 ) } = v _ { 0 }$ , we have*

$$
\begin{array}{r l} & v _ {\pi_ {1}} ^ {(0)} = v _ {0} \\ \mathrm{valueiteration} \leftarrow v _ {1} \longleftarrow & v _ {\pi_ {1}} ^ {(1)} = r _ {\pi_ {1}} + \gamma P _ {\pi_ {1}} v _ {\pi_ {1}} ^ {(0)} \\ & v _ {\pi_ {1}} ^ {(2)} = r _ {\pi_ {1}} + \gamma P _ {\pi_ {1}} v _ {\pi_ {1}} ^ {(1)} \\ & \vdots \\ \mathrm{truncatedpolicyiteration} \leftarrow \bar {v} _ {1} \longleftarrow & v _ {\pi_ {1}} ^ {(j)} = r _ {\pi_ {1}} + \gamma P _ {\pi_ {1}} v _ {\pi_ {1}} ^ {(j - 1)} \\ & \vdots \\ \mathrm{policyiteration} \leftarrow v _ {\pi_ {1}} \longleftarrow & v _ {\pi_ {1}} ^ {(\infty)} = r _ {\pi_ {1}} + \gamma P _ {\pi_ {1}} v _ {\pi_ {1}} ^ {(\infty)} \end{array}
$$

The following observations can be obtained from the above process.

If the iteration is run only once, then $v _ { \pi _ { 1 } } ^ { ( 1 ) }$ is actually $v _ { 1 }$ , as calculated in the value iteration algorithm.

If the iteration is run an infinite number of times, then $v _ { \pi _ { 1 } } ^ { ( \infty ) }$ is actually $v _ { \pi _ { 1 } } .$ , as calculated in the policy iteration algorithm.

If the iteration is run a finite number of times (denoted as $j _ { \mathrm { t r u n c a t e } } )$ , then such an algorithm is called truncated policy iteration. It is called truncated because the remaining iterations from $j _ { \mathrm { t r u n c a t e } }$ to are truncated.

As a result, the value iteration and policy iteration algorithms can be viewed as two extreme cases of the truncated policy iteration algorithm: value iteration terminates at $j _ { \mathrm { t r u n c a t e } } = 1$ , and policy iteration terminates at $j _ { \mathrm { t r u n c a t e } } = \infty$ . It should be noted that, although the above comparison is illustrative, it is based on the condition that $v _ { \pi _ { 1 } } ^ { ( 0 ) } = v _ { 0 } = v _ { \pi _ { 0 } }$ . The two algorithms cannot be directly compared without this condition.

### Algorithm 4.3: Truncated policy iteration algorithm

- **Initialization:** The probability models $p(r|s,a)$ and $p(s'|s,a)$ for all $(s,a)$ are known. Initial guess $\pi_{0}$ .
- **Goal:** Search for the optimal state value and an optimal policy.
- While $v_{k}$ has not converged, for the kth iteration, do

Policy evaluation:

Initialization: select the initial guess as $v_{k}^{(0)} = v_{k-1}$ . The maximum number of iterations is set as $j_{truncate}$ .

While $j < j_{truncate}$ , do

For every state $s \in S$ , do $v_{k}^{(j+1)}(s) = \sum_{a} \pi_{k}(a|s) \left[ \sum_{r} p(r|s,a)r + \gamma \sum_{s'} p(s'|s,a)v_{k}^{(j)}(s') \right]$ Set $v_{k} = v_{k}^{(j_{truncate})}$ Policy improvement:

For every state $s \in S$ , do

For every action $a \in \mathcal{A}(s)$ , do $q_{k}(s,a) = \sum_{r} p(r|s,a)r + \gamma \sum_{s'} p(s'|s,a)v_{k}(s')$ $a_{k}^{*}(s) = \arg\max_{a} q_{k}(s,a)$ $\pi_{k+1}(a|s) = 1$ if $a = a_{k}^{*}$ , and $\pi_{k+1}(a|s) = 0$ otherwise

### 4.3.2 Truncated policy iteration algorithm

In a nutshell, the truncated policy iteration algorithm is the same as the policy iteration algorithm except that it merely runs a finite number of iterations in the policy evaluation step. Its implementation details are summarized in Algorithm 4.3. It is notable that $v _ { k }$ and $v _ { k } ^ { ( j ) }$ in the algorithm are not state values. Instead, they are approximations of the true state values because only a finite number of iterations are executed in the policy evaluation step.

If $v _ { k }$ does not equal $v _ { \pi _ { k } }$ , will the algorithm still be able to find optimal policies? The answer is yes. Intuitively, truncated policy iteration is in between value iteration and policy iteration. On the one hand, it converges faster than the value iteration algorithm because it computes more than one iteration during the policy evaluation step. On the other hand, it converges slower than the policy iteration algorithm because it only computes a finite number of iterations. This intuition is illustrated in Figure 4.5. Such intuition is also supported by the following analysis.

Proposition 4.1 (Value improvement). Consider the iterative algorithm in the policy

![](f3a9bf01c414b47098390d07c25e46c7dd84abf5069ec347266fb18b4126004b.jpg)

*Figure 4.5: An illustration of the relationships between the value iteration, policy iteration, and truncated policy iteration algorithms. evaluation step:*

$$
v _ {\pi_ {k}} ^ {(j + 1)} = r _ {\pi_ {k}} + \gamma P _ {\pi_ {k}} v _ {\pi_ {k}} ^ {(j)}, \quad j = 0, 1, 2, \dots
$$

If the initial guess is selected as $v _ { \pi _ { k } } ^ { ( 0 ) } = v _ { \pi _ { k - 1 } }$ , it holds that

$$
v _ {\pi_ {k}} ^ {(j + 1)} \geq v _ {\pi_ {k}} ^ {(j)}
$$

for $j = 0 , 1 , 2 , \ldots .$

### Box 4.3: Proof of Proposition 4.1

First, since $v _ { \pi _ { k } } ^ { ( j ) } = r _ { \pi _ { k } } + \gamma P _ { \pi _ { k } } v _ { \pi _ { k } } ^ { ( j - 1 ) }$ and $\begin{array} { r } { v _ { \pi _ { k } } ^ { ( j + 1 ) } = r _ { \pi _ { k } } + \gamma P _ { \pi _ { k } } v _ { \pi _ { k } } ^ { ( j ) } } \end{array}$ , we have

$$
v _ {\pi_ {k}} ^ {(j + 1)} - v _ {\pi_ {k}} ^ {(j)} = \gamma P _ {\pi_ {k}} (v _ {\pi_ {k}} ^ {(j)} - v _ {\pi_ {k}} ^ {(j - 1)}) = \dots = \gamma^ {j} P _ {\pi_ {k}} ^ {j} (v _ {\pi_ {k}} ^ {(1)} - v _ {\pi_ {k}} ^ {(0)}).\tag{4.5}
$$

Second, since $v _ { \pi _ { k } } ^ { ( 0 ) } = v _ { \pi _ { k - 1 } }$ , we have

$$
v _ {\pi_ {k}} ^ {(1)} = r _ {\pi_ {k}} + \gamma P _ {\pi_ {k}} v _ {\pi_ {k}} ^ {(0)} = r _ {\pi_ {k}} + \gamma P _ {\pi_ {k}} v _ {\pi_ {k - 1}} \geq r _ {\pi_ {k - 1}} + \gamma P _ {\pi_ {k - 1}} v _ {\pi_ {k - 1}} = v _ {\pi_ {k - 1}} = v _ {\pi_ {k}} ^ {(0)},
$$

where the inequality is due to $\pi _ { k } = \arg \operatorname* { m a x } _ { \pi } ( r _ { \pi } + \gamma P _ { \pi } v _ { \pi _ { k - 1 } } )$ . Substituting $v _ { \pi _ { k } } ^ { ( 1 ) } \geq v _ { \pi _ { k } } ^ { ( 0 ) }$ into (4.5) yields $v _ { \pi _ { k } } ^ { ( j + 1 ) } \geq v _ { \pi _ { k } } ^ { ( j ) }$

Notably, Proposition 4.1 requires the assumption that $v _ { \pi _ { k } } ^ { ( 0 ) } = v _ { \pi _ { k - 1 } }$ . However, $v _ { \pi _ { k - 1 } }$ is unavailable in practice, and only $v _ { k - 1 }$ is available. Nevertheless, Proposition 4.1 still sheds light on the convergence of the truncated policy iteration algorithm. A more in-depth discussion of this topic can be found in [2, Section 6.5].

Up to now, the advantages of truncated policy iteration are clear. Compared to the policy iteration algorithm, the truncated one merely requires a finite number of iterations in the policy evaluation step and hence is more computationally efficient. Compared to value iteration, the truncated policy iteration algorithm can speed up its convergence rate by running for a few more iterations in the policy evaluation step.

## 4.4 Summary

This chapter introduced three algorithms that can be used to find optimal policies.

Value iteration: The value iteration algorithm is the same as the algorithm suggested by the contraction mapping theorem for solving the Bellman optimality equation. It can be decomposed into two steps: value update and policy update.

Policy iteration: The policy iteration algorithm is slightly more complicated than the value iteration algorithm. It also contains two steps: policy evaluation and policy improvement.

Truncated policy iteration: The value iteration and policy iteration algorithms can be viewed as two extreme cases of the truncated policy iteration algorithm.

A common property of the three algorithms is that every iteration has two steps. One step is to update the value, and the other step is to update the policy. The idea of interaction between value and policy updates widely exists in reinforcement learning algorithms. This idea is also called generalized policy iteration [3].

Finally, the algorithms introduced in this chapter require the system model. Starting in Chapter 5, we will study model-free reinforcement learning algorithms. We will see that the model-free can be obtained by extending the algorithms introduced in this chapter.

## 4.5 Q&A

Q: Is the value iteration algorithm guaranteed to find optimal policies?

A: Yes. This is because value iteration is exactly the algorithm suggested by the contraction mapping theorem for solving the Bellman optimality equation in the last chapter. The convergence of this algorithm is guaranteed by the contraction mapping theorem.

Q: Are the intermediate values generated by the value iteration algorithm state values?

A: No. These values are not guaranteed to satisfy the Bellman equation of any policy.

Q: What steps are included in the policy iteration algorithm?

A: Each iteration of the policy iteration algorithm contains two steps: policy evalu ation and policy improvement. In the policy evaluation step, the algorithm aims to solve the Bellman equation to obtain the state value of the current policy. In the policy improvement step, the algorithm aims to update the policy so that the newly generated policy has greater state values.

Q: Is another iterative algorithm embedded in the policy iteration algorithm? A: Yes. In the policy evaluation step of the policy iteration algorithm, an iterative algorithm is required to solve the Bellman equation of the current policy.

Q: Are the intermediate values generated by the policy iteration algorithm state val ues? A: Yes. This is because these values are the solutions of the Bellman equation of the current policy.

Q: Is the policy iteration algorithm guaranteed to find optimal policies? A: Yes. We have presented a rigorous proof of its convergence in this chapter.

Q: What is the relationship between the truncated policy iteration and policy iteration algorithms?

A: As its name suggests, the truncated policy iteration algorithm can be obtained from the policy iteration algorithm by simply executing a finite number of iterations during the policy evaluation step.

Q: What is the relationship between truncated policy iteration and value iteration? A: Value iteration can be viewed as an extreme case of truncated policy iteration, where a single iteration is run during the policy evaluation step.

Q: Are the intermediate values generated by the truncated policy iteration algorithm state values?

A: No. Only if we run an infinite number of iterations in the policy evaluation step, can we obtain true state values. If we run a finite number of iterations, we can only obtain approximates of the true state values.

Q: How many iterations should we run in the policy evaluation step of the truncated policy iteration algorithm?

A: The general guideline is to run a few iterations but not too many. The use of a few iterations in the policy evaluation step can speed up the overall convergence rate, but running too many iterations would not significantly speed up the convergence rate.

◇ Q: What is generalized policy iteration?

A: Generalized policy iteration is not a specific algorithm. Instead, it refers to the general idea of the interaction between value and policy updates. This idea is rooted in the policy iteration algorithm. Most of the reinforcement learning algorithms introduced in this book fall into the scope of generalized policy iteration.

Q: What are model-based and model-free reinforcement learning?

A: Although the algorithms introduced in this chapter can find optimal policies, they are usually called dynamic programming algorithms rather than reinforcement learning algorithms because they require the system model. Reinforcement learning algorithms can be classified into two categories: model-based and model-free. Here, “model-based” does not refer to the requirement of the system model. Instead, modelbased reinforcement learning uses data to estimate the system model and uses this model during the learning process. By contrast, model-free reinforcement learning does not involve model estimation during the learning process. More information about model-based reinforcement learning can be found in [13–16].
