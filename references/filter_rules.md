# Patch 过滤规则

## 通用规则（所有子系统适用）

### 只保留

- `[PATCH ...]` 或 `[RFC PATCH ...]` 开头的邮件
- 封面信（Subject 含 `0/N`）或单个 patch（无序号）
- 涉及**代码逻辑变更**的 patch：新功能、性能优化、重要 bug 修复、架构改进

### 排除

| 类型 | 示例 |
|------|------|
| 回复/讨论 | `Re: [PATCH] ...` |
| CI 报告 | `FAILED`, `linux-next`, `kbuild`, `htmldoc`, `sparse` |
| 纯文档 | `typo`, `grammar`, `comment`, `kernel-doc` |
| 维护类 | `MAINTAINERS`, `mailmap`, `SPDX` |
| 无功能变化 | cover letter 含 "No functional change" 且无性能提升说明 |

---

## NACK 处理

- 扫描所有回复邮件，检测正文中的 `NACK` 或 `NAK` 关键词（非引用行）
- 若某 patch 收到明确 NACK，在报告中该 feature 末尾标注：⚠️ NACK：[作者] "NACK 原因"
- 仅当明确写出 NACK/NAK 时才标注，普通技术质疑不算 NACK

---

## Feature vs Bug Fix 分类

**归为 Feature / 优化（详细分析）：**
- 引入新接口、新系统调用、新 sysfs/proc/debugfs 节点
- 性能优化（有 benchmark 数据更好）
- 架构重构（影响多个子系统）
- 新的算法、策略、机制

**归为 Bug Fix（简略分析，重要的详细写）：**
- Fixes: 标签指向已有 commit
- 标题含 `fix`、`BUG`、`oops`、`crash`、`race`、`leak`
- 附带 syzbot / Reported-by

**重要 bug fix（详细写）：**
- 数据损坏、内核崩溃、内存泄漏、死锁、生产可复现

---

## 子系统特定过滤 hint 补充

`lkml-index.py` 的 `hint_from_subject()` 会做通用判断，以下是各子系统额外的 interesting 触发词（供分析时人工参考）：

| 子系统 | 额外触发词 |
|--------|-----------|
| mm     | folio, hugetlb, thp, mglru, zswap, memcg, compaction, swap |
| sched  | eevdf, cfs, vruntime, preempt, wakeup, load balance, cpuset |
| fs     | vfs, inode, dentry, writeback, fsync, mount, xattr, splice |
| net    | xdp, sk_buff, qdisc, offload, gro, gso, napi, tls |
| block  | bio, nvme, ioscheduler, blkcg, zoned, multiqueue |
| bpf    | verifier, btf, kfunc, map, prog, arena, co-re |

---

## 报告排序原则

1. 新接口 / 新机制（影响面广）
2. 性能优化（有 benchmark 数据）
3. 重要 bug fix（生产可复现、数据损坏类）
4. 内部重构（影响面有限）
