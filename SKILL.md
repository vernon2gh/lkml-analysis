---
name: lkml-analysis
description: 分析 Linux 内核各子系统邮件列表中最近N天的新 feature，生成详细中文报告（Markdown/PDF）。支持内存管理（mm）、调度（sched）、文件系统（fs）、网络（net）、块IO（block）等子系统。当用户说"分析 mm/sched/fs feature"、"linux 内核新特性"、"分析内核邮件列表"等时激活。首次使用时会引导配置邮件目录和输出目录。
---

# Linux Kernel Mailing List Analysis Skill

分析内核子系统邮件列表，生成含**背景/问题/实现/收益**的详细中文报告。

`<skill_dir>` = `~/.claude/skills/lkml-analysis`

报告格式、写作规则统一定义在 `<skill_dir>/references/report_template.md`，所有 agent 均须遵循。

### Agent 角色命名

| 角色 | 名称 | 职责 |
|------|------|------|
| 主 agent | **coordinator** | 统筹全流程：建索引、分发任务、汇总报告 |
| 筛选 agent | **screener** | 分批阅读封面信，分类判定 interesting / 排除 |
| 分析 agent | **analyzer** | 深入阅读 patch，撰写 feature 分析段落 |
| 检查 agent | **reviewer** | 深入详细检查输出格式与写作规则 |

下文统一使用以上名称。

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

## 第三步：screener 分批筛选 interesting 系列

coordinator 读取 `./<subsystem>_index.json`，获取所有系列的概览（subject、author、date、files 路径）。

> **强制规则：**
> **必须启动 screener subagent 完成筛选**，coordinator 自身**禁止**直接根据标题、作者、patch 数等元数据做入选/排除判断。即便系列数很少（例如 < 20）也必须走 screener 流程；少量系列时 coordinator 仍启动 1 个 screener，而不是自行代劳。

### 分批处理

将系列列表按**每批 20 条**分组，对每一批启动一个 **screener** 并行筛选。系列总数 ≤ 20 时启动 1 个 screener 处理全部。

#### screener prompt 模板

```
你是 Linux 内核 <子系统> patch 筛选专家。请对以下 patch 系列逐条阅读封面信并分类。

## 工具
- 读取邮件：`python3 <skill_dir>/scripts/lkml-read.py <filepath>`

## 需要筛选的系列

（列出本批 20 条的编号、subject、files['0'] 或 files['-1'] 路径）

## 筛选规则

**禁止仅凭标题判断分类。** 必须先用 lkml-read.py 读取封面信/patch 完整内容，再根据内容分类。

| 分类 | 判定标准 | 是否需要 analyzer 分析 |
|------|----------|--------------------------|
| Feature / 优化 | 新机制、新算法/策略、性能优化 | 是 |
| Bug Fix | 数据损坏、内核崩溃、内存泄漏、死锁、Fixes: 标签 | 是 |
| 排除 | 与<子系统>无关，纯清理/重构/NFC、纯文档/spelling、维护类（MAINTAINERS/mailmap）、"No functional change" | 否 |

## 输出

返回一个编号列表，标明每条系列的分类。
对于分类为"排除"的，必须给出从内容中得出的理由，不可只说"标题看起来像清理"。
```

#### screener 使用方式

- 使用 `Agent` 工具，`subagent_type` 为 `general-purpose`
- 所有批次的 screener **并行**启动
- coordinator 收集所有批次的筛选结果，合并为完整的分类列表
- **校验步骤**：合并后 coordinator 必须核对"筛选结果编号集合 == 索引中系列编号集合"，
  若缺编号则补跑 screener；确认齐全后才能进入第四步

---

## 第四步：analyzer 并行深入分析

coordinator 将所有 interesting 系列分组（每组 2~4 个 feature），每组启动一个 **analyzer**。

### analyzer prompt 模板

给每个 analyzer 的 prompt 须包含以下内容：

```
你是 Linux 内核 <子系统> patch 分析专家。请对以下 patch 系列进行深入分析，为每个系列写一个完整的 feature 分析段落。

## 工具
- 读取邮件：`python3 <skill_dir>/scripts/lkml-read.py <filepath>`
- 读取 patch 文件：直接用 Read 工具

## 需要分析的系列

### 系列 A：<标题>
- 封面信：<files['0'] 或 files['-1'] 的路径>
- Patch 文件：<files['1'], files['2'], ... 的路径>

### 系列 B：<标题>
（同上格式）

## 输出格式与写作规则

严格遵循 `<skill_dir>/references/report_template.md` 中的"Feature 区块"格式和写作要求。

分析步骤：先读封面信理解动机 → 读关键 patch 理解实现，二者缺一不可，不能只读封面。
```

### analyzer 使用方式

- 使用 `Agent` 工具，`subagent_type` 为 `general-purpose`
- 独立的 analyzer 之间**并行**启动（同一条消息中发多个 Agent 调用）
- 每个 analyzer 返回其负责的 feature 分析文本

### 可选：打 patch 深入分析

运行 `python3 <skill_dir>/scripts/lkml-config.py check-kernel` 检测当前目录是否为内核源码树。

**KERNEL_TREE** 时，可在 analyzer prompt 中额外说明：

- 对仅凭 diff 难以理解上下文的系列，运行 `python3 <skill_dir>/scripts/lkml-apply.py <Message-ID> --maildir <maildir>` 应用 patch
- 用 `git show <branch>:<dir>/<file>` 查看改动
- 分析完后 `git checkout master && git branch -D <branch>` 清理

**NOT_KERNEL_TREE** 时跳过此步。

---

## 第五步：reviewer 校验 analyzer 输出

> **强制规则：**
> **必须启动 reviewer subagent 执行校验**，coordinator **禁止**用"看起来格式都对"之类的自我判断代替本步骤。即便 analyzer 自称已遵循模板，都必须走 reviewer subagent。

将系列列表按**每批 10 条**分组，对每一批启动一个 **reviewer** 并行校验。系列总数 ≤ 10 时启动 1 个 reviewer 处理全部。

### reviewer prompt 模板

```
你是 Linux 内核报告格式质量检查员。请逐条核对每个 feature 分析段落是否严格遵循写作规则。

## 权威规则

完整阅读 `<skill_dir>/references/report_template.md`，特别是"Feature 区块"与"写作要求"两节。

## 输入

以下是 N 个 analyzer 返回的 feature 分析文本（每段以 "## <编号>. " 开头）：

<贴入所有 analyzer 返回的文本>

## 输出

对每个 feature 段落单独给出判定：
- 编号 N：PASS / FAIL（若 FAIL，列出缺失项/违规项）

最后给出整体判定：
- **最终判定**：PASS（所有段落通过，可进入第五步）/ FAIL（列出需要重跑的段落编号，coordinator 将针对性重启 analyzer）
```

### reviewer 使用方式

- 使用 `Agent` 工具，`subagent_type` 为 `general-purpose`
- 启动多个 reviewer，并行校验其返回
- 把所有 analyzer 返回的分析文本拼接后作为输入交给 reviewer（不要让 reviewer 自己去读邮件，只检查格式与写作规则）

### 处理 reviewer 结果

- reviewer 返回 **PASS**：进入第六步
- reviewer 返回 **FAIL**：针对不合格段落必须使用 analyzer 重跑修复（只跑失败的，不必全量重跑），拿到新文本后再次进入第五步，直到 PASS

---

## 第六步：coordinator 汇总报告

收集所有 analyzer 返回的分析文本，**必须严格**按 `references/report_template.md` 组装完整报告。

保存报告：用 `python3 <skill_dir>/scripts/lkml-config.py report-path <subsystem>` 获取报告路径，写入该文件。

---

## 第七步：PDF（可选）

运行 `python3 <skill_dir>/scripts/lkml-pdf.py <report_file>` 将 Markdown 报告转换为 PDF。
