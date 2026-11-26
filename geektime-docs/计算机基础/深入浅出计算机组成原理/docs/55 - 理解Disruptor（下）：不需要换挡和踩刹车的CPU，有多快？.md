上一讲，我们学习了一个精妙的想法，Disruptor通过缓存行填充，来利用好CPU的高速缓存。不知道你做完课后思考题之后，有没有体会到高速缓存在实践中带来的速度提升呢？

不过，利用CPU高速缓存，只是Disruptor“快”的一个因素，那今天我们就来看一看Disruptor快的另一个因素，也就是“无锁”，而尽可能发挥CPU本身的高速处理性能。

## 缓慢的锁

Disruptor作为一个高性能的生产者-消费者队列系统，一个核心的设计就是通过RingBuffer实现一个无锁队列。

上一讲里我们讲过，Java里面的基础库里，就有像LinkedBlockingQueue这样的队列库。但是，这个队列库比起Disruptor里用的RingBuffer要慢上很多。慢的第一个原因我们说过，因为链表的数据在内存里面的布局对于高速缓存并不友好，而RingBuffer所使用的数组则不然。

![](https://static001.geekbang.org/resource/image/9c/69/9ce732cb22c49a8a26e870dddde66b69.jpeg?wh=2566%2A2059)

LinkedBlockingQueue慢，有另外一个重要的因素，那就是它对于锁的依赖。在生产者-消费者模式里，我们可能有多个消费者，同样也可能有多个生产者。多个生产者都要往队列的尾指针里面添加新的任务，就会产生多个线程的竞争。于是，在做这个事情的时候，生产者就需要拿到对于队列尾部的锁。同样地，在多个消费者去消费队列头的时候，也就产生竞争。同样消费者也要拿到锁。

那只有一个生产者，或者一个消费者，我们是不是就没有这个锁竞争的问题了呢？很遗憾，答案还是否定的。一般来说，在生产者-消费者模式下，消费者要比生产者快。不然的话，队列会产生积压，队列里面的任务会越堆越多。

一方面，你会发现越来越多的任务没有能够及时完成；另一方面，我们的内存也会放不下。虽然生产者-消费者模型下，我们都有一个队列来作为缓冲区，但是大部分情况下，这个缓冲区里面是空的。也就是说，即使只有一个生产者和一个消费者者，这个生产者指向的队列尾和消费者指向的队列头是同一个节点。于是，这两个生产者和消费者之间一样会产生锁竞争。

在LinkedBlockingQueue上，这个锁机制是通过ReentrantLock这个Java 基础库来实现的。这个锁是一个用Java在JVM上直接实现的加锁机制，这个锁机制需要由JVM来进行裁决。这个锁的争夺，会把没有拿到锁的线程挂起等待，也就需要经过一次上下文切换（Context Switch）。

不知道你还记不记得，我们在[第28讲](https://time.geekbang.org/column/article/103717)讲过的异常和中断，这里的上下文切换要做的和异常和中断里的是一样的。上下文切换的过程，需要把当前执行线程的寄存器等等的信息，保存到线程栈里面。而这个过程也必然意味着，已经加载到高速缓存里面的指令或者数据，又回到了主内存里面，会进一步拖慢我们的性能。

我们可以按照Disruptor介绍资料里提到的Benchmark，写一段代码来看看，是不是真是这样的。这里我放了一段Java代码，代码的逻辑很简单，就是把一个long类型的counter，从0自增到5亿。一种方式是没有任何锁，另外一个方式是每次自增的时候都要去取一个锁。

你可以在自己的电脑上试试跑一下这个程序。在我这里，两个方式执行所需要的时间分别是207毫秒和9603毫秒，性能差出了将近50倍。

```
package com.xuwenhao.perf.jmm;


import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;


public class LockBenchmark{


    public static void runIncrement()
    {
        long counter = 0;
        long max = 500000000L;
        long start = System.currentTimeMillis();
        while (counter < max) {
            counter++;
        }
        long end = System.currentTimeMillis();
        System.out.println("Time spent is " + (end-start) + "ms without lock");
    }


    public static void runIncrementWithLock()
    {
        Lock lock = new ReentrantLock();
        long counter = 0;
        long max = 500000000L;
        long start = System.currentTimeMillis();
        while (counter < max) {
            if (lock.tryLock()){
                counter++;
                lock.unlock();
            }
        }
        long end = System.currentTimeMillis();
        System.out.println("Time spent is " + (end-start) + "ms with lock");
    }


    public static void main(String[] args) {
        runIncrement();
        runIncrementWithLock();
```

加锁和不加锁自增counter

```
Time spent is 207ms without lock
Time spent is 9603ms with lock
```

性能差出将近10倍

## 无锁的RingBuffer

加锁很慢，所以Disruptor的解决方案就是“无锁”。这个“无锁”指的是没有操作系统层面的锁。实际上，Disruptor还是利用了一个CPU硬件支持的指令，称之为CAS（Compare And Swap，比较和交换）。在Intel CPU里面，这个对应的指令就是 cmpxchg。那么下面，我们就一起从Disruptor的源码，到具体的硬件指令来看看这是怎么一回事儿。

Disruptor的RingBuffer是这么设计的，它和直接在链表的头和尾加锁不同。Disruptor的RingBuffer创建了一个Sequence对象，用来指向当前的RingBuffer的头和尾。这个头和尾的标识呢，不是通过一个指针来实现的，而是通过一个**序号**。这也是为什么对应源码里面的类名叫Sequence。

![](https://static001.geekbang.org/resource/image/b6/ec/b64487a7b6b45393fdfa7e2d63e176ec.jpeg?wh=2566%2A3601)

在这个RingBuffer当中，进行生产者和消费者之间的资源协调，采用的是对比序号的方式。当生产者想要往队列里加入新数据的时候，它会把当前的生产者的Sequence的序号，加上需要加入的新数据的数量，然后和实际的消费者所在的位置进行对比，看看队列里是不是有足够的空间加入这些数据，而不会覆盖掉消费者还没有处理完的数据。

在Sequence的代码里面，就是通过compareAndSet这个方法，并且最终调用到了UNSAFE.compareAndSwapLong，也就是直接使用了CAS指令。

```
 public boolean compareAndSet(final long expectedValue, final long newValue)
	    {
	        return UNSAFE.compareAndSwapLong(this, VALUE_OFFSET, expectedValue, newValue);
	    }


public long addAndGet(final long increment)
    {
        long currentValue;
        long newValue;


        do
        {
            currentValue = get();
            newValue = currentValue + increment;
        }
        while (!compareAndSet(currentValue, newValue));


        return newValue;
```

Sequence源码中的addAndGet，如果CAS的操作没有成功，它会不断忙等待地重试

这个CAS指令，也就是比较和交换的操作，并不是基础库里的一个函数。它也不是操作系统里面实现的一个系统调用，而是**一个CPU硬件支持的机器指令**。在我们服务器所使用的Intel CPU上，就是cmpxchg这个指令。

```
compxchg [ax] (隐式参数，EAX累加器), [bx] (源操作数地址), [cx] (目标操作数地址)
```

cmpxchg指令，一共有三个操作数，第一个操作数不在指令里面出现，是一个隐式的操作数，也就是EAX累加寄存器里面的值。第二个操作数就是源操作数，并且指令会对比这个操作数和上面的累加寄存器里面的值。

如果值是相同的，那一方面，CPU会把ZF（也就是条件码寄存器里面零标志位的值）设置为1，然后再把第三个操作数（也就是目标操作数），设置到源操作数的地址上。如果不相等的话，就会把源操作数里面的值，设置到累加器寄存器里面。

我在这里放了这个逻辑对应的伪代码，你可以看一下。如果你对汇编指令、条件码寄存器这些知识点有点儿模糊了，可以回头去看看[第5](https://time.geekbang.org/column/article/93359)[讲](https://time.geekbang.org/column/article/93359)、[第6讲](https://time.geekbang.org/column/article/94075)关于汇编指令的部分。

```
IF [ax]< == [bx] THEN [ZF] = 1, [bx] = [cx]
                 ELSE [ZF] = 0, [ax] = [bx] 
```

单个指令是原子的，这也就意味着在使用CAS操作的时候，我们不再需要单独进行加锁，直接调用就可以了。

没有了锁，CPU这部高速跑车就像在赛道上行驶，不会遇到需要上下文切换这样的红灯而停下来。虽然会遇到像CAS这样复杂的机器指令，就好像赛道上会有U型弯一样，不过不用完全停下来等待，我们CPU运行起来仍然会快很多。

那么，CAS操作到底会有多快呢？我们还是用一段Java代码来看一下。

```
package com.xuwenhao.perf.jmm;


import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;


public class LockBenchmark {


    public static void runIncrementAtomic()
    {
        AtomicLong counter = new AtomicLong(0);
        long max = 500000000L;
        long start = System.currentTimeMillis();
        while (counter.incrementAndGet() < max) {
        }
        long end = System.currentTimeMillis();
        System.out.println("Time spent is " + (end-start) + "ms with cas");
    }


    public static void main(String[] args) {
        runIncrementAtomic();
    }
```

```
Time spent is 3867ms with cas
```

和上面的counter自增一样，只不过这一次，自增我们采用了AtomicLong这个Java类。里面的incrementAndGet最终到了CPU指令层面，在实现的时候用的就是CAS操作。可以看到，它所花费的时间，虽然要比没有任何锁的操作慢上一个数量级，但是比起使用ReentrantLock这样的操作系统锁的机制，还是减少了一半以上的时间。

## 总结延伸

好了，咱们专栏的正文内容到今天就要结束了。今天最后一讲，我带着你一起看了Disruptor代码的一个核心设计，也就是它的RingBuffer是怎么做到无锁的。

Java基础库里面的BlockingQueue，都需要通过显示地加锁来保障生产者之间、消费者之间，乃至生产者和消费者之间，不会发生锁冲突的问题。

但是，加锁会大大拖慢我们的性能。在获取锁过程中，CPU没有去执行计算的相关指令，而要等待操作系统或者JVM来进行锁竞争的裁决。而那些没有拿到锁而被挂起等待的线程，则需要进行上下文切换。这个上下文切换，会把挂起线程的寄存器里的数据放到线程的程序栈里面去。这也意味着，加载到高速缓存里面的数据也失效了，程序就变得更慢了。

Disruptor里的RingBuffer采用了一个无锁的解决方案，通过CAS这样的操作，去进行序号的自增和对比，使得CPU不需要获取操作系统的锁。而是能够继续顺序地执行CPU指令。没有上下文切换、没有操作系统锁，自然程序就跑得快了。不过因为采用了CAS这样的忙等待（Busy-Wait）的方式，会使得我们的CPU始终满负荷运转，消耗更多的电，算是一个小小的缺点。

程序里面的CAS调用，映射到我们的CPU硬件层面，就是一个机器指令，这个指令就是cmpxchg。可以看到，当想要追求最极致的性能的时候，我们会从应用层、贯穿到操作系统，乃至最后的CPU硬件，搞清楚从高级语言到系统调用，乃至最后的汇编指令，这整个过程是怎么执行代码的。而这个，也是学习组成原理这门专栏的意义所在。

## 推荐阅读

不知道上一讲说的Disruptor相关材料，你有没有读完呢？如果没有读完的话，我建议你还是先去研读一下。

如果你已经读完了，这里再给你推荐一些额外的阅读材料，那就是著名的[Implement Lock-Free Queues](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.53.8674&rep=rep1&type=pdf)这篇论文。你可以更深入地学习一下，怎么实现一个无锁队列。

## 课后思考

最后，给你留一道思考题。这道题目有点儿难，不过也很有意思。

请你阅读一下Disruptor开源库里面的Sequence这个类的代码，看看它和一个普通的AtomicLong到底有什么区别，以及为什么它要这样实现。

欢迎在留言区写下你的思考和答案，和大家一起探讨应用层和硬件层之间的关联性。如果有收获，你也可以把这篇文章分享给你的朋友。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>唐朝农民</span> 👍（30） 💬（1）<p>ReentrantLock内部不也是CAS实现的吗</p>2019-09-09</li><br/><li><span>姜戈</span> 👍（20） 💬（3）<p>课后问题：
对比了Sequence与AtomicLong源码，在于CAS之前，Disruptor直接取原有值，做CAS操作；而AtomicLong使用了getLongVolatile获值。
两者value都用了Volatile来修饰，这点是共同的；但在于获值时，AtomicLong又再次使用volatile(getLongVolatile), 由于Volatile会在内存中强行刷新此值，相比这样就会增加一次性能的消耗，另外还有Spinlock（自旋锁），这两点都会带来性能消耗。
为什么Disruptor可以这样做，免掉getLongVolatile操作，我猜想应该是缓存行的填充，避免了伪共享（False Sharing）的问题，线程对value值的修改，不会出现不同线程同时修改同一缓存行不同变量的问题，所以不需要再次强行刷内存的步骤。

请老师指正！！！

 &#47;**    Sequence关于取值是直接Get(), 查看内部方法直接返回value
     *
     * Atomically add the supplied value.
     *
     * @param increment The value to add to the sequence.
     * @return The value after the increment.
     *&#47;
    public long addAndGet(final long increment)
    {
        long currentValue;
        long newValue;

        do
        {
            currentValue = get();
            newValue = currentValue + increment;
        }
        while (!compareAndSet(currentValue, newValue));

        return newValue;
    }

&#47;**    AtomicLong关于取值时使用getLongVolatile，查看其源码，增加了Volatile和自旋锁
     *
     * getAndAddLong
     *
*&#47;
public final long getAndAddLong(Object var1, long var2, long var4) {
        long var6;
        do {
            var6 = this.getLongVolatile(var1, var2);
        } while(!this.compareAndSwapLong(var1, var2, var6, var6 + var4));

        return var6;
    }

&#47;**    getLongVolatile源码（C++）
   *
   *   1. volatile, 刷新内存
   *   2.Spinlock, 自旋锁
   *&#47;
jlong
sun::misc::Unsafe::getLongVolatile (jobject obj, jlong offset)
{
  volatile jlong *addr = (jlong *) ((char *) obj + offset);
  spinlock lock;
  return *addr;
}</p>2019-09-09</li><br/><li><span>活的潇洒</span> 👍（14） 💬（7）<p>极客时间买了13个专栏，终于完成了一个专栏的所有笔记
专栏所有笔记如下：https:&#47;&#47;www.cnblogs.com&#47;luoahong&#47;p&#47;10496701.html</p>2019-09-15</li><br/><li><span>南山</span> 👍（11） 💬（1）<p>    专栏最开始就订阅了，看到了这篇专栏目录中的这篇文档标题，当时就想着要从底层了解disruptor的原理，也一篇一篇认真的跟了下来，不知不觉就到了今天，虽然有很多后续还是要回去时常翻阅的知识点，但是也庆幸自己能一路跟着老师到现在。
     课后思考题会去翻源码再回来补充</p>2019-09-09</li><br/><li><span>D</span> 👍（8） 💬（2）<p>看了下jdk 1.8的 AtomicLong 和disruptor的sequence， 个人认为有两点不同：
1. disruptor 加了上一讲里面的padding, 以进一步利用缓存。
2. Atomiclong 里面提供了更多的方法，并且判断cpu是否支持无锁cas
相同点，底层都是调用unsafe类实现硬件层面的操作，以跳过jdk的限制。</p>2019-09-09</li><br/><li><span>姜戈</span> 👍（5） 💬（1）<p>LinkedBlockingQueue源码（JDK1.8）看了一下, 使用的是ReentrantLock和Condition来控制的，没发现老师说的synchronized关键字, 是不是哪里我忽略掉了？</p>2019-09-09</li><br/><li><span>免费的人</span> 👍（3） 💬（1）<p>Cas仍然会涉及到内存读取，老师能否介绍下rcu锁？</p>2019-09-11</li><br/><li><span>leslie</span> 👍（3） 💬（2）<p>       学习中一步步跟进：越来越明白其实真正弄明白为何学习的中间层其实是操作系统和计算机原理；就像老师的课程中不少就和操作系统相关，而在此基础上可以衍生出一系列相关的知识。
       就像老师的2个TOP：存储与IO系统，应用篇分别就是一个向下一个向上；代码题对于不做纯代码超过5年的来说有点难，跟课再去学Java有点难且时间实在不够-毕竟运维的coding能力都偏差，不过大致能明白原理，从原理层去解释一些问题的根源原因，以及某些场合下那些可能更加适用。
      其实通过操作系统和组成原理会衍生出很多知识：选择合适的方向专攻确实不错。向老师提个小的要求：希望在最后一堂课可以分享老师在做这个专栏所查阅的主要书籍，毕竟没人可以学完一遍就基本掌握的；老师所看的核心资料是我们后续再看课程提升自己的一个辅助手段吧。</p>2019-09-09</li><br/><li><span>逍遥法外</span> 👍（3） 💬（1）<p>ReentrantLock内部也有CAS的操作，只不过也会有Lock的操作。Disruptor直接使用CAS，是简化了操作。</p>2019-09-09</li><br/><li><span>分清云淡</span> 👍（4） 💬（1）<p>文章中加锁和不加锁性能比较的case老师的数据是差了50倍，我在intel E5 v4和鲲鹏920下跑出来都是查了80倍。
不过其中的原因不是因为加锁，而是lock.lock() 函数自身包含了几十条指令，而++只有简单的几个指令，也就是两者指令数就差了1个数量级。
例子中不加锁性能好的另外一个原因是 ++指令 对流水线十分友好，基本能跑满流水线（IPC 跑到4)；而lock()那堆指令只能把IPC跑到0.5-0.8之间。

在只有一个线程的情况下加锁中的&quot;锁&quot;对性能是没有任何影响的，比如假设你的业务逻辑几万个指令，加上lock()多出来的几十个指令基本，基本是没有啥影响的。只有一个线程不会真正发生切换、等锁的糟心操作。只需要考虑实际指令量和对pipeline的友好程度</p>2021-06-07</li><br/><li><span>大头爸爸</span> 👍（3） 💬（0）<p>runIncrementWithLock()里面对每个counter++执行lock和unlock操作，可是就只有一个线程用到这个reentrantlock，那么这个lock()和unlock()应该花不了多少时间啊，也不会有多少context switch操作啊?</p>2020-03-31</li><br/><li><span>陈冰清</span> 👍（1） 💬（0）<p>老师 你有没有兴趣去量化私募行业做CTO呢 或者架构系统优化之类的岗位呢？</p>2021-07-20</li><br/><li><span>文进</span> 👍（1） 💬（0）<p>老师，此处Java锁的例子不太准确，因为你是在单线程下获取以及释放锁，其实并没有产生锁竞争，并不会有线程上下文切换问题。所以对吧cas的程序差距不大，如果改成几个线程一起执行，抢夺一个锁，效果会更明显</p>2021-06-01</li><br/><li><span>Monday</span> 👍（1） 💬（2）<p>how  激动 ，第一遍花了大半年，终于撸完了</p>2020-06-20</li><br/><li><span>信长</span> 👍（1） 💬（0）<p>你说到序号的时候，我以为假如有两个消费者，这两个消费者一个按着奇数的序列号消费，另一个按着偶数消费，类似这种思维，想多了吗</p>2020-03-26</li><br/>
</ul>