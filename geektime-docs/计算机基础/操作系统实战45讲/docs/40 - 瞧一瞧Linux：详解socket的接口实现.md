你好，我是LMOS。

上节课，我们一起了解了套接字的工作机制和数据结构，但套接字有哪些基本接口实现呢？相信学完这节课，你就能够解决这个问题了。

今天我会和你探讨套接字从创建、协议接口注册与初始化过程，还会为你深入分析套接字系统，是怎样调用各个功能函数的。通过这节课，相信你可以学会基于套接字来编写网络应用程序。有了之前的基础，想理解这节课并不难，让我们正式开始吧。

## 套接字接口

套接字接口最初是BSD操作系统的一部分，在应用层与TCP/IP协议栈之间接供了一套标准的独立于协议的接口。

Linux内核实现的套接字接口，将UNIX的“一切都是文件操作”的概念应用在了网络连接访问上，让应用程序可以用常规文件操作API访问网络连接。

从TCP/IP协议栈的角度来看，传输层以上的都是应用程序的一部分，Linux与传统的UNIX类似，TCP/IP协议栈驻留在内核中，与内核的其他组件共享内存。传输层以上执行的网络功能，都是在用户地址空间完成的。

Linux使用内核套接字概念与用户空间套接字通信，这样可以让实现和操作变得更简单。Linux提供了一套API和套接字数据结构，这些服务向下与内核接口对接，向上与用户空间接口对接，应用程序正是使用这一套API访问内核中的网络功能。

### 套接字的创建

在应用程序使用TCP/IP协议栈的功能之前，我们必须调用套接字库函数API创建一个新的套接字，创建好以后，对库函数创建套接字的调用，就会转换为内核套接字创建函数的系统调用。

这时，完成的是通用套接字创建的初始化功能，跟具体的协议族并不相关。

这个过程具体是这样的，在应用程序中执行socket函数，socket产生系统调用中断执行内核的套接字分路函数sys\_socketcall，在sys\_socketcall套接字函数分路器中将调用传送到sys\_socket函数，由sys\_socket函数调用套接字的通用创建函数sock\_create。

sock\_create函数完成通用套接字创建、初始化任务后，再调用特定协议族的套接字创建函数。

这样描述你可能还没有直观感受，我特意画了图，帮你梳理socket创建的流程，你可以对照图片仔细体会调用过程。

![](https://static001.geekbang.org/resource/image/31/ef/313d5d8c3b3224633fab2bd121006aef.jpg?wh=2655x2255 "socket创建示意图")

结合图解，我再用一个具体例子帮你加深理解，比如由AF\_INET协议族的inet\_create函数完成套接字与特定协议族的关联。

一个新的struct socket数据结构起始由sock\_create函数创建，**该函数直接调用\_\_sock\_create函数，\_\_sock\_create函数的任务是为套接字预留需要的内存空间，由sock\_alloc函数完成这项功能。**

这个sock\_alloc函数不仅会为struct socket数据结构实例预留空间，也会为struct inode数据结构实例分配需要的内存空间，这样可以使两个数据结构的实例相关联。\_\_sock\_create函数代码如下。

```
static int __sock_create(struct net *net, int family, int type, int protocol,
 struct socket **res, int kern)
{
int err;
struct socket *sock;
const struct net_proto_family *pf;
// 首先检验是否支持协议族
/*
* 检查是否在内核支持的socket范围内
*/
if (family < 0 || family >= NPROTO)
return -EAFNOSUPPORT;
if (type < 0 || type >= SOCK_MAX)
return -EINVAL;
/*
* 为新的套接字分配内存空间，分配成功后返回新的指针
*/

sock = sock_alloc();
}
```

sock\_alloc函数如下所示。

```
static struct socket *sock_alloc(void) {
struct inode *inode;
struct socket *sock;
    // 初始化一个可用的inode节点， 在fs/inode.c中
    inode = new_inode(sock_mnt->mnt_sb);
    if (!inode)
    return NULL;
    // 实际创建的是socket_alloc复合对象，因此要使用SOCKET_I宏从inode中取出关联的socket对象用于返回
    sock = SOCKET_I(inode);

    kmemcheck_annotate_bitfield(sock, type);
    // 文件类型为套接字
    inode->i_mode = S_IFSOCK | S_IRWXUGO;
    inode->i_uid = current_fsuid();
    inode->i_gid = current_fsgid();

    percpu_add(sockets_in_use, 1);
return sock;
}
```

当具体的协议与新套接字相连时，其内部状态的管理由协议自身维护。

现在，函数将struct socket数据结构的struct proto\_ops \*ops设置为NULL。随后，当某个协议族中的协议成员的套接字创建函数被调用时，ops将指向协议实例的操作函数。这时将struct socket数据结构的flags数据域设置为0，创建时还没有任何标志需要设置。

在之后的调用中，应用程序调用send或receive套接字库函数时会设置flags数据域。最后将其他两个数据域sk和file初始化为NULL。sk数据域随后会把由协议特有的套接字创建函数设置为指向内部套接字结构。file将在调用sock\_ma\_fd函数时设置为分配的文件返回的指针。

文件指针用于访问打开套接字的虚拟文件系统的文件状态。在sock\_alloc函数返回后，sock\_create函数调用协议族的套接字创建函数err =pf-&gt;create(net, sock, protocol)，它通过访问net\_families数组获取协议族的创建函数，对于TCP/IP协议栈，协议族将设置为AF\_INET。

### 套接字的绑定

创建完套接字后，应用程序需要调用sys\_bind函数把套接字和地址绑定起来，代码如下所示。

```
asmlinkage long sysbind (bind, int, fd, struct sockaddr __user *, umyaddr, int, addrlen)
{
	struct socket *sock;
	struct sockaddr_storage address;
	int err, fput_needed;
 
	/*
	 * 获取socket实例。
	 */
	sock = sockfd_lookup_light(fd, &err, &fput_needed);
	if (sock) {
		err = move_addr_to_kernel(umyaddr, addrlen, (struct sockaddr *)&address);
		if (err >= 0) {
			err = security_socket_bind(sock,
						   (struct sockaddr *)&address,
						   addrlen);
			/*
			 * 如果是TCP套接字，sock->ops指向的是inet_stream_ops，
			 * sock->ops是在inet_create()函数中初始化，所以bind接口
			 * 调用的是inet_bind()函数。
			 */
			if (!err)
				err = sock->ops->bind(sock,
						      (struct sockaddr *)
						      &address, addrlen);
		}
		fput_light(sock->file, fput_needed);
	}
	return err;
}
```

结合代码，我们可以看到，sys\_bind函数首先会查找套接字对应的socket实例，调用**sockfd\_lookup\_light**。在绑定之前，将用户空间的地址拷贝到内核空间的缓冲区中，在拷贝过程中会检查用户传入的地址是否正确。

等上述的准备工作完成后，就会调用**inet\_bind函数**来完成绑定操作。**inet\_bind**函数代码如下所示。

```
int inet_bind(struct socket *sock, struct sockaddr *uaddr, int addr_len)
{
    struct sockaddr_in *addr = (struct sockaddr_in *)uaddr;
    struct sock *sk = sock->sk;  
    struct inet_sock *inet = inet_sk(sk);
    unsigned short snum;
    int chk_addr_ret;
    int err;

    if (sk->sk_prot->bind) {/* 如果传输层接口上实现了bind调用，则回调它。目前只有SOCK_RAW类型的传输层实现了该接口raw_bind */
        err = sk->sk_prot->bind(sk, uaddr, addr_len);
        goto out;
    }
    err = -EINVAL;
    if (addr_len < sizeof(struct sockaddr_in))
        goto out;
    err = -EADDRNOTAVAIL;
    if (!sysctl_ip_nonlocal_bind &&/* 必须绑定到本地接口的地址 */
        !inet->freebind &&
        addr->sin_addr.s_addr != INADDR_ANY &&/* 绑定地址不合法 */
        chk_addr_ret != RTN_LOCAL &&
        chk_addr_ret != RTN_MULTICAST &&
        chk_addr_ret != RTN_BROADCAST)
        goto out;

    snum = ntohs(addr->sin_port);
    err = -EACCES;
    if (snum && snum < PROT_SOCK && !capable(CAP_NET_BIND_SERVICE))
        goto out;

    lock_sock(sk);/* 对套接口进行加锁，因为后面要对其状态进行判断 */

    /* Check these errors (active socket, double bind). */
    err = -EINVAL;
    /**
     * 如果状态不为CLOSE，表示套接口已经处于活动状态，不能再绑定
     * 或者已经指定了本地端口号，也不能再绑定
     */
    if (sk->sk_state != TCP_CLOSE || inet->num)
        goto out_release_sock;

    /* 设置地址到传输控制块中 */
    inet->rcv_saddr = inet->saddr = addr->sin_addr.s_addr;
    /* 如果是广播或者多播地址，则源地址使用设备地址。 */
    if (chk_addr_ret == RTN_MULTICAST || chk_addr_ret == RTN_BROADCAST)
        inet->saddr = 0;  /* Use device */

    /* 调用传输层的get_port来进行地址绑定。如tcp_v4_get_port或udp_v4_get_port */
    if (sk->sk_prot->get_port(sk, snum)) {
        …
    }

    /* 设置标志，表示已经绑定了本地地址和端口 */
    if (inet->rcv_saddr)
        sk->sk_userlocks |= SOCK_BINDADDR_LOCK;
    if (snum)
        sk->sk_userlocks |= SOCK_BINDPORT_LOCK;
    inet->sport = htons(inet->num);
    /* 还没有连接到对方，清除远端地址和端口 */
    inet->daddr = 0;
    inet->dport = 0;
    /* 清除路由缓存 */
    sk_dst_reset(sk);
    err = 0;
out_release_sock:
    release_sock(sk);
out:
    return err;
}
```

### 主动连接

因为应用程序处理的是面向连接的网络服务（SOCK\_STREAM或SOCK\_SEQPACKET），所以在交换数据之前，需要在请求连接服务的进程（客户）与提供服务的进程（服务器）之间建立连接。

当应用程序调用**connect**函数发出连接请求时，内核会启动函数**sys\_connect**，详细代码如下。

```
int __sys_connect(int fd, struct sockaddr __user *uservaddr, int addrlen)
{
	int ret = -EBADF;
	struct fd f;
	f = fdget(fd);
	if (f.file) {
		struct sockaddr_storage address;
		ret = move_addr_to_kernel(uservaddr, addrlen, &address);
		if (!ret)
            // 调用__sys_connect_file
			ret = __sys_connect_file(f.file, &address, addrlen, 0);
		fdput(f);
	}
	return ret;
}
```

连接成功会返回socket的描述符，否则会返回一个错误码。

### 监听套接字

调用listen函数时，应用程序触发内核的**sys\_listen**函数，把套接字描述符fd对应的套接字设置为监听模式，观察连接请求。详细代码你可以看看后面的内容。

```
int __sys_listen(int fd, int backlog)
{
	struct socket *sock;
	int err, fput_needed;
	int somaxconn;
    // 通过套接字描述符找到struct socket
	sock = sockfd_lookup_light(fd, &err, &fput_needed);
	if (sock) {
		somaxconn = sock_net(sock->sk)->core.sysctl_somaxconn;
		if ((unsigned int)backlog > somaxconn)
			backlog = somaxconn;
		err = security_socket_listen(sock, backlog);
		if (!err)
            // 根据套接字类型调用监听函数
			err = sock->ops->listen(sock, backlog);
		fput_light(sock->file, fput_needed);
	}
	return err;
}
```

### 被动接收连接

前面说过主动连接，我们再来看看被动接受连接的情况。接受一个客户端的连接请求会调用**accept**函数，应用程序触发内核函数**sys\_accept**，等待接收连接请求。如果允许连接，则重新创建一个代表该连接的套接字，并返回其套接字描述符，代码如下。

```
int __sys_accept4_file(struct file *file, unsigned file_flags,
		       struct sockaddr __user *upeer_sockaddr,
		       int __user *upeer_addrlen, int flags,
		       unsigned long nofile)
{
	struct socket *sock, *newsock;
	struct file *newfile;
	int err, len, newfd;
	struct sockaddr_storage address;
	if (flags & ~(SOCK_CLOEXEC | SOCK_NONBLOCK))
		return -EINVAL;
	if (SOCK_NONBLOCK != O_NONBLOCK && (flags & SOCK_NONBLOCK))
		flags = (flags & ~SOCK_NONBLOCK) | O_NONBLOCK;
	sock = sock_from_file(file, &err);
	if (!sock)
		goto out;
	err = -ENFILE;
    // 创建一个新套接字
	newsock = sock_alloc();
	if (!newsock)
		goto out;
	newsock->type = sock->type;
	newsock->ops = sock->ops;
	__module_get(newsock->ops->owner);
	newfd = __get_unused_fd_flags(flags, nofile);
	if (unlikely(newfd < 0)) {
		err = newfd;
		sock_release(newsock);
		goto out;
	}
	newfile = sock_alloc_file(newsock, flags, sock->sk->sk_prot_creator->name);
	if (IS_ERR(newfile)) {
		err = PTR_ERR(newfile);
		put_unused_fd(newfd);
		goto out;
	}
	err = security_socket_accept(sock, newsock);
	if (err)
		goto out_fd;
    // 根据套接字类型调用不同的函数inet_accept
	err = sock->ops->accept(sock, newsock, sock->file->f_flags | file_flags,
					false);
	if (err < 0)
		goto out_fd;
	if (upeer_sockaddr) {
		len = newsock->ops->getname(newsock,
					(struct sockaddr *)&address, 2);
		if (len < 0) {
			err = -ECONNABORTED;
			goto out_fd;
		}
        // 从内核复制到用户空间
		err = move_addr_to_user(&address,
					len, upeer_sockaddr, upeer_addrlen);
		if (err < 0)
			goto out_fd;
	}
	/* File flags are not inherited via accept() unlike another OSes. */
	fd_install(newfd, newfile);
	err = newfd;
out:
	return err;
out_fd:
	fput(newfile);
	put_unused_fd(newfd);
	goto out;
}
```

这个新的套接字描述符与最初创建套接字时，设置的套接字地址族与套接字类型、使用的协议一样。原来创建的套接字不与连接关联，它继续在原套接字上侦听，以便接收其他连接请求。

### 发送数据

套接字应用中最简单的传送函数是**send**，send函数的作用类似于write，但send函数允许应用程序指定标志，规定如何对待传送数据。调用send函数时，会触发内核的**sys\_send**函数，把发送缓冲区的数据发送出去。

**sys\_send**函数具体调用流程如下。

1.应用程序的数据被复制到内核后，sys\_send函数调用**sock\_sendmsg**，依据协议族类型来执行发送操作。  
2.如果是INET协议族套接字，sock\_sendmsg将调用inet\_sendmsg函数。  
3.如果采用TCP协议，inet\_sendmsg函数将调用tcp\_sendmsg，并按照TCP协议规则来发送数据包。

send函数返回发送成功，并不意味着在连接的另一端的进程可以收到数据，这里只能保证发送send函数执行成功，发送给网络设备驱动程序的数据没有出错。

### 接收数据

**recv**函数与文件读read函数类似，recv函数中可以指定标志来控制如何接收数据，调用recv函数时，应用程序会触发内核的sys\_recv函数，把网络中的数据递交到应用程序。当然，read、recvfrom函数也会触发sys\_recv函数。具体流程如下。

1.为把内核的网络数据转入应用程序的接收缓冲区，sys\_recv函数依次调用**sys\_recvfrom、sock\_recvfrom和\_\_sock\_recvmsg**，并依据协议族类型来执行具体的接收操作。  
2.如果是INET协议族套接字，\_\_sock\_recvmsg将调用sock\_common\_recvmsg函数。  
3.如果采用TCP协议，sock\_common\_recvmsg函数将调用tcp\_recvmsg，按照TCP协议规则来接收数据包

如果接收方想获取数据包发送端的标识符，应用程序可以调用**sys\_recvfrom**函数来获取数据包发送方的源地址，下面是**sys\_recvfrom**函数的实现。

```
int __sys_recvfrom(int fd, void __user *ubuf, size_t size, unsigned int flags,
		   struct sockaddr __user *addr, int __user *addr_len)
{
	struct socket *sock;
	struct iovec iov;
	struct msghdr msg;
	struct sockaddr_storage address;
	int err, err2;
	int fput_needed;
	err = import_single_range(READ, ubuf, size, &iov, &msg.msg_iter);
	if (unlikely(err))
		return err;
    // 通过套接字描述符找到struct socket
	sock = sockfd_lookup_light(fd, &err, &fput_needed);
	if (!sock)
		goto out;
	msg.msg_control = NULL;
	msg.msg_controllen = 0;
	/* Save some cycles and don't copy the address if not needed */
	msg.msg_name = addr ? (struct sockaddr *)&address : NULL;
	/* We assume all kernel code knows the size of sockaddr_storage */
	msg.msg_namelen = 0;
	msg.msg_iocb = NULL;
	msg.msg_flags = 0;
	if (sock->file->f_flags & O_NONBLOCK)
		flags |= MSG_DONTWAIT;
    // sock_recvmsg为具体的接收函数
	err = sock_recvmsg(sock, &msg, flags);
	if (err >= 0 && addr != NULL) {
        // 从内核复制到用户空间
		err2 = move_addr_to_user(&address,
					 msg.msg_namelen, addr, addr_len);
		if (err2 < 0)
			err = err2;
	}
	fput_light(sock->file, fput_needed);
out:
	return err;
}
```

### 关闭连接

最后，我们来看看如何关闭连接。当应用程序调用shutdown函数关闭连接时，内核会启动函数sys\_shutdown，代码如下。

```
int __sys_shutdown(int fd, int how)
{
	int err, fput_needed;
	struct socket *sock;
	sock = sockfd_lookup_light(fd, &err, &fput_needed);/* 通过套接字，描述符找到对应的结构*/
	if (sock != NULL) {
		err = security_socket_shutdown(sock, how);
		if (!err)
             /* 根据套接字协议族调用关闭函数*/
			err = sock->ops->shutdown(sock, how);
    		fput_light(sock->file, fput_needed);
	}
	return err;
}
```

## 重点回顾

好，这节课的内容告一段落了，我来给你做个总结。这节课我们继续研究了套接字在Linux内核中的实现。

套接字是UNIX兼容系统的一大特色，Linux在此基础上实现了内核套接字与应用程序套接字接口，在用户地址空间与内核地址空间之间提供了一套标准接口，实现应用套接字库函数与内核功能之间的一一对应，简化了用户地址空间与内核地址空间交换数据的过程。

通过应用套接字API编写网络应用程序，我们可以利用Linux内核TCP/IP协议栈提供的网络通信服务，在网络上实现应用数据快速、有效的传送。除此之外，套接字编程还可以使我们获取网络、主机的各种管理、统计信息。

创建套接字应用程序一般要经过后面这6个步骤。

1.创建套接字。  
2.将套接字与地址绑定，设置套接字选项。  
3.建立套接字之间的连接。  
4.监听套接字  
5.接收、发送数据。  
6.关闭、释放套接字。

## 思考题

我们了解的TCP三次握手，发生在socket的哪几个函数中呢？

欢迎你在留言区跟我交流，也推荐你把这节课转发给有需要的朋友。

我是LMOS，我们下节课见！
<div><strong>精选留言（9）</strong></div><ul>
<li><span>neohope</span> 👍（5） 💬（1）<p>四次挥手过程分析下【V5.8，正常流程】
5、客户端收到FIN包，子状态从TCP_FIN_WAIT2变为TCP_TIME_WAIT，返回ACK包
A、状态和子状态都为TCP_TIME_WAIT
【tcp_protocol.handler】tcp_v4_rcv-&gt;
-&gt;if (sk-&gt;sk_state == TCP_TIME_WAIT) goto do_time_wait;
-&gt;do_time_wait:
-&gt;tcp_timewait_state_process
-&gt;-&gt;if (tw-&gt;tw_substate == TCP_FIN_WAIT2)
-&gt;-&gt;tw-&gt;tw_substate = TCP_TIME_WAIT;
-&gt;-&gt;inet_twsk_reschedule，重新设置回调时间
-&gt;-&gt;return TCP_TW_ACK;

B、返回ACK
-&gt;case TCP_TW_ACK:
-&gt;tcp_v4_timewait_ack(sk, skb);

6、服务端收到ACK包，状态从TCP_LAST_ACK变为TCP_CLOSE
【tcp_protocol.handler】tcp_v4_rcv-&gt;tcp_v4_do_rcv-&gt;tcp_rcv_state_process
-&gt;case TCP_LAST_ACK:
-&gt;tcp_done
-&gt;-&gt;tcp_set_state(sk, TCP_CLOSE);

7、客户端超时回调
A、超时时间定义
#define TCP_TIMEWAIT_LEN (60*HZ)
#define TCP_FIN_TIMEOUT TCP_TIMEWAIT_LEN

B、超时后，回调tw_timer_handler-&gt;inet_twsk_kill，进行inet_timewait_sock清理工作

C、没有找到状态变从TCP_TIME_WAIT变为TCP_CLOSE的代码

D、只看没调，有问题的，欢迎小伙伴告诉一下</p>2021-08-15</li><br/><li><span>neohope</span> 👍（3） 💬（0）<p>四次挥手过程分析上【V5.8，正常流程】
1、客户端主动断开连接，状态从TCP_ESTABLISHED变为TCP_FIN_WAIT1，发送FIN包给服务端
A、状态变为TCP_FIN_WAIT1
tcp_close-&gt;tcp_close_state
-&gt;tcp_set_state(sk, new_state[TCP_ESTABLISHED])，也就是TCP_FIN_WAIT1

B、发送FIN包
tcp_close-&gt;tcp_close_state
-&gt;tcp_send_fin

2、服务端收到FIN包，状态从TCP_ESTABLISHED变为TCP_CLOSE_WAIT，并返回ACK包
A、状态变为TCP_CLOSE_WAIT
【tcp_protocol.handler】tcp_v4_rcv-&gt;tcp_v4_do_rcv-&gt;tcp_rcv_established
-&gt;tcp_data_queue
-&gt;-&gt;tcp_fin
-&gt;-&gt;-&gt;inet_csk_schedule_ack; 安排ack
-&gt;-&gt;-&gt;sk-&gt;sk_shutdown |= RCV_SHUTDOWN; 模拟了close
-&gt;-&gt;-&gt;sock_set_flag(sk, SOCK_DONE);
-&gt;-&gt;-&gt;case TCP_ESTABLISHED:
-&gt;-&gt;-&gt;tcp_set_state(sk, TCP_CLOSE_WAIT); 修改状态
-&gt;-&gt;inet_csk(sk)-&gt;icsk_ack.pending |= ICSK_ACK_NOW;  ACS是否立即发送

B、发送ACK包
【tcp_protocol.handler】tcp_v4_rcv-&gt;tcp_v4_do_rcv-&gt;tcp_rcv_established【接上面】
-&gt;tcp_ack_snd_check-&gt;__tcp_ack_snd_check-&gt;tcp_send_ack

3、客户端收到ACK包，状态从TCP_FIN_WAIT1变为TCP_FIN_WAIT2，然后被替换为状态TCP_TIME_WAIT，子状态TCP_FIN_WAIT2
【tcp_protocol.handler】tcp_v4_rcv-&gt;tcp_v4_do_rcv-&gt;tcp_rcv_state_process
-&gt;case TCP_FIN_WAIT1:
-&gt;tcp_set_state(sk, TCP_FIN_WAIT2);
-&gt;tcp_time_wait(sk, TCP_FIN_WAIT2, tmo);
-&gt;-&gt;tw = inet_twsk_alloc(sk, tcp_death_row, state);
-&gt;-&gt;-&gt;tw-&gt;tw_state = TCP_TIME_WAIT;   
-&gt;-&gt;-&gt;tw-&gt;tw_substate = TCP_FIN_WAIT2;
-&gt;-&gt;-&gt;timer_setup(&amp;tw-&gt;tw_timer, tw_timer_handler, TIMER_PINNED);

4、服务端状态从TCP_CLOSE_WAIT变为TCP_LAST_ACK，发送FIN包
A、状态变为TCP_LAST_ACK
tcp_close-&gt;tcp_close_state
-&gt;tcp_set_state(sk, new_state[TCP_CLOSE_WAIT])，也就是TCP_LAST_ACK

B、发送FIN包
tcp_close-&gt;tcp_close_state
-&gt;tcp_send_fin</p>2021-08-15</li><br/><li><span>neohope</span> 👍（6） 💬（1）<p>三次握手过程分析【V5.8，正常流程】
1、客户端发起第一次握手，状态调变为TCP_SYN_SENT，发送SYN包
connect-&gt;__sys_connect-&gt;__sys_connect_file-&gt;【sock-&gt;ops-&gt;connect】tcp_v4_connect
A、状态变化
-&gt;tcp_set_state(sk, TCP_SYN_SENT);
B、发送SYN
-&gt;tcp_connect-&gt;tcp_send_syn_data

2、服务端收到客户端的SYN包，初始化socket，状态从TCP_LISTEN变为TCP_NEW_SYN_RECV，发送第二次握手SYN_ACK包
A、收到连接，初始化socket
accept-&gt;__sys_accept4-&gt;__sys_accept4_file-&gt;【sock-&gt;ops-&gt;accept】inet_csk_accept

B、收到SYN，改变状态
【tcp_protocol.handler】tcp_v4_rcv-&gt;tcp_v4_do_rcv-&gt;tcp_rcv_state_process-&gt;
-&gt;case TCP_LISTEN:
-&gt;[sock-&gt;ops-&gt;conn_request]tcp_v4_conn_request-&gt;tcp_conn_request
-&gt;-&gt;inet_reqsk_alloc
-&gt;-&gt;-&gt;ireq-&gt;ireq_state = TCP_NEW_SYN_RECV;

C、发送SYN_ACK包
-&gt;[sock-&gt;ops-&gt;conn_request]tcp_v4_conn_request-&gt;tcp_conn_request【和B路径一样】
-&gt;-&gt;【af_ops-&gt;send_synack】tcp_v4_send_synack
-&gt;-&gt;-&gt;tcp_make_synack
-&gt;-&gt;-&gt;__tcp_v4_send_check

3、客户端收到SYN_ACK包，状态从TCP_SYN_SENT变为TCP_ESTABLISHED，并发送ACK包
A、收到SYN_ACK包
【tcp_protocol.handler】tcp_v4_rcv-&gt;tcp_v4_do_rcv-&gt;tcp_rcv_state_process
-&gt;case TCP_SYN_SENT:
-&gt;tcp_rcv_synsent_state_process-&gt;tcp_finish_connect
-&gt;-&gt;tcp_set_state(sk, TCP_ESTABLISHED);

B、发送ACK包
-&gt;tcp_rcv_synsent_state_process-&gt;tcp_send_ack-&gt;__tcp_send_ack

4、服务端收到ACK包，状态从TCP_NEW_SYN_RECV变为TCP_SYN_RECV【实际上是新建了一个sock】
【tcp_protocol.handler】tcp_v4_rcv-&gt;
-&gt;if (sk-&gt;sk_state == TCP_NEW_SYN_RECV)
-&gt;tcp_check_req
-&gt;-&gt;【inet_csk(sk)-&gt;icsk_af_ops-&gt;syn_recv_sock】tcp_v4_syn_recv_sock-&gt;tcp_create_openreq_child-&gt;inet_csk_clone_lock
-&gt;-&gt;-&gt;inet_sk_set_state(newsk, TCP_SYN_RECV);

5、服务端状态从TCP_SYN_RECV变为TCP_ESTABLISHED
【tcp_protocol.handler】tcp_v4_rcv-&gt;tcp_v4_do_rcv-&gt;tcp_rcv_state_process
-&gt;case TCP_SYN_RECV:
-&gt;tcp_set_state(sk, TCP_ESTABLISHED);

只看没调，有问题的欢迎各位小伙伴指出。</p>2021-08-14</li><br/><li><span>pedro</span> 👍（2） 💬（3）<p>今天的问题不好回答，因为文中无明显三次握手的代码，而且三次握手的机制其实比较复杂，涉及到几个状态和几个队列之间的切换，笼统的 connect 和 accept 函数是说不清楚的，感兴趣可以看看这里：
https:&#47;&#47;blog.csdn.net&#47;tennysonsky&#47;article&#47;details&#47;45621341

当然这些不能全信，所以还是得自己看linux内核代码，待我看了再来补充😂</p>2021-08-09</li><br/><li><span>王子虾</span> 👍（0） 💬（1）<p>老师，有一个问题，tcp在调用listen的时候，有全连接队列的概念，一般上限是128。但是问题是，我们比如实现单机百万链接的时候，一个server端的源组（server_ip+port），比如有65535个client，那会不会受限于这个全连接队列？</p>2022-04-09</li><br/><li><span>ifelse</span> 👍（0） 💬（1）<p>nice</p>2022-02-25</li><br/><li><span>GeekCoder</span> 👍（0） 💬（1）<p>能讲讲epoll吗？</p>2021-10-24</li><br/><li><span>pedro</span> 👍（0） 💬（1）<p>这里有一篇三次握手的源码图解：https:&#47;&#47;mp.weixin.qq.com&#47;s&#47;vlrzGc5bFrPIr9a7HIr2eA</p>2021-08-09</li><br/><li><span>MacBao</span> 👍（1） 💬（0）<p>服务器端处于listen状态，客户端connect发起TCP三次握手？</p>2021-08-09</li><br/>
</ul>