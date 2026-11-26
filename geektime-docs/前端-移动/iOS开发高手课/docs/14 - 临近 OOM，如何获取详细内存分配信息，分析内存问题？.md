你好，我是戴铭。今天我们来聊聊，临近OOM，如何获取详细的内存分配信息，分析内存问题的话题。

OOM，是Out of Memory的缩写，指的是App占用的内存达到了iOS系统对单个App占用内存上限后，而被系统强杀掉的现象。这么说的话，OOM其实也属于我们在第12篇文章“[iOS 崩溃千奇百怪，如何全面监控？](https://time.geekbang.org/column/article/88600)”中提到的应用“崩溃”中的一种，是由iOS的Jetsam机制导致的一种“另类”崩溃，并且日志无法通过信号捕捉到。

JetSam机制，指的就是操作系统为了控制内存资源过度使用而采用的一种资源管控机制。

我们都知道，物理内存和 CPU 对于手机这样的便携设备来说，可谓稀缺资源。所以说，在iOS 系统的虚拟内存管理中，内存压力的管控就是一项很重要的内容。

接下来，我就跟你介绍一下如何获取内存上限值，以及如何监控到App因为占用内存过大而被强杀的问题？

## 通过 JetsamEvent 日志计算内存限制值

想要了解不同机器在不同系统版本的情况下，对 App 的内存限制是怎样的，有一种方法就是查看手机中以 JetsamEvent 开头的系统日志（我们可以从设置-&gt;隐私-&gt;分析中看到这些日志）。

在这些系统日志中，查找崩溃原因时我们需要关注 per-process-limit 部分的 rpages。rpages 表示的是 ，App 占用的内存页数量；per-process-limit 表示的是，App 占用的内存超过了系统对单个App 的内存限制。

这部分日志的结构如下：

```
"rpages" : 89600,
"reason" : "per-process-limit",
```

现在，我们已经知道了内存页数量 rpages 为 89600，只要再知道内存页大小的值，就可以计算出系统对单个App限制的内存是多少了。

内存页大小的值，我们也可以在 JetsamEvent 开头的系统日志里找到，也就是pageSize的值。如下图红框部分所示：

![](https://static001.geekbang.org/resource/image/f6/2a/f60391e3109494b411cef7d936b4792a.png?wh=1354%2A1256)  
可以看到，内存页大小 pageSize 的值是16384。接下来，我们就可以计算出当前 App 的内存限制值：pageSize * rpages / 1024 /1024 =16384 * 89600 / 1024 / 1024 得到的值是 1400 MB，即 1.4G。

这些 JetsamEvent 日志，都是系统在杀掉 App 后留在手机里的。在查看这些日志时，我们就会发现，很多日志都是 iOS 系统内核强杀掉那些优先级不高，并且占用的内存超过限制的 App 后留下的。

这些日志属于系统级的，会存在系统目录下。App上线后开发者是没有权限获取到系统目录内容的，也就是说，被强杀掉的 App 是无法获取到系统级日志的，只能线下设备通过连接 Xcode 获取到这部分日志。获取到Jetsam 后，就能够算出系统对 App 设置的内存限制值。

那么，**iOS系统是怎么发现 Jetsam 的呢？**

iOS 系统会开启优先级最高的线程 vm\_pressure\_monitor 来监控系统的内存压力情况，并通过一个堆栈来维护所有 App 的进程。另外，iOS系统还会维护一个内存快照表，用于保存每个进程内存页的消耗情况。

当监控系统内存的线程发现某 App 内存有压力了，就发出通知，内存有压力的 App 就会去执行对应的代理，也就是你所熟悉的 didReceiveMemoryWarning 代理。通过这个代理，你可以获得最后一个编写逻辑代码释放内存的机会。这段代码的执行，就有可能会避免你的App被系统强杀。

系统在强杀App前，会先做优先级判断。那么，这个**优先级判断的依据是什么呢？**

iOS系统内核里有一个数组，专门用于维护线程的优先级。这个优先级规定就是：内核用线程的优先级是最高的，操作系统的优先级其次，App 的优先级排在最后。并且，前台 App 程序的优先级是高于后台运行 App 的；线程使用优先级时，CPU 占用多的线程的优先级会被降低。

iOS系统在因为内存占用原因强杀掉App前，至少有6秒钟的时间可以用来做优先级判断。同时，JetSamEvent日志也是在这6秒内生成的。

除了JetSamEvent日志外，我们还可以通过XNU来获取内存的限制值。

## 通过 XNU 获取内存限制值

在 XNU 中，有专门用于获取内存上限值的函数和宏。我们可以通过 memorystatus\_priority\_entry 这个结构体，得到进程的优先级和内存限制值。结构体代码如下：

```
typedef struct memorystatus_priority_entry {
	pid_t pid;
	int32_t priority;
	uint64_t user_data;
	int32_t limit;
	uint32_t state;
} memorystatus_priority_entry_t;
```

在这个结构体中，priority 表示的是进程的优先级，limit就是我们想要的进程内存限制值。

## 通过内存警告获取内存限制值

通过XNU 的宏获取内存限制，需要有 root 权限，而App 内的权限是不够的，所以正常情况下，作为App开发者你是看不到这个信息的。那么，如果你不想越狱去获取这个权限的话，还可以利用 didReceiveMemoryWarning 这个内存压力代理事件来动态地获取内存限制值。

iOS系统在强杀掉App之前还有6秒钟的时间，足够你去获取记录内存信息了。那么，**如何获取当前内存使用情况呢？**

iOS系统提供了一个函数 task\_info， 可以帮助我们获取到当前任务的信息。关键代码如下：

```
struct mach_task_basic_info info;
mach_msg_type_number_t size = sizeof(info);
kern_return_t kl = task_info(mach_task_self(), MACH_TASK_BASIC_INFO, (task_info_t)&info, &size);
```

代码中，task\_info\_t 结构里包含了一个resident\_size 字段，用于表示使用了多少内存。这样，我们就可以获取到发生内存警告时，当前App 占用了多少内存。代码如下：

```
float used_mem = info.resident_size;
NSLog(@"使用了 %f MB 内存", used_mem / 1024.0f / 1024.0f)
```

## 定位内存问题信息收集

现在，我们已经可以通过三种方法来获取内存上限值了，而且通过内存警告的方式还能够动态地获取到这个值。有了这个内存上限值以后，你就可以进行内存问题的信息收集工作了。

要想精确地定位问题，我们就需要 dump 出完整的内存信息，包括所有对象及其内存占用值，在内存接近上限值的时候，收集并记录下所需信息，并在合适的时机上报到服务器里，方便分析问题。

获取到了每个对象的内存占用量还不够，你还需要知道是谁分配的内存，这样才可以精确定位到问题的关键所在。一个对象可能会在不同的函数里被分配了内存并被创建了出来，当这个对象内存占用过大时，如果不知道是在哪个函数里创建的话，问题依然很难精确定位出来。那么，**怎样才能知道是谁分配的内存呢？**

这个问题，我觉得应该从根儿上去找答案。内存分配函数 malloc 和 calloc 等默认使用的是 nano\_zone。nano\_zone 是256B以下小内存的分配，大于256B 的时候会使用 scalable\_zone 来分配。

在这里，我主要是针对大内存的分配监控，所以只针对 scalable\_zone 进行分析，同时也可以过滤掉很多小内存分配监控。比如，malloc函数用的是 malloc\_zone\_malloc，calloc 用的是 malloc\_zone\_calloc。

使用scalable\_zone 分配内存的函数都会调用 malloc\_logger 函数，因为系统总是需要有一个地方来统计并管理内存的分配情况。

具体实现的话，你可以查看 malloc\_zone\_malloc 函数的实现，代码如下：

```
void *malloc_zone_malloc(malloc_zone_t *zone, size_t size)
{
	MALLOC_TRACE(TRACE_malloc | DBG_FUNC_START, (uintptr_t)zone, size, 0, 0);
	void *ptr;
	if (malloc_check_start && (malloc_check_counter++ >= malloc_check_start)) {
		internal_check();
	}
	if (size > MALLOC_ABSOLUTE_MAX_SIZE) {
		return NULL;
	}
	ptr = zone->malloc(zone, size);
	// 在 zone 分配完内存后就开始使用 malloc_logger 进行进行记录
	if (malloc_logger) {
		malloc_logger(MALLOC_LOG_TYPE_ALLOCATE | MALLOC_LOG_TYPE_HAS_ZONE, (uintptr_t)zone, (uintptr_t)size, 0, (uintptr_t)ptr, 0);
	}
	MALLOC_TRACE(TRACE_malloc | DBG_FUNC_END, (uintptr_t)zone, size, (uintptr_t)ptr, 0);
	return ptr;
}
```

其他使用 scalable\_zone 分配内存的函数的方法也类似，所有大内存的分配，不管外部函数是怎么包装的，最终都会调用 malloc\_logger 函数。这样的话，问题就好解决了，你可以使用 fishhook 去 Hook 这个函数，加上自己的统计记录就能够通盘掌握内存的分配情况。出现问题时，将内存分配记录的日志捞上来，你就能够跟踪到导致内存不合理增大的原因了。

## 小结

为了达到监控内存的目的，我们需要做两件事情：一是，能够根据不同机器和系统获取到内存有问题的那个时间点；二是，到了出现内存问题的那个时间点时，还能要取到足够多的可以分析内存问题的信息。

针对这两件事，我在今天这篇文章里和你分享了在 JetsamEvent 日志里、在 XNU 代码里、在 task\_info 函数中怎么去找内存的上限值。然后，我和你一起分析了在内存到达上限值时，怎么通过内存分配时都会经过的 malloc\_logger 函数来掌握内存分配的详细信息，从而精确定位内存问题。

说到这里你可能会回过头来想，为什么用于占用内存过大时会被系统强杀呢？macOS 打开一堆应用也会远超物理内存，怎么没见系统去强杀 macOS 的应用呢？

其实，这里涉及到的是设备资源的问题。苹果公司考虑到手持设备存储空间小的问题，在 iOS 系统里去掉了交换空间，这样虚拟内存就没有办法记录到外部的存储上。于是，苹果公司引入了 MemoryStatus 机制。

这个机制的主要思路就是，在 iOS 系统上弹出尽可能多的内存供当前应用使用。把这个机制落到优先级上，就是先强杀后台应用；如果内存还不够多就强杀掉当前应用。而在macOS 系统里，MemoryStatus 只会强杀掉标记为空闲退出的进程。

在实现上，MemoryStatus 机制会开启一个memorystatus\_jetsam\_thread 的线程。这个线程，和内存压力监测线程 vm\_pressure\_monitor 没有联系，只负责强杀应用和记录日志，不会发送消息，所以内存压力检测线程无法获取到强杀应用的消息。

除内存过大被系统强杀这种内存问题以外，还有以下三种内存问题：

- 访问未分配的内存： XNU 会报 EXC\_BAD\_ACCESS错误，信号为 SIGSEGV Signal #11 。
- 访问已分配但未提交的内存：XNU 会拦截分配物理内存，出现问题的线程分配内存页时会被冻结。
- 没有遵守权限访问内存：内存页面的权限标准类似 UNIX 文件权限。如果去写只读权限的内存页面就会出现错误，XNU 会发出 SIGBUS Signal #7 信号。

第一种和第三种问题都可以通过崩溃信息获取到，在收集崩溃信息时如果发现是这两类，我们就可以把内存分配的记录同时传过来进行分析，对于不合理的内存分配进行优化和修改。

## 课后小作业

我今天提到了定位内存问题需要获取更多的信息，比如内存分配。那么，请你来根据我们今天所讲的 hook malloc\_logger 的方法，来实现一个记录内存分配的小工具吧。

感谢你的收听，欢迎你在评论区给我留言分享你的观点，也欢迎把它分享给更多的朋友一起阅读。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>鼠辈</span> 👍（3） 💬（2）<p>info.resident_size这个获取的内存和xcode上显示的内存是对不上的。不知道您怎么看这个问题？</p>2019-04-11</li><br/><li><span>drunkenMouse</span> 👍（2） 💬（1）<p>线程使用优先级时，CPU 占用多的线程的优先级会被降低。这句话怎么读不懂呢？

利用didReceivedMemoryWarning 这个代理时间，看得我一愣。。应该是代理事件，我这算不算鸡蛋里面挑骨头？

task_infk的使用需要导入&lt;mach&#47;mach.h&gt; 

最后一段意思是，系统通过malloc_logger来统计并管理内存的分配情况？</p>2019-04-12</li><br/><li><span>无名</span> 👍（0） 💬（1）<p>当系统还剩多少内存时，会发出内存不足的通知。</p>2019-06-25</li><br/><li><span>drunkenMouse</span> 👍（0） 💬（1）<p>系统在强杀App前，会先做优先级判断。意思是：如果优先级高的话，本来会强杀的也不强杀了，而去强杀那些没有达到limit的进程？</p>2019-04-13</li><br/><li><span>drunkenMouse</span> 👍（0） 💬（1）<p>didReceivedMemory 动态获取内存值的方法，没有找到啊 大佬能说一下吗？</p>2019-04-13</li><br/><li><span>mαnajay</span> 👍（0） 💬（1）<p>hook malloc_logger aop收集日志，然后在OOM那6秒内收集所有内存分配信息，然后在再次启动应用时 上报这两部分日志吗？ 
oom那一刻是指的哪个时机，接受内存警告？ didReceiveMemoryWarning 中判断 是否靠近 limit吗 </p>2019-04-11</li><br/><li><span>欢乐的小马驹</span> 👍（17） 💬（0）<p>我建议，以后写这样的专栏，最后把所有参考的原始资料都下。你觉得呢？</p>2020-05-21</li><br/><li><span>白开了杯水</span> 👍（16） 💬（1）<p>一直不知道内存分配最大值获取和怎么获取当前内存分配，看了文章豁然开朗，想问的是，老师这些知识都是通过分析源码得来的吗？</p>2019-04-11</li><br/><li><span>drunkenMouse</span> 👍（10） 💬（0）<p>iOS通过堆栈管理所有的app进程，通过一个优先级最高的线程去监控系统内存的压力，还有一个快速对照表记录所有app的内存使用情况。如果内存有压力了，就按照优先级去释放优先级低还使用内存多的。

所以app得内存阈值是没有固定大小的。我一直以为每个app可以使用的内存大小是固定的。。</p>2019-04-14</li><br/><li><span>D</span> 👍（6） 💬（0）<p>腾讯的OOMDetector就是干这个事的https:&#47;&#47;github.com&#47;Tencent&#47;OOMDetector</p>2021-08-16</li><br/><li><span>我唔知点死啊</span> 👍（4） 💬（2）<p>fishhook初学者提问：
关于fishhook malloc_logger，在libmalloc中找到malloc_logger是一个结构体：
typedef void(malloc_logger_t)(uint32_t type,
		uintptr_t arg1,
		uintptr_t arg2,
		uintptr_t arg3,
		uintptr_t result,
		uint32_t num_hot_frames_to_skip);

fishhook malloc_logger没有任何作用，然后在_malloc_initialize方法里面，找到这句malloc_logger = __disk_stack_logging_log_stack;
fishhhok __disk_stack_logging_log_stack同样不起作用，现在无从下手，请指教。

我的fishhook方法如下：
static void (*original_disk_stack_logging_log_stack)(uint32_t type_flags,
                               uintptr_t zone_ptr,
                               uintptr_t arg2,
                               uintptr_t arg3,
                               uintptr_t return_val,
                                  uint32_t num_hot_to_skip);
void new_disk_stack_logging_log_stack(uint32_t type_flags,
                               uintptr_t zone_ptr,
                               uintptr_t arg2,
                               uintptr_t arg3,
                               uintptr_t return_val,
                               uint32_t num_hot_to_skip) {
    NSLog(@&quot;========== __disk_stack_logging_log_stack ==========&quot;);
}

        struct rebinding malloc_logger_rebinding = { &quot;__disk_stack_logging_log_stack&quot;, original_disk_stack_logging_log_stack, (void *)&amp;original_disk_stack_logging_log_stack};
        rebind_symbols((struct rebinding[1]){malloc_logger_rebinding}, 1);</p>2019-04-18</li><br/><li><span>无名</span> 👍（3） 💬（2）<p>我问这个问题的原因是看到SDWebImage 2.6版本的源码中释放内存缓存有两种方式：
第一种：监听到内存不足时，释放所有内存缓存；
第二种：当系统剩余内存小于12M时，释放内存缓存。

刚开始版本是没有加第二种判断的。我的疑问是加上第二种判断有必要吗？如果有必要的话，那么就是，当系统只剩12M内存都还没有触发内存不足的通知。

所以说这个内存不足通知是否在应用能给它分配的最大内存都全部使用完了才发出通知还是？
如：当前app能使用的最大内存为2G，系统总共内存为4G。那是否说不管系统是否还剩余多少内存，只要app的内存达到2G就发出内存警告通知？还是说快到2G,如达到最大可用内存的百分之95以上就发出内存警告通知。有哪里可以看到这个值吗？</p>2019-06-25</li><br/><li><span>徐秀滨</span> 👍（3） 💬（0）<p>老师，我没找到malloc_logger这个方法，没法hook，咋搞？</p>2019-04-17</li><br/><li><span>Master</span> 👍（2） 💬（1）<p>有个疑问，就算 hook 了malloc_logger ，知晓了内存分配地址和大小，又如何知道是代码中哪块或者哪个对象申请的呢？望各位大佬不吝赐教！</p>2020-03-11</li><br/><li><span>Jaker</span> 👍（2） 💬（1）<p>接上面的问题，问一下老师，task_vm_info_data_t的phys_footprint 打印输出的内存值和xcode的显示内存还是不一致啊，这是怎么回事，望解惑，谢谢。</p>2019-04-16</li><br/>
</ul>