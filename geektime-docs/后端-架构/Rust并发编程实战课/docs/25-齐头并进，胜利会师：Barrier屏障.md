你好，我是鸟窝。

在上节课，我们已经了解了在生产者消费者场景中常用的同步原语——条件变量。这节课我们继续学习Barrier，我们这里把它翻译成屏障。

在并发编程中，多个线程或进程协同工作以完成一项任务是很常见的。然而，在某些情况下，我们需要确保所有参与者都到达某个特定的“汇合点”后，才能继续执行。这时，Barrier（屏障）就派上了用场。

如果你是个体育爱好者，当你看田径比赛中百米赛跑或者跨栏比赛时，你会看到比赛前所有的运动员都会站在起跑线上，这就相当于一个屏障。等所有的运动员就位后，发令枪响起，运动员就可以跑起来了。

Barrier就是这样一种同步原语，**它允许一组线程或进程相互等待，直到所有成员都到达某个预定的点。**

- 到达屏障的线程或进程会被阻塞，直到所有其他成员也到达。
- 一旦所有成员都到达，它们才能同时继续执行。

Barrier内部维护一个计数器，初始化为参与者的数量。每个线程或进程到达屏障时，计数器减一。当计数器变为零时，表示所有参与者都已到达，屏障释放所有线程或进程。

Rust标准库中 `Barrier` 是可重用的。也就是等所有的参与者都已经达到后， `Barrier` 又可以用来下一轮的等待了。

![](https://static001.geekbang.org/resource/image/ff/d9/ff59b04b995af2f60d4d4a4a0cf0b4d9.jpg?wh=3673x2165)

## Barrier介绍

标准库中的Barrier的使用非常简单, 因为主要就new和wait两个函数。

### new 创建一个Barrier

就像函数名一样，new函数创建一个Barrier实例。

`Barrier` 会阻塞调用 `wait()` 的 n-1 个线程，并在第 n 个线程调用 `wait()` 时，同时唤醒所有线程。

创建 `Barrier` 必须指定参与者（线程）的数量。

下面的例子创建了包含三个参与者的实例。

```rust
use std::sync::Barrier;

let barrier = Barrier::new(3);
```

### wait 等待其他线程到达同步点

调用此函数阻塞当前线程，直至所有线程在此处（同步点）完成同步汇合。

当此函数返回时，一个（随机选择的）线程将接收一个 `BarrierWaitResult` 实例，该实例的 `is_leader()` 方法返回 `true`，而所有其他线程将接收 `is_leader()` 方法返回 `false` 的结果。

下面是一个完整的例子。三个参与者同时到达同步点后，其中一个被选做leader：

```rust
use std::sync::{Arc, Barrier};
use std::thread;

fn main() {
    let barrier = Arc::new(Barrier::new(3));
    let mut handles = vec![];
    for i in 0..3 {
        let b = barrier.clone();
        handles.push(thread::spawn(move || {
            println!("Thread {} is waiting at the barrier", i);
            let result = b.wait();
            println!("Thread {} has passed the barrier. is leader: {}", i, result.is_leader());
        }
        ));
    }
    for handle in handles {
        handle.join().unwrap();
    }
    println!("All threads have passed the barrier");
}
```

### 重用

`Barrier` 这个数据结构是可以重用的，这意味着我可以使用 `Barrier` 执行多轮的同步。下面这个例子演示了三个线程执行两轮的同步：

```rust
use std::sync::{Arc, Barrier};
use std::thread;
use std::time::Duration;

fn main() {
    let thread_count = 3;
    let barrier = Arc::new(Barrier::new(thread_count));

    let mut handles = vec![];

    for i in 0..thread_count {
        let barrier_clone = Arc::clone(&barrier);

        let handle = thread::spawn(move || {
            for round in 0..2 { // 每个线程执行两轮
                println!("线程 {}，第 {} 轮，等待...", i, round);

                // 模拟线程执行一些任务
                thread::sleep(Duration::from_millis((i as u64 + 1) * 500));

                barrier_clone.wait(); // 等待所有线程到达屏障

                println!("线程 {}，第 {} 轮，继续执行...", i, round);

                // 模拟线程执行一些任务
                thread::sleep(Duration::from_millis((i as u64 + 1) * 500));
            }
        });

        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("所有线程完成！");
}
```

虽然Rust没有正式定义自己的内存规范，但是 `Barrier` 这个数据结构隐含着当前的 `wait` 的执行一定 `happen before` 它的前一次的 `wait` 成功执行，否则就不能被重用了。

### Barrier vs Condvar

虽然这两者都有阻塞和等待的功能，但是这两个同步原语还是有着明显的不同我梳理了一张表格，方便你直观做对比。

![](https://static001.geekbang.org/resource/image/dd/e2/ddfceb0580f28e0233dd375815b82ee2.jpg?wh=3148x1681)

## 一个并发计算的例子

假设我们需要计算一个大型矩阵的乘法。由于矩阵非常大，单线程计算会非常耗时。为了提高计算效率，我们希望使用多线程并行计算。然而，矩阵乘法的计算过程可以分为多个阶段，每个阶段都需要所有线程完成才能进入下一个阶段。这时，`Barrier` 就非常有用。

```rust
use std::sync::{Arc, Barrier, Mutex};
use std::thread;
use rand::Rng;

// 模拟矩阵数据结构
struct Matrix {
    rows: usize,
    cols: usize,
    data: Vec<Vec<i32>>,
}

fn main() {
    let matrix_size = 100;
    let thread_count = 4;

    // 创建一个随机矩阵
    let matrix1 = Arc::new(Mutex::new(Matrix {
        rows: matrix_size,
        cols: matrix_size,
        data: generate_matrix(matrix_size, matrix_size),
    }));

    // 创建另一个随机矩阵
    let matrix2 = Arc::new(Mutex::new(Matrix {
        rows: matrix_size,
        cols: matrix_size,
        data: generate_matrix(matrix_size, matrix_size),
    }));

    // 创建一个结果矩阵
    let result_matrix = Arc::new(Mutex::new(Matrix {
        rows: matrix_size,
        cols: matrix_size,
        data: vec![vec![0; matrix_size]; matrix_size],
    }));

    let barrier = Arc::new(Barrier::new(thread_count));

    let mut handles = vec![];

    // 创建线程,每个线程计算矩阵乘法的一部分
    for i in 0..thread_count {
        let matrix1_clone = Arc::clone(&matrix1);
        let matrix2_clone = Arc::clone(&matrix2);
        let result_matrix_clone = Arc::clone(&result_matrix);
        let barrier_clone = Arc::clone(&barrier);

        let handle = thread::spawn(move || {
            // 将矩阵分块处理。每个线程处理一部分矩阵
            for row in (i*matrix_size/thread_count)..((i+1)*matrix_size/thread_count) {
                for col in 0..matrix_size {
                    let matrix1_lock = matrix1_clone.lock().unwrap();
                    let matrix2_lock = matrix2_clone.lock().unwrap();
                    let mut result_matrix_lock = result_matrix_clone.lock().unwrap();

                    for k in 0..matrix_size {
                        result_matrix_lock.data[row][col] += matrix1_lock.data[row][k] * matrix2_lock.data[k][col];
                    }
                }
            }

            println!("线程 {}，完成部分计算，等待其他线程...", i);
            barrier_clone.wait(); // 等待所有线程到达屏障
        });

        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("矩阵乘法计算完成！");
}

// 辅助函数：生成随机矩阵
fn generate_matrix(rows: usize, cols: usize) -> Vec<Vec<i32>> {
    let mut rng = rand::thread_rng();
    (0..rows)
        .map(|_| (0..cols).map(|_| rng.gen_range(1..10)).collect())
        .collect()
}
```

这个例子中使用四个线程，每个线程负责计算矩阵乘法的一部分。使用一个`Barrier`同步四个线程，等四个线程都完成后矩阵相乘才完成。

## 总结

好了，在这一节课中，我们了解了Barrier（屏障）这个同步原语，Barrier用于确保多个线程或进程在继续执行之前都到达某个特定的同步点。它通过维护一个计数器实现，当所有参与者都到达时，计数器变为零，屏障释放所有线程。

Rust标准库中的Barrier是可重用的，主要通过`new`函数创建，并使用`wait`函数等待其他线程到达同步点。`wait`函数会阻塞当前线程，直到所有线程完成同步汇合。一个重要的特点是，Barrier可以进行多轮的同步等待。

## 思考题

并发经典的H2O工厂问题描述如下，请使用Barrier实现。

**问题描述**

假设你是一个水分子工厂的工程师。你的工厂接受氢原子（H）和氧原子（O）作为输入，并生产水分子（H₂O）。为了生产水分子，你需要：

- 两个氢原子和一个氧原子。
- 一旦你有了这两个氢原子和一个氧原子，它们必须同时结合形成一个水分子。
- 如果其中一个原子准备好了，它必须等待直到所有原子都准备好。
- 你不能让氢原子或氧原子等待太久。

**目标**

编写一个程序，模拟H₂O工厂，确保满足后面的要求：

- 线程安全：多个氢原子和氧原子线程可以并发运行。
- 正确性：只有当两个氢原子和一个氧原子都准备好时，才能形成水分子。
- 效率：避免不必要的等待。

欢迎你在留言区记录你的思考或疑问。如果今天的内容对你有所帮助，也期待你转发给你的同事或者朋友，大家一起学习，共同进步。我们下节课再见！