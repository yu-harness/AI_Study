---
title: "Chapter 03 Optimal State Values and Bellman Optimality Equation"
topic: "2模型后训练"
type: note
date: 2026-11-06
---

# Chapter 3 Optimal State Values and Bellman Optimality Equation

![](2276a68f5b87a6fd1603a0a561259e94174896d05db516064a63761893a4d584.jpg)

*Figure 3.1: Where we are in this book.*

The ultimate goal of reinforcement learning is to seek optimal policies. It is, therefore, necessary to define what optimal policies are. In this chapter, we introduce a core concept and an important tool. The core concept is the optimal state value, based on which we can define optimal policies. The important tool is the Bellman optimality equation, from which we can solve the optimal state values and policies.

The relationship between the previous, present, and subsequent chapters is as follows. The previous chapter (Chapter 2) introduced the Bellman equation of any given policy.

The present chapter introduces the Bellman optimality equation, which is a special Bellman equation whose corresponding policy is optimal. The next chapter (Chapter 4) will introduce an important algorithm called value iteration, which is exactly the algorithm for solving the Bellman optimality equation as introduced in the present chapter.

Be prepared that this chapter is slightly mathematically intensive. However, it is worth it because many fundamental questions can be clearly answered.

## 3.1 Motivating example: How to improve policies?

![](14c1634ee2c0ca75efca8c16a1f6c4c830a1bff1f37f17745c49a24769c88175.jpg)

*Figure 3.2: An example for demonstrating policy improvement.*

Consider the policy shown in Figure 3.2. Here, the orange and blue cells represent the forbidden and target areas, respectively. The policy here is not good because it selects $a _ { 2 }$ (rightward) in state $s _ { 1 }$ . How can we improve the given policy to obtain a better policy? The answer lies in state values and action values.

Intuition: It is intuitively clear that the policy can improve if it selects $a _ { 3 }$ (downward) instead of $a _ { 2 }$ (rightward) at $s _ { 1 }$ . This is because moving downward enables the agent to avoid entering the forbidden area.

Mathematics: The above intuition can be realized based on the calculation of state values and action values.

First, we calculate the state values of the given policy. In particular, the Bellman equation of this policy is

$$
\begin{array}{r l} & v _ {\pi} (s _ {1}) = - 1 + \gamma v _ {\pi} (s _ {2}), \\ & v _ {\pi} (s _ {2}) = + 1 + \gamma v _ {\pi} (s _ {4}), \\ & v _ {\pi} (s _ {3}) = + 1 + \gamma v _ {\pi} (s _ {4}), \\ & v _ {\pi} (s _ {4}) = + 1 + \gamma v _ {\pi} (s _ {4}). \end{array}
$$

Let $\gamma = 0 . 9$ . It can be easily solved that

$$
\begin{array}{l} v _ {\pi} (s _ {4}) = v _ {\pi} (s _ {3}) = v _ {\pi} (s _ {2}) = 1 0, \\ v _ {\pi} (s _ {1}) = 8. \end{array}
$$

Second, we calculate the action values for state $s _ { 1 }$ :

$$
q _ {\pi} (s _ {1}, a _ {1}) = - 1 + \gamma v _ {\pi} (s _ {1}) = 6. 2,
$$

$$
q _ {\pi} (s _ {1}, a _ {2}) = - 1 + \gamma v _ {\pi} (s _ {2}) = 8,
$$

$$
q _ {\pi} (s _ {1}, a _ {3}) = 0 + \gamma v _ {\pi} (s _ {3}) = 9,
$$

$$
q _ {\pi} (s _ {1}, a _ {4}) = - 1 + \gamma v _ {\pi} (s _ {1}) = 6. 2,
$$

$$
q _ {\pi} (s _ {1}, a _ {5}) = 0 + \gamma v _ {\pi} (s _ {1}) = 7. 2.
$$

It is notable that action $a _ { 3 }$ has the greatest action value:

$$
q _ {\pi} (s _ {1}, a _ {3}) \geq q _ {\pi} (s _ {1}, a _ {i}), \quad \mathrm{forall} i \neq 3.
$$

Therefore, we can update the policy to select $a _ { 3 }$ at $s _ { 1 }$ .

This example illustrates that we can obtain a better policy if we update the policy to select the action with the greatest action value. This is the basic idea of many reinforcement learning algorithms.

This example is very simple in the sense that the given policy is only not good for state $s _ { 1 }$ . If the policy is also not good for the other states, will selecting the action with the greatest action value still generate a better policy? Moreover, whether there always exist optimal policies? What does an optimal policy look like? We will answer all of these questions in this chapter.

## 3.2 Optimal state values and optimal policies

While the ultimate goal of reinforcement learning is to obtain optimal policies, it is necessary to first define what an optimal policy is. The definition is based on state values. In particular, consider two given policies $\pi _ { 1 }$ and $\pi _ { 2 }$ . If the state value of $\pi _ { 1 }$ is greater than or equal to that of $\pi _ { 2 }$ for any state:

$$
v _ {\pi_ {1}} (s) \geq v _ {\pi_ {2}} (s), \quad \text { for   all } s \in \mathcal {S},
$$

then $\pi _ { 1 }$ is said to be better than $\pi _ { 2 }$ . Furthermore, if a policy is better than all the other possible policies, then this policy is optimal. This is formally stated below.

Definition 3.1 (Optimal policy and optimal state value). A policy $\pi ^ { * }$ is optimal if $v _ { \pi ^ { * } } ( s ) \geq v _ { \pi } ( s )$ for all $s \in S$ and for any other policy $\pi .$ . The state values $o f \pi ^ { * }$ are the optimal state values.

The above definition indicates that an optimal policy has the greatest state value for every state compared to all the other policies. This definition also leads to many questions:

◇ Existence: Does the optimal policy exist?

◇ Uniqueness: Is the optimal policy unique?

Stochasticity: Is the optimal policy stochastic or deterministic?

Algorithm: How to obtain the optimal policy and the optimal state values?

These fundamental questions must be clearly answered to thoroughly understand optimal policies. For example, regarding the existence of optimal policies, if optimal policies do not exist, then we do not need to bother to design algorithms to find them.

We will answer all these questions in the remainder of this chapter.

## 3.3 Bellman optimality equation

The tool for analyzing optimal policies and optimal state values is the Bellman optimality equation (BOE). By solving this equation, we can obtain optimal policies and optimal state values. We next present the expression of the BOE and then analyze it in detail.

For every $s \in S$ , the elementwise expression of the BOE is

$$
\begin{array}{r l} & v (s) = \max _ {\pi (s) \in \Pi (s)} \sum_ {a \in \mathcal {A}} \pi (a | s) \left(\sum_ {r \in \mathcal {R}} p (r | s, a) r + \gamma \sum_ {s ^ {\prime} \in \mathcal {S}} p (s ^ {\prime} | s, a) v (s ^ {\prime})\right) \\ & \quad = \max _ {\pi (s) \in \Pi (s)} \sum_ {a \in \mathcal {A}} \pi (a | s) q (s, a), \end{array}\tag{3.1}
$$

where $v ( s ) , v ( s ^ { \prime } )$ are unknown variables to be solved and

$$
q (s, a) \doteq \sum_ {r \in \mathcal {R}} p (r | s, a) r + \gamma \sum_ {s ^ {\prime} \in \mathcal {S}} p (s ^ {\prime} | s, a) v (s ^ {\prime}).
$$

Here, $\pi ( s )$ denotes a policy for state s, and $\Pi ( s )$ is the set of all possible policies for s.

The BOE is an elegant and powerful tool for analyzing optimal policies. However, it may be nontrivial to understand this equation. For example, this equation has two unknown variables $v ( s )$ and $\pi ( a | s )$ . It may be confusing to beginners how to solve two unknown variables from one equation. Moreover, the BOE is actually a special Bellman equation. However, it is nontrivial to see that since its expression is quite different from that of the Bellman equation. We also need to answer the following fundamental questions about the BOE.

Existence: Does this equation have a solution?

Uniqueness: Is the solution unique?

◇ Algorithm: How to solve this equation?

Optimality: How is the solution related to optimal policies?

Once we can answer these questions, we will clearly understand optimal state values and optimal policies.

### 3.3.1 Maximization of the right-hand side of the BOE

We next clarify how to solve the maximization problem on the right-hand side of the BOE in (3.1). At first glance, it may be confusing to beginners how to solve two unknown variables $v ( s )$ and $\pi ( a | s )$ from one equation. In fact, these two unknown variables can be solved one by one. This idea is illustrated by the following example.

Example 3.1. Consider two unknown variables x, $y \in \mathbb { R }$ that satisfy

$$
x = \max _ {y \in \mathbb {R}} (2 x - 1 - y ^ {2}).
$$

The first step is to solve y on the right-hand side of the equation. Regardless of the value $o f x ,$ , we always have ma $\mathrm { x } _ { y } ( 2 x - 1 - y ^ { 2 } ) = 2 x - 1$ , where the maximum is achieved when $y = 0$ . The second step is to solve x. When $y = 0$ , the equation becomes $x = 2 x - 1$ , which leads to $x = 1$ . Therefore, $y = 0$ and $x = 1$ are the solutions of the equation. □

We now turn to the maximization problem on the right-hand side of the BOE. The BOE in (3.1) can be written concisely as

$$
v (s) = \max _ {\pi (s) \in \Pi (s)} \sum_ {a \in \mathcal {A}} \pi (a | s) q (s, a), \quad s \in \mathcal {S}.
$$

Inspired by Example 3.1, we can first solve the optimal π on the right-hand side. How to do that? The following example demonstrates its basic idea.

Example 3.2. Given $q _ { 1 } , q _ { 2 } , q _ { 3 } \in \mathbb { R }$ , we would like to find the optimal values of $c _ { 1 } , c _ { 2 } , c _ { 3 }$ to maximize

$$
\sum_ {i = 1} ^ {3} c _ {i} q _ {i} = c _ {1} q _ {1} + c _ {2} q _ {2} + c _ {3} q _ {3},
$$

where $c _ { 1 } + c _ { 2 } + c _ { 3 } = 1$ and $c _ { 1 } , c _ { 2 } , c _ { 3 } \geq 0 \quad$

Without loss of generality, suppose that $q _ { 3 } \geq q _ { 1 } , q _ { 2 }$ . Then, the optimal solution is $c _ { 3 } ^ { * } = 1$ and $c _ { 1 } ^ { * } = c _ { 2 } ^ { * } = 0$ . This is because

$$
q _ {3} = (c _ {1} + c _ {2} + c _ {3}) q _ {3} = c _ {1} q _ {3} + c _ {2} q _ {3} + c _ {3} q _ {3} \geq c _ {1} q _ {1} + c _ {2} q _ {2} + c _ {3} q _ {3}
$$

for any $c _ { 1 } , c _ { 2 } , c _ { 3 }$

Inspired by the above example, since $\begin{array} { r } { \sum _ { a } \pi ( a | s ) = 1 } \end{array}$ , we have

$$
\sum_ {a \in \mathcal {A}} \pi (a | s) q (s, a) \leq \sum_ {a \in \mathcal {A}} \pi (a | s) \max _ {a \in \mathcal {A}} q (s, a) = \max _ {a \in \mathcal {A}} q (s, a),
$$

where equality is achieved when

$$
\pi (a | s) = \left\{ \begin{array}{l l} 1, & a = a ^ {*}, \\ 0, & a \neq a ^ {*}. \end{array} \right.
$$

Here, $a ^ { * } = \arg \operatorname* { m a x } _ { a } q ( s , a )$ . In summary, the optimal policy $\pi ( s )$ is the one that selects the action that has the greatest value of $q ( s , a )$

### 3.3.2 Matrix-vector form of the BOE

The BOE refers to a set of equations defined for all states. If we combine these equations, we can obtain a concise matrix-vector form, which will be extensively used in this chapter.

The matrix-vector form of the BOE is

$$
v = \max _ {\pi \in \Pi} (r _ {\pi} + \gamma P _ {\pi} v),\tag{3.2}
$$

where $v \in \mathbb { R } ^ { | s | }$ and $\mathrm { m a x } _ { \pi }$ is performed in an elementwise manner. The structures of $r _ { \pi }$ and $P _ { \pi }$ are the same as those in the matrix-vector form of the normal Bellman equation:

$$
[ r _ {\pi} ] _ {s} \doteq \sum_ {a \in \mathcal {A}} \pi (a | s) \sum_ {r \in \mathcal {R}} p (r | s, a) r, \quad [ P _ {\pi} ] _ {s, s ^ {\prime}} = p (s ^ {\prime} | s) \doteq \sum_ {a \in \mathcal {A}} \pi (a | s) p (s ^ {\prime} | s, a).
$$

Since the optimal value of $\pi$ is determined by $v ,$ the right-hand side of (3.2) is a function of $v ,$ denoted as

$$
f (v) \doteq \max _ {\pi \in \Pi} (r _ {\pi} + \gamma P _ {\pi} v).
$$

Then, the BOE can be expressed in a concise form as

$$
v = f (v).\tag{3.3}
$$

In the remainder of this section, we show how to solve this nonlinear equation.

### 3.3.3 Contraction mapping theorem

Since the BOE can be expressed as a nonlinear equation $v = f ( v )$ , we next introduce the contraction mapping theorem [6] to analyze it. The contraction mapping theorem is a powerful tool for analyzing general nonlinear equations. It is also known as the fixedpoint theorem. Readers who already know this theorem can skip this part. Otherwise, the reader is advised to be familiar with this theorem since it is the key to analyzing the

BOE.

Consider a function $f ( x )$ , where $\boldsymbol { x } \in \mathbb { R } ^ { d }$ and $f : \mathbb { R } ^ { d }  \mathbb { R } ^ { d }$ . A point $x ^ { * }$ is called a fixed point if

$$
f (x ^ {*}) = x ^ {*}.
$$

The interpretation of the above equation is that the map of $x ^ { * }$ is itself. This is the reason why $x ^ { * }$ is called “fixed”. The function f is a contraction mapping (or contractive function) if there exists $\gamma \in ( 0 , 1 )$ such that

$$
\| f (x _ {1}) - f (x _ {2}) \| \leq \gamma \| x _ {1} - x _ {2} \|
$$

for any $x _ { 1 } , x _ { 2 } \in \mathbb { R } ^ { d }$ . In this book,    denotes a vector or matrix norm.

Example 3.3. We present three examples to demonstrate fixed points and contraction mappings.

$$
\diamond x = f (x) = 0. 5 x, x \in \mathbb {R}.
$$

It is easy to verify that $x = 0$ is a fixed point since $0 = 0 . 5 \cdot 0$ . Moreover, $f ( x ) = 0 . 5 x$ is a contraction mapping because $\left\| 0 . 5 x _ { 1 } - 0 . 5 x _ { 2 } \right\| = 0 . 5 \| x _ { 1 } - x _ { 2 } \| \leq \gamma \| x _ { 1 } - x _ { 2 } \|$ for any $\gamma \in [ 0 . 5 , 1 )$ $x = f ( x ) = A x$ , where $x \in \mathbb { R } ^ { n } , A \in \mathbb { R } ^ { n \times n }$ and $\| A \| \leq \gamma < 1$

It is easy to verify that $x = 0$ is a fixed point since $0 = A 0$ . To see the contraction property, $\| A x _ { 1 } - A x _ { 2 } \| = \| A ( x _ { 1 } - x _ { 2 } ) \| \leq \| A \| \| x _ { 1 } - x _ { 2 } \| \leq \gamma \| x _ { 1 } - x _ { 2 } \|$ . Therefore, $f ( x ) = A x$ is a contraction mapping.

$x = f ( x ) = 0 . 5 \sin x , x \in \mathbb { R } .$

It is easy to see that $x = 0$ is a fixed point since $0 = 0 . 5 \sin { 0 }$ . Moreover, it follows from the mean value theorem $[ \gamma , 8 ]$ that

$$
\left| \frac {0 . 5 \sin x _ {1} - 0 . 5 \sin x _ {2}}{x _ {1} - x _ {2}} \right| = | 0. 5 \cos x _ {3} | \leq 0. 5, \quad x _ {3} \in [ x _ {1}, x _ {2} ].
$$

As a result, 0.5 sin $x _ { 1 } - 0 . 5$ sin $x _ { 2 } | \le 0 . 5 | x _ { 1 } - x _ { 2 } |$ and hence $f ( x ) = 0 . 5$ sin x is a contraction mapping. □

The relationship between a fixed point and the contraction property is characterized by the following classic theorem.

Theorem 3.1 (Contraction mapping theorem). For any equation that has the form $x =$ $f ( x )$ where x and $f ( x )$ are real vectors, if f is a contraction mapping, then the following properties hold.

◇ Existence: There exists a fixed point x∗ satisfying $f ( x ^ { * } ) = x ^ { * }$

◇ Uniqueness: The fixed point $x ^ { * }$ is unique.

◇ Algorithm: Consider the iterative process:

$$
x _ {k + 1} = f (x _ {k}),
$$

where $k = 0 , 1 , 2 , \ldots .$ Then, $x _ { k } \to x ^ { * }$ as $k  \infty$ for any initial guess $x _ { 0 }$ . Moreover, the convergence rate is exponentially fast.

The contraction mapping theorem not only can tell whether the solution of a nonlinear equation exists but also suggests a numerical algorithm for solving the equation. The proof of the theorem is given in Box 3.1.

The following example demonstrates how to calculate the fixed points of some equations using the iterative algorithm suggested by the contraction mapping theorem.

Example 3.4. Let us revisit the abovementioned examples: $x = 0 . 5 x , x = A x _ { 1 }$ , and $x = 0 . 5 \sin { x }$ . While it has been shown that the right-hand sides of these three equations are all contraction mappings, it follows from the contraction mapping theorem that they each have a unique fixed point, which can be easily verified to be $x ^ { * } = 0$ . Moreover, the fixed points of the three equations can be iteratively solved by the following algorithms:

$$
\begin{array}{l} {x _ {k + 1} = 0. 5 x _ {k},} \\ {x _ {k + 1} = A x _ {k},} \\ {x _ {k + 1} = 0. 5 \sin x _ {k},} \end{array}
$$

given any initial guess $x _ { 0 }$

### Box 3.1: Proof of the contraction mapping theorem

Part 1: We prove that the sequence $\{ x _ { k } \} _ { k = 1 } ^ { \infty }$ with $x _ { k } = f ( x _ { k - 1 } )$ is convergent.

The proof relies on Cauchy sequences. A sequence $x _ { 1 } , x _ { 2 } , \cdots \in \mathbb { R }$ is called Cauchy if for any small $\varepsilon > 0$ there exists N such that $\| x _ { m } - x _ { n } \| < \varepsilon$ for all $m , n > N$ The intuitive interpretation is that there exists a finite integer N such that all the elements after N are suficiently close to each other. Cauchy sequences are important because it is guaranteed that a Cauchy sequence converges to a limit. Its convergence property will be used to prove the contraction mapping theorem. Note that we must have $\| x _ { m } - x _ { n } \| < \varepsilon$ for all $m , n \ > \ N$ If we simply have $x _ { n + 1 } - x _ { n } \to 0$ it is insuficient to claim that the sequence is a Cauchy sequence. For example, it holds that $x _ { n + 1 } - x _ { n } \to 0$ for $x _ { n } = { \sqrt { n } }$ , but apparently, $x _ { n } = { \sqrt { n } }$ diverges.

We next show that $\{ x _ { k } = f ( x _ { k - 1 } ) \} _ { k = 1 } ^ { \infty }$ is a Cauchy sequence and hence converges.

First, since f is a contraction mapping, we have

$$
\| x _ {k + 1} - x _ {k} \| = \| f (x _ {k}) - f (x _ {k - 1}) \| \leq \gamma \| x _ {k} - x _ {k - 1} \|.
$$

Similarly, we have $\| x _ { k } - x _ { k - 1 } \| \leq \gamma \| x _ { k - 1 } - x _ { k - 2 } \| , \ldots , \| x _ { 2 } - x _ { 1 } \| \leq \gamma \| x _ { 1 } - x _ { 0 } \|$ . Thus, we have

$$
\begin{array}{r l} & {\| x _ {k + 1} - x _ {k} \| \leq \gamma \| x _ {k} - x _ {k - 1} \|} \\ & {\qquad \leq \gamma^ {2} \| x _ {k - 1} - x _ {k - 2} \|} \\ & {\qquad \vdots} \\ & {\qquad \leq \gamma^ {k} \| x _ {1} - x _ {0} \|.} \end{array}
$$

Since $\gamma < 1$ , we know that $\| x _ { k + 1 } - x _ { k } \|$ converges to zero exponentially fast as $k \to \infty$ given any $x _ { 1 } , x _ { 0 }$ Notably, the convergence of $\{ \| x _ { k + 1 } - x _ { k } \| \}$ is not sufficient for implying the convergence of $\{ x _ { k } \}$ Therefore, we need to further consider $\| x _ { m } - x _ { n } \|$ for any $m > n$ . In particular,

$$
\begin{array}{r l} & {\| x _ {m} - x _ {n} \| = \| x _ {m} - x _ {m - 1} + x _ {m - 1} - \dots - x _ {n + 1} + x _ {n + 1} - x _ {n} \|} \\ & {\qquad \leq \| x _ {m} - x _ {m - 1} \| + \dots + \| x _ {n + 1} - x _ {n} \|} \\ & {\qquad \leq \gamma^ {m - 1} \| x _ {1} - x _ {0} \| + \dots + \gamma^ {n} \| x _ {1} - x _ {0} \|} \\ & {\qquad = \gamma^ {n} (\gamma^ {m - 1 - n} + \dots + 1) \| x _ {1} - x _ {0} \|} \\ & {\qquad \leq \gamma^ {n} (1 + \dots + \gamma^ {m - 1 - n} + \gamma^ {m - n} + \gamma^ {m - n + 1} + \ldots) \| x _ {1} - x _ {0} \|} \\ & {\qquad = \frac {\gamma^ {n}}{1 - \gamma} \| x _ {1} - x _ {0} \|.} \end{array}\tag{3.4}
$$

As a result, for any ε, we can always find N such that $\| x _ { m } - x _ { n } \| < \varepsilon$ for all m, $n > N$ Therefore, this sequence is Cauchy and hence converges to a limit point denoted as $x ^ { * } = \operatorname* { l i m } _ { k \to \infty } x _ { k }$

Part 2: We show that the limit $x ^ { * } = \operatorname* { l i m } _ { k \to \infty } x _ { k }$ is a fixed point. To do that, since

$$
\| f (x _ {k}) - x _ {k} \| = \| x _ {k + 1} - x _ {k} \| \leq \gamma^ {k} \| x _ {1} - x _ {0} \|,
$$

we know that $\| f ( x _ { k } ) - x _ { k } \|$ converges to zero exponentially fast. Hence, we have $f ( x ^ { * } ) = x ^ { * }$ at the limit.

Part 3: We show that the fixed point is unique. Suppose that there is another fixed point $x ^ { \prime }$ satisfying $f ( x ^ { \prime } ) = x ^ { \prime }$ . Then,

$$
\| x ^ {\prime} - x ^ {*} \| = \| f (x ^ {\prime}) - f (x ^ {*}) \| \leq \gamma \| x ^ {\prime} - x ^ {*} \|.
$$

Since $\gamma < 1$ , this inequality holds if and only if $\| x ^ { \prime } - x ^ { * } \| = 0$ Therefore, $x ^ { \prime } = x ^ { \ast }$ Part 4: We show that $x _ { k }$ converges to $x ^ { * }$ exponentially fast. Recall that $\Vert x _ { m } -$ $\textstyle x _ { n } \| \leq { \frac { \gamma ^ { n } } { 1 - \gamma } } \| x _ { 1 } - x _ { 0 } \|$ , as proven in (3.4). Since m can be arbitrarily large, we have

$$
\| x ^ {*} - x _ {n} \| = \lim _ {m \to \infty} \| x _ {m} - x _ {n} \| \leq \frac {\gamma^ {n}}{1 - \gamma} \| x _ {1} - x _ {0} \|.
$$

Since $\gamma < 1$ , the error converges to zero exponentially fast as $n \to \infty$

### 3.3.4 Contraction property of the right-hand side of the BOE

We next show that $f ( v )$ in the BOE in (3.3) is a contraction mapping. Thus, the contraction mapping theorem introduced in the previous subsection can be applied.

Theorem 3.2 (Contraction property of $f ( v ) )$ . The function $f ( v )$ on the right-hand side of the BOE in (3.3) is a contraction mapping. In particular, for any $v _ { 1 } , v _ { 2 } \in \mathbb { R } ^ { | S | }$ , it holds that

$$
\| f (v _ {1}) - f (v _ {2}) \| _ {\infty} \leq \gamma \| v _ {1} - v _ {2} \| _ {\infty},
$$

where $\gamma \in \mathsf { ( 0 , 1 ) }$ is the discount rate, and $\| \cdot \| _ { \infty }$ is the maximum norm, which is the maximum absolute value of the elements of a vector.

The proof of the theorem is given in Box 3.2. This theorem is important because we can use the powerful contraction mapping theorem to analyze the BOE.

### Box 3.2: Proof of Theorem 3.2

Consider any two vectors $v _ { 1 } , v _ { 2 } \in \mathbb { R } ^ { | S | }$ , and suppose that $\pi _ { 1 } ^ { * } \doteq \arg \operatorname* { m a x } _ { \pi } ( r _ { \pi } + \gamma P _ { \pi } v _ { 1 } )$ and $\pi _ { 2 } ^ { * } \doteq \arg \operatorname* { m a x } _ { \pi } ( r _ { \pi } + \gamma P _ { \pi } v _ { 2 } )$ . Then,

$$
f (v _ {1}) = \max _ {\pi} (r _ {\pi} + \gamma P _ {\pi} v _ {1}) = r _ {\pi_ {1} ^ {*}} + \gamma P _ {\pi_ {1} ^ {*}} v _ {1} \geq r _ {\pi_ {2} ^ {*}} + \gamma P _ {\pi_ {2} ^ {*}} v _ {1},
$$

$$
f (v _ {2}) = \max _ {\pi} (r _ {\pi} + \gamma P _ {\pi} v _ {2}) = r _ {\pi_ {2} ^ {*}} + \gamma P _ {\pi_ {2} ^ {*}} v _ {2} \geq r _ {\pi_ {1} ^ {*}} + \gamma P _ {\pi_ {1} ^ {*}} v _ {2},
$$

where $\geq$ is an elementwise comparison. As a result,

$$
\begin{array}{r l} & f (v _ {1}) - f (v _ {2}) = r _ {\pi_ {1} ^ {*}} + \gamma P _ {\pi_ {1} ^ {*}} v _ {1} - (r _ {\pi_ {2} ^ {*}} + \gamma P _ {\pi_ {2} ^ {*}} v _ {2}) \\ & \qquad \leq r _ {\pi_ {1} ^ {*}} + \gamma P _ {\pi_ {1} ^ {*}} v _ {1} - (r _ {\pi_ {1} ^ {*}} + \gamma P _ {\pi_ {1} ^ {*}} v _ {2}) \\ & \qquad = \gamma P _ {\pi_ {1} ^ {*}} (v _ {1} - v _ {2}). \end{array}
$$

Similarly, it can be shown that $f ( v _ { 2 } ) - f ( v _ { 1 } ) \leq \gamma P _ { \pi _ { 2 } ^ { * } } ( v _ { 2 } - v _ { 1 } )$ . Therefore,

$$
\gamma P _ {\pi_ {2} ^ {*}} (v _ {1} - v _ {2}) \leq f (v _ {1}) - f (v _ {2}) \leq \gamma P _ {\pi_ {1} ^ {*}} (v _ {1} - v _ {2}).
$$

Define

$$
z \doteq \max \left\{| \gamma P _ {\pi_ {2} ^ {*}} (v _ {1} - v _ {2}) |, | \gamma P _ {\pi_ {1} ^ {*}} (v _ {1} - v _ {2}) | \right\} \in \mathbb {R} ^ {| \mathcal {S} |},
$$

where max $( \cdot ) , | \cdot |$ , and $\geq$ are all elementwise operators. By definition, $z \geq 0$ . On the one hand, it is easy to see that

$$
- z \leq \gamma P _ {\pi_ {2} ^ {*}} (v _ {1} - v _ {2}) \leq f (v _ {1}) - f (v _ {2}) \leq \gamma P _ {\pi_ {1} ^ {*}} (v _ {1} - v _ {2}) \leq z,
$$

which implies

$$
| f (v _ {1}) - f (v _ {2}) | \leq z.
$$

It then follows that

$$
\| f (v _ {1}) - f (v _ {2}) \| _ {\infty} \leq \| z \| _ {\infty},\tag{3.5}
$$

where $\| \cdot \| _ { \infty }$ is the maximum norm.

On the other hand, suppose that $z _ { i }$ is the ith entry of $z ,$ and $p _ { i } ^ { T }$ and $q _ { i } ^ { T }$ are the ith row of $P _ { \pi _ { 1 } ^ { * } }$ and $P _ { \pi _ { 2 } ^ { * } }$ , respectively. Then,

$$
z _ {i} = \max \{\gamma | p _ {i} ^ {T} (v _ {1} - v _ {2}) |, \gamma | q _ {i} ^ {T} (v _ {1} - v _ {2}) | \}.
$$

Since $p _ { i }$ is a vector with all nonnegative elements and the sum of the elements is equal to one, it follows that

$$
| p _ {i} ^ {T} (v _ {1} - v _ {2}) | \leq p _ {i} ^ {T} | v _ {1} - v _ {2} | \leq \| v _ {1} - v _ {2} \| _ {\infty}.
$$

Similarly, we have $| q _ { i } ^ { T } ( v _ { 1 } - v _ { 2 } ) | \leq \| v _ { 1 } - v _ { 2 } \| _ { \infty }$ . Therefore, $z _ { i } \leq \gamma \| v _ { 1 } - v _ { 2 } \| _ { \infty }$ and hence

$$
\| z \| _ {\infty} = \max _ {i} | z _ {i} | \leq \gamma \| v _ {1} - v _ {2} \| _ {\infty}.
$$

Substituting this inequality to (3.5) gives

$$
\| f (v _ {1}) - f (v _ {2}) \| _ {\infty} \leq \gamma \| v _ {1} - v _ {2} \| _ {\infty},
$$

which concludes the proof of the contraction property of $f ( v )$

## 3.4 Solving an optimal policy from the BOE

With the preparation in the last section, we are ready to solve the BOE to obtain the optimal state value $v ^ { * }$ and an optimal policy $\pi ^ { * }$

Solving $v ^ { * } \colon \mathrm { H } \mathrm { \Lambda } v ^ { * }$ is a solution of the BOE, then it satisfies

$$
v ^ {*} = \max _ {\pi \in \Pi} (r _ {\pi} + \gamma P _ {\pi} v ^ {*}).
$$

Clearly, $v ^ { * }$ is a fixed point because $v ^ { * } = f ( v ^ { * } )$ . Then, the contraction mapping theorem suggests the following results.

Theorem 3.3 (Existence, uniqueness, and algorithm). For the BOE $v = f ( v ) = $ $\mathrm { m a x } _ { \pi \in \Pi } ( r _ { \pi } + \gamma P _ { \pi } v )$ , there always exists a unique solution $v ^ { * }$ , which can be solved iteratively by

$$
v _ {k + 1} = f (v _ {k}) = \max _ {\pi \in \Pi} (r _ {\pi} + \gamma P _ {\pi} v _ {k}), \quad k = 0, 1, 2, \ldots .
$$

The value of $v _ { k }$ converges to $v ^ { * }$ exponentially fast as $k  \infty$ given any initial guess $v _ { 0 }$

The proof of this theorem directly follows from the contraction mapping theorem since $f ( v )$ is a contraction mapping. This theorem is important because it answers some fundamental questions.

- Existence of $v ^ { * }$ : The solution of the BOE always exists.

- Uniqueness of $v ^ { * } { \mathrm { . } }$ The solution $v ^ { * }$ is always unique.

- Algorithm for solving $v ^ { * } \colon$ The value of $v ^ { * }$ can be solved by the iterative algorithm suggested by Theorem 3.3. This iterative algorithm has a specific name called value iteration. Its implementation will be introduced in detail in Chapter 4. We mainly focus on the fundamental properties of the BOE in the present chapter.

Solving $\pi ^ { * }$ : Once the value of $v ^ { * }$ has been obtained, we can easily obtain $\pi ^ { * }$ by solving

$$
\pi^ {*} = \arg \max _ {\pi \in \Pi} (r _ {\pi} + \gamma P _ {\pi} v ^ {*}).\tag{3.6}
$$

The value of $\pi ^ { * }$ will be given in Theorem 3.5. Substituting (3.6) into the BOE yields

$$
v ^ {*} = r _ {\pi^ {*}} + \gamma P _ {\pi^ {*}} v ^ {*}.
$$

Therefore, $v ^ { * } = v _ { \pi }$ ∗ is the state value of $\pi ^ { * }$ , and the BOE is a special Bellman equation whose corresponding policy is $\pi ^ { * }$

At this point, although we can solve $v ^ { * }$ and $\pi ^ { * }$ , it is still unclear whether the solution is optimal. The following theorem reveals the optimality of the solution.

Theorem 3.4 (Optimality of $v ^ { * }$ and $\pi ^ { * } )$ . The solution $v ^ { * }$ is the optimal state value, and $\pi ^ { * }$ is an optimal policy. That is, for any policy $\pi _ { \perp }$ , it holds that

$$
v ^ {*} = v _ {\pi^ {*}} \geq v _ {\pi},
$$

where $v _ { \pi }$ is the state value of $\pi$ , and $\geq i s$ an elementwise comparison.

Now, it is clear why we must study the BOE: its solution corresponds to optimal state values and optimal policies. The proof of the above theorem is given in the following box.

### Box 3.3: Proof of Theorem 3.4
For any policy π, it holds that $v_{\pi} = r_{\pi} + \gamma P_{\pi}v_{\pi}.$ Since $v^{*}=\max_{\pi}(r_{\pi}+\gamma P_{\pi}v^{*})=r_{\pi^{*}}+\gamma P_{\pi^{*}}v^{*}\geq r_{\pi}+\gamma P_{\pi}v^{*},$ we have $v^{*}-v_{\pi}\geq(r_{\pi}+\gamma P_{\pi}v^{*})-(r_{\pi}+\gamma P_{\pi}v_{\pi})=\gamma P_{\pi}(v^{*}-v_{\pi}).$ Repeatedly applying the above inequality gives $v^{*}-v_{\pi}\geq\gamma P_{\pi}(v^{*}-v_{\pi})\geq\gamma^{2}P_{\pi}^{2}(v^{*}-v_{\pi})\geq\cdots\geq\gamma^{n}P_{\pi}^{n}(v^{*}-v_{\pi})$ . It follows that $v^{*}-v_{\pi}\geq\lim_{n\to\infty}\gamma^{n}P_{\pi}^{n}(v^{*}-v_{\pi})=0,$ where the last equality is true because γ<1 and $P_{\pi}^{n}$ is a nonnegative matrix with all its elements less than or equal to 1 (because $P_{\pi}^{n}1=1$ ). Therefore, $v^{*}\geq v_{\pi}$ for any $\pi$ .

We next examine $\pi ^ { * }$ in (3.6) more closely. In particular, the following theorem shows that there always exists a deterministic greedy policy that is optimal.

Theorem 3.5 (Greedy optimal policy). For any $s \in S$ , the deterministic greedy policy

$$
\pi^ {*} (a | s) = \left\{ \begin{array}{l l} 1, & a = a ^ {*} (s), \\ 0, & a \neq a ^ {*} (s), \end{array} \right.\tag{3.7}
$$

is an optimal policy for solving the BOE. Here,

$$
a ^ {*} (s) = \arg \max _ {a} q ^ {*} (a, s),
$$

where

$$
q ^ {*} (s, a) \doteq \sum_ {r \in \mathcal {R}} p (r | s, a) r + \gamma \sum_ {s ^ {\prime} \in \mathcal {S}} p (s ^ {\prime} | s, a) v ^ {*} (s ^ {\prime}).
$$

### Box 3.4: Proof of Theorem 3.5

While the matrix-vector form of the optimal policy is $\pi ^ { * } = \arg \operatorname* { m a x } _ { \pi } ( r _ { \pi } + \gamma P _ { \pi } v ^ { * } )$ , its elementwise form is

$$
\pi^ {*} (s) = \arg \max _ {\pi \in \Pi} \sum_ {a \in \mathcal {A}} \pi (a | s) \underbrace {\left(\sum_ {r \in \mathcal {R}} p (r | s , a) r + \gamma \sum_ {s ^ {\prime} \in \mathcal {S}} p (s ^ {\prime} | s , a) v ^ {*} (s ^ {\prime})\right)} _ {q ^ {*} (s, a)}, \quad s \in \mathcal {S}.
$$

It is clear that $\textstyle \sum _ { a \in { \mathcal { A } } } \pi ( a | s ) q ^ { * } ( s , a )$ is maximized if $\pi ( s )$ selects the action with the greatest $\boldsymbol q ^ { * } ( s , a )$

The policy in (3.7) is called greedy because it seeks the actions with the greatest $\boldsymbol q ^ { * } ( s , a )$ . Finally, we discuss two important properties of $\pi ^ { * }$

Uniqueness of optimal policies: Although the value of $v ^ { * }$ is unique, the optimal policy that corresponds to $v ^ { * }$ may not be unique. This can be easily verified by counterexamples. For example, the two policies shown in Figure 3.3 are both optimal.

Stochasticity of optimal policies: An optimal policy can be either stochastic or deterministic, as demonstrated in Figure 3.3. However, it is certain that there always exists a deterministic optimal policy according to Theorem 3.5.

![](c3aeafd462fe2fe408a238d5972e7bba80327d0f6cc3a51a1348ef324672e65e.jpg)

![](7178a20fdc4bbf2d01fb37d325ed413e1f2826191ef320551535d407dc1404b5.jpg)

*Figure 3.3: Examples for demonstrating that optimal policies may not be unique. The two policies are different but are both optimal.*

## 3.5 Factors that influence optimal policies

The BOE is a powerful tool for analyzing optimal policies. We next apply the BOE to study what factors can influence optimal policies. This question can be easily answered by observing the elementwise expression of the BOE:

$$
v (s) = \max _ {\pi (s) \in \Pi (s)} \sum_ {a \in \mathcal {A}} \pi (a | s) \left(\sum_ {r \in \mathcal {R}} p (r | s, a) r + \gamma \sum_ {s ^ {\prime} \in \mathcal {S}} p (s ^ {\prime} | s, a) v (s ^ {\prime})\right), \quad s \in \mathcal {S}.
$$

The optimal state value and optimal policy are determined by the following parameters: 1) the immediate reward $r , \ 2 )$ the discount rate $\gamma ,$ and 3) the system model $p ( s ^ { \prime } | s , a ) , p ( r | s , a )$ . While the system model is fixed, we next discuss how the optimal policy varies when we change the values of $r$ and $\gamma .$ . All the optimal policies presented in this section can be obtained via the algorithm in Theorem 3.3. The implementation details of the algorithm will be given in Chapter 4. The present chapter mainly focuses on the fundamental properties of optimal policies.

### A baseline example

Consider the example in Figure 3.4. The reward settings are $r _ { \mathrm { b o u n d a r y } } = r _ { \mathrm { f o r b i d d e n } } = - 1$ and $r _ { \mathrm { t a r g e t } } = 1$ . In addition, the agent receives a reward of $r _ { \mathrm { o t h e r } } = 0$ for every movement step. The discount rate is selected as $\gamma = 0 . 9$

With the above parameters, the optimal policy and optimal state values are given in Figure 3.4(a). It is interesting that the agent is not afraid of passing through forbidden areas to reach the target area. More specifically, starting from the state at (row=4, column=1), the agent has two options for reaching the target area. The first option is to avoid all the forbidden areas and travel a long distance to the target area. The second option is to pass through forbidden areas. Although the agent obtains negative rewards when entering forbidden areas, the cumulative reward of the second trajectory is greater than that of the first trajectory. Therefore, the optimal policy is far-sighted due to the relatively large value of $\gamma$

### Impact of the discount rate

If we change the discount rate from $\gamma = 0 . 9 \mathrm { \ t o \ } \gamma = 0 . 5$ and keep other parameters unchanged, the optimal policy becomes the one shown in Figure 3.4(b). It is interesting that the agent does not dare to take risks anymore. Instead, it would travel a long distance to reach the target while avoiding all the forbidden areas. This is because the optimal policy becomes short-sighted due to the relatively small value of $\gamma$ .

In the extreme case where $\gamma ~ = ~ 0$ , the corresponding optimal policy is shown in Figure 3.4(c). In this case, the agent is not able to reach the target area. This is

![](50e6268afbd560be6b742dd27f5882772e227841877b85db17adfd47249b676c.jpg)

![](a89723eed9ed94afa7778f605ab2dc81ef241587bd516ec4f7e9ddebc0fd7ae4.jpg)

(a) Baseline example: rboundary = rforbidden = −1, rtarget = 1, γ = 0.9.

![](6a7e0920078b36f22634bf77a0610069fdf34d69aa667f2d7861697ccca14855.jpg)

$$
\begin{array}{c c c c c} & 1 & 2 & 3 & 4 & 5 \\ \hline 1 & 0. 0 & 0. 0 & 0. 0 & 0. 0 & 0. 0 \\ \hline 2 & 0. 0 & 0. 0 & 0. 0 & 0. 0 & 0. 1 \\ \hline 3 & 0. 0 & 0. 0 & 2. 0 & 0. 1 & 0. 1 \\ \hline 4 & 0. 0 & 2. 0 & 2. 0 & 2. 0 & 0. 2 \\ \hline 5 & 0. 0 & 1. 0 & 2. 0 & 1. 0 & 0. 5 \end{array}
$$

(b) The discount rate is changed to γ = 0.5. The other parameters are the same as those in (a).

![](5bd8884dd000150e4cd574ab52b2fc965a6cef78bb055a9d13ee386f2b16b28e.jpg)

$$
\begin{array}{c c c c c} & 1 & 2 & 3 & 4 & 5 \\ \hline 1 & 0. 0 & 0. 0 & 0. 0 & 0. 0 & 0. 0 \\ \hline 2 & 0. 0 & 0. 0 & 0. 0 & 0. 0 & 0. 0 \\ \hline 3 & 0. 0 & 0. 0 & 1. 0 & 0. 0 & 0. 0 \\ \hline 4 & 0. 0 & 1. 0 & 1. 0 & 1. 0 & 0. 0 \\ \hline 5 & 0. 0 & 0. 0 & 1. 0 & 0. 0 & 0. 0 \end{array}
$$

(c) The discount rate is changed to γ = 0. The other parameters are the same as those in (a).

![](ee8d3acef391bb75a0300961f16162fbf78b6ca16e359966d6ab810116a1e404.jpg)

|  | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| 1 | 3.5 | 3.9 | 4.3 | 4.8 | 5.3 |
| 2 | 3.1 | 3.5 | 4.8 | 5.3 | 5.9 |
| 3 | 2.8 | 2.5 | 10.0 | 5.9 | 6.6 |
| 4 | 2.5 | 10.0 | 10.0 | 10.0 | 7.3 |
| 5 | 2.3 | 9.0 | 10.0 | 9.0 | 8.1 |

(d) r is changed from 1 to 10. The other parameters are the same as those in (a).

*Figure 3.4: The optimal policies and optimal state values given different parameter values. because the optimal policy for each state is extremely short-sighted and merely selects the action with the greatest immediate reward instead of the greatest total reward.*

In addition, the spatial distribution of the state values exhibits an interesting pattern: the states close to the target have greater state values, whereas those far away have lower values. This pattern can be observed from all the examples shown in Figure 3.4. It can be explained by using the discount rate: if a state must travel along a longer trajectory to reach the target, its state value is smaller due to the discount rate.

### Impact of the reward values

If we want to strictly prohibit the agent from entering any forbidden area, we can increase the punishment received for doing so. For instance, if $r _ { \mathrm { f o r b i d d e n } }$ is changed from 1 to 10, the resulting optimal policy can avoid all the forbidden areas (see Figure 3.4(d)).

However, changing the rewards does not always lead to different optimal policies. One important fact is that optimal policies are invariant to afine transformations of the rewards. In other words, if we scale all the rewards or add the same value to all the rewards, the optimal policy remains the same.

Theorem 3.6 (Optimal policy invariance). Consider a Markov decision process with $v ^ { * } \in \mathbb { R } ^ { | s | }$ as the optimal state value satisfying $v ^ { * } = \mathrm { m a x } _ { \pi \in \Pi } ( r _ { \pi } + \gamma P _ { \pi } v ^ { * } )$ . If every reward $r \in \mathcal { R }$ is changed by an afine transformation to $\alpha r + \beta _ { \cdot }$ , where $\alpha , \beta \in \mathbb { R }$ and $\alpha > 0$ , then the corresponding optimal state value $v ^ { \prime }$ is also an afine transformation of $v ^ { * }$ :

$$
v ^ {\prime} = \alpha v ^ {*} + \frac {\beta}{1 - \gamma} \mathbf {1},\tag{3.8}
$$

where $\gamma \in ( 0 , 1 )$ is the discount rate and $\mathbf { 1 } = [ 1 , \dots , 1 ] ^ { T }$ . Consequently, the optimal policy derived from $v ^ { \prime }$ is invariant to the afine transformation of the reward values.

### Box 3.5: Proof of Theorem 3.6

For any policy $\pi ,$ define $\boldsymbol { r } _ { \pi } = [ . . . , r _ { \pi } ( s ) , . . . ] ^ { T }$ where

$$
r _ {\pi} (s) = \sum_ {a \in \mathcal {A}} \pi (a | s) \sum_ {r \in \mathcal {R}} p (r | s, a) r, \quad s \in \mathcal {S}.
$$

If $r  \alpha r + \beta _ { \mathrm { { \scriptsize ~ \cdot ~ } } }$ , then $r _ { \pi } ( s ) \to \alpha r _ { \pi } ( s ) + \beta$ and hence $r _ { \pi }  \alpha r _ { \pi } + \beta { \bf 1 }$ , where ${ \textbf { 1 } } =$ $[ 1 , \ldots , 1 ] ^ { T }$ . In this case, the BOE becomes

$$
v ^ {\prime} = \max _ {\pi \in \Pi} (\alpha r _ {\pi} + \beta \mathbf {1} + \gamma P _ {\pi} v ^ {\prime}).\tag{3.9}
$$

We next solve the new BOE in (3.9) by showing that $v ^ { \prime } = \alpha v ^ { * } +$ c1 with $c = \beta / ( 1 - \gamma )$ is a solution of (3.9). In particular, substituting $v ^ { \prime } = \alpha v ^ { * } + c \mathbf { 1 }$ into (3.9) gives

$$
\alpha v ^ {*} + c \mathbf {1} = \max _ {\pi \in \Pi} (\alpha r _ {\pi} + \beta \mathbf {1} + \gamma P _ {\pi} (\alpha v ^ {*} + c \mathbf {1})) = \max _ {\pi \in \Pi} (\alpha r _ {\pi} + \beta \mathbf {1} + \alpha \gamma P _ {\pi} v ^ {*} + c \gamma \mathbf {1}),
$$

where the last equality is due to the fact that $P _ { \pi } { \bf 1 } = { \bf 1 }$ . The above equation can be reorganized as

$$
\alpha v ^ {*} = \max _ {\pi \in \Pi} (\alpha r _ {\pi} + \alpha \gamma P _ {\pi} v ^ {*}) + \beta \mathbf {1} + c \gamma \mathbf {1} - c \mathbf {1},
$$

which is equivalent to

$$
\beta \mathbf {1} + c \gamma \mathbf {1} - c \mathbf {1} = 0.
$$

Since $c = \beta / ( 1 - \gamma )$ , the above equation is valid and hence $v ^ { \prime } = \alpha v ^ { * } + c \mathbf { 1 }$ is the solution of (3.9). Since (3.9) is the BOE, $v ^ { \prime }$ is also the unique solution. Finally, since $v ^ { \prime }$ is an afine transformation of $v ^ { * }$ , the relative relationships between the action values remain the same. Hence, the greedy optimal policy derived from $v ^ { \prime }$ is the same as that from $v ^ { * } \colon$ arg $\begin{array} { r } { \operatorname* { m a x } _ { \pi \in \Pi } ( r _ { \pi } + \gamma P _ { \pi } v ^ { \prime } ) } \end{array}$ is the same as arg max<sub>π</sub> $. ( r _ { \pi } + \gamma P _ { \pi } v ^ { * } )$

Readers may refer to [9] for a further discussion on the conditions under which modifications to the reward values preserve the optimal policy.

### Avoiding meaningless detours

In the reward setting, the agent receives a reward of $r _ { \mathrm { o t h e r } } ~ = ~ 0$ for every movement step (unless it enters a forbidden area or the target area or attempts to go beyond the boundary). Since a zero reward is not a punishment, would the optimal policy take meaningless detours before reaching the target? Should we set $r _ { \mathrm { o t h e r } }$ to be negative to encourage the agent to reach the target as quickly as possible?

![](4490b4292fadc50ca6674e5b0e05addec58476a3f09c83a27b3e94f62b21b587.jpg)

(a) Optimal policy

![](fa984f938987b2f1d5114ba9b7fefba4937a2b32cf8dbf0ac55733653c3568a7.jpg)

(b) Non-optimal policy

*Figure 3.5: Examples illustrating that optimal policies do not take meaningless detours due to the discount rate.*

Consider the examples in Figure 3.5, where the bottom-right cell is the target area to reach. The two policies here are the same except for state $s _ { 2 }$ . By the policy in Figure 3.5(a), the agent moves downward at $s _ { 2 }$ and the resulting trajectory is $s _ { 2 }  s _ { 4 }$ By the policy in Figure 3.5(b), the agent moves leftward and the resulting trajectory is $s _ { 2 }  s _ { 1 }  s _ { 3 }  s _ { 4 }$

It is notable that the second policy takes a detour before reaching the target area. If we merely consider the immediate rewards, taking this detour does not matter because no negative immediate rewards will be obtained. However, if we consider the discounted return, then this detour matters. In particular, for the first policy, the discounted return is

$$
\mathrm{return} = 1 + \gamma 1 + \gamma^ {2} 1 + \dots = 1 / (1 - \gamma) = 1 0.
$$

As a comparison, the discounted return for the second policy is

$$
\mathrm{return} = 0 + \gamma 0 + \gamma^ {2} 1 + \gamma^ {3} 1 + \dots = \gamma^ {2} / (1 - \gamma) = 8. 1.
$$

It is clear that the shorter the trajectory is, the greater the return is. Therefore, although the immediate reward of every step does not encourage the agent to approach the target as quickly as possible, the discount rate does encourage it to do so.

A misunderstanding that beginners may have is that adding a negative reward $( \mathrm { e . g . } )$ 1) on top of the rewards obtained for every movement is necessary to encourage the agent to reach the target as quickly as possible. This is a misunderstanding because adding the same reward on top of all rewards is an afine transformation, which preserves the optimal policy. Moreover, optimal policies do not take meaningless detours due to the discount rate, even though a detour may not receive any immediate negative rewards.

## 3.6 Summary

The core concepts in this chapter include optimal policies and optimal state values. In particular, a policy is optimal if its state values are greater than or equal to those of any other policy. The state values of an optimal policy are the optimal state values. The BOE is the core tool for analyzing optimal policies and optimal state values. This equation is a nonlinear equation with a nice contraction property. We can apply the contraction mapping theorem to analyze this equation. It was shown that the solutions of the BOE correspond to the optimal state value and optimal policy. This is the reason why we need to study the BOE.

The contents of this chapter are important for thoroughly understanding many fundamental ideas of reinforcement learning. For example, Theorem 3.3 suggests an iterative algorithm for solving the BOE. This algorithm is exactly the value iteration algorithm that will be introduced in Chapter 4. A further discussion about the BOE can be found in [2].

## 3.7 Q&A

Q: What is the definition of optimal policies?

A: A policy is optimal if its corresponding state values are greater than or equal to any other policy.

It should be noted that this specific definition of optimality is valid only for tabular reinforcement learning algorithms. When the values or policies are approximated by functions, different metrics must be used to define optimal policies. This will become clearer in Chapters 8 and 9.

Q: Why is the Bellman optimality equation important?

A: It is important because it characterizes both optimal policies and optimal state values. Solving this equation yields an optimal policy and the corresponding optimal state value.

V Q: Is the Bellman optimality equation a Bellman equation?

A: Yes. The Bellman optimality equation is a special Bellman equation whose corresponding policy is optimal.

Q: Is the solution of the Bellman optimality equation unique?

A: The Bellman optimality equation has two unknown variables. The first unknown variable is a value, and the second is a policy. The value solution, which is the optimal state value, is unique. The policy solution, which is an optimal policy, may not be unique.

Q: What is the key property of the Bellman optimality equation for analyzing its solution?

A: The key property is that the right-hand side of the Bellman optimality equation is a contraction mapping. As a result, we can apply the contraction mapping theorem to analyze its solution.

Q: Do optimal policies exist?

A: Yes. Optimal policies always exist according to the analysis of the BOE.

Q: Are optimal policies unique?

A: No. There may exist multiple or infinite optimal policies that have the same optimal state values.

Q: Are optimal policies stochastic or deterministic?

A: An optimal policy can be either deterministic or stochastic. A nice fact is that there always exist deterministic greedy optimal policies.

Q: How to obtain an optimal policy?

A: Solving the BOE using the iterative algorithm suggested by Theorem 3.3 yields an optimal policy. The detailed implementation of this iterative algorithm will be given in Chapter 4. Notably, all the reinforcement learning algorithms introduced in this book aim to obtain optimal policies under different settings.

Q: What is the general impact on the optimal policies if we reduce the value of the discount rate?

A: The optimal policy becomes more short-sighted when we reduce the discount rate. That is, the agent does not dare to take risks even though it may obtain greater cumulative rewards afterward.

◇ Q: What happens if we set the discount rate to zero?

A: The resulting optimal policy would become extremely short-sighted. The agent would take the action with the greatest immediate reward, even though that action is not good in the long run.

Q: If we increase all the rewards by the same amount, will the optimal state value change? Will the optimal policy change?

A: Increasing all the rewards by the same amount is an afine transformation of the rewards, which would not affect the optimal policies. However, the optimal state value would increase, as shown in (3.8).

Q: If we hope that the optimal policy can avoid meaningless detours before reaching the target, should we add a negative reward to every step so that the agent reaches the target as quickly as possible?

A: First, introducing an additional negative reward to every step is an afine transformation of the rewards, which does not change the optimal policy. Second, the discount rate can automatically encourage the agent to reach the target as quickly as possible. This is because meaningless detours would increase the trajectory length and reduce the discounted return.
