---
name: lkml-analysis
description: 分析 Linux 内核各子系统邮件列表中最近N天的新 feature，生成详细中文报告（Markdown/PDF）。支持内存管理（mm）、调度（sched）、文件系统（fs）、网络（net）、块IO（block）等子系统。当用户说"分析 mm/sched/fs feature"、"linux 内核新特性"、"分析内核邮件列表"等时激活。首次使用时会引导配置邮件目录和输出目录。
---

# Linux Kernel Mailing List Analysis Skill

分析内核子系统邮件列表，生成含**背景/问题/实现/收益**的详细中文报告。

`<skill_dir>` = `~/.claude/skills/lkml-analysis`

---

## 第一步：确定目标

从用户消息识别**子系统**（mm/sched/fs/net/block/io_uring/bpf，默认 mm）和**天数**（默认 30）。

---

## 第二步：更新邮件

运行 `python3 <skill_dir>/scripts/lkml-sync.py <subsystem> --days <天数>` 同步邮件。

> `sched` 首次拉取耗时较长（lkml 邮件量大）。

---

## 第三步：建立索引

依次运行：

- `python3 <skill_dir>/scripts/lkml-index.py <subsystem> --days <天数>`
- `python3 <skill_dir>/scripts/lkml-list.py <subsystem> --hint interesting,maybe --files`

自定义 maildir（如 mm-stable）时，给 lkml-index.py 添加 `--maildir ~/Mail/lei/mm-stable`。

---

## 第四步（可选）：打 patch 深入分析

运行 `python3 <skill_dir>/scripts/lkml-config.py check-kernel` 检测当前目录是否为内核源码树。

**KERNEL_TREE** 时，对仅凭 diff 难以理解上下文的系列打 patch：

- 运行 `python3 <skill_dir>/scripts/lkml-apply.py <Message-ID> --maildir <maildir>`，脚本自动创建 `analysis/<subsys>-<YYYY-MM>` 分支并应用 patch
- 用 `git log -p origin/master..HEAD -- <核心目录>` 查看改动（核心目录见 `references/report_template.md` 子系统参考）
- 分析完后运行 `git checkout master && git branch -D <branch>` 清理分支

**NOT_KERNEL_TREE** 时直接进入第五步。

---

## 第五步：生成报告

过滤策略见 `references/filter_rules.md`，格式**必须严格遵循** `references/report_template.md`。

| hint | 操作 |
|------|------|
| `interesting` | 直接读邮件，深度分析 |
| `maybe` | 先读封面信，再决定是否分析 |
| `skip` | 跳过 |

读取邮件内容：`python3 <skill_dir>/scripts/lkml-read.py <filepath>`

- `files['0']`：封面（动机/背景/benchmark）；仅写 changelog 时读 `prev_covers[0]['file']`
- `files['1']`...：关键 patch 文件（代码实现）
- 有 benchmark 数据必须引用；无数据写推断收益
- NACK → feature 末尾标注 ⚠️

保存报告：用 `python3 <skill_dir>/scripts/lkml-config.py report-path <subsystem>` 获取报告路径，写入该文件。

---

## 第六步：PDF（可选）

运行 `python3 <skill_dir>/scripts/lkml-pdf.py <report_file>` 将 Markdown 报告转换为 PDF。
