# 内核子系统定义

各子系统的邮件列表、lei 订阅命令、核心目录、术语保留表。

---

## mm — 内存管理

- **邮件列表**：linux-mm@kvack.org
- **lore URL**：`https://lore.kernel.org/linux-mm`
- **maildir 目录**：`<mail_base_dir>/mm`
- **lei 首次拉取**：`lei q --only=https://lore.kernel.org/linux-mm --output="<mail_base_dir>/mm" 'rt:<days>.days.ago..'`
- **lei 更新**：`lei up <mail_base_dir>/mm`
- **核心代码目录**：`mm/`, `include/linux/mm*.h`, `include/linux/memcontrol.h`
- **报告标题**：`Linux 内存管理最新 Feature 分析报告`

**保留英文术语**：folio, mTHP, THP, MGLRU, khugepaged, zswap, memcg, lruvec, compaction, migration, LRU, slab, vmalloc, mmap, hugetlb, page fault, swap, OOM, NUMA, zsmalloc, balloon

**interesting 关键词**（额外补充，在 filter_rules 基础上）：
`mmap`, `hugetlb`, `thp`, `folio`, `mglru`, `zswap`, `memcg`, `numa`, `swap`, `compaction`, `migrat`, `slab`, `vmalloc`, `oom`

---

## sched — 进程调度

- **邮件列表**：linux-kernel@vger.kernel.org
- **lore URL**：`https://lore.kernel.org/lkml`
- **maildir 目录**：`<mail_base_dir>/sched`
- **lei 首次拉取**：`lei q --only=https://lore.kernel.org/lkml --output="<mail_base_dir>/sched" 'rt:<days>.days.ago.. AND (sched OR scheduler OR cfs OR eevdf)'`
- **lei 更新**：`lei up <mail_base_dir>/sched`
- **核心代码目录**：`kernel/sched/`, `include/linux/sched*.h`, `include/uapi/linux/sched.h`
- **报告标题**：`Linux 调度子系统最新 Feature 分析报告`

**保留英文术语**：CFS, EEVDF, vruntime, runqueue, cgroup, cpuset, load balancing, migration, throttling, preemption, RT, FIFO, deadline, idle, nohz, tick, latency, wakeup, affinity, cpufreq, energy-aware scheduling (EAS), NUMA balancing

**interesting 关键词**：
`sched`, `scheduler`, `cfs`, `eevdf`, `vruntime`, `runqueue`, `preempt`, `wakeup`, `load.balance`, `cpuset`, `cgroup`, `affinity`, `latency`, `deadline`, `throttl`, `idle`, `nohz`

---

## fs — 文件系统 / VFS

- **邮件列表**：linux-fsdevel@vger.kernel.org
- **lore URL**：`https://lore.kernel.org/linux-fsdevel`
- **maildir 目录**：`<mail_base_dir>/fs`
- **lei 首次拉取**：`lei q --only=https://lore.kernel.org/linux-fsdevel --output="<mail_base_dir>/fs" 'rt:<days>.days.ago..'`
- **lei 更新**：`lei up <mail_base_dir>/fs`
- **核心代码目录**：`fs/`, `include/linux/fs*.h`, `include/linux/dcache.h`
- **报告标题**：`Linux 文件系统最新 Feature 分析报告`

**保留英文术语**：VFS, inode, dentry, dcache, page cache, writeback, fsync, fallocate, xattr, mount, namei, readdir, splice, sendfile, mmap, tmpfs, ext4, btrfs, xfs, erofs, overlayfs, fuse

**interesting 关键词**：
`vfs`, `inode`, `dentry`, `dcache`, `page.cache`, `writeback`, `fsync`, `mount`, `xattr`, `fallocate`, `splice`, `readdir`, `namei`, `extent`, `journal`, `btree`

---

## net — 网络子系统

- **邮件列表**：netdev@vger.kernel.org
- **lore URL**：`https://lore.kernel.org/netdev`
- **maildir 目录**：`<mail_base_dir>/net`
- **lei 首次拉取**：`lei q --only=https://lore.kernel.org/netdev --output="<mail_base_dir>/net" 'rt:<days>.days.ago..'`
- **lei 更新**：`lei up <mail_base_dir>/net`
- **核心代码目录**：`net/`, `include/net/`, `include/linux/netdevice.h`
- **报告标题**：`Linux 网络子系统最新 Feature 分析报告`

**保留英文术语**：sk_buff, netdev, XDP, eBPF, TC, qdisc, socket, TCP, UDP, QUIC, TLS, offload, GRO, GSO, RSS, RPS, NAPI, bonding, bridge, vlan, vxlan, wireguard

**interesting 关键词**：
`tcp`, `udp`, `xdp`, `socket`, `netdev`, `qdisc`, `offload`, `gro`, `gso`, `napi`, `sk_buff`, `tls`, `quic`, `bridge`, `vlan`, `vxlan`, `route`, `neighbour`, `netfilter`

---

## block — 块 IO

- **邮件列表**：linux-block@vger.kernel.org
- **lore URL**：`https://lore.kernel.org/linux-block`
- **maildir 目录**：`<mail_base_dir>/block`
- **lei 首次拉取**：`lei q --only=https://lore.kernel.org/linux-block --output="<mail_base_dir>/block" 'rt:<days>.days.ago..'`
- **lei 更新**：`lei up <mail_base_dir>/block`
- **核心代码目录**：`block/`, `drivers/block/`, `include/linux/blk*.h`
- **报告标题**：`Linux 块IO子系统最新 Feature 分析报告`

**保留英文术语**：bio, request queue, blkcg, io scheduler, mq-deadline, kyber, bfq, nvme, virtio-blk, scsi, multipath, dm, md, zoned storage, uring

**interesting 关键词**：
`bio`, `blk`, `nvme`, `scsi`, `ioscheduler`, `mq.deadline`, `kyber`, `bfq`, `virtio`, `zoned`, `multiqueue`, `dm.`, `md.`

---

## io_uring — io_uring

- **邮件列表**：io-uring@vger.kernel.org
- **lore URL**：`https://lore.kernel.org/io-uring`
- **maildir 目录**：`<mail_base_dir>/io_uring`
- **lei 首次拉取**：`lei q --only=https://lore.kernel.org/io-uring --output="<mail_base_dir>/io_uring" 'rt:<days>.days.ago..'`
- **lei 更新**：`lei up <mail_base_dir>/io_uring`
- **核心代码目录**：`io_uring/`, `include/linux/io_uring*.h`
- **报告标题**：`Linux io_uring 最新 Feature 分析报告`

**保留英文术语**：SQE, CQE, ring, submission queue, completion queue, fixed file, registered buffer, IOSQE, IORING, multishot, zero-copy

---

## bpf — BPF / eBPF

- **邮件列表**：bpf@vger.kernel.org
- **lore URL**：`https://lore.kernel.org/bpf`
- **maildir 目录**：`<mail_base_dir>/bpf`
- **lei 首次拉取**：`lei q --only=https://lore.kernel.org/bpf --output="<mail_base_dir>/bpf" 'rt:<days>.days.ago..'`
- **lei 更新**：`lei up <mail_base_dir>/bpf`
- **核心代码目录**：`kernel/bpf/`, `net/core/filter.c`, `include/linux/bpf*.h`, `tools/lib/bpf/`
- **报告标题**：`Linux BPF 最新 Feature 分析报告`

**保留英文术语**：map, prog, verifier, BTF, CO-RE, kprobe, uprobe, tracepoint, XDP, TC, cgroup, socket filter, ring buffer, arena, kfunc

---

## 如何添加自定义子系统

用户也可以指定自定义子系统，只需提供：
1. maildir 路径（绝对路径）
2. 子系统名称（用于命名报告文件）

示例：
```bash
# 用户说：分析 ~/Mail/lei/mm-stable 里的邮件
python3 <skill_dir>/scripts/extract_patches.py \
  --days 30 \
  --maildir ~/Mail/lei/mm-stable \
  > /tmp/mm-stable_index.json
```
