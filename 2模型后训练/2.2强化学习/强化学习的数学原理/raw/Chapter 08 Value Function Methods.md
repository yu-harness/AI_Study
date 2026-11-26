---
title: "Chapter 08 Value Function Methods"
topic: "2模型后训练"
type: note
date: 2026-11-06
---

# Chapter 8 Value Function Methods

![](ff1a7f5fae0b8adc64da1e2cde93829fbd23a4232cfb4b1b431d7d5296ef3052.jpg)

*Figure 8.1: Where we are in this book.*

In this chapter, we continue to study temporal-difference learning algorithms. However, a different method is used to represent state/action values. So far in this book, state/action values have been represented by tables. The tabular method is straightforward to understand, but it is ineficient for handling large state or action spaces. To solve this problem, this chapter introduces the value function method, which has become a standard way to represent values. It is also where artificial neural networks are incorporated into reinforcement learning as function approximators. The idea of value function can also be extended to policy function, as introduced in Chapter 9.

![](bf1f9b8f9a52b6766b754b5fa22adb29aed79c55fd4bb684ca2981bda8f25352.jpg)

*Figure 8.2: An illustration of the function approximation method. The x-axis and y-axis correspond to s and ˆv(s), respectively.*

## 8.1 Value representation: From table to function

We next use an example to demonstrate the difference between the tabular and function approximation methods.

Suppose that there are n states $\{ s _ { i } \} _ { i = 1 } ^ { n }$ , whose state values are $\{ v _ { \pi } ( s _ { i } ) \} _ { i = 1 } ^ { n }$ . Here, π is a given policy. Let $\{ \hat { v } ( s _ { i } ) \} _ { i = 1 } ^ { n }$ denote the estimates of the true state values. If we use the tabular method, the estimated values can be maintained in the following table. This table can be stored in memory as an array or a vector. To retrieve or update any value, we can directly read or rewrite the corresponding entry in the table.

| State | $s_1$ | $s_2$ | $\cdots$ | $s_n$ |
| --- | --- | --- | --- | --- |
| Estimated value | $\hat{v}(s_1)$ | $\hat{v}(s_2)$ | $\cdots$ | $\hat{v}(s_n)$ |

We next show that the values in the above table can be approximated by a function. In particular, $\{ ( s _ { i } , \hat { v } ( s _ { i } ) ) \} _ { i = 1 } ^ { n }$ are shown as n points in Figure 8.2. These points can be fitted or approximated by a curve. The simplest curve is a straight line, which can be described as

$$
\hat {v} (s, w) = a s + b = \underbrace {[ s , 1 ]} _ {\phi^ {T} (s)} \underbrace {\left[ \begin{array}{c} a \\ b \end{array} \right]} _ {w} = \phi^ {T} (s) w.\tag{8.1}
$$

Here, ${ \hat { v } } ( s , w )$ is a function for approximating $v _ { \pi } ( s )$ . It is determined jointly by the state s and the parameter vector $w \in \mathbb { R } ^ { 2 } . \ \hat { v } ( s , w )$ is sometimes written as $\hat { v } _ { w } ( s )$ . Here, $\phi ( s ) \in \mathbb { R } ^ { 2 }$ is called the feature vector of s.

The first notable difference between the tabular and function approximation methods concerns how they retrieve and update a value.

How to retrieve a value: When the values are represented by a table, if we want to retrieve a value, we can directly read the corresponding entry in the table. However, when the values are represented by a function, it becomes slightly more complicated to retrieve a value. In particular, we need to input the state index s into the function and calculate the function value (Figure 8.3). For the example in (8.1), we first need to calculate the feature vector $\phi ( s )$ and then calculate $\phi ^ { T } ( s ) w$ . If the function is an artificial neural network, a forward propagation from the input to the output is needed.

![](5a21e306bae4b708b247fd65069167d7ee0c76e2bb5ce485e9cc41c66dd364bc.jpg)

*Figure 8.3: An illustration of the process for retrieving the value of s when using the function approximation method.*

The function approximation method is more efficient in terms of storage due to the way in which the state values are retrieved. Specifically, while the tabular method needs to store n values, we now only need to store a lower dimensional parameter vector w. Thus, the storage efficiency can be significantly improved. Such a benefit is, however, not free. It comes with a cost: the state values may not be accurately represented by the function. For example, a straight line is not able to accurately fit the points in Figure 8.2. That is why this method is called approximation. From a fundamental point of view, some information will certainly be lost when we use a lowdimensional vector to represent a high-dimensional dataset. Therefore, the function approximation method enhances storage efficiency by sacrificing accuracy.

How to update a value: When the values are represented by a table, if we want to update one value, we can directly rewrite the corresponding entry in the table. However, when the values are represented by a function, the way to update a value is completely different. Specifically, we must update w to change the values indirectly. How to update w to find optimal state values will be addressed in detail later.

Thanks to the way in which the state values are updated, the function approximation method has another merit: its generalization ability is stronger than that of the tabular method. The reason is as follows. When using the tabular method, we can update a value if the corresponding state is visited in an episode. The values of the states that have not been visited cannot be updated. However, when using the function approximation method, we need to update w to update the value of a state. The update of w also affects the values of some other states even though these states have not been visited. Therefore, the experience sample for one state can generalize to help estimate the values of some other states.

The above analysis is illustrated in Figure 8.4, where there are three states $\{ s _ { 1 } , s _ { 2 } , s _ { 3 } \}$

Suppose that we have an experience sample for $s _ { 3 }$ and would like to update $\hat { v } ( s _ { 3 } )$ When using the tabular method, we can only update $\hat { v } ( s _ { 3 } )$ without changing $\hat { v } ( s _ { 1 } )$ or $\hat { v } ( s _ { 2 } )$ , as shown in Figure $8 . 4 ( \mathrm { a } )$ . When using the function approximation method, updating w not only can update $\hat { v } ( s _ { 3 } )$ but also would change $\hat { v } ( s _ { 1 } )$ and $\hat { v } ( s _ { 2 } )$ , as shown in Figure $8 . 4 ( \mathrm { b } )$ . Therefore, the experience sample of $s _ { 3 }$ can help update the values of its neighboring states.

![](6cc1d3a8854089c31831376cb17b9ceacb00dd51dd437d16803a09d8c9dd600f.jpg)

(a) Tabular method: when $\hat { v } ( s _ { 3 } )$ is updated, the other values remain the same.

![](7a9a928c2c4946d870666d69860c29b17c89044ec4a487705cf0a2659cddf888.jpg)

(b) Function approximation method: when we update $\hat { v } ( s _ { 3 } )$ by changing $w ,$ the values of the neighboring states are also changed.

*Figure 8.4: An illustration of how to update the value of a state.*

We can use more complex functions that have stronger approximation abilities than straight lines. For example, consider a second-order polynomial:

$$
\hat {v} (s, w) = a s ^ {2} + b s + c = \underbrace {[ s ^ {2} , s , 1 ]} _ {\phi^ {T} (s)} \underbrace {\left[ \begin{array}{c} a \\ b \\ c \end{array} \right]} _ {w} = \phi^ {T} (s) w.\tag{8.2}
$$

We can use even higher-order polynomial curves to fit the points. As the order of the curve increases, the approximation accuracy can be improved, but the dimension of the parameter vector also increases, requiring more storage and computational resources.

Note that ${ \hat { v } } ( s , w )$ in either (8.1) or (8.2) is linear in $w$ (though it may be nonlinear in s). This type of method is called linear function approximation, which is the simplest function approximation method. To realize linear function approximation, we need to select an appropriate feature vector $\phi ( s )$ . That is, we must decide, for example, whether we should use a first-order straight line or a second-order curve to fit the points. The selection of appropriate feature vectors is nontrivial. It requires prior knowledge of the given task: the better we understand the task, the better the feature vectors we can select. For instance, if we know that the points in Figure 8.2 are approximately located on a straight line, we can use a straight line to fit the points. However, such prior knowledge is usually unknown in practice. If we do not have any prior knowledge, a popular solution is to use artificial neural networks as nonlinear function approximations.

Another important problem is how to find the optimal parameter vector. If we know $\{ v _ { \pi } ( s _ { i } ) \} _ { i = 1 } ^ { n }$ , this is a least-squares problem. The optimal parameter can be obtained by optimizing the following objective function:

$$
\begin{array}{r l r} & & {J _ {1} = \sum_ {i = 1} ^ {n} \left(\hat {v} (s _ {i}, w) - v _ {\pi} (s _ {i})\right) ^ {2} = \sum_ {i = 1} ^ {n} \left(\phi^ {T} (s _ {i}) w - v _ {\pi} (s _ {i})\right) ^ {2}} \\ & & {= \left\| \left[ \begin{array}{c} \phi^ {T} (s _ {1}) \\ \vdots \\ \phi^ {T} (s _ {n}) \end{array} \right] w - \left[ \begin{array}{c} v _ {\pi} (s _ {1}) \\ \vdots \\ v _ {\pi} (s _ {n}) \end{array} \right] \right\| ^ {2} \doteq \| \Phi w - v _ {\pi} \| ^ {2},} \end{array}
$$

where

$$
\Phi \doteq \left[ \begin{array}{c} \phi^ {T} (s _ {1}) \\ \vdots \\ \phi^ {T} (s _ {n}) \end{array} \right] \in \mathbb {R} ^ {n \times 2}, \qquad v _ {\pi} \doteq \left[ \begin{array}{c} v _ {\pi} (s _ {1}) \\ \vdots \\ v _ {\pi} (s _ {n}) \end{array} \right] \in \mathbb {R} ^ {n}.
$$

It can be verified that the optimal solution to this least-squares problem is

$$
w ^ {*} = (\Phi^ {T} \Phi) ^ {- 1} \Phi v _ {\pi}.
$$

More information about least-squares problems can be found in [47, Section 3.3] and [48, Section 5.14].

The curve-fitting example presented in this section illustrates the basic idea of value function approximation. This idea will be formally introduced in the next section.

## 8.2 TD learning of state values based on function approximation

In this section, we show how to integrate the function approximation method into TD learning to estimate the state values of a given policy. This algorithm will be extended to learn action values and optimal policies in Section 8.3.

This section contains quite a few subsections and many coherent contents. It is better for us to review the contents first before diving into the details.

The function approximation method is formulated as an optimization problem. The objective function of this problem is introduced in Section 8.2.1. The TD learning algorithm for optimizing this objective function is introduced in Section 8.2.2.

To apply the TD learning algorithm, we need to select appropriate feature vectors. Section 8.2.3 discusses this problem.

Examples are given in Section 8.2.4 to demonstrate the TD algorithm and the impacts of different feature vectors.

A theoretical analysis of the TD algorithm is given in Section 8.2.5. This subsection is mathematically intensive. Readers may read it selectively based on their interests.

### 8.2.1 Objective function

Let $v _ { \pi } ( s )$ and ${ \hat { v } } ( s , w )$ be the true state value and approximated state value of $s \in S$ 2 respectively. The problem to be solved is to find an optimal w so that ${ \hat { v } } ( s , w )$ can best approximate $v _ { \pi } ( s )$ for every s. In particular, the objective function is

$$
J (w) = \mathbb {E} [ (v _ {\pi} (S) - \hat {v} (S, w)) ^ {2} ],\tag{8.3}
$$

where the expectation is calculated with respect to the random variable $S \in S$ . While S is a random variable, what is its probability distribution? This question is important for understanding this objective function. There are several ways to define the probability distribution of S.

The first way is to use a uniform distribution. That is to treat all the states as equally important by setting the probability of each state to $1 / n$ . In this case, the objective function in (8.3) becomes

$$
J (w) = \frac {1}{n} \sum_ {s \in \mathcal {S}} (v _ {\pi} (s) - \hat {v} (s, w)) ^ {2},\tag{8.4}
$$

which is the average value of the approximation errors of all the states. However, this way does not consider the real dynamics of the Markov process under the given policy. Since some states may be rarely visited by a policy, it may be unreasonable to treat all the states as equally important.

The second way, which is the focus of this chapter, is to use the stationary distribution. The stationary distribution describes the long-term behavior of a Markov decision process. More specifically, after the agent executes a given policy for a suficiently long period, the probability of the agent being located at any state can be described by this stationary distribution. Interested readers may see the details in Box 8.1.

Let $\{ d _ { \pi } ( s ) \} _ { s \in { \cal S } }$ denote the stationary distribution of the Markov process under policy π. That is, the probability for the agent visiting s after a long period of time is $d _ { \pi } ( s )$ By definition, $\begin{array} { r } { \sum _ { s \in { \mathcal { S } } } d _ { \pi } ( s ) = 1 } \end{array}$ . Then, the objective function in (8.3) can be rewritten as

$$
J (w) = \sum_ {s \in \mathcal {S}} d _ {\pi} (s) (v _ {\pi} (s) - \hat {v} (s, w)) ^ {2},\tag{8.5}
$$

which is a weighted average of the approximation errors. The states that have higher probabilities of being visited are given greater weights.

It is notable that the value of $d _ { \pi } ( s )$ is nontrivial to obtain because it requires knowing the state transition probability matrix $P _ { \pi }$ (see Box 8.1). Fortunately, we do not need to calculate the specific value of $d _ { \pi } ( s )$ to minimize this objective function as shown in the next subsection. In addition, it was assumed that the number of states was finite when we introduced (8.4) and (8.5). When the state space is continuous, we can replace the summations with integrals.

### Box 8.1: Stationary distribution of a Markov decision process

The key tool for analyzing stationary distribution is $P _ { \pi } \in \mathbb { R } ^ { n \times n }$ , which is the probability transition matrix under the given policy $\pi$ . If the states are indexed as $s _ { 1 } , \ldots , s _ { n } ,$ then $[ P _ { \pi } ] _ { i j }$ is defined as the probability for the agent moving from $s _ { i }$ to $s _ { j }$ The definition of $P _ { \pi }$ can be found in Section 2.6.

$$
P _ {\pi} ^ {k} (k = 1, 2, 3, \dots)
$$

First of all, it is necessary to examine the interpretation of the entries in $P _ { \pi } ^ { k }$ . The probability of the agent transitioning from $s _ { i }$ to $s _ { j }$ using exactly k steps is denoted as

$$
p _ {i j} ^ {(k)} = \mathrm{Pr} (S _ {t _ {k}} = j | S _ {t _ {0}} = i),
$$

where $t _ { 0 }$ and $t _ { k }$ are the initial and kth time steps, respectively. First, by the definition of $P _ { \pi }$ , we have

$$
[ P _ {\pi} ] _ {i j} = p _ {i j} ^ {(1)},
$$

which means that $[ P _ { \pi } ] _ { i j }$ is the probability of transitioning from $s _ { i }$ to $s _ { j }$ using a single step. Second, consider $P _ { \pi } ^ { 2 }$ . It can be verified that

$$
[ P _ {\pi} ^ {2} ] _ {i j} = [ P _ {\pi} P _ {\pi} ] _ {i j} = \sum_ {q = 1} ^ {n} [ P _ {\pi} ] _ {i q} [ P _ {\pi} ] _ {q j}.
$$

Since $[ P _ { \pi } ] _ { i q } [ P _ { \pi } ] _ { q j }$ is the joint probability of transitioning from $s _ { i }$ to $s _ { q }$ and then from $s _ { q }$ to $s _ { j }$ , we know that $[ P _ { \pi } ^ { 2 } ] _ { i j }$ is the probability of transitioning from $s _ { i }$ to $s _ { j }$ using exactly two steps. That is

$$
[ P _ {\pi} ^ {2} ] _ {i j} = p _ {i j} ^ {(2)}.
$$

Similarly, we know that

$$
[ P _ {\pi} ^ {k} ] _ {i j} = p _ {i j} ^ {(k)},
$$

which means that $[ P _ { \pi } ^ { k } ] _ { i j }$ is the probability of transitioning from $s _ { i }$ to $s _ { j }$ using exactly k steps.

Definition of stationary distributions.

Let $d _ { 0 } \in \mathbb { R } ^ { n }$ be a vector representing the probability distribution of the states at the initial time step. For example, if s is always selected as the starting state, then $d _ { 0 } ( s ) = 1$ and the other entries of $d _ { 0 }$ are 0. Let $d _ { k } \in \mathbb { R } ^ { n }$ be the vector representing the probability distribution obtained after exactly k steps starting from $d _ { 0 }$ . Then, we have

$$
d _ {k} (s _ {i}) = \sum_ {j = 1} ^ {n} d _ {0} (s _ {j}) [ P _ {\pi} ^ {k} ] _ {j i}, \quad i = 1, 2, \dots .\tag{8.6}
$$

This equation indicates that the probability of the agent visiting $s _ { i }$ at step k equals the sum of the probabilities of the agent transitioning from $\{ s _ { j } \} _ { j = 1 } ^ { n }$ to $s _ { i }$ using exactly k steps. The matrix-vector form of (8.6) is

$$
d _ {k} ^ {T} = d _ {0} ^ {T} P _ {\pi} ^ {k}.\tag{8.7}
$$

When we consider the long-term behavior of the Markov process, it holds under certain conditions that

$$
\lim _ {k \to \infty} P _ {\pi} ^ {k} = \mathbf {1} _ {n} d _ {\pi} ^ {T},\tag{8.8}
$$

where $\mathbf { 1 } _ { n } \ = \ [ 1 , \ldots , 1 ] ^ { T } \in \mathbb { R } ^ { n }$ and ${ \bf 1 } _ { n } d _ { \pi } ^ { T }$ is a constant matrix with all its rows equal to $d _ { \pi } ^ { T }$ . The conditions under which (8.8) is valid will be discussed later. Substituting (8.8) into (8.7) yields

$$
\lim _ {k \to \infty} d _ {k} ^ {T} = d _ {0} ^ {T} \lim _ {k \to \infty} P _ {\pi} ^ {k} = d _ {0} ^ {T} \mathbf {1} _ {n} d _ {\pi} ^ {T} = d _ {\pi} ^ {T},\tag{8.9}
$$

where the last equality is valid because $d _ { 0 } ^ { T } \mathbf { 1 } _ { n } = 1$

Equation (8.9) means that the state distribution $d _ { k }$ converges to a constant value $d _ { \pi }$ which is called the limiting distribution. The limiting distribution depends on the system model and the policy π. Interestingly, it is independent of the initial distribution $d _ { 0 }$ That is, regardless of which state the agent starts from, the probability distribution of the agent after a suficiently long period can always be described by the limiting distribution.

The value of $d _ { \pi }$ can be calculated in the following way. Taking the limit of both sides of $d _ { k } ^ { T } = d _ { k - 1 } ^ { T } P _ { \pi }$ gives lim $\begin{array} { r } { { 1 } _ { k \to \infty } d _ { k } ^ { T } = \operatorname* { l i m } _ { k \to \infty } d _ { k - 1 } ^ { T } P _ { \pi } } \end{array}$ and hence

$$
d _ {\pi} ^ {T} = d _ {\pi} ^ {T} P _ {\pi}.\tag{8.10}
$$

As a result, $d _ { \pi }$ is the left eigenvector of $P _ { \pi }$ associated with the eigenvalue 1. The solution of (8.10) is called the stationary distribution. It holds that $\begin{array} { r } { \sum _ { s \in \mathcal { S } } d _ { \pi } ( s ) = } \end{array}$ 1 and $d _ { \pi } ( s ) > 0$ for all $s \in S$ . The reason why $d _ { \pi } ( s ) > 0$ (not $d _ { \pi } ( s ) \geq 0 )$ will be explained later.

Conditions for the uniqueness of stationary distributions.

The solution $d _ { \pi }$ of (8.10) is usually called a stationary distribution, whereas the distribution $d _ { \pi }$ in (8.9) is usually called the limiting distribution. Note that (8.9) implies (8.10), but the converse may not be true. A general class of Markov processes that have unique stationary (or limiting) distributions is irreducible (or regular) Markov processes. Some necessary definitions are given below. More details can be found in [49, Chapter IV].

State $s _ { j }$ is said to be accessible from state $s _ { i }$ if there exists a finite integer k so that $[ P _ { \pi } ] _ { i j } ^ { k } > 0$ which means that the agent starting from $s _ { i }$ can possibly reach $s _ { j }$ after a finite number of transitions.

If two states $s _ { i }$ and $s _ { j }$ are mutually accessible, then the two states are said to communicate.

A Markov process is called irreducible if all of its states communicate with each other. In other words, the agent starting from an arbitrary state can possibly reach any other state within a finite number of steps. Mathematically, it indicates that, for any $s _ { i }$ and $s _ { j }$ , there exists $k \geq 1$ such that $[ { P _ { \pi } ^ { k } } ] _ { i j } > 0$ (the value of k may vary for different $i , j )$

A Markov process is called regular if there exists $k \geq 1$ such that $[ { P _ { \pi } ^ { k } } ] _ { i j } > 0$ for all $i , j$ Equivalently, there exists $k \geq 1$ such that $P _ { \pi } ^ { k } > 0$ where $>$ is elementwise. As a result, it is possible that every state is reachable from any other state within at most k steps. A regular Markov process is also irreducible, but the converse is not true. However, if a Markov process is irreducible and there exists i such that $[ { \cal P } _ { \pi } ] _ { i i } > 0$ , then it is also regular. Moreover, if $P _ { \pi } ^ { k } > 0 .$ then $P _ { \pi } ^ { k ^ { \prime } } > 0$ for any $k ^ { \prime } \geq k$ since $P _ { \pi } \geq 0$ It then follows from (8.9) that $d _ { \pi } ( s ) > 0$ for every s.

Policies that may lead to unique stationary distributions.

Once the policy is given, a Markov decision process becomes a Markov process, whose long-term behavior is jointly determined by the given policy and the system model. Then, an important question is what kind of policies can lead to regular Markov processes? In general, the answer is exploratory policies such as ε-greedy policies. That is because an exploratory policy has a positive probability of taking any action at any state. As a result, the states can communicate with each other when the system model allows them to do so.

◇ An example is given in Figure 8.5 to illustrate stationary distributions. The policy in this example is ε-greedy with $\epsilon = 0 . 5$ The states are indexed as $s _ { 1 } , s _ { 2 } , s _ { 3 } , s _ { 4 } .$ which correspond to the top-left, top-right, bottom-left, and bottom-right cells in the grid, respectively.

We compare two methods to calculate the stationary distributions. The first method is to solve (8.10) to get the theoretical value of $d _ { \pi }$ . The second method is to estimate $d _ { \pi }$ numerically: we start from an arbitrary initial state and generate a suficiently long episode by following the given policy. Then, $d _ { \pi }$ can be estimated by the ratio between the number of times each state is visited in the episode and the total length of the episode. The estimation result is more accurate when the episode is longer. We next compare the theoretical and estimated results.

![](c8bad296109e1b389a8cbf7286f457f734323e2acceaeec5fed19818bc6f08ff.jpg)

![](e4675761c353c9ef7edbda5c98aeb55f8b8581e42fd8d2f6e86361ea924e63eb.jpg)

*Figure 8.5: Long-term behavior of an ε-greedy policy with $\epsilon = 0 . 5$ The asterisks in the right figure represent the theoretical values of the elements of $d _ { \pi }$*

Theoretical value of $d _ { \pi }$ : It can be verified that the Markov process induced by the policy is both irreducible and regular. That is due to the following reasons. First, since all the states communicate, the resulting Markov process is irreducible. Second, since every state can transition to itself, the resulting

Markov process is regular. It can be seen from Figure 8.5 that

$$
P _ {\pi} ^ {T} = \left[ \begin{array}{c c c c} 0. 3 & 0. 1 & 0. 1 & 0 \\ 0. 1 & 0. 3 & 0 & 0. 1 \\ 0. 6 & 0 & 0. 3 & 0. 1 \\ 0 & 0. 6 & 0. 6 & 0. 8 \end{array} \right].
$$

The eigenvalues of $P _ { \pi } ^ { T }$ can be calculated as $\{ - 0 . 0 4 4 9 , 0 . 3 , 0 . 4 4 4 9 , 1 \}$ The unit-length (right) eigenvector of $P _ { \pi } ^ { T }$ corresponding to the eigenvalue 1 is $[ 0 . 0 4 6 3 , 0 . 1 4 5 5 , 0 . 1 7 8 5 , 0 . 9 7 2 0 ] ^ { T }$ After scaling this vector so that the sum of all its elements is equal to 1, we obtain the theoretical value of $d _ { \pi }$ as follows:

$$
d _ {\pi} = \left[ \begin{array}{l} 0. 0 3 4 5 \\ 0. 1 0 8 4 \\ 0. 1 3 3 0 \\ 0. 7 2 4 1 \end{array} \right].
$$

The ith element of $d _ { \pi }$ corresponds to the probability of the agent visiting $s _ { i }$ in the long run.

Estimated value of $d _ { \pi }$ : We next verify the above theoretical value of $d _ { \pi }$ by executing the policy for suficiently many steps in the simulation. Specifically, we select $s _ { 1 }$ as the starting state and run 1,000 steps by following the policy. The proportion of the visits of each state during the process is shown in Figure 8.5. It can be seen that the proportions converge to the theoretical value of $d _ { \pi }$ after hundreds of steps.

### 8.2.2 Optimization algorithms

To minimize the objective function $J ( w )$ in (8.3), we can use the gradient descent algorithm:

$$
w _ {k + 1} = w _ {k} - \alpha_ {k} \nabla_ {w} J (w _ {k}),
$$

where

$$
\begin{array}{r l} & {\nabla_ {w} J (w _ {k}) = \nabla_ {w} \mathbb {E} [ (v _ {\pi} (S) - \hat {v} (S, w _ {k})) ^ {2} ]} \\ & {\qquad = \mathbb {E} [ \nabla_ {w} (v _ {\pi} (S) - \hat {v} (S, w _ {k})) ^ {2} ]} \\ & {\qquad = 2 \mathbb {E} [ (v _ {\pi} (S) - \hat {v} (S, w _ {k})) (- \nabla_ {w} \hat {v} (S, w _ {k})) ]} \\ & {\qquad = - 2 \mathbb {E} [ (v _ {\pi} (S) - \hat {v} (S, w _ {k})) \nabla_ {w} \hat {v} (S, w _ {k}) ].} \end{array}
$$

Therefore, the gradient descent algorithm is

$$
w _ {k + 1} = w _ {k} + 2 \alpha_ {k} \mathbb {E} [ (v _ {\pi} (S) - \hat {v} (S, w _ {k})) \nabla_ {w} \hat {v} (S, w _ {k}) ],\tag{8.11}
$$

where the coefficient 2 before $\alpha _ { k }$ can be merged into $\alpha _ { k }$ without loss of generality. The algorithm in (8.11) requires calculating the expectation. In the spirit of stochastic gradient descent, we can replace the true gradient with a stochastic gradient. Then, (8.11) becomes

$$
w _ {t + 1} = w _ {t} + \alpha_ {t} \big (v _ {\pi} (s _ {t}) - \hat {v} (s _ {t}, w _ {t}) \big) \nabla_ {w} \hat {v} (s _ {t}, w _ {t}),\tag{8.12}
$$

where $s _ { t }$ is a sample of $S$ at time $t .$

Notably, (8.12) is not implementable because it requires the true state value $v _ { \pi }$ , which is unknown and must be estimated. We can replace $v _ { \pi } ( s _ { t } )$ with an approximation to make the algorithm implementable. The following two methods can be used to do so.

Monte Carlo method: Suppose that we have an episode $( s _ { 0 } , r _ { 1 } , s _ { 1 } , r _ { 2 } , \dots )$ . Let $g _ { t }$ be the discounted return starting from $s _ { t }$ . Then, $g _ { t }$ can be used as an approximation of $v _ { \pi } ( s _ { t } )$ . The algorithm in (8.12) becomes

$$
w _ {t + 1} = w _ {t} + \alpha_ {t} \big (g _ {t} - \hat {v} (s _ {t}, w _ {t}) \big) \nabla_ {w} \hat {v} (s _ {t}, w _ {t}).
$$

This is the algorithm of Monte Carlo learning with function approximation.

Temporal-difference method: In the spirit of TD learning, $r _ { t + 1 } + \gamma \hat { v } ( s _ { t + 1 } , w _ { t } )$ can be used as an approximation of $v _ { \pi } ( s _ { t } )$ . The algorithm in (8.12) becomes

$$
w _ {t + 1} = w _ {t} + \alpha_ {t} \left[ r _ {t + 1} + \gamma \hat {v} (s _ {t + 1}, w _ {t}) - \hat {v} (s _ {t}, w _ {t}) \right] \nabla_ {w} \hat {v} (s _ {t}, w _ {t}).\tag{8.13}
$$

This is the algorithm of TD learning with function approximation. This algorithm is summarized in Algorithm 8.1.

Understanding the TD algorithm in (8.13) is important for studying the other algorithms in this chapter. Notably, (8.13) can only learn the state values of a given policy. It will be extended to algorithms that can learn action values in Sections 8.3.1 and 8.3.2.

### 8.2.3 Selection of function approximators

To apply the TD algorithm in (8.13), we need to select appropriate ${ \hat { v } } ( s , w )$ . There are two ways to do that. The first is to use an artificial neural network as a nonlinear function approximator. The input of the neural network is the state, the output is ${ \hat { v } } ( s , w )$ , and the network parameter is $w .$ . The second is to simply use a linear function:

$$
\hat {v} (s, w) = \phi^ {T} (s) w,
$$

### Algorithm 8.1: TD learning of state values with function approximation

- **Initialization:** A function $\hat{v}(s,w)$ that is differentiable in w. Initial parameter $w_{0}$ .
- **Goal:** Learn the true state values of a given policy $\pi$ .
- For each episode $\{(s_{t},r_{t+1},s_{t+1})\}_{t}$ generated by $\pi$ , do
- For each sample $(s_{t},r_{t+1},s_{t+1})$ , do

In the general case, $w_{t+1}=w_{t}+\alpha_{t}[r_{t+1}+\gamma\hat{v}(s_{t+1},w_{t})-\hat{v}(s_{t},w_{t})]\nabla_{w}\hat{v}(s_{t},w_{t})$ In the linear case, $w_{t+1}=w_{t}+\alpha_{t}[r_{t+1}+\gamma\phi^{T}(s_{t+1})w_{t}-\phi^{T}(s_{t})w_{t}]\phi(s_{t})$ where $\phi ( s ) \in \mathbb { R } ^ { m }$ is the feature vector of $s .$ . The lengths of $\phi ( s )$ and w are equal to $m ,$ which is usually much smaller than the number of states. In the linear case, the gradient is

$$
\nabla_ {w} \hat {v} (s, w) = \phi (s),
$$

Substituting which into (8.13) yields

$$
w _ {t + 1} = w _ {t} + \alpha_ {t} \big [ r _ {t + 1} + \gamma \phi^ {T} (s _ {t + 1}) w _ {t} - \phi^ {T} (s _ {t}) w _ {t} \big ] \phi (s _ {t}).\tag{8.14}
$$

This is the algorithm of TD learning with linear function approximation. We call it TD-Linear for short.

The linear case is much better understood in theory than the nonlinear case. However, its approximation ability is limited. It is also nontrivial to select appropriate feature vectors for complex tasks. By contrast, artificial neural networks can approximate values as black-box universal nonlinear approximators, which are more friendly to use.

Nevertheless, it is still meaningful to study the linear case. A better understanding of the linear case can help readers better grasp the idea of the function approximation method. Moreover, the linear case is sufficient for solving the simple grid world tasks considered in this book. More importantly, the linear case is still powerful in the sense that the tabular method can be viewed as a special linear case. More information can be found in Box 8.2.

### Box 8.2: Tabular TD learning is a special case of TD-Linear

We next show that the tabular TD algorithm in (7.1) in Chapter 7 is a special case of the TD-Linear algorithm in (8.14).

Consider the following special feature vector for any $s \in S { \mathrm { : } }$

$$
\phi (s) = e _ {s} \in \mathbb {R} ^ {n},
$$

where $e _ { s }$ is the vector with the entry corresponding to s equal to 1 and the other entries equal to 0. In this case,

$$
\hat {v} (s, w) = e _ {s} ^ {T} w = w (s),
$$

where $w ( s )$ is the entry in w that corresponds to s. Substituting the above equation into (8.14) yields

$$
w _ {t + 1} = w _ {t} + \alpha_ {t} \big (r _ {t + 1} + \gamma w _ {t} (s _ {t + 1}) - w _ {t} (s _ {t}) \big) e _ {s _ {t}}.
$$

The above equation merely updates the entry $w _ { t } ( s _ { t } )$ due to the definition of $e _ { s _ { t } }$ Motivated by this, multiplying $e _ { s _ { t } } ^ { T }$ on both sides of the equation yields

$$
w _ {t + 1} (s _ {t}) = w _ {t} (s _ {t}) + \alpha_ {t} \big (r _ {t + 1} + \gamma w _ {t} (s _ {t + 1}) - w _ {t} (s _ {t}) \big),
$$

which is exactly the tabular TD algorithm in (7.1).

In summary, by selecting the feature vector as $\phi ( s ) = e _ { s }$ , the TD-Linear algorithm becomes the tabular TD algorithm.

### 8.2.4 Illustrative examples

We next present some examples for demonstrating how to use the TD-Linear algorithm in (8.14) to estimate the state values of a given policy. In the meantime, we demonstrate how to select feature vectors.

![](db6945cdd9671decbb8a076efdd71ffa661c85c2b3ef54219ed681555e1e68ca.jpg)

(a)

![](d73141cbfe6c391a96395554592aa85393f0d69ce30ca7ee293b2b7ea2383ee9.jpg)

(b)

![](a4568007bf65cc3138a3178d8383903c5734bb3de7afc930611eae4927ad4d0d.jpg)

(c)

*Figure 8.6: (a) The policy to be evaluated. (b) The true state values are represented as a table. (c) The true state values are represented as a 3D surface.*

The grid world example is shown in Figure 8.6. The given policy takes any action at a state with a probability of 0.2. Our goal is to estimate the state values under this policy. There are 25 state values in total. The true state values are shown in Figure 8.6(b). The true state values are visualized as a three-dimensional surface in Figure 8.6(c).

We next show that we can use fewer than 25 parameters to approximate these state values. The simulation setup is as follows. Five hundred episodes are generated by the given policy. Each episode has 500 steps and starts from a randomly selected state-action pair following a uniform distribution. In addition, in each simulation trial, the parameter vector w is randomly initialized such that each element is drawn from a standard normal distribution with a zero mean and a standard deviation of 1. We set $r _ { \mathrm { f o r b i d d e n } } = r _ { \mathrm { b o u n d a r y } } =$ $- 1 , r _ { \mathrm { t a r g e t } } = 1$ , and $\gamma = 0 . 9$

To implement the TD-Linear algorithm, we need to select the feature vector $\phi ( s )$ first. There are different ways to do that as shown below.

◇ The first type of feature vector is based on polynomials. In the grid world example, a state s corresponds to a 2D location. Let x and y denote the column and row indexes of s, respectively. To avoid numerical issues, we normalize x and y so that their values are within the interval of $[ - 1 , + 1 ]$ . With a slight abuse of notation, the normalized values are also represented by x and y. Then, the simplest feature vector is

$$
\phi (s) = \left[ \begin{array}{c} x \\ y \end{array} \right] \in \mathbb {R} ^ {2}.
$$

In this case, we have

$$
\hat {v} (s, w) = \phi^ {T} (s) w = [ x, y ] \left[ \begin{array}{l} w _ {1} \\ w _ {2} \end{array} \right] = w _ {1} x + w _ {2} y.
$$

When w is given, $\hat { v } ( s , w ) = w _ { 1 } x + w _ { 2 } y$ represents a 2D plane that passes through the origin. Since the surface of the state values may not pass through the origin, we need to introduce a bias to the 2D plane to better approximate the state values. To do that, we consider the following 3D feature vector:

$$
\phi (s) = \left[ \begin{array}{c} 1 \\ x \\ y \end{array} \right] \in \mathbb {R} ^ {3}.\tag{8.15}
$$

In this case, the approximated state value is

$$
\hat {v} (s, w) = \phi^ {T} (s) w = [ 1, x, y ] \left[ \begin{array}{l} w _ {1} \\ w _ {2} \\ w _ {3} \end{array} \right] = w _ {1} + w _ {2} x + w _ {3} y.
$$

When w is given, ${ \hat { v } } ( s , w )$ corresponds to a plane that may not pass through the origin. Notably, $\phi ( s )$ can also be defined as $\phi ( s ) = [ x , y , 1 ] ^ { T }$ , where the order of the elements does not matter.

The estimation result when we use the feature vector in (8.15) is shown in Figure 8.7(a). It can be seen that the estimated state values form a 2D plane. Although the estimation error converges as more episodes are used, the error cannot decrease to zero due to the limited approximation ability of a 2D plane.

To enhance the approximation ability, we can increase the dimension of the feature vector. To that end, consider

$$
\phi (s) = [ 1, x, y, x ^ {2}, y ^ {2}, x y ] ^ {T} \in \mathbb {R} ^ {6}.\tag{8.16}
$$

In this case, $\hat { v } ( s , w ) = \phi ^ { T } ( s ) w = w _ { 1 } + w _ { 2 } x + w _ { 3 } y + w _ { 4 } x ^ { 2 } + w _ { 5 } y ^ { 2 } + w _ { 6 } x y$ , which corresponds to a quadratic 3D surface. We can further increase the dimension of the feature vector:

$$
\phi (s) = [ 1, x, y, x ^ {2}, y ^ {2}, x y, x ^ {3}, y ^ {3}, x ^ {2} y, x y ^ {2} ] ^ {T} \in \mathbb {R} ^ {1 0}.\tag{8.17}
$$

The estimation results when we use the feature vectors in (8.16) and (8.17) are shown in Figures $8 . 7 ( \mathrm { b } ) \mathrm { - ( c ) }$ . As can be seen, the longer the feature vector is, the more accurately the state values can be approximated. However, in all three cases, the estimation error cannot converge to zero because these linear approximators still have limited approximation abilities.

![](5d60c7ebca81e623224250d9be25029b5007a1a476be7887085b23ed58836bd2.jpg)

![](948fbac9bf873c3f2ccdc92ccd09a828cc720403edfa374a664229e8c1d4587b.jpg)

![](0fab81e0c3af0ed94691ecec1aaed229e180ef7bd035a0bb73bca1f6ea2bfc0d.jpg)

![](889771f65ff80f1dc954c8d3b91df8e4830e3d0c316d67b9f838becdb83c86c5.jpg)

(a) $\phi ( s ) \in \mathbb { R } ^ { 3 }$

![](0c8cbba91de516ccb376e16675d0acb2f09d290e67b88be630c1be136d93247a.jpg)

(b) $\phi ( s ) \in \mathbb { R } ^ { 6 }$

![](cd5d874c516b3143673dc37eff57b56fe55dd6bd51b68226c3ddbdf2b5503d72.jpg)

(c) $\phi ( s ) \in \mathbb { R } ^ { 1 0 }$

*Figure 8.7: TD-Linear estimation results obtained with the polynomial features in (8.15), (8.16), and (8.17).*

In addition to polynomial feature vectors, many other types of features are available such as Fourier basis and tile coding [3, Chapter 9]. First, the values of x and y of each state are normalized to the interval of [0, 1]. The resulting feature vector is

![](3be510deb6538b58c74f362085f09240384304694da03d372135e592abf5d6d0.jpg)

![](a29a73c55edade98f11f72444722168fd1c384ae6cf90dbdae24fef57c128d1d.jpg)

![](009d47117a7864c3669a6a24c10ca61534c9d8c2c18d4d90a15434b10c4fef35.jpg)

![](29c9ffdbb5dfbcf229865c83c4ca1b0a231fd69561a4f9457d898a15521cfffa.jpg)

(a) q = 1 and $\phi ( s ) \in \mathbb { R } ^ { 4 }$

![](990ea9ddd1c1b93a4dc1cde4de8e8bfee5985865e94b44b7dc40f8f89aaf8606.jpg)

(b) q = 2 and φ(s) $\in \mathbb { R } ^ { 9 }$

![](cbc1673b3cc8a03dc4b937c6d354b6aa4b0f7d496641d7f4c228ae7ece084872.jpg)

(c) q = 3 and φ(s) $\in \mathbb { R } ^ { 1 6 }$

*Figure 8.8: TD-Linear estimation results obtained with the Fourier features in (8.18).*

$$
\phi (s) = \left[ \begin{array}{c} \vdots \\ \cos \big (\pi (c _ {1} x + c _ {2} y) \big) \\ \vdots \end{array} \right] \in \mathbb {R} ^ {(q + 1) ^ {2}},\tag{8.18}
$$

where $\pi$ denotes the circumference ratio, which is $3 . 1 4 1 5 \ldots$ , instead of a policy. Here, $c _ { 1 }$ or $c _ { 2 }$ can be set as any integers in $\{ 0 , 1 , \ldots , q \}$ , where q is a user-specified integer. $\mathrm { A s }$ a result, there are $( q + 1 ) ^ { 2 }$ possible values for the pair $( c _ { 1 } , c _ { 2 } )$ to take. Hence, the dimension of $\phi ( s )$ is $( q + 1 ) ^ { 2 }$ . For example, in the case of $q = 1$ , the feature vector is

$$
\phi (s) = \left[ \begin{array}{c} \cos (\pi (0 x + 0 y)) \\ \cos (\pi (0 x + 1 y)) \\ \cos (\pi (1 x + 0 y)) \\ \cos (\pi (1 x + 1 y)) \end{array} \right] = \left[ \begin{array}{c} 1 \\ \cos (\pi y) \\ \cos (\pi x) \\ \cos (\pi (x + y)) \end{array} \right] \in \mathbb {R} ^ {4}.
$$

The estimation results obtained when we use the Fourier features with $q = 1 , 2 , 3$ are shown in Figure 8.8. The dimensions of the feature vectors in the three cases are 4, 9, 16, respectively. As can be seen, the higher the dimension of the feature vector is, the more accurately the state values can be approximated.

### 8.2.5 Theoretical analysis

Thus far, we have finished describing the story of TD learning with function approximation. This story started from the objective function in (8.3). To optimize this objective function, we introduced the stochastic algorithm in (8.12). Later, the true value function in the algorithm, which was unknown, was replaced by an approximation, leading to the TD algorithm in (8.13). Although this story is helpful for understanding the basic idea of value function approximation, it is not mathematically rigorous. For example, the algorithm in (8.13) actually does not minimize the objective function in (8.3).

We next present a theoretical analysis of the TD algorithm in (8.13) to reveal why the algorithm works effectively and what mathematical problems it solves. Since general nonlinear approximators are difficult to analyze, this part only considers the linear case. Readers are advised to read selectively based on their interests since this part is mathematically intensive.

### Convergence analysis

To study the convergence property of (8.13), we first consider the following deterministic algorithm:

$$
w _ {t + 1} = w _ {t} + \alpha_ {t} \mathbb {E} \left[ \left(r _ {t + 1} + \gamma \phi^ {T} (s _ {t + 1}) w _ {t} - \phi^ {T} (s _ {t}) w _ {t}\right) \phi (s _ {t}) \right],\tag{8.19}
$$

where the expectation is calculated with respect to the random variables $s _ { t } , s _ { t + 1 } , r _ { t + 1 }$ The distribution of $s _ { t }$ is assumed to be the stationary distribution $d _ { \pi }$ . The algorithm in (8.19) is deterministic because the random variables $s _ { t } , s _ { t + 1 } , r _ { t + 1 }$ all disappear after calculating the expectation.

Why would we consider this deterministic algorithm? First, the convergence of this deterministic algorithm is easier (though nontrivial) to analyze. Second and more im portantly, the convergence of this deterministic algorithm implies the convergence of the stochastic TD algorithm in (8.13). That is because (8.13) can be viewed as a stochastic gradient descent (SGD) implementation of (8.19). Therefore, we only need to study the convergence property of the deterministic algorithm.

Although the expression of (8.19) may look complex at first glance, it can be greatly simplified. To do that, define

$$
\Phi = \left[ \begin{array}{c} \vdots \\ \phi^ {T} (s) \\ \vdots \end{array} \right] \in \mathbb {R} ^ {n \times m}, \quad D = \left[ \begin{array}{c c c} \ddots & & \\ & d _ {\pi} (s) & \\ & & \ddots \end{array} \right] \in \mathbb {R} ^ {n \times n},\tag{8.20}
$$

where $\Phi$ is the matrix containing all the feature vectors, and D is a diagonal matrix with the stationary distribution in its diagonal entries. The two matrices will be frequently used.

Lemma 8.1. The expectation in (8.19) can be rewritten as

$$
\mathbb {E} \Big [ \big (r _ {t + 1} + \gamma \phi^ {T} (s _ {t + 1}) w _ {t} - \phi^ {T} (s _ {t}) w _ {t} \big) \phi (s _ {t}) \Big ] = b - A w _ {t},
$$

where

$$
\begin{array}{l} A \doteq \Phi^ {T} D (I - \gamma P _ {\pi}) \Phi \in \mathbb {R} ^ {m \times m}, \\ b \doteq \Phi^ {T} D r _ {\pi} \in \mathbb {R} ^ {m}. \end{array}\tag{8.21}
$$

Here, $P _ { \pi } , r _ { \pi }$ are the two terms in the Bellman equation $\boldsymbol { v } _ { \pi } = \boldsymbol { r } _ { \pi } + \gamma \boldsymbol { P } _ { \pi } \boldsymbol { v } _ { \pi }$ , and I is the identity matrix with appropriate dimensions.

The proof is given in Box 8.3. With the expression in Lemma 8.1, the deterministic algorithm in (8.19) can be rewritten as

$$
w _ {t + 1} = w _ {t} + \alpha_ {t} (b - A w _ {t}),\tag{8.22}
$$

which is a simple deterministic process. Its convergence is analyzed below.

First, what is the converged value of $w _ { t } ?$ Hypothetically, if $w _ { t }$ converges to a constant value $w ^ { * }$ as $t \to \infty$ , then (8.22) implies $w ^ { * } = w ^ { * } + \alpha _ { \infty } ( b - A w ^ { * } )$ , which suggests that $b - A w ^ { * } = 0$ and hence

$$
w ^ {*} = A ^ {- 1} b.
$$

Several remarks about this converged value are given below.

Is A invertible? The answer is yes. In fact, A is not only invertible but also positive definite. That is, for any nonzero vector x with appropriate dimensions, $x ^ { T } A x > 0$ The proof is given in Box 8.4.

What is the interpretation of $w ^ { * } = A ^ { - 1 } b !$ It is actually the optimal solution for minimizing the projected Bellman error. The details will be introduced in Section 8.2.5.

The tabular method is a special case. One interesting result is that, when the dimensionality of w equals $n = | S |$ and $\phi ( s ) = [ 0 , \ldots , 1 , \ldots , 0 ] ^ { T }$ , where the entry corresponding to s is 1, we have

$$
w ^ {*} = A ^ {- 1} b = v _ {\pi}.\tag{8.23}
$$

This equation indicates that the parameter vector to be learned is actually the true state value. This conclusion is consistent with the fact that the tabular TD algorithm is a special case of the TD-Linear algorithm, as introduced in Box 8.2. The proof of (8.23) is given below. It can be verified that $\Phi = I$ in this case and hence $A =$ $\Phi ^ { T } D ( I - \gamma P _ { \pi } ) \Phi \ = \ D ( I - \gamma P _ { \pi } )$ and $b = \Phi ^ { T } D r _ { \pi } = D r _ { \pi }$ . Thus, $w ^ { * } = A ^ { - 1 } b =$ $( I - \gamma P _ { \pi } ) ^ { - 1 } D ^ { - 1 } D r _ { \pi } = ( I - \gamma P _ { \pi } ) ^ { - 1 } r _ { \pi } = v _ { \pi }$

Second, we prove that $w _ { t }$ in (8.22) converges to $w ^ { * } = A ^ { - 1 } b \mathrm { \ a s \ } t  \infty$ . Since (8.22) is a simple deterministic process, it can be proven in many ways. We present two proofs as follows.

Proof 1: Define the convergence error as $\delta _ { t } \doteq w _ { t } - w ^ { * }$ . We only need to show that $\delta _ { t }$ converges to zero. To do that, substituting $\boldsymbol { w } _ { t } = \boldsymbol { \delta } _ { t } + \boldsymbol { w } ^ { * }$ into (8.22) gives

$$
\delta_ {t + 1} = \delta_ {t} - \alpha_ {t} A \delta_ {t} = (I - \alpha_ {t} A) \delta_ {t}.
$$

It then follows that

$$
\delta_ {t + 1} = (I - \alpha_ {t} A) \dots (I - \alpha_ {0} A) \delta_ {0}.
$$

Consider the simple case where $\alpha _ { t } = \alpha$ for all t. Then, we have

$$
\| \delta_ {t + 1} \| _ {2} \leq \| I - \alpha A \| _ {2} ^ {t + 1} \| \delta_ {0} \| _ {2}.
$$

When $\alpha > 0$ is suficiently small, we have that $\| I - \alpha A \| _ { 2 } < 1$ and hence $\delta _ { t } \to 0$ as $t \to \infty$ . The reason why $\| I - \alpha A \| _ { 2 } < 1$ holds is that A is positive definite and hence $x ^ { T } ( I - \alpha A ) x < 1$ for any x.

Proof 2: Consider $g ( w ) \doteq b - A w$ . Since $w ^ { * }$ is the root of $g ( w ) = 0$ , the task is actually a root-finding problem. The algorithm in (8.22) is actually a Robbins-Monro (RM) algorithm. Although the original RM algorithm was designed for stochastic processes, it can also be applied to deterministic cases. The convergence of RM algorithms can shed light on the convergence of $w _ { t + 1 } = w _ { t } + \alpha _ { t } ( b - A w _ { t } )$ . That is, $w _ { t }$ converges to $w ^ { * }$ when $\textstyle \sum _ { t } \alpha _ { t } = \infty$ and $\textstyle \sum _ { t } \alpha _ { t } ^ { 2 } < \infty$

### Box 8.3: Proof of Lemma 8.1

By using the law of total expectation, we have

$$
\begin{array}{r l} & {\mathbb {E} \Big [ r _ {t + 1} \phi (s _ {t}) + \phi (s _ {t}) \big (\gamma \phi^ {T} (s _ {t + 1}) - \phi^ {T} (s _ {t}) \big) w _ {t} \Big ]} \\ & {= \sum_ {s \in \mathcal {S}} d _ {\pi} (s) \mathbb {E} \Big [ r _ {t + 1} \phi (s _ {t}) + \phi (s _ {t}) \big (\gamma \phi^ {T} (s _ {t + 1}) - \phi^ {T} (s _ {t}) \big) w _ {t} | s _ {t} = s \Big ]} \\ & {= \sum_ {s \in \mathcal {S}} d _ {\pi} (s) \mathbb {E} \Big [ r _ {t + 1} \phi (s _ {t}) | s _ {t} = s \Big ] + \sum_ {s \in \mathcal {S}} d _ {\pi} (s) \mathbb {E} \Big [ \phi (s _ {t}) \big (\gamma \phi^ {T} (s _ {t + 1}) - \phi^ {T} (s _ {t}) \big) w _ {t} | s _ {t} = s \Big ].} \end{array}\tag{8.24}
$$

Here, $s _ { t }$ is assumed to obey the stationary distribution $d _ { \pi }$

First, consider the first term in (8.24). Note that

$$
\mathbb {E} \Big [ r _ {t + 1} \phi (s _ {t}) \big | s _ {t} = s \Big ] = \phi (s) \mathbb {E} \Big [ r _ {t + 1} \big | s _ {t} = s \Big ] = \phi (s) r _ {\pi} (s),
$$

where $\begin{array} { r } { r _ { \pi } ( s ) = \sum _ { a } \pi ( a \vert s ) \sum _ { r } r p ( r \vert s , a ) } \end{array}$ . Then, the first term in (8.24) can be rewritten as

$$
\sum_ {s \in \mathcal {S}} d _ {\pi} (s) \mathbb {E} \Big [ r _ {t + 1} \phi (s _ {t}) \big | s _ {t} = s \Big ] = \sum_ {s \in \mathcal {S}} d _ {\pi} (s) \phi (s) r _ {\pi} (s) = \Phi^ {T} D r _ {\pi},\tag{8.25}
$$

where $r _ { \pi } = [ \cdots , r _ { \pi } ( s ) , \cdot \cdot \cdot ] ^ { T } \in \mathbb { R } ^ { n }$

Second, consider the second term in (8.24). Since

$$
\begin{array}{r l} & {\mathbb {E} \Big [ \phi (s _ {t}) \big (\gamma \phi^ {T} (s _ {t + 1}) - \phi^ {T} (s _ {t}) \big) w _ {t} \big | s _ {t} = s \Big ]} \\ & {= - \mathbb {E} \Big [ \phi (s _ {t}) \phi^ {T} (s _ {t}) w _ {t} \big | s _ {t} = s \Big ] + \mathbb {E} \Big [ \gamma \phi (s _ {t}) \phi^ {T} (s _ {t + 1}) w _ {t} \big | s _ {t} = s \Big ]} \\ & {= - \phi (s) \phi^ {T} (s) w _ {t} + \gamma \phi (s) \mathbb {E} \Big [ \phi^ {T} (s _ {t + 1}) \big | s _ {t} = s \Big ] w _ {t}} \\ & {= - \phi (s) \phi^ {T} (s) w _ {t} + \gamma \phi (s) \sum_ {s ^ {\prime} \in \mathcal {S}} p (s ^ {\prime} | s) \phi^ {T} (s ^ {\prime}) w _ {t},} \end{array}
$$

the second term in (8.24) becomes

$$
\begin{array}{r l} & {\sum_ {s \in \mathcal {S}} d _ {\pi} (s) \mathbb {E} \Big [ \phi (s _ {t}) \big (\gamma \phi^ {T} (s _ {t + 1}) - \phi^ {T} (s _ {t}) \big) w _ {t} \big | s _ {t} = s \Big ]} \\ & {= \sum_ {s \in \mathcal {S}} d _ {\pi} (s) \Big [ - \phi (s) \phi^ {T} (s) w _ {t} + \gamma \phi (s) \sum_ {s ^ {\prime} \in \mathcal {S}} p (s ^ {\prime} | s) \phi^ {T} (s ^ {\prime}) w _ {t} \Big ]} \\ & {= \sum_ {s \in \mathcal {S}} d _ {\pi} (s) \phi (s) \Big [ - \phi (s) + \gamma \sum_ {s ^ {\prime} \in \mathcal {S}} p (s ^ {\prime} | s) \phi (s ^ {\prime}) \Big ] ^ {T} w _ {t}} \\ & {= \Phi^ {T} D (- \Phi + \gamma P _ {\pi} \Phi) w _ {t}} \\ & {= - \Phi^ {T} D (I - \gamma P _ {\pi}) \Phi w _ {t}.} \end{array}\tag{8.26}
$$

Combining (8.25) and (8.26) gives

$$
\begin{array}{r l} & {\mathbb {E} \Big [ \big (r _ {t + 1} + \gamma \phi^ {T} (s _ {t + 1}) w _ {t} - \phi^ {T} (s _ {t}) w _ {t} \big) \phi (s _ {t}) \Big ] = \Phi^ {T} D r _ {\pi} - \Phi^ {T} D (I - \gamma P _ {\pi}) \Phi w _ {t}} \\ & {\qquad \doteq b - A w _ {t},} \end{array}\tag{8.27}
$$

where $b \doteq \Phi ^ { T } D r _ { \pi }$ and $A \doteq \Phi ^ { T } D ( I - \gamma P _ { \pi } ) \Phi$

### Box 8.4: Proving that $A = \Phi ^ { T } D ( I - \gamma P _ { \pi } ) \Phi$ is invertible and positive definite.

The matrix A is positive definite if $x ^ { T } A x > 0$ for any nonzero vector x with appropriate dimensions. If A is positive (or negative) definite, it is denoted as $A \succ 0$ $( \mathrm { o r } \ A \prec 0 )$ . Here, and should be differentiated from $>$ and $<$ , which indicate elementwise comparisons. Note that A may not be symmetric. Although positive definite matrices often refer to symmetric matrices, nonsymmetric ones can also be positive definite.

We next prove that $A \succ 0$ and hence A is invertible. The idea for proving $A \succ 0$ is to show that

$$
D (I - \gamma P _ {\pi}) \doteq M \succ 0.\tag{8.28}
$$

It is clear that $M \succ 0$ implies $A = \Phi ^ { T } M \Phi \succ 0$ since Φ is a tall matrix with full column rank (suppose that the feature vectors are selected to be linearly independent). Note that

$$
M = \frac {M + M ^ {T}}{2} + \frac {M - M ^ {T}}{2}.
$$

Since $M - M ^ { T }$ is skew-symmetric and hence $x ^ { T } ( M - M ^ { T } ) x = 0$ for any x, we know that $M \succ 0$ if and only if $M + M ^ { T } \succ 0$ To show $M + M ^ { T } \succ 0$ , we apply the fact that strictly diagonal dominant matrices are positive definite [4].

First, it holds that

$$
(M + M ^ {T}) \mathbf {1} _ {n} > 0,\tag{8.29}
$$

where $\mathbf { 1 } _ { n } = [ 1 , \ldots , 1 ] ^ { T } \in \mathbb { R } ^ { n }$ The proof of (8.29) is given below. Since $P _ { \pi } \mathbf { 1 } _ { n } = \mathbf { 1 } _ { n } ,$ we have $M { \bf 1 } _ { n } = D ( I - \gamma P _ { \pi } ) { \bf 1 } _ { n } = D ( { \bf 1 } _ { n } - \gamma { \bf 1 } _ { n } ) = ( 1 - \gamma ) d _ { \pi }$ Moreover, $M ^ { T } \mathbf { 1 } _ { n } =$ $( I - \gamma P _ { \pi } ^ { T } ) D { \bf 1 } _ { n } = ( I - \gamma P _ { \pi } ^ { T } ) d _ { \pi } = ( 1 - \gamma ) d _ { \pi }$ , where the last equality is valid because $P _ { \pi } ^ { T } d _ { \pi } = d _ { \pi }$ . In summary, we have

$$
(M + M ^ {T}) \mathbf {1} _ {n} = 2 (1 - \gamma) d _ {\pi}.
$$

Since all the entries of $d _ { \pi }$ are positive (see Box 8.1), we have $( M + M ^ { T } ) \mathbf { 1 } _ { n } > 0$

Second, the elementwise form of (8.29) is

$$
\sum_ {j = 1} ^ {n} [ M + M ^ {T} ] _ {i j} > 0, \quad i = 1, \dots , n,
$$

which can be further written as

$$
[ M + M ^ {T} ] _ {i i} + \sum_ {j \neq i} [ M + M ^ {T} ] _ {i j} > 0.
$$

It can be verified according to the expression of M in (8.28) that the diagonal entries of M are positive and the of-diagonal entries of M are nonpositive. Therefore, the above inequality can be rewritten as

$$
\left| \left[ M + M ^ {T} \right] _ {i i} \right| > \sum_ {j \neq i} \left| \left[ M + M ^ {T} \right] _ {i j} \right|.
$$

The above inequality indicates that the absolute value of the ith diagonal entry in $M + M ^ { T }$ is greater than the sum of the absolute values of the of-diagonal entries in the same row. Thus, $M + M ^ { T }$ is strictly diagonal dominant and the proof is complete.

### TD learning minimizes the projected Bellman error

While we have shown that the TD-Linear algorithm converges to $w ^ { * } = A ^ { - 1 } b ,$ we next show that $w ^ { * }$ is the optimal solution that minimizes the projected Bellman error. To do that, we review three objective functions.

The first objective function is

$$
J _ {E} (w) = \mathbb {E} [ (v _ {\pi} (S) - \hat {v} (S, w)) ^ {2} ],
$$

which has been introduced in (8.3). By the definition of expectation, $J _ { E } ( w )$ can be reexpressed in a matrix-vector form as

$$
J _ {E} (w) = \| \hat {v} (w) - v _ {\pi} \| _ {D} ^ {2},
$$

where $v _ { \pi }$ is the true state value vector and $\hat { v } ( w )$ is the approximated one. Here, $\| \cdot \| _ { D } ^ { 2 }$ is a weighted norm: $\| x \| _ { D } ^ { 2 } = x ^ { T } D x = \| D ^ { 1 / 2 } x \| _ { 2 } ^ { 2 }$ , where $D$ is given in (8.20).

This is the simplest objective function that we can imagine when talking about function approximation. However, it relies on the true state, which is unknown. To obtain an implementable algorithm, we must consider other objective functions such as the Bellman error and projected Bellman error [50–54].

◇ The second objective function is the Bellman error. In particular, since $v _ { \pi }$ satisfies the Bellman equation $\boldsymbol { v } _ { \pi } = \boldsymbol { r } _ { \pi } + \gamma P _ { \pi } \boldsymbol { v } _ { \pi }$ , it is expected that the estimated value $\hat { v } ( w )$ should also satisfy this equation to the greatest extent possible. Thus, the Bellman error is

$$
J _ {B E} (w) = \| \hat {v} (w) - (r _ {\pi} + \gamma P _ {\pi} \hat {v} (w)) \| _ {D} ^ {2} \doteq \| \hat {v} (w) - T _ {\pi} (\hat {v} (w)) \| _ {D} ^ {2}.\tag{8.30}
$$

Here, $T _ { \pi } ( \cdot )$ is the Bellman operator. In particular, for any vector $x \in \mathbb { R } ^ { n }$ , the Bellman operator is defined as

$$
T _ {\pi} (x) \doteq r _ {\pi} + \gamma P _ {\pi} x.
$$

Minimizing the Bellman error is a standard least-squares problem. The details of the solution are omitted here.

Third, it is notable that $J _ { B E } ( w )$ in (8.30) may not be minimized to zero due to the limited approximation ability of the approximator. By contrast, an objective function that can be minimized to zero is the projected Bellman error :

$$
J _ {P B E} (w) = \| \hat {v} (w) - M T _ {\pi} (\hat {v} (w)) \| _ {D} ^ {2},
$$

where $M \in \mathbb { R } ^ { n \times n }$ is the orthogonal projection matrix that geometrically projects any vector onto the space of all approximations.

In fact, the TD learning algorithm in (8.13) aims to minimize the projected Bellman error $J _ { P B E }$ rather than $J _ { E }$ or $J _ { B E }$ . The reason is as follows. For the sake of simplicity, consider the linear case where $\hat { v } ( w ) = \Phi w$ . Here, Φ is defined in (8.20). The range space of Φ is the set of all possible linear approximations. Then,

$$
M = \Phi (\Phi^ {T} D \Phi) ^ {- 1} \Phi^ {T} D \in \mathbb {R} ^ {n \times n}
$$

is the projection matrix that geometrically projects any vector onto the range space $\Phi .$ Since $\hat { v } ( w )$ is in the range space of $\Phi$ , we can always find a value of $w$ that can minimize $J _ { P B E } ( w )$ to zero. It can be proven that the solution minimizing $J _ { P B E } ( w )$ is $w ^ { * } = A ^ { - 1 } b$ That is

$$
w ^ {*} = A ^ {- 1} b = \arg \min _ {w} J _ {P B E} (w),
$$

The proof is given in Box 8.5.

### Box 8.5: Showing that $w ^ { * } = A^{-1}b$ minimizes $J _ { P B E } ( w )$

We next show that $w ^ { * } = A ^ { - 1 } b$ is the optimal solution that minimizes $J _ { P B E } ( w )$ . Since $J _ { P B E } ( w ) = 0 \Leftrightarrow \hat { v } ( w ) - M T _ { \pi } ( \hat { v } ( w ) ) = 0$ , we only need to study the root of

$$
\hat {v} (w) = M T _ {\pi} (\hat {v} (w)).
$$

In the linear case, substituting $\hat { v } ( w ) = \Phi w$ and the expression of M into the above equation gives

$$
\Phi w = \Phi (\Phi^ {T} D \Phi) ^ {- 1} \Phi^ {T} D (r _ {\pi} + \gamma P _ {\pi} \Phi w).\tag{8.31}
$$

Since Φ has full column rank, we have $\Phi x = \Phi y \Leftrightarrow x = y$ for any $x , y$ Therefore, (8.31) implies

$$
\begin{array}{r l} & w = (\Phi^ {T} D \Phi) ^ {- 1} \Phi^ {T} D (r _ {\pi} + \gamma P _ {\pi} \Phi w) \\ & \Longleftrightarrow \Phi^ {T} D (r _ {\pi} + \gamma P _ {\pi} \Phi w) = (\Phi^ {T} D \Phi) w \\ & \Longleftrightarrow \Phi^ {T} D r _ {\pi} + \gamma \Phi^ {T} D P _ {\pi} \Phi w = (\Phi^ {T} D \Phi) w \\ & \Longleftrightarrow \Phi^ {T} D r _ {\pi} = \Phi^ {T} D (I - \gamma P _ {\pi}) \Phi w \\ & \Longleftrightarrow w = (\Phi^ {T} D (I - \gamma P _ {\pi}) \Phi) ^ {- 1} \Phi^ {T} D r _ {\pi} = A ^ {- 1} b, \end{array}
$$

where $A , b$ are given in (8.21). Therefore, $w ^ { * } = A ^ { - 1 } b$ is the optimal solution that minimizes $J _ { P B E } ( w )$

Since the TD algorithm aims to minimize $J _ { P B E }$ rather than $J _ { E }$ , it is natural to ask how close the estimated value $\hat { v } ( w )$ is to the true state value $v _ { \pi }$ . In the linear case, the estimated value that minimizes the projected Bellman error is $\hat { v } ( w ^ { * } ) = \Phi w ^ { * }$ . Its deviation from the true state value $v _ { \pi }$ satisfies

$$
\| \hat {v} (w ^ {*}) - v _ {\pi} \| _ {D} = \| \Phi w ^ {*} - v _ {\pi} \| _ {D} \leq \frac {1}{1 - \gamma} \min _ {w} \| \hat {v} (w) - v _ {\pi} \| _ {D} = \frac {1}{1 - \gamma} \min _ {w} \sqrt {J _ {E} (w)}.\tag{8.32}
$$

The proof of this inequality is given in Box 8.6. Inequality (8.32) indicates that the discrepancy between $\Phi w ^ { * }$ and $v _ { \pi }$ is bounded from above by the minimum value of $J _ { E } ( w )$ However, this bound is loose, especially when $\gamma$ is close to one. It is thus mainly of theoretical value.

### Box 8.6: Proof of the error bound in (8.32)

Note that

$$
\begin{array}{r l} & {\| \Phi w ^ {*} - v _ {\pi} \| _ {D} = \| \Phi w ^ {*} - M v _ {\pi} + M v _ {\pi} - v _ {\pi} \| _ {D}} \\ & {\qquad \leq \| \Phi w ^ {*} - M v _ {\pi} \| _ {D} + \| M v _ {\pi} - v _ {\pi} \| _ {D}} \\ & {\qquad = \| M T _ {\pi} (\Phi w ^ {*}) - M T _ {\pi} (v _ {\pi}) \| _ {D} + \| M v _ {\pi} - v _ {\pi} \| _ {D},} \end{array}\tag{8.33}
$$

where the last equality is due to $\Phi w ^ { * } = M T _ { \pi } ( \Phi w ^ { * } )$ and $v _ { \pi } = T _ { \pi } ( v _ { \pi } )$ . Substituting

$$
M T _ {\pi} (\Phi w ^ {*}) - M T _ {\pi} (v _ {\pi}) = M (r _ {\pi} + \gamma P _ {\pi} \Phi w ^ {*}) - M (r _ {\pi} + \gamma P _ {\pi} v _ {\pi}) = \gamma M P _ {\pi} (\Phi w ^ {*} - v _ {\pi})
$$

into (8.33) yields

$$
\begin{array}{r l} & {\| \Phi w ^ {*} - v _ {\pi} \| _ {D} \leq \| \gamma M P _ {\pi} (\Phi w ^ {*} - v _ {\pi}) \| _ {D} + \| M v _ {\pi} - v _ {\pi} \| _ {D}} \\ & {\quad \leq \gamma \| M \| _ {D} \| P _ {\pi} (\Phi w ^ {*} - v _ {\pi}) \| _ {D} + \| M v _ {\pi} - v _ {\pi} \| _ {D}} \\ & {\quad = \gamma \| P _ {\pi} (\Phi w ^ {*} - v _ {\pi}) \| _ {D} + \| M v _ {\pi} - v _ {\pi} \| _ {D} \qquad \mathrm{(because} \| M \| _ {D} = 1)} \\ & {\quad \leq \gamma \| \Phi w ^ {*} - v _ {\pi} \| _ {D} + \| M v _ {\pi} - v _ {\pi} \| _ {D}. \qquad \mathrm{(because} \| P _ {\pi} x \| _ {D} \leq \| x \| _ {D} \mathrm{forall} x)} \end{array}
$$

The proof of $\| M \| _ { D } = 1$ and $\| P _ { \pi } x \| _ { D } \leq \| x \| _ { D }$ are postponed to the end of the box. Recognizing the above inequality gives

$$
\begin{array}{c} \| \Phi w ^ {*} - v _ {\pi} \| _ {D} \leq \frac {1}{1 - \gamma} \| M v _ {\pi} - v _ {\pi} \| _ {D} \\ = \frac {1}{1 - \gamma} \min _ {w} \| \hat {v} (w) - v _ {\pi} \| _ {D}, \end{array}
$$

where the last equality is because $\| M v _ { \pi } - v _ { \pi } \| _ { D }$ is the error between $v _ { \pi }$ and its orthogonal projection into the space of all possible approximations. Therefore, it is the minimum value of the error between $v _ { \pi }$ and any $\hat { v } ( w )$

We next prove some useful facts, which have already been used in the above proof.

◇ Properties of matrix weighted norms. By definition, $\| x \| _ { D } = \sqrt { x ^ { T } D x } = \| D ^ { 1 / 2 } x \| _ { 2 }$ The induced matrix norm is $\begin{array} { r } { \| A \| _ { D } = \operatorname* { m a x } _ { x \neq 0 } \| A x \| _ { D } / \| x \| _ { D } = \| D ^ { 1 / 2 } A D ^ { - 1 / 2 } \| _ { 2 } } \end{array}$ . For matrices A, B with appropriate dimensions, we have $\| A B x \| _ { D } \leq \| A \| _ { D } \| B \| _ { D } \| x \| _ { D }$ To see that, $\| A B x \| _ { D } ~ = ~ \| D ^ { 1 / 2 } A B x \| _ { 2 } ~ = ~ \| D ^ { 1 / 2 } A D ^ { - 1 / 2 } D ^ { 1 / 2 } B D ^ { - 1 / 2 } D ^ { 1 / 2 } x \| _ { 2 } ~ \leq ~ \| D ^ { 1 / 2 } A D ^ { 1 / 2 } B D ^ { - 1 / 2 } B D ^ { 1 / 2 } x \| _ { 2 } ~ .$ $\| D ^ { 1 / 2 } A D ^ { - 1 / 2 } \| _ { 2 } \| D ^ { 1 / 2 } B D ^ { - 1 / 2 } \| _ { 2 } \| D ^ { 1 / 2 } x \| _ { 2 } = \| A \| _ { D } \| B \| _ { D } \| x \| _ { D } .$

◇ Proof of $\| M \| _ { D } = 1$ This is valid because $\| M \| _ { D } ~ = ~ \| \Phi ( \Phi ^ { T } D \Phi ) ^ { - 1 } \Phi ^ { T } D \| _ { D } ~ = ~$ $\| D ^ { 1 / 2 } \Phi ( \Phi ^ { T } D \Phi ) ^ { - 1 } \Phi ^ { T } D D ^ { - 1 / 2 } \| _ { 2 } = 1$ where the last equality is valid due to the fact that the matrix in the $L _ { \mathrm { { 2 } } } \mathrm { { - n o r m } }$ is an orthogonal projection matrix and the $L _ { 2 }$ -norm of any orthogonal projection matrix is equal to one.

Proof of $\| P _ { \pi } x \| _ { D } \leq \| x \| _ { D }$ for any $x \in \mathbb { R } ^ { n }$ . First,

$$
\| P _ {\pi} x \| _ {D} ^ {2} = x ^ {T} P _ {\pi} ^ {T} D P _ {\pi} x = \sum_ {i, j} x _ {i} \left[ P _ {\pi} ^ {T} D P _ {\pi} \right] _ {i j} x _ {j} = \sum_ {i, j} x _ {i} \left(\sum_ {k} \left[ P _ {\pi} ^ {T} \right] _ {i k} [ D ] _ {k k} \left[ P _ {\pi} \right] _ {k j}\right) x _ {j}.
$$

Reorganizing the above equation gives

$$
\begin{array}{r l} & {\| P _ {\pi} x \| _ {D} ^ {2} = \sum_ {k} [ D ] _ {k k} \Big (\sum_ {i} [ P _ {\pi} ] _ {k i} x _ {i} \Big) ^ {2}} \\ & {\quad \leq \sum_ {k} [ D ] _ {k k} \Big (\sum_ {i} [ P _ {\pi} ] _ {k i} x _ {i} ^ {2} \Big) \qquad \mathrm {(due to Jensen^ {\prime} s inequality [ 5 5 , 5 6 ])}} \\ & {\quad = \sum_ {i} \Big (\sum_ {k} [ D ] _ {k k} [ P _ {\pi} ] _ {k i} \Big) x _ {i} ^ {2}} \\ & {\quad = \sum_ {i} [ D ] _ {i i} x _ {i} ^ {2} \qquad \mathrm {(due to d_ {\pi} ^ {T} P_ {\pi} = d_ {\pi} ^ {T})}} \\ & {\quad = \| x \| _ {D} ^ {2}.} \end{array}
$$

### Least-squares TD

We next introduce an algorithm called least-squares TD (LSTD) [57]. Like the TD-Linear algorithm, LSTD aims to minimize the projected Bellman error. However, it has some advantages over the TD-Linear algorithm.

Recall that the optimal parameter for minimizing the projected Bellman error is $w ^ { * } = A ^ { - 1 } b$ , where $A = \Phi ^ { T } D ( I - \gamma P _ { \pi } ) \Phi$ and $b = \Phi ^ { T } D r _ { \pi }$ . In fact, it follows from (8.27) that A and b can also be written as

$$
\begin{array}{r l} & {A = \mathbb {E} \Big [ \phi (s _ {t}) (\phi (s _ {t}) - \gamma \phi (s _ {t + 1})) ^ {T} \Big ],} \\ & {b = \mathbb {E} \Big [ r _ {t + 1} \phi (s _ {t}) \Big ].} \end{array}
$$

The above two equations show that A and b are expectations of $s _ { t } , s _ { t + 1 } , r _ { t + 1 }$ . The idea of LSTD is simple: if we can use random samples to directly obtain the estimates of A and $b ,$ which are denoted as $\hat { A }$ and $\hat { b } _ { : }$ , then the optimal parameter can be directly estimated as $w ^ { * } \approx \hat { A } ^ { - 1 } \hat { b }$

In particular, suppose that $\left( s _ { 0 } , r _ { 1 } , s _ { 1 } , \ldots , s _ { t } , r _ { t + 1 } , s _ { t + 1 } , \ldots \right)$ is a trajectory obtained by following a given policy π. Let $\hat { A } _ { t }$ and $\hat { b } _ { t }$ be the estimates of A and $b$ at time t, respectively. They are calculated as the averages of the samples:

$$
\begin{array}{l} \hat {A} _ {t} = \sum_ {k = 0} ^ {t - 1} \phi (s _ {k}) \big (\phi (s _ {k}) - \gamma \phi (s _ {k + 1}) \big) ^ {T}, \\ \hat {b} _ {t} = \sum_ {k = 0} ^ {t - 1} r _ {k + 1} \phi (s _ {k}). \end{array}\tag{8.34}
$$

Then, the estimated parameter is

$$
w _ {t} = \hat {A} _ {t} ^ {- 1} \hat {b} _ {t}.
$$

The reader may wonder if a coefficient of $1 / t$ is missing on the right-hand side of (8.34). In fact, it is omitted for the sake of simplicity since the value of $w _ { t }$ remains the same when it is omitted. Since $\hat { A } _ { t }$ may not be invertible especially when t is small, $\hat { A } _ { t }$ is usually biased by a small constant matrix $\sigma I$ , where I is the identity matrix and $\sigma$ is a small positive number.

The advantage of LSTD is that it uses experience samples more efficiently and converges faster than the TD method. That is because this algorithm is specifically designed based on the knowledge of the optimal solution’s expression. The better we understand a problem, the better algorithms we can design.

The disadvantages of LSTD are as follows. First, it can only estimate state values. By contrast, the TD algorithm can be extended to estimate action values as shown in the next section. Moreover, while the TD algorithm allows nonlinear approximators, LSTD does not. That is because this algorithm is specifically designed based on the expression of $w ^ { * }$ . Second, the computational cost of LSTD is higher than that of TD since LSTD updates an $m \times m$ matrix in each update step, whereas TD updates an m-dimensional vector. More importantly, in every step, LSTD needs to compute the inverse of $\hat { A } _ { t }$ , whose computational complexity is $O ( m ^ { 3 } )$ . The common method for resolving this problem is to directly update the inverse of $\hat { A } _ { t }$ rather than updating $\hat { A } _ { t }$ . In particular, $\hat { A } _ { t + 1 }$ can be calculated recursively as follows:

$$
\begin{array}{l} \hat {A} _ {t + 1} = \sum_ {k = 0} ^ {t} \phi (s _ {k}) \big (\phi (s _ {k}) - \gamma \phi (s _ {k + 1}) \big) ^ {T} \\ = \sum_ {k = 0} ^ {t - 1} \phi (s _ {k}) \big (\phi (s _ {k}) - \gamma \phi (s _ {k + 1}) \big) ^ {T} + \phi (s _ {t}) \big (\phi (s _ {t}) - \gamma \phi (s _ {t + 1}) \big) ^ {T} \\ = \hat {A} _ {t} + \phi (s _ {t}) \big (\phi (s _ {t}) - \gamma \phi (s _ {t + 1}) \big) ^ {T}. \end{array}
$$

The above expression decomposes $\hat { A } _ { t + 1 }$ into the sum of two matrices. Its inverse can be calculated as [58]

$$
\begin{array}{r l r} & & {\hat {A} _ {t + 1} ^ {- 1} = \left(\hat {A} _ {t} + \phi (s _ {t}) (\phi (s _ {t}) - \gamma \phi (s _ {t + 1})) ^ {T}\right) ^ {- 1}} \\ & & {= \hat {A} _ {t} ^ {- 1} + \frac {\hat {A} _ {t} ^ {- 1} \phi (s _ {t}) (\phi (s _ {t}) - \gamma \phi (s _ {t + 1})) ^ {T} \hat {A} _ {t} ^ {- 1}}{1 + (\phi (s _ {t}) - \gamma \phi (s _ {t + 1})) ^ {T} \hat {A} _ {t} ^ {- 1} \phi (s _ {t})}.} \end{array}
$$

Therefore, we can directly store and update $\hat { A } _ { t } ^ { - 1 }$ to avoid the need to calculate the matrix inverse. This recursive algorithm does not require a step size. However, it requires setting the initial value of $\hat { A } _ { 0 } ^ { - 1 }$ . The initial value of such a recursive algorithm can be selected as $\hat { A } _ { 0 } ^ { - 1 } = \sigma I$ , where $\sigma$ is a positive number. A good tutorial on the recursive least-squares approach can be found in [59].

## 8.3 TD learning of action values based on function approximation

While Section 8.2 introduced the problem of state value estimation, the present section introduces how to estimate action values. The tabular Sarsa and tabular Q-learning algorithms are extended to the case of value function approximation. Readers will see that the extension is straightforward.

### 8.3.1 Sarsa with function approximation

The Sarsa algorithm with function approximation can be readily obtained from (8.13) by replacing the state values with action values. In particular, suppose that $q _ { \pi } ( s , a )$ is approximated by ${ \hat { q } } ( s , a , w )$ . Replacing ${ \hat { v } } ( s , w )$ in (8.13) by ${ \hat { q } } ( s , a , w )$ gives

$$
w _ {t + 1} = w _ {t} + \alpha_ {t} \Big [ r _ {t + 1} + \gamma \hat {q} (s _ {t + 1}, a _ {t + 1}, w _ {t}) - \hat {q} (s _ {t}, a _ {t}, w _ {t}) \Big ] \nabla_ {w} \hat {q} (s _ {t}, a _ {t}, w _ {t}).\tag{8.35}
$$

The analysis of (8.35) is similar to that of (8.13) and is omitted here. When linear functions are used, we have

$$
\hat {q} (s, a, w) = \phi^ {T} (s, a) w,
$$

where $\phi ( s , a )$ is a feature vector. In this case, $\nabla _ { w } \widehat { q } ( s , a , w ) = \phi ( s , a )$

The value estimation step in (8.35) can be combined with a policy improvement step to learn optimal policies. The procedure is summarized in Algorithm 8.2. It should be noted that accurately estimating the action values of a given policy requires (8.35) to be run suficiently many times. However, (8.35) is executed only once before switching to the policy improvement step. This is similar to the tabular Sarsa algorithm. Moreover, the implementation in Algorithm 8.2 aims to solve the task of finding a good path to the target state from a prespecified starting state. As a result, it cannot find the optimal policy for every state. However, if sufficient experience data are available, the implementation process can be easily adapted to find optimal policies for every state.

An illustrative example is shown in Figure 8.9. In this example, the task is to find a good policy that can lead the agent to the target when starting from the top-left state. Both the total reward and the length of each episode gradually converge to steady values. In this example, the linear feature vector is selected as the Fourier function of order 5. The expression of a Fourier feature vector is given in (8.18).

*Figure 8.9: Sarsa with linear function approximation. Here, $\gamma = 0 . 9 , \epsilon = 0 . 1$ $r _ { \mathrm { b o u n d a r y } } = r _ { \mathrm { f o r b i d d e n } } =$ $- 1 0 , r _ { \mathrm { t a r g e t } } = 1$ , and $\alpha = 0 . 0 0 1$*

### Algorithm 8.2: Sarsa with function approximation

- **Initialization:** Initial parameter $w_{0}$ . Initial policy $\pi_{0}$ . $\alpha_{t} = \alpha > 0$ for all $t. \epsilon \in (0,1)$ .
- **Goal:** Learn an optimal policy that can lead the agent to the target state from an initial state $s_{0}$ .
- For each episode, do
- Generate $a_{0}$ at $s_{0}$ following $\pi_{0}(s_{0})$ If $s_{t}$ ( $t = 0, 1, 2, \ldots$ ) is not the target state, do

Collect the experience sample ( $r_{t+1}, s_{t+1}, a_{t+1}$ ) given ( $s_{t}, a_{t}$ ): generate $r_{t+1}, s_{t+1}$ by interacting with the environment; generate $a_{t+1}$ following $\pi_{t}(s_{t+1})$ .

Update q-value: $w_{t+1} = w_{t} + \alpha_{t} \left[ r_{t+1} + \gamma \hat{q}(s_{t+1}, a_{t+1}, w_{t}) - \hat{q}(s_{t}, a_{t}, w_{t}) \right] \nabla_{w} \hat{q}(s_{t}, a_{t}, w_{t})$ Update policy: $\pi_{t+1}(a|s_{t}) = 1 - \frac{\varepsilon}{|\mathcal{A}(s_{t})|}(|\mathcal{A}(s_{t})| - 1)$ if $a = \arg\max_{a \in \mathcal{A}(s_{t})} \hat{q}(s_{t}, a, w_{t+1})$ $\pi_{t+1}(a|s_{t}) = \frac{\epsilon}{|\mathcal{A}(s_{t})|}$ otherwise $s_{t} \leftarrow s_{t+1}, a_{t} \leftarrow a_{t+1}$

### 8.3.2 Q-learning with function approximation

Tabular Q-learning can also be extended to the case of function approximation. The update rule is

$$
w _ {t + 1} = w _ {t} + \alpha_ {t} \Big [ r _ {t + 1} + \gamma \max _ {a \in \mathcal {A} (s _ {t + 1})} \hat {q} (s _ {t + 1}, a, w _ {t}) - \hat {q} (s _ {t}, a _ {t}, w _ {t}) \Big ] \nabla_ {w} \hat {q} (s _ {t}, a _ {t}, w _ {t}).\tag{8.36}
$$

The above update rule is similar to (8.35) except that $\hat { q } ( s _ { t + 1 } , a _ { t + 1 } , w _ { t } )$ in (8.35) is replaced with ma $\operatorname { u x } _ { a \in \mathcal { A } ( s _ { t + 1 } ) } \hat { q } ( s _ { t + 1 } , a , w _ { t } )$

Similar to the tabular case, (8.36) can be implemented in either an on-policy or off-policy fashion. An on-policy version is given in Algorithm 8.3. An example for demonstrating the on-policy version is shown in Figure 8.10. In this example, the task is to find a good policy that can lead the agent to the target state from the top-left state.

### Algorithm 8.3: Q-learning with function approximation (on-policy version)

- **Initialization:** Initial parameter $w_{0}$ . Initial policy $\pi_{0}$ . $\alpha_{t} = \alpha > 0$ for all $t. \epsilon \in (0,1)$ .
- **Goal:** Learn an optimal path that can lead the agent to the target state from an initial state $s_{0}$ .
- For each episode, do
- If $s_{t}$ ( $t = 0, 1, 2, \ldots$ ) is not the target state, do

Collect the experience sample ( $a_{t}, r_{t+1}, s_{t+1}$ ) given $s_{t}$ : generate $a_{t}$ following $\pi_{t}(s_{t})$ ; generate $r_{t+1}, s_{t+1}$ by interacting with the environment.

Update q-value: $w_{t+1} = w_{t} + \alpha_{t} \left[ r_{t+1} + \gamma \max_{a \in \mathcal{A}(s_{t+1})} \hat{q}(s_{t+1}, a, w_{t}) - \hat{q}(s_{t}, a_{t}, w_{t}) \right] \nabla_{w} \hat{q}(s_{t}, a_{t}, w_{t})$ Update policy: $\pi_{t+1}(a|s_{t}) = 1 - \frac{\varepsilon}{|\mathcal{A}(s_{t})|}(|\mathcal{A}(s_{t})| - 1)$ if $a = \arg\max_{a \in \mathcal{A}(s_{t})} \hat{q}(s_{t}, a, w_{t+1})$ $\pi_{t+1}(a|s_{t}) = \frac{\varepsilon}{|\mathcal{A}(s_{t})|}$ otherwise

As can be seen, Q-learning with linear function approximation can successfully learn an optimal policy. Here, linear Fourier basis functions of order five are used. The off-policy version will be demonstrated when we introduce deep Q-learning in Section 8.4.

![](7232025795dd381f234b44578adefaaffb04409429fe8a833b2dab301d5185ce.jpg)

![](59c9ffca6a798d7f762325a469323163841877be0a87e5f3b8bd1ba74fd1db6e.jpg)

*Figure 8.10: Q-learning with linear function approximation. Here, $\gamma = 0 . 9 , \epsilon = 0 . 1$ , r<sub>boundary</sub> $r _ { \mathrm { f o r b i d d e n } } = - 1 0 , r _ { \mathrm { t a r g e t } } = 1$ , and $\alpha = 0 . 0 0 1$*

One may notice in Algorithm 8.2 and Algorithm 8.3 that, although the values are represented as functions, the policy $\pi ( a | s )$ is still represented as a table. Thus, it still assumes finite numbers of states and actions. In Chapter 9, we will see that the policies can be represented as functions so that continuous state and action spaces can be handled.

## 8.4 Deep Q-learning

We can integrate deep neural networks into Q-learning to obtain an approach called deep Q-learning or deep Q-network (DQN) [22, 60, 61]. Deep Q-learning is one of the earliest and most successful deep reinforcement learning algorithms. Notably, the neural networks do not have to be deep. For simple tasks such as our grid world examples, shallow networks with one or two hidden layers may be sufficient.

Deep Q-learning can be viewed as an extension of the algorithm in (8.36). However, its mathematical formulation and implementation techniques are substantially different and deserve special attention.

### 8.4.1 Algorithm description

Mathematically, deep Q-learning aims to minimize the following objective function:

$$
J = \mathbb {E} \left[ \left(R + \gamma \max _ {a \in \mathcal {A} (S ^ {\prime})} \hat {q} (S ^ {\prime}, a, w) - \hat {q} (S, A, w)\right) ^ {2} \right],\tag{8.37}
$$

where $( S , A , R , S ^ { \prime } )$ are random variables that denote a state, an action, the immediate reward, and the next state, respectively. This objective function can be viewed as the squared Bellman optimality error. That is because

$$
q (s, a) = \mathbb {E} \left[ R _ {t + 1} + \gamma \max _ {a \in \mathcal {A} (S _ {t + 1})} q (S _ {t + 1}, a) \Big | S _ {t} = s, A _ {t} = a \right], \quad \text { for   all } s, a
$$

is the Bellman optimality equation (the proof is given in Box 7.5). Therefore, $R +$ $\begin{array} { r } { \gamma \operatorname* { m a x } _ { a \in A ( S ^ { \prime } ) } \hat { q } ( S ^ { \prime } , a , w ) - \hat { q } ( S , A , w ) } \end{array}$ should equal zero in the expectation sense when ${ \hat { q } } ( S , A , w )$ can accurately approximate the optimal action values.

To minimize the objective function in (8.37), we can use the gradient descent algorithm. To that end, we need to calculate the gradient of J with respect to w. It is noted that the parameter w appears not only in ${ \hat { q } } ( S , A , w )$ but also in $\begin{array} { r } { y \doteq R \mathrm { + } \gamma \operatorname* { m a x } _ { a \in \mathcal { A } ( S ^ { \prime } ) } \hat { q } ( S ^ { \prime } , a , w ) } \end{array}$ As a result, it is nontrivial to calculate the gradient. For the sake of simplicity, it is as sumed that the value of w in y is fixed (for a short period of time) so that the calculation of the gradient becomes much easier. In particular, we introduce two networks: one is a main network representing ${ \hat { q } } ( s , a , w )$ and the other is a target network $\hat { q } ( s , a , w _ { T } )$ . The objective function in this case becomes

$$
J = \mathbb {E} \left[ \left(R + \gamma \max _ {a \in \mathcal {A} (S ^ {\prime})} \hat {q} (S ^ {\prime}, a, w _ {T}) - \hat {q} (S, A, w)\right) ^ {2} \right],
$$

where $w _ { T }$ is the target network’s parameter. When $w _ { T }$ is fixed, the gradient of J is

$$
\nabla_ {w} J = - \mathbb {E} \left[ \left(R + \gamma \max _ {a \in \mathcal {A} (S ^ {\prime})} \hat {q} (S ^ {\prime}, a, w _ {T}) - \hat {q} (S, A, w)\right) \nabla_ {w} \hat {q} (S, A, w) \right],\tag{8.38}
$$

where some constant coeficients are omitted without loss of generality.

To use the gradient in (8.38) to minimize the objective function, we need to pay attention to the following techniques.

The first technique is to use two networks, a main network and a target network, as mentioned when we calculate the gradient in (8.38). The implementation details are explained below. Let w and $w _ { T }$ denote the parameters of the main and target networks, respectively. They are initially set to the same value.

In every iteration, we draw a mini-batch of samples $\{ ( s , a , r , s ^ { \prime } ) \}$ from the replay bufer (the replay bufer will be explained soon). The inputs of the main network are s and a. The output $\boldsymbol { y } = \boldsymbol { \hat { q } } ( s , a , w )$ is the estimated q-value. The target value of the output is $\begin{array} { r } { y _ { T } \doteq r + \gamma \operatorname* { m a x } _ { a \in \mathcal { A } ( s ^ { \prime } ) } \hat { q } ( s ^ { \prime } , a , w _ { T } ) } \end{array}$ . The main network is updated to minimize the TD error (also called the loss function) $\Sigma ( y - y _ { T } ) ^ { 2 }$ over the samples $\{ ( s , a , y _ { T } ) \}$

Updating w in the main network does not explicitly use the gradient in (8.38). Instead, it relies on the existing software tools for training neural networks. As a result, we need a mini-batch of samples to train a network instead of using a single sample to update the main network based on (8.38). This is one notable difference between deep and nondeep reinforcement learning algorithms.

The main network is updated in every iteration. By contrast, the target network is set to be the same as the main network every certain number of iterations to satisfy the assumption that $w _ { T }$ is fixed when calculating the gradient in (8.38).

◇ The second technique is experience replay [22,60,62]. That is, after we have collected some experience samples, we do not use these samples in the order they were collected. Instead, we store them in a dataset called the replay bufer. In particular, let $( s , a , r , s ^ { \prime } )$ be an experience sample and $B \doteq \{ ( s , a , r , s ^ { \prime } ) \}$ be the replay bufer. Every time we update the main network, we can draw a mini-batch of experience samples from the replay bufer. The draw of samples, or called experience replay, should follow a uniform distribution.

Why is experience replay necessary in deep Q-learning, and why must the replay follow a uniform distribution? The answer lies in the objective function in (8.37). In particular, to well define the objective function, we must specify the probability distributions for $S , A , R , S ^ { \prime }$ . The distributions of R and $S ^ { \prime }$ are determined by the system model once (S, A) is given. The simplest way to describe the distribution of the state-action pair (S, A) is to assume it to be uniformly distributed.

However, the state-action samples may not be uniformly distributed in practice since they are generated as a sample sequence according to the behavior policy. It is necessary to break the correlation between the samples in the sequence to satisfy the assumption of uniform distribution. To do this, we can use the experience replay tech nique by uniformly drawing samples from the replay bufer. This is the mathematical reason why experience replay is necessary and why experience replay must follow a uniform distribution. A benefit of random sampling is that each experience sample may be used multiple times, which can increase the data efficiency. This is especially important when we have a limited amount of data.

### Algorithm 8.3: Deep Q-learning (off-policy version)

- **Initialization:** A main network and a target network with the same initial parameter.
Goal: Learn an optimal target network to approximate the optimal action values from the experience samples generated by a given behavior policy $\pi_{b}$ .
Store the experience samples generated by $\pi_{b}$ in a replay buffer $\mathcal{B}=\{(s,a,r,s')\}$ For each iteration, do
Uniformly draw a mini-batch of samples from B
For each sample $(s,a,r,s')$ , calculate the target value as $y_{T}=r+\gamma\max_{a\in\mathcal{A}(s')} \hat{q}(s',a,w_{T})$ , where $w_{T}$ is the parameter of the target network
Update the main network to minimize $(y_{T}-\hat{q}(s,a,w))^{2}$ using the mini-batch of samples
Set $w_{T}=w$ every C iterations

The implementation procedure of deep Q-learning is summarized in Algorithm 8.3. This implementation is off-policy. It can also be adapted to become on-policy if needed.

### 8.4.2 Illustrative examples

An example is given in Figure 8.11 to demonstrate Algorithm 8.3. This example aims to learn the optimal action values for every state-action pair. Once the optimal action values are obtained, the optimal greedy policy can be obtained immediately.

A single episode is generated by the behavior policy shown in Figure 8.11(a). This behavior policy is exploratory in the sense that it has the same probability of taking any action at any state. The episode has only 1,000 steps as shown in Figure 8.11(b). Although there are only 1,000 steps, almost all the state action pairs are visited in this episode due to the strong exploration ability of the behavior policy. The replay bufer is a set of 1,000 experience samples. The mini-batch size is 100, meaning that we uniformly draw 100 samples from the replay bufer every time we acquire samples.

The main and target networks have the same structure: a neural network with one hidden layer of 100 neurons (the numbers of layers and neurons can be tuned). The neural network has three inputs and one output. The first two inputs are the normalized row and column indexes of a state. The third input is the normalized action index. Here, “normalization” means converting a value to the interval of [0,1]. The output of the network is the estimated value. The reason why we design the inputs as the row and column of a state rather than a state index is that we know that a state corresponds to a two-dimensional location in the grid. The more information about the state we use when designing the network, the better the network can perform. Moreover, the neural network can also be designed in other ways. For example, it can have two inputs and five outputs, where the two inputs are the normalized row and column of a state and the outputs are the five estimated action values for the input state [22].

![](9ebb335b7116989101572c75c0402e4e16f8133298f62425a3cf0b0218e1349e.jpg)

(a) The behavior policy.

![](d214adc3cc695588ac11b22ff1239653d6ad31e4490e70b00e8cc99589cf3929.jpg)

(b) An episode with 1,000 steps.

![](e449ddd84f1e975416f26417b872b31eb5c2dc5c44926576362452e129298fbc.jpg)

(c) The final learned policy.

![](7660135cc1674eb96efb0537f83501e217f582c929756f9beb0893a1b7e15932.jpg)

(d) The loss function converges to zero.

![](872be0375d6db96bb87a410fd30a97a230ed5bdb4aad9e6e58bf82c3865fab9a.jpg)

(e) The value error converges to zero.

*Figure 8.11: Optimal policy learning via deep Q-learning. Here, $\gamma = 0 . 9$ , $r _ { \mathrm { b o u n d a r y } } = r _ { \mathrm { f o r b i d d e n } } = - 1 0$ and $r _ { \mathrm { t a r g e t } } = 1$ . The batch size is 100.*

As shown in Figure 8.11(d), the loss function, defined as the average squared TD error of each mini-batch, converges to zero, meaning that the network can fit the training samples well. As shown in Figure 8.11(e), the state value estimation error also converges to zero, indicating that the estimates of the optimal action values become suficiently accurate. Then, the corresponding greedy policy is optimal.

This example demonstrates the high efficiency of deep Q-learning. In particular, a short episode of 1,000 steps is sufficient for obtaining an optimal policy here. By contrast, an episode with 100,000 steps is required by tabular Q-learning, as shown in Figure 7.4. One reason for the high efficiency is that the function approximation method has a strong generalization ability. Another reason is that the experience samples can be repeatedly used.

We next deliberately challenge the deep Q-learning algorithm by considering a scenario with fewer experience samples. Figure 8.12 shows an example of an episode with merely 100 steps. In this example, although the network can still be well-trained in the sense that the loss function converges to zero, the state estimation error cannot converge to zero. That means the network can properly fit the given experience samples, but the experience samples are too few to accurately estimate the optimal action values.

![](05abe676f2161cda94f0ab365a62a067b531bc59afaeb53d3eb86ddd3a302aed.jpg)

(a) The behavior policy.

![](635b38ee97f0c8ea6d591875ba76c3202f188fb0f4e91d53bccec008b512194f.jpg)

(b) An episode with 100 steps.

![](00b5c883d1c5a65dbdf7f9678fd35041847d4fb7af43e0cf325527b0ee342df3.jpg)

(c) The final learned policy.

![](1ddc76d5b30df56943b720e43f58c826e3ac59d2fc184b7499a7c4d4cf5a73f8.jpg)

(d) The loss function converges to zero.

![](4215d8329d873504b625589f2c20469cbf7384f91ecd6120a5d4cb21ea071323.jpg)

(e) The value error does not converge to zero.

*Figure 8.12: Optimal policy learning via deep Q-learning. Here, $\gamma = 0 . 9 , r _ { \mathrm { b o u n d a r y } } = r _ { \mathrm { f o r b i d d e n } } = - 1 0 \mathrm { { _ { \cdot } } }$ and $r _ { \mathrm { t a r g e t } } = 1$ . The batch size is 50.*

## 8.5 Summary

This chapter continued introducing TD learning algorithms. However, it switches from the tabular method to the function approximation method. The key to understanding the function approximation method is to know that it is an optimization problem. The simplest objective function is the squared error between the true state values and the estimated values. There are also other objective functions such as the Bellman error and the projected Bellman error. We have shown that the TD-Linear algorithm actually minimizes the projected Bellman error. Several optimization algorithms such as Sarsa and Q-learning with value approximation have been introduced.

One reason why the value function approximation method is important is that it allows artificial neural networks to be integrated with reinforcement learning. For example, deep Q-learning is one of the most successful deep reinforcement learning algorithms.

Although neural networks have been widely used as nonlinear function approximators, this chapter provides a comprehensive introduction to the linear function case. Fully understanding the linear case is important for better understanding the nonlinear case. Interested readers may refer to [63] for a thorough analysis of TD learning algorithms with function approximation. A more theoretical discussion on deep Q-learning can be found in [61].

An important concept named stationary distribution is introduced in this chapter. The stationary distribution plays an important role in defining an appropriate objective function in the value function approximation method. It also plays a key role in Chapter 9 when we use functions to approximate policies. An excellent introduction to this topic can be found in [49, Chapter IV]. The contents of this chapter heavily rely on matrix analysis. Some results are used without explanation. Excellent references regarding matrix analysis and linear algebra can be found in [4, 48].

## 8.6 Q&A

Q: What is the difference between the tabular and function approximation methods? A: One important difference is how a value is updated and retrieved.

How to retrieve a value: When the values are represented by a table, if we would like to retrieve a value, we can directly read the corresponding entry in the table. However, when the values are represented by a function, we need to input the state index s into the function and calculate the function value. If the function is an artificial neural network, a forward propagation process from the input to the output is needed.

How to update a value: When the values are represented by a table, if we would like to update one value, we can directly rewrite the corresponding entry in the table. However, when the values are represented by a function, we must update the function parameter to change the values indirectly.

Q: What are the advantages of the function approximation method over the tabular method?

A: Due to the way state values are retrieved, the function approximation method is more efficient in storage. In particular, while the tabular method needs to store values, the function approximation method only needs to store a parameter vector whose dimension is usually much less than .

Due to the way in which state values are updated, the function approximation method has another merit: its generalization ability is stronger than that of the tabular method. The reason is as follows. With the tabular method, updating one state value would not change the other state values. However, with the function approximation method, updating the function parameter affects the values of many states.
