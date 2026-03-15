---
name: lkml-analysis
description: 分析 Linux 内核各子系统邮件列表中最近N天的新 feature，生成详细中文报告（Markdown/PDF）。支持内存管理（mm）、调度（sched）、文件系统（fs）、网络（net）、块IO（block）等子系统。当用户说"分析 mm/sched/fs feature"、"linux 内核新特性"、"分析内核邮件列表"等时激活。首次使用时会引导配置邮件目录和输出目录。
---

# Linux Kernel Mailing List Analysis Skill

分析内核子系统邮件列表，生成含**背景/问题/实现/收益**的详细中文报告。

`<skill_dir>` = `~/.claude/skills/lkml-analysis`

报告格式、写作规则统一定义在 `<skill_dir>/references/report_template.md`，subagent 和主 agent 均须遵循。

---

## 第一步：确定目标

从用户消息识别**子系统**（mm/sched/fs/net/block/io_uring/bpf，默认 mm）和**天数**（默认 30）。

---

## 第二步：更新邮件 & 建立索引

依次运行：

1. `python3 <skill_dir>/scripts/lkml-sync.py <subsystem> --days <天数>`
2. `python3 <skill_dir>/scripts/lkml-index.py <subsystem> --days <天数>`

> 自定义 maildir（如 mm-stable）时，给 lkml-index.py 添加 `--maildir ~/Mail/lei/mm-stable`。

---

## 第三步：主 agent 阅读封面信，筛选 interesting

1. 读取 `/tmp/<subsystem>_index.json`，获取所有系列的概览（subject、author、date、files 路径）
2. 逐个用 `python3 <skill_dir>/scripts/lkml-read.py <files['0'] 或 files['-1']>` 读取封面信/单 patch 完整内容

主 agent **逐条阅读**每条封面信的完整内容，分类判定：

| 分类 | 判定标准 | 分析深度 |
|------|---------|---------|
| Feature / 优化 | 新接口、新机制、新算法/策略、性能优化、架构重构、LSF/MM/BPF | 详细（≥500字） |
| 重要 Bug Fix | 数据损坏、内核崩溃、内存泄漏、死锁、生产可复现 | 详细（≥500字） |
| 普通 Bug Fix | Fixes: 标签、syzbot / Reported-by | 简略 |
| 排除 | 纯清理/重构/NFC、纯文档/spelling、维护类（MAINTAINERS/mailmap）、"No functional change" | 跳过 |

输出：一个**编号列表**，标明每条系列的分类和简要理由。

---

## 第四步：分发 subagent 并行深入分析

将所有 interesting 系列分组（每组 2~4 个 feature），每组启动一个 **subagent**。

### subagent 任务 prompt 模板

给每个 subagent 的 prompt 须包含以下内容：

```
你是 Linux 内核 <子系统> patch 分析专家。请对以下 patch 系列进行深入分析，为每个系列写一个完整的 feature 分析段落。

## 工具
- 读取邮件：`python3 <skill_dir>/scripts/lkml-read.py <filepath>`
- 读取 patch 文件：直接用 Read 工具

## 需要分析的系列

### 系列 A：<标题>
- 封面信：<files['0'] 或 files['-1'] 的路径>
- Patch 文件：<files['1'], files['2'], ... 的路径>
- 历史版本封面：<prev_covers 路径（如有）>

### 系列 B：<标题>
（同上格式）

## 输出格式与写作规则

严格遵循 `<skill_dir>/references/report_template.md` 中的"Feature 区块"格式和写作要求。

分析步骤：先读封面信理解动机 → 读关键 patch 理解实现 → 如有历史版本对比 changelog
```

### subagent 使用方式

- 使用 `Agent` 工具，`subagent_type` 为 `general-purpose`
- 独立的 subagent 之间**并行**启动（同一条消息中发多个 Agent 调用）
- 每个 subagent 返回其负责的 feature 分析文本

### 可选：打 patch 深入分析

运行 `python3 <skill_dir>/scripts/lkml-config.py check-kernel` 检测当前目录是否为内核源码树。

**KERNEL_TREE** 时，可在 subagent prompt 中额外说明：

- 对仅凭 diff 难以理解上下文的系列，运行 `python3 <skill_dir>/scripts/lkml-apply.py <Message-ID> --maildir <maildir>` 应用 patch
- 用 `git show <branch>:<dir>/<file>` 查看改动
- 分析完后 `git checkout master && git branch -D <branch>` 清理

**NOT_KERNEL_TREE** 时跳过此步。

---

## 第五步：主 agent 汇总报告

收集所有 subagent 返回的分析文本，**必须严格**按 `references/report_template.md` 组装完整报告。

保存报告：用 `python3 <skill_dir>/scripts/lkml-config.py report-path <subsystem>` 获取报告路径，写入该文件。

---

## 第六步：PDF（可选）

运行 `python3 <skill_dir>/scripts/lkml-pdf.py <report_file>` 将 Markdown 报告转换为 PDF。
