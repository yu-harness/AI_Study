你好，我是鸟窝。

在这节课我会介绍一个使用广泛的并发数据结构：mpsc。

`mpsc` 是 “**m**ultiple **p**roducer, **s**ingle **c**onsumer” 的缩写，指的是一种消息传递模式，在这种模式下，可以有多个发送者（生产者）向同一个接收者（消费者）发送消息。

这种模式在并发编程中非常常见，尤其适用于需要将来自多个来源的数据汇总到一个处理单元的场景，或者将任务分发给一个专门的工作线程。例如，在一个日志系统中，多个线程可能需要将日志信息发送到中央日志记录器；在一个任务处理系统中，多个请求可能需要发送给一个后台任务执行器。

![](https://static001.geekbang.org/resource/image/65/39/65c980dc96a68d7e1753b9155e70a039.jpg?wh=3941x2131)

多个来源一致强调 “multiple producer, single consumer” 这一特性 ，这表明它是 `std::sync::mpsc` 的基本特征。这种模式自然适用于多个工作线程需要向中央协调器报告结果或发送任务的情况。这体现了将多个数据流或控制流汇聚到单一处理点的设计思想。

`mpmc` 是 “Multiple Producer Multiple Consumer” 的缩写，指的是一种并发模式，在这种模式下：

- 有多个生产者线程，它们可以同时向一个数据结构（通常是队列）中写入数据。
- 有多个消费者线程，它们可以同时从这个数据结构中读取数据。

`mpmc` 队列在并发编程中非常重要，因为它们允许线程之间高效地传递数据，而无需显式的锁机制（虽然在实现中可能需要内部锁）。这对于构建高性能的并发系统至关重要。

## 消息传递的优势

消息传递是一种越来越流行的确保并发安全的方法，它通过在线程或actor之间发送包含数据的消息来实现通信。这种通信方式与共享内存的并发模型形成对比，后者需要复杂的锁机制来保护共享数据。Go语言的文档中有一句著名的格言：“不要通过共享内存来通信；相反，要通过通信来共享内存” ，这句话精辟地概括了消息传递的核心思想。

通过发送数据而不是共享内存进行通信，可以有效地避免数据竞争和死锁等并发问题。在共享内存模型中，多个线程同时访问和修改同一块内存区域时，如果没有适当的同步机制，就可能导致数据不一致或程序崩溃。而消息传递模型中，数据的所有权在发送时会转移给接收者，发送者在发送后不再持有该数据的引用，从而避免多个线程同时修改数据的风险。

## Rust中所有权和借用在并发中的作用

Rust的所有权和借用规则在消息传递中扮演着至关重要的角色，它们确保了发送的数据在发送后不会被原始线程意外修改或访问。当一个值通过通道发送时，它的所有权会转移到接收端。这意味着发送者在调用 `send()` 方法后，就不能再使用该值。这种所有权转移机制是Rust保证线程安全的关键。

对所有权及其在安全并发中作用的强调表明，Rust 中的 `mpsc` /`mpmc` 与语言的核心内存安全特性紧密集成。这意味着使用 `mpsc` /`mpmc` 本质上受益于Rust的编译时数据竞争检查。语言通过其内存管理系统来实现并发安全，而消息传递正是这种安全策略的重要组成部分。

Go语言使用Channel，将这个思想内置到语言本身中。Rust则通过标准库和第三方库的方式实现类似Go Channel的功能。

首先我们先来介绍 `mpsc`。

## mpsc

`std::sync::mpsc` 模块是Rust标准库中专门用于实现多生产者单消费者（mpsc）通道的模块，它是一个先进先出的队列。

我们重点介绍它的两个函数和三个类型。

### `channel` 和 `sync_channel` 函数

`std::sync::mpsc` 模块提供了两个主要的函数用于创建 mpsc 通道：`channel()` 和 `sync_channel()`，用来创建异步和同步的通道。

异步 (`channel`) 和同步 (`sync_channel`) 两种通道的并存，为不同的并发需求提供了灵活性。当发送者不应被阻塞时，异步通道是合适的选择，而同步通道则提供了背压控制机制。开发者可以根据具体的应用场景，选择最合适的通道类型。

### channel 函数

`channel()` 函数用于创建一个**异步、无限缓冲**的 mpsc 通道，它返回一个元组，包含一个 `Sender`（发送端）和一个 `Receiver`（接收端）。

通过 `Sender` 发送的所有数据，将在 `Receiver` 中按照发送顺序依次可用。并且，任何 `send` 操作都不会阻塞调用线程。只要至少有一个 `Sender` 存活（包括克隆），`recv` 操作就会阻塞，直到有消息可用。

`Sender` 可以被克隆，多个生产者可以并发的向同一通道发送数据，但仅支持一个 `Receiver`。

如果在 `Sender` 尝试 `send` 时 `Receiver` 断开连接，则 `send` 方法将返回 `SendError`。类似地，如果在 `Receiver` 尝试 `recv` 时 `Sender` 断开连接，则 `recv` 方法将返回 `RecvError`。

```rust
use std::sync::mpsc::channel;
use std::thread;

fn main() {
    // 创建一个异步通道
    let (sender, receiver) = channel();

    // 启动一个线程来发送一个值
    thread::spawn(move || {
        sender.send(42).unwrap();
    });

    // 做一些其他的工作
    println!("Doing some work in the main thread...");

    // 打印接收值
    // 注意：在这里我们会阻塞，直到接收到值
    println!("{:?}", receiver.recv().unwrap());
}
```

### sync\_channel 函数

`sync_channel(buffer)` 函数则用于创建一个**同步、有缓冲**的 mpsc 通道，它也返回一个元组，包含一个 `SyncSender`（同步发送端）和一个 `Receiver`（接收端）。

与异步通道不同，同步通道拥有一个固定大小的缓冲区，这个大小在调用 `sync_channel()` 时通过参数 `buffer` 来指定。

通过 `SyncSender` 发送的所有数据，将在 `Receiver` 中按照发送顺序依次可用。与异步通道类似，`Receiver` 会阻塞，直到有消息可用。

然而，`sync_channel` 在发送端的语义上有很大不同。此通道有一个内部缓冲区，消息将在其中排队。`bound` 指定缓冲区大小。当内部缓冲区变满时，后续的发送操作将会**阻塞**，直到接收端从通道中接收一个消息，释放出缓冲区空间。

```rust
use std::sync::mpsc::sync_channel;
use std::thread;

fn main() {
    // 创建一个同步通道，缓冲区大小为1
    let (sender, receiver) = sync_channel(1);

    // 这次调用会立即返回
    sender.send(1).unwrap();

    thread::spawn(move || {
        // 这次调用会阻塞，直到前一个消息被接收
        sender.send(2).unwrap();
    });

    assert_eq!(receiver.recv().unwrap(), 1);
    assert_eq!(receiver.recv().unwrap(), 2);
}
```

特别地，当缓冲区大小设置为0时，同步通道会变成一个“会合通道”（rendezvous channel），此时发送者发送数据的时候会被阻塞，每个 `send` 操作都不会返回，直到接收者准备好立即接收消息。在这种类型的channel中，发送者和接收者必须同时就绪才能完成消息传递。

![](https://static001.geekbang.org/resource/image/30/5c/302a93e1fff34e8d6e5e9182e19c0f5c.jpg?wh=3726x1873)

```rust
use std::sync::mpsc::sync_channel;
use std::thread;

fn main() {
    // 创建一个同步通道，缓冲区大小为1
    let (sender, receiver) = sync_channel(0);

    thread::spawn(move || {
        // 这次调用会阻塞，直到消费者准备接收数据
        sender.send(42).unwrap();
    });

    // 准备接收数据，生产者不会阻塞了
    assert_eq!(receiver.recv().unwrap(), 42);
}
```

## mpsc 的三个类型

在上面的例子中我们已经看到了三种类型：`Receiver`、`Sender` 和 `SyncSender`。

### Receiver 消费者

此接收端只能由一个线程拥有。

发送到通道的消息可以使用 `recv` 方法进行接收。

#### recv 接收数据

尝试等待 `Receiver` 上的一个值，**如果对应的通道已挂起，则返回错误**。

如果没有可用数据，并且未来有可能发送更多数据（至少存在一个发送者），则此函数将始终阻塞当前线程。一旦消息被发送到对应的 `Sender`（或 `SyncSender`），此接收器将唤醒并返回该消息。

如果对应的 `Sender` 已断开连接，或者在调用阻塞时断开连接，则此调用将唤醒并返回 `Err`，以表明此通道上无法再接收任何消息。但是，由于通道具有缓冲区，因此在断开连接之前发送的消息仍将被正确接收。这个和Go通道的处理方式是一样的。

```rust
use std::sync::mpsc;
use std::sync::mpsc::RecvError;
use std::thread;

fn main() {
    let (send, recv) = mpsc::channel();
    let handle = thread::spawn(move || {
        send.send(1u8).unwrap();
        send.send(2).unwrap();
        send.send(3).unwrap();
        drop(send);
    });

    // 等待发送线程结束，确保发送者被丢弃
    handle.join().unwrap();

    // 虽然发送者已被丢弃，但是通道中缓存的数据还是可以取出
    assert_eq!(Ok(1), recv.recv());
    assert_eq!(Ok(2), recv.recv());
    assert_eq!(Ok(3), recv.recv());
    assert_eq!(Err(RecvError), recv.recv());
}
```

还有两个和超时相关的方法，我们继续往下看。

#### recv\_timeout 带超时功能的接收数据

尝试等待接收器上的一个值，如果对应的通道已挂起，或者等待时间超过 `timeout`**，**则返回错误。

如果没有可用数据，并且有可能发送更多数据（至少存在一个发送者），则此函数将始终阻塞当前线程。一旦消息被发送到对应的 `Sender`（或 `SyncSender`），此接收器将唤醒并返回该消息。

如果对应的 `Sender` 已断开连接，或者在调用阻塞时断开连接，则此调用将唤醒并返回 `Err`，以表明此通道上无法再接收任何消息。但是，由于通道具有缓冲区，因此在断开连接之前发送的消息仍将被正确接收。

```rust
use std::thread;
use std::time::Duration;
use std::sync::mpsc;

fn main() {
    let (tx, rx) = mpsc::channel();
    // 启动一个线程来发送一个消息，延迟2秒
    thread::spawn(move || {
        thread::sleep(Duration::from_secs(2));
        tx.send("Hello").unwrap();
    });

    // 这里的超时是1秒
    match rx.recv_timeout(Duration::from_secs(1)) {
        Ok(msg) => println!("Received: {}", msg),
        Err(e) => println!("Error: {}", e),
    }
}
```

#### recv\_deadlime 带deadline功能的接收数据

尝试等待接收器上的一个值，如果对应的通道已挂起，或者到达 `deadline` 指定的截止时间，则返回错误。

如果没有可用数据，并且有可能发送更多数据，则此函数将始终阻塞当前线程。一旦消息被发送到对应的 `Sender`（或 `SyncSender`），此接收器将唤醒并返回该消息。

如果对应的 `Sender` 已断开连接，或者在调用阻塞时断开连接，则此调用将唤醒并返回 `Err`，以表明此通道上无法再接收任何消息。但是，由于通道具有缓冲区，因此在断开连接之前发送的消息仍将被正确接收。

```rust
#![feature(deadline_api)]
use std::thread;
use std::time::{Duration, Instant};
use std::sync::mpsc;

fn main() {
    let (send, recv) = mpsc::channel();

    thread::spawn(move || {
        send.send('a').unwrap();
    });

    assert_eq!(
        // 这里会阻塞，直到接收到值
        // 但是如果在400ms内没有接收到值，就会返回一个错误
        recv.recv_deadline(Instant::now() + Duration::from_millis(400)),
        Ok('a')
    );
}
```

#### try\_recv 非阻塞接收数据

尝试在不阻塞的情况下，从此接收器返回一个待处理的值。

此方法永远不会为了等待数据可用而阻塞调用者。相反，它总是会立即返回，并可能包含通道上的待处理数据。

与`recv` 相比，此函数有两个失败情况而不是一个（一个用于断开连接，一个用于空缓冲区）。如果空缓冲区还没有发送者发送数据，它就返回一个Err。

```rust
use std::sync::mpsc::{Receiver, channel};

fn main() {
    let (_, receiver): (_, Receiver<i32>) = channel();

    assert!(receiver.try_recv().is_err());
}
```

#### iter 转换成迭代器

返回一个迭代器，该迭代器会阻塞等待消息，但绝不会发生 `panic!` 异常。当通道挂起时，它将返回 `None`。

```rust
use std::sync::mpsc::channel;
use std::thread;

fn main() {
    let (send, recv) = channel();

    thread::spawn(move || {
        // 发送三个值, 然后send会被丢弃
        send.send(1).unwrap();
        send.send(2).unwrap();
        send.send(3).unwrap();
    });

    let mut iter = recv.iter();
    for i in 1..=3 {
        assert_eq!(iter.next(), Some(i));
    }
    // 通道被挂起后(send被丢弃)，它会返回一个 None
    assert_eq!(iter.next(), None);

}
```

在我们的日常使用中，我们更常用的是下面的方式，将接收器自动转换成迭代器，并在循环中一直接收，直到通道被挂起：

```rust
use std::sync::mpsc::channel;
use std::thread;

fn main() {
    let (send, recv) = channel();

    thread::spawn(move || {
        // 发送三个值, 然后send会被丢弃
        send.send(1).unwrap();
        send.send(2).unwrap();
        send.send(3).unwrap();
    });

    for n in recv {
        // 迭代器会阻塞，直到接收到值
        println!("Received: {}", n);
    }
}
```

#### try\_iter 非阻塞的迭代器

返回一个迭代器，该迭代器将尝试产生所有待处理的值。如果没有更多待处理的值或通道已挂起，它将返回 `None`。该迭代器绝不会发生 `panic!` 异常，也不会因等待值而阻塞用户。

```rust
use std::sync::mpsc::channel;
use std::thread;
use std::time::Duration;

fn main() {
    let (sender, receiver) = channel();

    // 还没有数据，返回None
    assert!(receiver.try_iter().next().is_none());
    
    thread::spawn(move || {
        thread::sleep(Duration::from_secs(1));
        sender.send(1).unwrap();
        sender.send(2).unwrap();
        sender.send(3).unwrap();
    });
    
    // 还没有数据，返回None
    assert!(receiver.try_iter().next().is_none());
    
    // 等待两秒
    thread::sleep(Duration::from_secs(2));
    
    let mut iter = receiver.try_iter();
    assert_eq!(iter.next(), Some(1));
    assert_eq!(iter.next(), Some(2));
    assert_eq!(iter.next(), Some(3));
    // 迭代器已经没有数据了
    assert_eq!(iter.next(), None);
}
```

### Sender 异步生产者

Rust 异步通道类型的发送端。

消息可以通过此通道使用 `send` 方法发送。

**注意：**只有当所有发送端（原始的和它的克隆）都被丢弃后，接收端才会停止阻塞等待接收消息。

#### send 发送数据

尝试在此通道上发送一个值，如果发送失败则将其返回。

当确定通道的另一端尚未挂起时，发送即为成功。发送不成功的情况是指对应的接收端已被释放。请注意，返回 `Err` 意味着数据将永远不会被接收，但返回 `Ok` **并不**意味着数据一定会被接收。对应的接收端可能在此函数返回 `Ok` 后立即挂起。

**此方法永远不会阻塞当前线程。**

```rust
use std::sync::mpsc::channel;

fn main() {
    // 创建一个异步通道
    let (sender, receiver) = channel();
    let result = sender.send(42);
    println!("{:?}", result); // 发送成功，返回 Ok

    drop(receiver); // 关闭接收器

    let result = sender.send(42);
    println!("{:?}", result); // 发送失败，返回 Err
}
```

### SyncSender 同步生产者

Rust 同步通道 `sync_channel` 类型的发送端。

消息可以通过此通道使用 `send` 或 `try_send` 方法发送。

如果内部缓冲区没有空间，`send` 方法将会阻塞。

#### send 发送数据

在此同步通道上发送一个值。

此函数将会**阻塞**，直到内部缓冲区有可用空间，或者由接收端准备好接收消息。

请注意，即使发送成功，如果此通道存在缓冲区，也**不能**保证接收端最终会看到数据。数据可能会在内部缓冲区中排队，供接收端稍后接收，接收端如果放弃接收数据，接收端就看不到这个数据了。

然而，如果缓冲区大小为 0，则该通道会变成一个会合通道，并且如果此函数返回成功，则保证接收端已经接收到了数据。

此函数绝不会发生 panic，但如果 `Receiver` 已经断开连接并且无法再接收信息，则可能会返回 `Err`。

```rust
use std::sync::mpsc::sync_channel;
use std::thread;

fn main() {
    // 创建一个同步通道，缓冲区大小为0
    let (sync_sender, receiver) = sync_channel(0);

    thread::spawn(move || {
        println!("sending message...");
        sync_sender.send(1).unwrap(); // 线程会被阻塞，直到接收者准备好接收数据
        println!("...message received!");
    });

    let msg = receiver.recv().unwrap();
    assert_eq!(1, msg);
}
```

#### try\_send 非阻塞发送数据

尝试在此通道上发送一个值，但不阻塞。

如果通道的缓冲区已满或没有接收端等待获取数据，此方法会立即返回，这与 `send` 方法不同。与 `send` 相比，此函数有两个失败情况而不是一个（一个用于断开连接，一个用于缓冲区已满）。

请注意，即使发送成功，如果此通道存在缓冲区，也**不能**保证接收端最终会看到数据。数据可能会在内部缓冲区中排队，供接收端稍后接收，接收端如果放弃接收数据，接收端就看不到这个数据了。

然而，如果缓冲区大小为 0，则该通道会变成一个会合通道，并且如果此函数返回成功，则保证接收端已经接收到了数据。

## mpsc 异常情况 (Error)

我们看到，创建通道的时候会返回一个元组，一个是接收者（消费者），一个是可克隆的发送者（生产者），它们之间建立了连接。

通道上的发送和接收操作都会返回一个 `Result`，指示操作是否成功。不成功的操作通常表明通道的另一半已“挂起”，即在其对应的线程中被丢弃。

一旦通道的一半被释放，大多数操作都无法继续进行，因此会返回 `Err`。许多应用程序会继续解包（unwrap）从此模块返回的结果，如果某个线程意外终止，则会在线程之间引发故障传播。

这个模块下定义了发送和接收数据的Error类型：

- SendError: 此通道已经挂起，也就是此通道的Receiver已经被丢弃。
- RecvError：此通道已经挂起，也就是此通道的所有Send已经被丢弃，且缓冲区没有数据了。
- TrySendError: 此通道已被挂起，或者缓冲区已满。
- TryRecvError: 此通道已被挂起，或者缓冲区已空。

不像Go语言中的通道存在潜在的panic的场景， Rust的mpsc通道基本不会出现panic的情况，使用起来没有心理负担（话不能说满，除非你非得构造一种panic的场景）。

## mpsc 常见使用场景

`mpsc` 通道是实现线程间安全通信的常用方法。在需要将数据从一个线程传递到另一个线程的场景中，例如工作线程向主线程报告进度或结果，或者主线程向工作线程发送任务指令，`mpsc` 都非常适用。

以下代码示例演示了如何使用 `mpsc` 让多个工作线程将计算结果发送回主线程。

```rust
use std::sync::mpsc;
use std::thread;

fn main() {
    let num_workers = 4;
    let (tx, rx) = mpsc::channel();

    for i in 0..num_workers {
        let tx_clone = tx.clone();
        thread::spawn(move |
| {
            // 模拟一些计算
            let result = i * i;
            println!("Worker {} finished, sending result: {}", i, result);
            tx_clone.send(result).unwrap();
        });
    }

    let mut results = Vec::new();
    for _ in 0..num_workers {
        results.push(rx.recv().unwrap());
    }

    println!("All results received: {:?}", results);
}
```

## mpmc

了解了mpsc, 我们就容易理解mpmc了。

这是一个仅限 Nightly 版本使用的实验性 API，所以还没有在正式版中发布。

它提供了基于通道的消息通信，具体由以下两种类型定义：

- `Sender`（发送者）
- `Receiver`（接收者）

`Sender` 用于将数据发送到一组 `Receiver`。`Sender` 和 `Receiver` **都是可克隆**的（多生产者），因此多个线程可以同时向多个接收者发送消息（多消费者）。

这些通道有两种类型：

- 异步、无限缓冲通道。`channel` 函数将返回一个 `(Sender, Receiver)` 元组，其中所有发送操作都是*异步*的（它们永远不会阻塞）。从概念上讲，该通道具有无限缓冲区。
- 同步、有界通道。`sync_channel` 函数将返回一个 `(Sender, Receiver)` 元组，其中用于存储待处理消息的存储空间是一个预分配的、固定大小的缓冲区。所有发送操作都是*同步*的，即会阻塞，直到有可用的缓冲区空间。请注意，允许缓冲区大小为 0，这会导致通道变为“会合”通道，其中每个发送者原子地将消息交给一个接收者。

因为和mpsc的使用方法很像，所以我就不详细介绍它了。下面是一个例子：

```rust
#![feature(mpmc_channel)]

use std::thread;
use std::sync::mpmc::channel;

thread::scope(|s| {
    // 创建一个通道，可以多线程写，多线程读
    let (tx, rx) = channel();
    for i in 0..10 {
        let tx = tx.clone();
        s.spawn(move || {
            tx.send(i).unwrap();
        });
    }

    for _ in 0..5 {
        let rx1 = rx.clone();
        let rx2 = rx.clone();
        s.spawn(move || {
            let j = rx1.recv().unwrap();
            assert!(0 <= j && j < 10);
        });
        s.spawn(move || {
            let j = rx2.recv().unwrap();
            assert!(0 <= j && j < 10);
        });
    }
})
```

需要注意的是，多个消费者是负载均衡的读取通道的数据，而不是每个消费者都接收同样的数据。

## 总结

好了，在这一节课中，我们介绍了 Rust 中广泛使用的并发数据结构 `mpsc`，它是 “multiple producer, single consumer” 的缩写，意指多个发送者可以向同一个接收者发送消息。这种模式常用于并发编程中，特别是在需要汇总多个来源的数据或将任务分发给单个处理单元的场景。

消息传递通过在线程间发送数据而非共享内存来实现安全并发，避免了数据竞争和死锁。Rust 的所有权和借用机制确保了发送数据的安全转移。`std::sync::mpsc` 模块提供了创建异步 (`channel`) 和同步 (`sync_channel`) 通道的函数，以及 `Receiver`（接收者）、`Sender`（异步发送者）和 `SyncSender`（同步发送者）三种类型。

通道操作会返回 `Result`，指示操作是否成功，不成功通常表示通道的另一端已断开。`mpsc` 通道常用于线程间安全通信，例如工作线程向主线程报告结果或接收任务。

## 思考题

`mpsc`代表多生产者单消费者，我们还了解到了一个未正式发布的多生产者多消费者（`mpmc`），那么是否还存在单生产者多消费者（`spmc`）以及以及单生产者单消费者（`spsc`）的数据结构？你知道有哪些么，请罗列出来。

欢迎你在留言区记录你的思考或疑问。如果今天的内容对你有所帮助，也期待你转发给你的同事或者朋友，大家一起学习，共同进步。我们下节课再见！