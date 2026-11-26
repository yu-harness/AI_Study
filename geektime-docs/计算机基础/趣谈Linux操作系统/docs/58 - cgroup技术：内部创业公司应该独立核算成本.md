我们前面说了，容器实现封闭的环境主要靠两种技术，一种是“看起来是隔离”的技术Namespace，另一种是用起来是隔离的技术cgroup。

上一节我们讲了“看起来隔离“的技术Namespace，这一节我们就来看一下“用起来隔离“的技术cgroup。

cgroup全称是control group，顾名思义，它是用来做“控制”的。控制什么东西呢？当然是资源的使用了。那它都能控制哪些资源的使用呢？我们一起来看一看。

首先，cgroup定义了下面的一系列子系统，每个子系统用于控制某一类资源。

- CPU子系统，主要限制进程的CPU使用率。
- cpuacct 子系统，可以统计 cgroup 中的进程的 CPU 使用报告。
- cpuset 子系统，可以为 cgroup 中的进程分配单独的 CPU 节点或者内存节点。
- memory 子系统，可以限制进程的 Memory 使用量。
- blkio 子系统，可以限制进程的块设备 IO。
- devices 子系统，可以控制进程能够访问某些设备。
- net\_cls 子系统，可以标记 cgroups 中进程的网络数据包，然后可以使用 tc 模块（traffic control）对数据包进行控制。
- freezer 子系统，可以挂起或者恢复 cgroup 中的进程。

这么多子系统，你可能要说了，那我们不用都掌握吧？没错，这里面最常用的是对于CPU和内存的控制，所以下面我们详细来说它。

在容器这一章的第一节，我们讲了，Docker有一些参数能够限制CPU和内存的使用，如果把它落地到cgroup里面会如何限制呢？

为了验证Docker的参数与cgroup的映射关系，我们运行一个命令特殊的docker run命令，这个命令比较长，里面的参数都会映射为cgroup的某项配置，然后我们运行docker ps，可以看到，这个容器的id为3dc0601189dd。

```
docker run -d --cpu-shares 513 --cpus 2 --cpuset-cpus 1,3 --memory 1024M --memory-swap 1234M --memory-swappiness 7 -p 8081:80 testnginx:1

# docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED              STATUS              PORTS                  NAMES
3dc0601189dd        testnginx:1         "/bin/sh -c 'nginx -…"   About a minute ago   Up About a minute   0.0.0.0:8081->80/tcp   boring_cohen
```

在Linux上，为了操作cgroup，有一个专门的cgroup文件系统，我们运行mount命令可以查看。

```
# mount -t cgroup
cgroup on /sys/fs/cgroup/systemd type cgroup (rw,nosuid,nodev,noexec,relatime,xattr,release_agent=/usr/lib/systemd/systemd-cgroups-agent,name=systemd)
cgroup on /sys/fs/cgroup/net_cls,net_prio type cgroup (rw,nosuid,nodev,noexec,relatime,net_prio,net_cls)
cgroup on /sys/fs/cgroup/perf_event type cgroup (rw,nosuid,nodev,noexec,relatime,perf_event)
cgroup on /sys/fs/cgroup/devices type cgroup (rw,nosuid,nodev,noexec,relatime,devices)
cgroup on /sys/fs/cgroup/blkio type cgroup (rw,nosuid,nodev,noexec,relatime,blkio)
cgroup on /sys/fs/cgroup/cpu,cpuacct type cgroup (rw,nosuid,nodev,noexec,relatime,cpuacct,cpu)
cgroup on /sys/fs/cgroup/memory type cgroup (rw,nosuid,nodev,noexec,relatime,memory)
cgroup on /sys/fs/cgroup/cpuset type cgroup (rw,nosuid,nodev,noexec,relatime,cpuset)
cgroup on /sys/fs/cgroup/hugetlb type cgroup (rw,nosuid,nodev,noexec,relatime,hugetlb)
cgroup on /sys/fs/cgroup/freezer type cgroup (rw,nosuid,nodev,noexec,relatime,freezer)
cgroup on /sys/fs/cgroup/pids type cgroup (rw,nosuid,nodev,noexec,relatime,pids)
```

cgroup文件系统多挂载到/sys/fs/cgroup下，通过上面的命令行，我们可以看到我们可以用cgroup控制哪些资源。

对于CPU的控制，我在这一章的第一节讲过，Docker可以控制cpu-shares、cpus和cpuset。

我们在/sys/fs/cgroup/下面能看到下面的目录结构。

```
drwxr-xr-x 5 root root  0 May 30 17:00 blkio
lrwxrwxrwx 1 root root 11 May 30 17:00 cpu -> cpu,cpuacct
lrwxrwxrwx 1 root root 11 May 30 17:00 cpuacct -> cpu,cpuacct
drwxr-xr-x 5 root root  0 May 30 17:00 cpu,cpuacct
drwxr-xr-x 3 root root  0 May 30 17:00 cpuset
drwxr-xr-x 5 root root  0 May 30 17:00 devices
drwxr-xr-x 3 root root  0 May 30 17:00 freezer
drwxr-xr-x 3 root root  0 May 30 17:00 hugetlb
drwxr-xr-x 5 root root  0 May 30 17:00 memory
lrwxrwxrwx 1 root root 16 May 30 17:00 net_cls -> net_cls,net_prio
drwxr-xr-x 3 root root  0 May 30 17:00 net_cls,net_prio
lrwxrwxrwx 1 root root 16 May 30 17:00 net_prio -> net_cls,net_prio
drwxr-xr-x 3 root root  0 May 30 17:00 perf_event
drwxr-xr-x 5 root root  0 May 30 17:00 pids
drwxr-xr-x 5 root root  0 May 30 17:00 systemd
```

我们可以想象，CPU的资源控制的配置文件，应该在cpu,cpuacct这个文件夹下面。

```
# ls
cgroup.clone_children  cpu.cfs_period_us  notify_on_release
cgroup.event_control   cpu.cfs_quota_us   release_agent
cgroup.procs           cpu.rt_period_us   system.slice
cgroup.sane_behavior   cpu.rt_runtime_us  tasks
cpuacct.stat           cpu.shares         user.slice
cpuacct.usage          cpu.stat
cpuacct.usage_percpu   docker
```

果真，这下面是对CPU的相关控制，里面还有一个路径叫docker。我们进入这个路径。

```
]# ls
cgroup.clone_children
cgroup.event_control
cgroup.procs
cpuacct.stat
cpuacct.usage
cpuacct.usage_percpu
cpu.cfs_period_us
cpu.cfs_quota_us
cpu.rt_period_us
cpu.rt_runtime_us
cpu.shares
cpu.stat
3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd
notify_on_release
tasks
```

这里面有个很长的id，是我们创建的docker的id。

```
[3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd]# ls
cgroup.clone_children  cpuacct.usage_percpu  cpu.shares
cgroup.event_control   cpu.cfs_period_us     cpu.stat
cgroup.procs           cpu.cfs_quota_us      notify_on_release
cpuacct.stat           cpu.rt_period_us      tasks
cpuacct.usage          cpu.rt_runtime_us
```

在这里，我们能看到cpu.shares，还有一个重要的文件tasks。这里面是这个容器里所有进程的进程号，也即所有这些进程都被这些CPU策略控制。

```
[3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd]# cat tasks 
39487
39520
39526
39527
39528
39529
```

如果我们查看cpu.shares，里面就是我们设置的513。

```
[3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd]# cat cpu.shares
513
```

另外，我们还配置了cpus，这个值其实是由cpu.cfs\_period\_us和cpu.cfs\_quota\_us共同决定的。cpu.cfs\_period\_us是运行周期，cpu.cfs\_quota\_us是在周期内这些进程占用多少时间。我们设置了cpus为2，代表的意思是，在周期100000微秒的运行周期内，这些进程要占用200000微秒的时间，也即需要两个CPU同时运行一个整的周期。

```
[3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd]# cat cpu.cfs_period_us
100000
[3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd]# cat cpu.cfs_quota_us
200000
```

对于cpuset，也即CPU绑核的参数，在另外一个文件夹里面/sys/fs/cgroup/cpuset，这里面同样有一个docker文件夹，下面同样有docker id 也即3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd文件夹，这里面的cpuset.cpus就是配置的绑定到1、3两个核。

```
[3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd]# cat cpuset.cpus
1,3
```

这一章的第一节我们还讲了Docker可以限制内存的使用量，例如memory、memory-swap、memory-swappiness。这些在哪里控制呢？

/sys/fs/cgroup/下面还有一个memory路径，控制策略就是在这里面定义的。

```
[root@deployer memory]# ls
cgroup.clone_children               memory.memsw.failcnt
cgroup.event_control                memory.memsw.limit_in_bytes
cgroup.procs                        memory.memsw.max_usage_in_bytes
cgroup.sane_behavior                memory.memsw.usage_in_bytes
docker                              memory.move_charge_at_immigrate
memory.failcnt                      memory.numa_stat
memory.force_empty                  memory.oom_control
memory.kmem.failcnt                 memory.pressure_level
memory.kmem.limit_in_bytes          memory.soft_limit_in_bytes
memory.kmem.max_usage_in_bytes      memory.stat
memory.kmem.slabinfo                memory.swappiness
memory.kmem.tcp.failcnt             memory.usage_in_bytes
memory.kmem.tcp.limit_in_bytes      memory.use_hierarchy
memory.kmem.tcp.max_usage_in_bytes  notify_on_release
memory.kmem.tcp.usage_in_bytes      release_agent
memory.kmem.usage_in_bytes          system.slice
memory.limit_in_bytes               tasks
memory.max_usage_in_bytes           user.slice
```

这里面全是对于memory的控制参数，在这里面我们可看到了docker，里面还有容器的id作为文件夹。

```
[docker]# ls
3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd
cgroup.clone_children
cgroup.event_control
cgroup.procs
memory.failcnt
memory.force_empty
memory.kmem.failcnt
memory.kmem.limit_in_bytes
memory.kmem.max_usage_in_bytes
memory.kmem.slabinfo
memory.kmem.tcp.failcnt
memory.kmem.tcp.limit_in_bytes
memory.kmem.tcp.max_usage_in_bytes
memory.kmem.tcp.usage_in_bytes
memory.kmem.usage_in_bytes
memory.limit_in_bytes
memory.max_usage_in_bytes
memory.memsw.failcnt
memory.memsw.limit_in_bytes
memory.memsw.max_usage_in_bytes
memory.memsw.usage_in_bytes
memory.move_charge_at_immigrate
memory.numa_stat
memory.oom_control
memory.pressure_level
memory.soft_limit_in_bytes
memory.stat
memory.swappiness
memory.usage_in_bytes
memory.use_hierarchy
notify_on_release
tasks

[3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd]# ls
cgroup.clone_children               memory.memsw.failcnt
cgroup.event_control                memory.memsw.limit_in_bytes
cgroup.procs                        memory.memsw.max_usage_in_bytes
memory.failcnt                      memory.memsw.usage_in_bytes
memory.force_empty                  memory.move_charge_at_immigrate
memory.kmem.failcnt                 memory.numa_stat
memory.kmem.limit_in_bytes          memory.oom_control
memory.kmem.max_usage_in_bytes      memory.pressure_level
memory.kmem.slabinfo                memory.soft_limit_in_bytes
memory.kmem.tcp.failcnt             memory.stat
memory.kmem.tcp.limit_in_bytes      memory.swappiness
memory.kmem.tcp.max_usage_in_bytes  memory.usage_in_bytes
memory.kmem.tcp.usage_in_bytes      memory.use_hierarchy
memory.kmem.usage_in_bytes          notify_on_release
memory.limit_in_bytes               tasks
memory.max_usage_in_bytes
```

在docker id的文件夹下面，有一个memory.limit\_in\_bytes，里面配置的就是memory。

```
[3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd]# cat memory.limit_in_bytes
1073741824
```

还有memory.swappiness，里面配置的就是memory-swappiness。

```
[3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd]# cat memory.swappiness
7
```

还有就是memory.memsw.limit\_in\_bytes，里面配置的是memory-swap。

```
[3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd]# cat memory.memsw.limit_in_bytes
1293942784
```

我们还可以看一下tasks文件的内容，tasks里面是容器里面所有进程的进程号。

```
[3dc0601189dd218898f31f9526a6cfae83913763a4da59f95ec789c6e030ecfd]# cat tasks 
39487
39520
39526
39527
39528
39529
```

至此，我们看到了cgroup对于Docker资源的控制，在用户态是如何表现的。我画了一张图总结一下。

![](https://static001.geekbang.org/resource/image/1c/0f/1c762a6283429ff3587a7fc370fc090f.png?wh=3106%2A1366)

在内核中，cgroup是如何实现的呢？

首先，在系统初始化的时候，cgroup也会进行初始化，在start\_kernel中，cgroup\_init\_early和cgroup\_init都会进行初始化。

```
asmlinkage __visible void __init start_kernel(void)
{
......
  cgroup_init_early();
......
  cgroup_init();
......
}
```

在cgroup\_init\_early和cgroup\_init中，会有下面的循环。

```
for_each_subsys(ss, i) {
	ss->id = i;
	ss->name = cgroup_subsys_name[i];
......
	cgroup_init_subsys(ss, true);
}

#define for_each_subsys(ss, ssid)					\
	for ((ssid) = 0; (ssid) < CGROUP_SUBSYS_COUNT &&		\
	     (((ss) = cgroup_subsys[ssid]) || true); (ssid)++)
```

for\_each\_subsys会在cgroup\_subsys数组中进行循环。这个cgroup\_subsys数组是如何形成的呢？

```
#define SUBSYS(_x) [_x ## _cgrp_id] = &_x ## _cgrp_subsys,
struct cgroup_subsys *cgroup_subsys[] = {
#include <linux/cgroup_subsys.h>
};
#undef SUBSYS
```

SUBSYS这个宏定义了这个cgroup\_subsys数组，数组中的项定义在cgroup\_subsys.h头文件中。例如，对于CPU和内存有下面的定义。

```
//cgroup_subsys.h

#if IS_ENABLED(CONFIG_CPUSETS)
SUBSYS(cpuset)
#endif

#if IS_ENABLED(CONFIG_CGROUP_SCHED)
SUBSYS(cpu)
#endif

#if IS_ENABLED(CONFIG_CGROUP_CPUACCT)
SUBSYS(cpuacct)
#endif

#if IS_ENABLED(CONFIG_MEMCG)
SUBSYS(memory)
#endif
```

根据SUBSYS的定义，SUBSYS(cpu)其实是\[cpu\_cgrp\_id] = &amp;cpu\_cgrp\_subsys，而SUBSYS(memory)其实是\[memory\_cgrp\_id] = &amp;memory\_cgrp\_subsys。

我们能够找到cpu\_cgrp\_subsys和memory\_cgrp\_subsys的定义。

```
cpuset_cgrp_subsys
struct cgroup_subsys cpuset_cgrp_subsys = {
	.css_alloc	= cpuset_css_alloc,
	.css_online	= cpuset_css_online,
	.css_offline	= cpuset_css_offline,
	.css_free	= cpuset_css_free,
	.can_attach	= cpuset_can_attach,
	.cancel_attach	= cpuset_cancel_attach,
	.attach		= cpuset_attach,
	.post_attach	= cpuset_post_attach,
	.bind		= cpuset_bind,
	.fork		= cpuset_fork,
	.legacy_cftypes	= files,
	.early_init	= true,
};

cpu_cgrp_subsys
struct cgroup_subsys cpu_cgrp_subsys = {
	.css_alloc	= cpu_cgroup_css_alloc,
	.css_online	= cpu_cgroup_css_online,
	.css_released	= cpu_cgroup_css_released,
	.css_free	= cpu_cgroup_css_free,
	.fork		= cpu_cgroup_fork,
	.can_attach	= cpu_cgroup_can_attach,
	.attach		= cpu_cgroup_attach,
	.legacy_cftypes	= cpu_files,
	.early_init	= true,
};

memory_cgrp_subsys
struct cgroup_subsys memory_cgrp_subsys = {
	.css_alloc = mem_cgroup_css_alloc,
	.css_online = mem_cgroup_css_online,
	.css_offline = mem_cgroup_css_offline,
	.css_released = mem_cgroup_css_released,
	.css_free = mem_cgroup_css_free,
	.css_reset = mem_cgroup_css_reset,
	.can_attach = mem_cgroup_can_attach,
	.cancel_attach = mem_cgroup_cancel_attach,
	.post_attach = mem_cgroup_move_task,
	.bind = mem_cgroup_bind,
	.dfl_cftypes = memory_files,
	.legacy_cftypes = mem_cgroup_legacy_files,
	.early_init = 0,
};
```

在for\_each\_subsys的循环里面，cgroup\_subsys\[]数组中的每一个cgroup\_subsys，都会调用cgroup\_init\_subsys，对于cgroup\_subsys对于初始化。

```
static void __init cgroup_init_subsys(struct cgroup_subsys *ss, bool early)
{
	struct cgroup_subsys_state *css;
......
	idr_init(&ss->css_idr);
	INIT_LIST_HEAD(&ss->cfts);

	/* Create the root cgroup state for this subsystem */
	ss->root = &cgrp_dfl_root;
	css = ss->css_alloc(cgroup_css(&cgrp_dfl_root.cgrp, ss));
......
	init_and_link_css(css, ss, &cgrp_dfl_root.cgrp);
......
	css->id = cgroup_idr_alloc(&ss->css_idr, css, 1, 2, GFP_KERNEL);
	init_css_set.subsys[ss->id] = css;
......
	BUG_ON(online_css(css));
......
}
```

cgroup\_init\_subsys里面会做两件事情，一个是调用cgroup\_subsys的css\_alloc函数创建一个cgroup\_subsys\_state；另外就是调用online\_css，也即调用cgroup\_subsys的css\_online函数，激活这个cgroup。

对于CPU来讲，css\_alloc函数就是cpu\_cgroup\_css\_alloc。这里面会调用 sched\_create\_group创建一个struct task\_group。在这个结构中，第一项就是cgroup\_subsys\_state，也就是说，task\_group是cgroup\_subsys\_state的一个扩展，最终返回的是指向cgroup\_subsys\_state结构的指针，可以通过强制类型转换变为task\_group。

```
struct task_group {
	struct cgroup_subsys_state css;

#ifdef CONFIG_FAIR_GROUP_SCHED
	/* schedulable entities of this group on each cpu */
	struct sched_entity **se;
	/* runqueue "owned" by this group on each cpu */
	struct cfs_rq **cfs_rq;
	unsigned long shares;

#ifdef	CONFIG_SMP
	atomic_long_t load_avg ____cacheline_aligned;
#endif
#endif

	struct rcu_head rcu;
	struct list_head list;

	struct task_group *parent;
	struct list_head siblings;
	struct list_head children;

	struct cfs_bandwidth cfs_bandwidth;
};
```

在task\_group结构中，有一个成员是sched\_entity，前面我们讲进程调度的时候，遇到过它。它是调度的实体，也即这一个task\_group也是一个调度实体。

接下来，online\_css会被调用。对于CPU来讲，online\_css调用的是cpu\_cgroup\_css\_online。它会调用sched\_online\_group-&gt;online\_fair\_sched\_group。

```
void online_fair_sched_group(struct task_group *tg)
{
	struct sched_entity *se;
	struct rq *rq;
	int i;

	for_each_possible_cpu(i) {
		rq = cpu_rq(i);
		se = tg->se[i];
		update_rq_clock(rq);
		attach_entity_cfs_rq(se);
		sync_throttle(tg, i);
	}
}
```

在这里面，对于每一个CPU，取出每个CPU的运行队列rq，也取出task\_group的sched\_entity，然后通过attach\_entity\_cfs\_rq将sched\_entity添加到运行队列中。

对于内存来讲，css\_alloc函数就是mem\_cgroup\_css\_alloc。这里面会调用 mem\_cgroup\_alloc，创建一个struct mem\_cgroup。在这个结构中，第一项就是cgroup\_subsys\_state，也就是说，mem\_cgroup是cgroup\_subsys\_state的一个扩展，最终返回的是指向cgroup\_subsys\_state结构的指针，我们可以通过强制类型转换变为mem\_cgroup。

```
struct mem_cgroup {
	struct cgroup_subsys_state css;

	/* Private memcg ID. Used to ID objects that outlive the cgroup */
	struct mem_cgroup_id id;

	/* Accounted resources */
	struct page_counter memory;
	struct page_counter swap;

	/* Legacy consumer-oriented counters */
	struct page_counter memsw;
	struct page_counter kmem;
	struct page_counter tcpmem;

	/* Normal memory consumption range */
	unsigned long low;
	unsigned long high;

	/* Range enforcement for interrupt charges */
	struct work_struct high_work;

	unsigned long soft_limit;

......
	int	swappiness;
......
	/*
	 * percpu counter.
	 */
	struct mem_cgroup_stat_cpu __percpu *stat;

	int last_scanned_node;

	/* List of events which userspace want to receive */
	struct list_head event_list;
	spinlock_t event_list_lock;

	struct mem_cgroup_per_node *nodeinfo[0];
	/* WARNING: nodeinfo must be the last member here */
};
```

在cgroup\_init函数中，cgroup的初始化还做了一件很重要的事情，它会调用cgroup\_init\_cftypes(NULL, cgroup1\_base\_files)，来初始化对于cgroup文件类型cftype的操作函数，也就是将struct kernfs\_ops \*kf\_ops设置为cgroup\_kf\_ops。

```
struct cftype cgroup1_base_files[] = {
......
    {   
        .name = "tasks",
        .seq_start = cgroup_pidlist_start,
        .seq_next = cgroup_pidlist_next,
        .seq_stop = cgroup_pidlist_stop,
        .seq_show = cgroup_pidlist_show,
        .private = CGROUP_FILE_TASKS,
        .write = cgroup_tasks_write,
    },  
}

static struct kernfs_ops cgroup_kf_ops = {
	.atomic_write_len	= PAGE_SIZE,
	.open			= cgroup_file_open,
	.release		= cgroup_file_release,
	.write			= cgroup_file_write,
	.seq_start		= cgroup_seqfile_start,
	.seq_next		= cgroup_seqfile_next,
	.seq_stop		= cgroup_seqfile_stop,
	.seq_show		= cgroup_seqfile_show,
};
```

在cgroup初始化完毕之后，接下来就是创建一个cgroup的文件系统，用于配置和操作cgroup。

cgroup是一种特殊的文件系统。它的定义如下：

```
struct file_system_type cgroup_fs_type = {
	.name = "cgroup",
	.mount = cgroup_mount,
	.kill_sb = cgroup_kill_sb,
	.fs_flags = FS_USERNS_MOUNT,
};
```

当我们mount这个cgroup文件系统的时候，会调用cgroup\_mount-&gt;cgroup1\_mount。

```
struct dentry *cgroup1_mount(struct file_system_type *fs_type, int flags,
			     void *data, unsigned long magic,
			     struct cgroup_namespace *ns)
{
	struct super_block *pinned_sb = NULL;
	struct cgroup_sb_opts opts;
	struct cgroup_root *root;
	struct cgroup_subsys *ss;
	struct dentry *dentry;
	int i, ret;
	bool new_root = false;
......
	root = kzalloc(sizeof(*root), GFP_KERNEL);
	new_root = true;

	init_cgroup_root(root, &opts);

	ret = cgroup_setup_root(root, opts.subsys_mask, PERCPU_REF_INIT_DEAD);
......
	dentry = cgroup_do_mount(&cgroup_fs_type, flags, root,
				 CGROUP_SUPER_MAGIC, ns);
......
	return dentry;
}
```

cgroup被组织成为树形结构，因而有cgroup\_root。init\_cgroup\_root会初始化这个cgroup\_root。cgroup\_root是cgroup的根，它有一个成员kf\_root，是cgroup文件系统的根struct kernfs\_root。kernfs\_create\_root就是用来创建这个kernfs\_root结构的。

```
int cgroup_setup_root(struct cgroup_root *root, u16 ss_mask, int ref_flags)
{
	LIST_HEAD(tmp_links);
	struct cgroup *root_cgrp = &root->cgrp;
	struct kernfs_syscall_ops *kf_sops;
	struct css_set *cset;
	int i, ret;

	root->kf_root = kernfs_create_root(kf_sops,
					   KERNFS_ROOT_CREATE_DEACTIVATED,
					   root_cgrp);
	root_cgrp->kn = root->kf_root->kn;

	ret = css_populate_dir(&root_cgrp->self);
	ret = rebind_subsystems(root, ss_mask);
......
	list_add(&root->root_list, &cgroup_roots);
	cgroup_root_count++;
......
	kernfs_activate(root_cgrp->kn);
......
}
```

就像在普通文件系统上，每一个文件都对应一个inode，在cgroup文件系统上，每个文件都对应一个struct kernfs\_node结构，当然kernfs\_root作为文件系的根也对应一个kernfs\_node结构。

接下来，css\_populate\_dir会调用cgroup\_addrm\_files-&gt;cgroup\_add\_file-&gt;cgroup\_add\_file，来创建整棵文件树，并且为树中的每个文件创建对应的kernfs\_node结构，并将这个文件的操作函数设置为kf\_ops，也即指向cgroup\_kf\_ops 。

```
static int cgroup_add_file(struct cgroup_subsys_state *css, struct cgroup *cgrp,
			   struct cftype *cft)
{
	char name[CGROUP_FILE_NAME_MAX];
	struct kernfs_node *kn;
......
	kn = __kernfs_create_file(cgrp->kn, cgroup_file_name(cgrp, cft, name),
				  cgroup_file_mode(cft), 0, cft->kf_ops, cft,
				  NULL, key);
......
}

struct kernfs_node *__kernfs_create_file(struct kernfs_node *parent,
					 const char *name,
					 umode_t mode, loff_t size,
					 const struct kernfs_ops *ops,
					 void *priv, const void *ns,
					 struct lock_class_key *key)
{
	struct kernfs_node *kn;
	unsigned flags;
	int rc;

	flags = KERNFS_FILE;

	kn = kernfs_new_node(parent, name, (mode & S_IALLUGO) | S_IFREG, flags);

	kn->attr.ops = ops;
	kn->attr.size = size;
	kn->ns = ns;
	kn->priv = priv;
......
	rc = kernfs_add_one(kn);
......
	return kn;
}
```

从cgroup\_setup\_root返回后，接下来，在cgroup1\_mount中，要做的一件事情是cgroup\_do\_mount，调用kernfs\_mount真的去mount这个文件系统，返回一个普通的文件系统都认识的dentry。这种特殊的文件系统对应的文件操作函数为kernfs\_file\_fops。

```
const struct file_operations kernfs_file_fops = {
	.read		= kernfs_fop_read,
	.write		= kernfs_fop_write,
	.llseek		= generic_file_llseek,
	.mmap		= kernfs_fop_mmap,
	.open		= kernfs_fop_open,
	.release	= kernfs_fop_release,
	.poll		= kernfs_fop_poll,
	.fsync		= noop_fsync,
};
```

当我们要写入一个CGroup文件来设置参数的时候，根据文件系统的操作，kernfs\_fop\_write会被调用，在这里面会调用kernfs\_ops的write函数，根据上面的定义为cgroup\_file\_write，在这里会调用cftype的write函数。对于CPU和内存的write函数，有以下不同的定义。

```
static struct cftype cpu_files[] = {
#ifdef CONFIG_FAIR_GROUP_SCHED
    {   
        .name = "shares",
        .read_u64 = cpu_shares_read_u64,
        .write_u64 = cpu_shares_write_u64,
    },  
#endif
#ifdef CONFIG_CFS_BANDWIDTH
    {   
        .name = "cfs_quota_us",
        .read_s64 = cpu_cfs_quota_read_s64,
        .write_s64 = cpu_cfs_quota_write_s64,
    },  
    {   
        .name = "cfs_period_us",
        .read_u64 = cpu_cfs_period_read_u64,
        .write_u64 = cpu_cfs_period_write_u64,
    },  
}


static struct cftype mem_cgroup_legacy_files[] = {
    {   
        .name = "usage_in_bytes",
        .private = MEMFILE_PRIVATE(_MEM, RES_USAGE),
        .read_u64 = mem_cgroup_read_u64,
    },  
    {   
        .name = "max_usage_in_bytes",
        .private = MEMFILE_PRIVATE(_MEM, RES_MAX_USAGE),
        .write = mem_cgroup_reset,
        .read_u64 = mem_cgroup_read_u64,
    },  
    {   
        .name = "limit_in_bytes",
        .private = MEMFILE_PRIVATE(_MEM, RES_LIMIT),
        .write = mem_cgroup_write,
        .read_u64 = mem_cgroup_read_u64,
    },  
    {   
        .name = "soft_limit_in_bytes",
        .private = MEMFILE_PRIVATE(_MEM, RES_SOFT_LIMIT),
        .write = mem_cgroup_write,
        .read_u64 = mem_cgroup_read_u64,
    },  
}
```

如果设置的是cpu.shares，则调用cpu\_shares\_write\_u64。在这里面，task\_group的shares变量更新了，并且更新了CPU队列上的调度实体。

```
int sched_group_set_shares(struct task_group *tg, unsigned long shares)
{
	int i;

	shares = clamp(shares, scale_load(MIN_SHARES), scale_load(MAX_SHARES));

	tg->shares = shares;
	for_each_possible_cpu(i) {
		struct rq *rq = cpu_rq(i);
		struct sched_entity *se = tg->se[i];
		struct rq_flags rf;

		update_rq_clock(rq);
		for_each_sched_entity(se) {
			update_load_avg(se, UPDATE_TG);
			update_cfs_shares(se);
		}
	}
......
}
```

但是这个时候别忘了，我们还没有将CPU的文件夹下面的tasks文件写入进程号呢。写入一个进程号到tasks文件里面，按照cgroup1\_base\_files里面的定义，我们应该调用cgroup\_tasks\_write。

接下来的调用链为：cgroup\_tasks\_write-&gt;\_\_cgroup\_procs\_write-&gt;cgroup\_attach\_task-&gt; cgroup\_migrate-&gt;cgroup\_migrate\_execute。将这个进程和一个cgroup关联起来，也即将这个进程迁移到这个cgroup下面。

```
static int cgroup_migrate_execute(struct cgroup_mgctx *mgctx)
{
	struct cgroup_taskset *tset = &mgctx->tset;
	struct cgroup_subsys *ss;
	struct task_struct *task, *tmp_task;
	struct css_set *cset, *tmp_cset;
......
	if (tset->nr_tasks) {
		do_each_subsys_mask(ss, ssid, mgctx->ss_mask) {
			if (ss->attach) {
				tset->ssid = ssid;
				ss->attach(tset);
			}
		} while_each_subsys_mask();
	}
......
}
```

每一个cgroup子系统会调用相应的attach函数。而CPU调用的是cpu\_cgroup\_attach-&gt; sched\_move\_task-&gt; sched\_change\_group。

```
static void sched_change_group(struct task_struct *tsk, int type)
{
	struct task_group *tg;

	tg = container_of(task_css_check(tsk, cpu_cgrp_id, true),
			  struct task_group, css);
	tg = autogroup_task_group(tsk, tg);
	tsk->sched_task_group = tg;

#ifdef CONFIG_FAIR_GROUP_SCHED
	if (tsk->sched_class->task_change_group)
		tsk->sched_class->task_change_group(tsk, type);
	else
#endif
		set_task_rq(tsk, task_cpu(tsk));
}
```

在sched\_change\_group中设置这个进程以这个task\_group的方式参与调度，从而使得上面的cpu.shares起作用。

对于内存来讲，写入内存的限制使用函数mem\_cgroup\_write-&gt;mem\_cgroup\_resize\_limit来设置struct mem\_cgroup的memory.limit成员。

在进程执行过程中，申请内存的时候，我们会调用handle\_pte\_fault-&gt;do\_anonymous\_page()-&gt;mem\_cgroup\_try\_charge()。

```
int mem_cgroup_try_charge(struct page *page, struct mm_struct *mm,
			  gfp_t gfp_mask, struct mem_cgroup **memcgp,
			  bool compound)
{
	struct mem_cgroup *memcg = NULL;
......
	if (!memcg)
		memcg = get_mem_cgroup_from_mm(mm);

	ret = try_charge(memcg, gfp_mask, nr_pages);
......
}
```

在mem\_cgroup\_try\_charge中，先是调用get\_mem\_cgroup\_from\_mm获得这个进程对应的mem\_cgroup结构，然后在try\_charge中，根据mem\_cgroup的限制，看是否可以申请分配内存。

至此，cgroup对于内存的限制才真正起作用。

## 总结时刻

内核中cgroup的工作机制，我们在这里总结一下。

![](https://static001.geekbang.org/resource/image/c9/c4/c9cc56d20e6a4bac0f9657e6380a96c4.png?wh=5836%2A5203)

第一步，系统初始化的时候，初始化cgroup的各个子系统的操作函数，分配各个子系统的数据结构。

第二步，mount cgroup文件系统，创建文件系统的树形结构，以及操作函数。

第三步，写入cgroup文件，设置cpu或者memory的相关参数，这个时候文件系统的操作函数会调用到cgroup子系统的操作函数，从而将参数设置到cgroup子系统的数据结构中。

第四步，写入tasks文件，将进程交给某个cgroup进行管理，因为tasks文件也是一个cgroup文件，统一会调用文件系统的操作函数进而调用cgroup子系统的操作函数，将cgroup子系统的数据结构和进程关联起来。

第五步，对于CPU来讲，会修改scheduled entity，放入相应的队列里面去，从而下次调度的时候就起作用了。对于内存的cgroup设定，只有在申请内存的时候才起作用。

## 课堂练习

这里我们用cgroup限制了CPU和内存，如何限制网络呢？给你一个提示tc，请你研究一下。

欢迎留言和我分享你的疑惑和见解，也欢迎收藏本节内容，反复研读。你也可以把今天的内容分享给你的朋友，和他一起学习和进步。
<div><strong>精选留言（13）</strong></div><ul>
<li><span>安排</span> 👍（5） 💬（1）<p>Cgroup文件系统是只存在内存中吗？每一次设置之后在掉电后是不是就消失了？</p>2019-08-09</li><br/><li><span>刘桢</span> 👍（4） 💬（6）<p>二十天闭关冲北邮</p>2019-08-09</li><br/><li><span>行者</span> 👍（8） 💬（1）<p>老师，麻烦讲下华为鸿蒙系统，它和linux区别与联系是什么？</p>2019-08-10</li><br/><li><span>张亚琛</span> 👍（4） 💬（0）<p>补充一些背景：

Cgroup是Linux系统内核提供的一种机制，它是在Linux 内核版本 2.6.24中引入的，来解决资源管理和隔离的问题。在它出现之前，Linux只能对单个进程进行资源限制，例如通过sched_setaffinity设置进程CPU亲和性，使用ulimit限制进程打开文件上限、栈大小等。

在这个时代，有一些早期的容器技术，如Chroot和Linux VServer。
Chroot 可以将进程及其子进程与操作系统的其余部分隔离开来，但是，对于 root process，却可以任意退出 chroot。
Linux VServer 是一种基于 Security Contexts 的软分区技术，可以做到虚拟服务器隔离，共享相同的硬件资源。主要问题是 VServer 应用程序针对 &quot;chroot-again&quot; 类型的攻击没有很好的进行安全保护，攻击者可以利用这个漏洞脱离限制环境，访问限制目录之外的任意文件。

虽然在没有 Cgroup 技术的情况下，还有其他的方法可以实现一定程度的资源隔离和管理，但是这些方法在处理多进程或者进程组的资源管理时显得力不从心，而且在安全性和功能性方面也存在一些问题。

随着容器技术的发展，Docker的开发者在了解并掌握了 Cgroup 技术之后，应用这项技术去实现Docker 的资源管理和隔离功能。因此，Cgroup 不仅解决了 Linux 系统的资源管理问题，也为容器技术的发展提供了基础。


</p>2024-02-23</li><br/><li><span>fhchina</span> 👍（3） 💬（0）<p>cpu.cfs_period_us的单位是us, 微秒不是毫秒</p>2019-11-23</li><br/><li><span>羊仔爸比</span> 👍（1） 💬（1）<p>老师：
      请教一下docker 里面我设置了 内存的limit是2g，cgroup 文件中memory.usage_in_bytes这个文件是是包含memory.stat中的total_rss 和total_cache 相加的大小，oom kill的时候会根据memory.usage_in_bytes的值kill吗，如果不是根据这个文件的值kill是根据哪个值进行kill的？</p>2020-05-29</li><br/><li><span>Bravery168</span> 👍（0） 💬（0）<p>容器从概念上就是通过各种数据结构的定义建构了一个模型，从执行层面，本质上是对进程资源和行为的定义和控制。牛</p>2022-12-15</li><br/><li><span>幼儿编程教学</span> 👍（0） 💬（0）<p>&gt;第五步，对于 CPU 来讲，会修改 scheduled entity，放入相应的队列里面去，从而下次调度的时候就起作用了。对于内存的 cgroup 设定，只有在申请内存的时候才起作用。

请教老师，2个我比较非常的问题。
* 设置 cgroup cpu后，极端情况下，是否会突发cpu超过限制？
文章中说”对于 CPU 来讲，会修改 scheduled entity，放入相应的队列里面去，从而下次调度的时候就起作用了“。如果1个进程，占用时间太长，或者短时间内，耗费了很多cpu，是否会引发cpu超量使用，导致系统卡死？k8s中，如果cpu设置的不好（配置大于宿主机实际量），是会引发宿主机卡死的情况。这时候，只能重启宿主机
* 设置 cgroup memory后，极端情况下，是否会突发memory超过限制？
内存好像会？因为上面说，”只有在申请内存的时候才起作用“。那之前申请的内存呢？申请内存的时候，申请的都是虚拟内存。假设宿主机只有1g内存。2个进程a,b，都申请内存1g。内存应该是在实际使用时，才会去分配。所以，进程a,b运行起来，可以超过宿主机实际1g内存。这时，操作系统会oom。应该是这样吧？</p>2022-11-02</li><br/><li><span>Sudouble</span> 👍（0） 💬（0）<p>这么多篇深度文章，很好的诠释了十几年前的一个疑问，为什么不让电脑突然断电！内存、缓存里存的大量数据，操作系统还没有触发写，这时突然断电，这部分数据全都丢了。</p>2022-06-19</li><br/><li><span>EST4What</span> 👍（0） 💬（0）<p>为什么我mount -t cgroup会显示，而切换到&#47;sys&#47;fs&#47;cgroup时，文件却不见了呢

[root@jenkins cgroup]# mount -t cgroup 
cgroup on &#47;sys&#47;fs&#47;cgroup&#47;systemd type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,xattr,release_agent=&#47;usr&#47;lib&#47;systemd&#47;systemd-cgroups-agent,name=systemd)
cgroup on &#47;sys&#47;fs&#47;cgroup&#47;memory type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,memory)
cgroup on &#47;sys&#47;fs&#47;cgroup&#47;devices type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,devices)
cgroup on &#47;sys&#47;fs&#47;cgroup&#47;cpu,cpuacct type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,cpuacct,cpu)
cgroup on &#47;sys&#47;fs&#47;cgroup&#47;hugetlb type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,hugetlb)
cgroup on &#47;sys&#47;fs&#47;cgroup&#47;cpuset type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,cpuset)
cgroup on &#47;sys&#47;fs&#47;cgroup&#47;freezer type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,freezer)
cgroup on &#47;sys&#47;fs&#47;cgroup&#47;perf_event type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,perf_event)
cgroup on &#47;sys&#47;fs&#47;cgroup&#47;blkio type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,blkio)
cgroup on &#47;sys&#47;fs&#47;cgroup&#47;net_cls,net_prio type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,net_prio,net_cls)
cgroup on &#47;sys&#47;fs&#47;cgroup&#47;pids type cgroup (rw,nosuid,nodev,noexec,relatime,seclabel,pids)
[root@jenkins cgroup]# ls
[root@jenkins cgroup]# ll
total 0

</p>2022-03-02</li><br/><li><span>songyy</span> 👍（0） 💬（0）<p>testnginx 不在docker的repo里面吧。示例里面

 docker run -d --cpu-shares 513 --cpus 2 --cpuset-cpus 1,3 --memory 1024M --memory-swap 1234M --memory-swappiness 7 -p 8081:80 testnginx:1

这个代码就跑不起来了</p>2021-07-04</li><br/><li><span>吴钩</span> 👍（0） 💬（0）<p>对namespace和cgroup了解增加了很多，赞！</p>2021-04-26</li><br/><li><span>许童童</span> 👍（0） 💬（0）<p>跟着老师一起精进。</p>2019-08-09</li><br/>
</ul>