你好，我是鸟窝。

在上节课我们已经了解了Rust的异步编程的基本知识，而且我们也学会了编写异步编程的代码。但是Rust标准库并没有提供异步运行时的实现，所以我们需要借助第三方实现的异步运行时库。

信号量（Semaphore）是一种经典的同步原语，用于控制对共享资源的访问。**它维护一个计数器，表示可用资源的数量**。线程可以通过以下两种操作来使用信号量：

- **acquire()（P操作或down操作）**：尝试获取一个许可。如果计数器大于0，则计数器减1，线程继续执行；否则，线程将被阻塞，直到有许可可用。
- **release()（V操作或up操作）**：释放一个许可，使计数器加1。如果有等待的线程，则唤醒其中一个。

**信号量的核心在于对计数器的管理**，通过限制计数器的值，可以控制同时访问共享资源的线程数量。

信号量在并发编程中有广泛的应用，以下是一些常见的场景：

- **资源限制**：限制同时访问某个资源的线程数量，例如数据库连接池、文件句柄等。
- **线程同步**：协调多个线程的执行顺序，例如生产者-消费者模型。
- **互斥锁**：实现互斥访问共享资源，相当于二元信号量（计数器初始值为1）。
- **流量控制**：限制系统的并发请求数量，防止系统过载。

Rust标准库中并没有实现信号量同步原语，就像Go语言一样（Go官方扩展库中实现了一个信号量），我也觉得很奇怪，这个信号量是最早被研究的同步原语之一，使用场景也很广泛，为啥两大编程语言都不在标准库中实现呢？

Rust生态圈中有一些第三方的实现，这节课我们就来学习Tokio中实现的信号量 `Semaphore`。

## Tokio中的信号量

在Rust中，`tokio` 库提供了信号量的实现，通过 `tokio::sync::Semaphore` 结构体实现这点。

![](https://static001.geekbang.org/resource/image/8a/6b/8a5fc2044fec71f76e1fe2c795a0b96b.jpg?wh=2766x1673)

`tokio` 库实现的信号量维护一组**许可**（**permits**），这些许可用于同步对共享资源的访问。与互斥锁（mutex）不同，信号量允许同时有多个调用者访问共享资源。

当调用 `acquire` 方法且信号量仍有剩余许可时，该方法会立即返回一个许可。然而，如果许可已全部耗尽，`acquire` 方法将（异步地）等待，直到某个已分配的许可被释放。此时，被释放的许可将被分配给等待的调用者。

此信号量采用**公平策略**，即按照请求的顺序分配许可。当调用 `acquire_many` 方法时，也遵循此公平原则。因此，如果队列前端的 `acquire_many` 请求的许可数量超过当前可用数量，即使信号量有足够的许可来满足 `acquire` 方法的请求，也可能阻止 `acquire` 方法完成（先请求先满足）。

就像前面讲的那样，信号量最重要的是两个方法：`acquire` 和 `release`，但是基于Rust的RAII（Resource Acquisition Is Initialization）语言特性，Rust并没有提供 `release` 函数，而是通过 `drop(permit)` 的方式释放许可，也就是当线程完成对共享资源的使用后，它通过丢弃 `permit` 对象，将许可归还给信号量。

`tokio::sync::Semaphore` 结构提供了很多 `acquire` 的相关方法以及`try_acquire` 相关方法，我们首先学习它们，然后看看其他的一些方法，最后我们再去了解 `SemaphorePermit`。

### new 和 const\_new

按照惯例，我们还是先讲 `new` 和 `const_new`。

`new` 函数用来创建一个指定初始许可的信号量。

`const_new` 函数则是创建一个指定初始许可的信号量常量。它是一个常量函数 (`const fn`)，这意味着它可以在编译时被调用。这允许你在编译时创建 `Semaphore` 实例，例如，在静态变量或常量中。这提供了潜在的性能优势，因为对象在编译时创建，而不是在运行时。

使用 `const_new` 创建的 `Semaphore` 不会被 `tracing` 库（用于 tokio-console）检测到。因此，这些信号量不会在 tokio-console 中显示。这个函数被设计为在常量环境中使用，因此牺牲了运行时的性能分析能力。

```rust
use tokio::sync::Semaphore;

static SEM: Semaphore = Semaphore::const_new(10);
```

### acquire 方法族

接下来我们看看acquire 方法族。

#### acquire 获取一个许可

从信号量中获取一个许可，如果当前没有许可，则等待。

如果信号量已被关闭，则返回一个 `AcquireError`。否则，返回一个表示已获取许可的 `SemaphorePermit`。

此方法使用队列按请求顺序公平地分配许可。取消对 `acquire` 的调用将导致您在队列中失去位置。

```rust
use tokio::sync::Semaphore;

#[tokio::main]
async fn main() {
    let semaphore = Semaphore::new(2);

    // 请求一个许可
    let permit_1 = semaphore.acquire().await.unwrap();
    assert_eq!(semaphore.available_permits(), 1);

    // 请求另一个许可
    let permit_2 = semaphore.acquire().await.unwrap();
    assert_eq!(semaphore.available_permits(), 0);

    // 主动释放第一个许可
    drop(permit_1);
    assert_eq!(semaphore.available_permits(), 1);
}
```

#### acquire\_many 请求多个许可

从信号量中获取 n 个许可。

如果信号量已被关闭，则返回一个 `AcquireError`。否则，返回一个 `SemaphorePermit`，该对象表示已获取的许可集合，所以释放的时候也是一起释放多个许可。

```rust
use tokio::sync::Semaphore;

#[tokio::main]
async fn main() {
    // 创建一个信号量，初始许可数为5
    let semaphore = Semaphore::new(5);

    // 请求3个许可
    let permit = semaphore.acquire_many(3).await.unwrap();
    assert_eq!(semaphore.available_permits(), 2); // 剩余许可数为2
}
```

#### acquire\_owned 请求一个许可

从信号量获取一个“拥有的”许可。

调用此方法需要将信号量封装于 `Arc`。若信号量已关闭，返回 `AcquireError`。否则，返回表示所获许可的 `OwnedSemaphorePermit`。

常常用在多线程的场景中，如下面的例子：

```rust
use std::sync::Arc;
use tokio::sync::Semaphore;

#[tokio::main]
async fn main() {
    // 创建一个信号量，初始许可数为3。
    // 并且使用 `Arc` 来共享信号量的所有权。
    let semaphore = Arc::new(Semaphore::new(3));
    let mut join_handles = Vec::new();

    // 启动5个异步任务，每个任务都请求一个许可。
    // 由于信号量的初始许可数为3，所以只有3个任务可以同时获得许可。
    // 其他任务会被阻塞，直到有许可可用。
    for _ in 0..5 {
        let permit = semaphore.clone().acquire_owned().await.unwrap();
        join_handles.push(tokio::spawn(async move {
            // 在这个任务中拥有许可
            println!("任务拥有许可，正在执行...");
            // 执行一些业务逻辑

            // 当任务完成时，释放许可
            drop(permit);
        }));
    }

    for handle in join_handles {
        handle.await.unwrap();
    }
}
```

#### acquire\_owned\_many 请求多个许可

类似的，从信号量获取多个“拥有的”许可。

调用此方法需要将信号量封装于 `Arc`。若信号量已关闭，返回 `AcquireError`。否则，返回表示所获许可的 `OwnedSemaphorePermit`。

```rust
use std::sync::Arc;
use tokio::sync::Semaphore;

#[tokio::main]
async fn main() {
    // 创建一个信号量，初始许可数为10。
    // 并且使用 `Arc` 来共享信号量的所有权。
    let semaphore = Arc::new(Semaphore::new(10));
    let mut join_handles = Vec::new();

    for _ in 0..5 {
        // 请求2个许可
        let permit = semaphore.clone().acquire_many_owned(2).await.unwrap();
        join_handles.push(tokio::spawn(async move {
            // 在这个任务中拥有许可
            println!("任务拥有许可，正在执行...");
            // 执行一些业务逻辑

            // 当任务完成时，释放许可
            drop(permit);
        }));
    }

    for handle in join_handles {
        handle.await.unwrap();
    }
}
```

当信号量没有足够的许可时，这四个请求许可的函数会被阻塞，直到有充足的许可可以被分配。如果不想被阻塞，可以使用这四个函数对应的 `try_xxx` 函数，它们可以保证不会被阻塞。如果有足够的许可，它们会返回分配的许可，否则返回 `TryAcquireError::Closed` 或 `TryAcquireError::NoPermits`。

- `try_acquire`
- `try_acquire_many`
- `try_owned`
- `try_owned_many`

接下来我们再介绍几个辅助方法。

### add\_permits 增加许可

信号量在创建的时候不是提供了一个初始的许可么？运行时我们还可以使用这个函数动态的添加n个许可。

但是总得许可数不能超过 `Semaphore::MAX_PERMITS`，否则就会panic。

### forget\_permits 减少许可

同样的我们也可以减少n个许可。(为啥函数的命令不是那么对称呢？)

如果没有充足的许可可以被减少，那么就会返回能够减少的许可的总数。

### available\_permits 返回当前可用的许可

返回当前可用的许可数。

### close 关闭信号量

此操作会阻止信号量发放新的许可，并通知所有等待中的任务。

### is\_closed 返回信号量是否已经关闭

此操作用于返回信号量是否已经关闭。

## 使用场景

了解了这么多方法，我们再来关注一下使用场景。信号量在资源控制、限流场景中都有用武之地。

事实上在 `acquire_owned` 那一节我们的例子里，已经展示了利用信号量限制最多三个线程同时处理。接下来我们再来看一个限制并发发送请求数量的例子。

### 限制并发发送的请求数量

为遵守 API 或系统网络资源限制，有时需控制并发请求量。比如你的爬虫如果没有控制，有可能把别人的网站整垮，惹上不必要的法律纠纷。

这个使用 10 个许可的 `Arc<Semaphore>`。每个任务克隆 `Arc<Semaphore>` 获取信号量引用。任务发送请求前，需调用 `Semaphore::acquire` 获取许可，保证最多 10 个请求并发。请求发送后，任务释放许可，允许其他任务发送。

```rust
use std::sync::Arc;
use tokio::sync::Semaphore;

#[tokio::main]
async fn main() {
    // 定义一个信号量，初始许可数为10,也是我们的发送并发量。
    // 使用 `Arc` 来共享信号量的所有权。
    let semaphore = Arc::new(Semaphore::new(10));
    // 创建非常多的异步任务，每个任务都尝试获取信号量的许可。
    let mut jhs = Vec::new();
    for task_id in 0..100 {
        let semaphore = semaphore.clone();
        let jh = tokio::spawn(async move {
            // 发送请求之前，先获取信号量的许可。
            let _permit = semaphore.acquire().await.unwrap();
            // 发送请求
            let response = send_request(task_id).await;
            // 请求完成后，释放许可。
            drop(_permit);
            
            // 返回请求的响应
            response
        });
        jhs.push(jh);
    }
    
    // 等待所有任务完成
    let mut responses = Vec::new();
    for jh in jhs {
        let response = jh.await.unwrap();
        responses.push(response);
    }
}

async fn send_request(task_id: usize) -> String {
    // 模拟发送请求的延迟
    // 实际的请求发送逻辑会在这里实现
    tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    format!("Response from task {}", task_id)
}
```

### 限流

我们可以通过实现令牌桶的方式实现限流。

这个例子演示 `add_permits` 和 `SemaphorePermit::forget` 的用法。为避免性能下降或错误，应用和系统常对操作频率设限，这个例子用令牌桶实现速率限制，允许短时突发请求。令牌桶中，每个请求消耗一个令牌，并按设定速率补充。突发请求会立即消耗令牌，直至桶空。桶空了之后，请求需等待新令牌。

与限制并发请求数的例子不同，请求完成后不归还令牌，令牌仅由定时器补充。这里需要注意的是，短周期下，此实现非最优，持续循环休眠会消耗大量 CPU。

```rust
use std::sync::Arc;
use tokio::sync::Semaphore;
use tokio::time::{interval, Duration};

struct TokenBucket {
    sem: Arc<Semaphore>,
    jh: tokio::task::JoinHandle<()>,
}

impl TokenBucket {
    fn new(duration: Duration, capacity: usize) -> Self {
        let sem = Arc::new(Semaphore::new(capacity));

        // 每个周期内，信号量的许可数会增加1。
        let jh = tokio::spawn({
            let sem = sem.clone();
            let mut interval = interval(duration);
            interval.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);

            async move {
                loop {
                    interval.tick().await;

                    if sem.available_permits() < capacity {
                        sem.add_permits(1);
                    }
                }
            }
        });

        Self { jh, sem }
    }

    async fn acquire(&self) {
        // 请求1个许可，然后信号量会减少一个
        let permit = self.sem.acquire().await.unwrap();
        permit.forget();
    }
}

impl Drop for TokenBucket {
    fn drop(&mut self) {
        // 这是一个小技巧，在drop时取消任务，避免泄露。
        self.jh.abort();
    }
}

#[tokio::main]
async fn main() {
    simple_logger::SimpleLogger::new().env().init().unwrap();
    let capacity = 3;
    let update_interval = Duration::from_secs_f32(1.0 / capacity as f32);
    let bucket = TokenBucket::new(update_interval, capacity);

    // 应该每秒释放三个许可
    loop  {
        bucket.acquire().await;  
        log::info!("acquired a token");
    }
}
```

## 总结

好了，在这一节课中，我们了解了信号量的知识。

信号量是一种同步工具，通过维护一个计数器来控制对共享资源的访问，它可以用来限制同时访问某个资源的线程数量，或者用来做流量控制。

Tokio 库等第三方库提供了信号量的实现，它允许同时有多个调用者访问共享资源，这与互斥锁不同。

信号量在资源限制、线程同步、流量控制等场景中都有丰富的应用，虽然二元信号量（只有一个许可）也可以当互斥锁使用，但是因为我们有了专门的互斥锁Mutex，所以二元信号量当锁使用不是那么广泛。

## 思考题

请你使用信号量实现有一个有界缓冲区（固定大小的队列），支持多生产者-多消费者。可以使用这两个信号量：

- `empty`：表示缓冲区中空闲位置的数量。
- `full`：表示缓冲区中数据的数量。

欢迎你在留言区记录你的思考或疑问。如果今天的内容对你有所帮助，也期待你转发给你的同事或者朋友，大家一起学习，共同进步。我们下节课再见！