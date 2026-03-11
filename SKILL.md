---
name: lkml-analysis
description: 分析 Linux 内核各子系统邮件列表中最近N天的新 feature，生成详细中文报告（Markdown/PDF）。支持内存管理（mm）、调度（sched）、文件系统（fs）、网络（net）、块IO（block）等子系统。当用户说"分析 mm/sched/fs feature"、"生成内核子系统报告"、"linux 内核新特性"、"分析内核邮件列表"、"linux-mm 分析"、"内核 patch 分析"等时激活。首次使用时会引导配置邮件目录和输出目录。
---

# Linux Kernel Mailing List Analysis Skill

分析指定内核子系统的邮件列表，生成包含**背景/解决的问题/如何做/收益**的详细中文报告，可选转 PDF。

`<skill_dir>` = 本 skill 实际路径：`~/.claude/skills/lkml-analysis`

---

## 第零步：配置检查（首次使用必做）

检查配置文件是否存在：

```bash
cat ~/.config/lkml-analysis/config.json 2>/dev/null || echo "NOT_FOUND"
```

**如果不存在**，询问用户以下信息并创建配置：

```
我需要先配置几个路径，后续使用时就无需再配置了：

1. 邮件基础目录（lei 同步邮件的根目录，如 ~/Mail/lei）：
2. 输出目录（报告保存位置，如 ~/kernel-reports）：
```

收到用户回答后创建配置文件：

```bash
mkdir -p ~/.config/lkml-analysis
cat > ~/.config/lkml-analysis/config.json << 'EOF'
{
  "mail_base_dir": "<用户填写的邮件基础目录>",
  "output_dir": "<用户填写的输出目录>"
}
EOF
mkdir -p <用户填写的输出目录>
```

**如果已存在**，读取配置，继续下一步（用户可以说"更新配置"来重新配置）。

---

## 第一步：确定分析目标

从用户消息中识别：
- **子系统**：mm / sched / fs / net / block / io_uring / bpf（默认 mm）
- **时间范围**：天数（默认 30 天）

若用户未明确指定子系统，列出选项让用户选择：

```
请选择要分析的内核子系统：
  mm       - 内存管理
  sched    - 进程调度
  fs       - 文件系统/VFS
  net      - 网络子系统
  block    - 块IO
  io_uring - io_uring
  bpf      - BPF
```

各子系统详细信息见 `references/subsystems.md`。

---

## 第二步：获取/更新邮件列表

各子系统的 lore URL 见 `references/subsystems.md`。

读取配置，拼接该子系统的 maildir：

```bash
MAIL_BASE=$(python3 -c "import json,os; c=json.load(open(os.path.expanduser('~/.config/lkml-analysis/config.json'))); print(os.path.expanduser(c['mail_base_dir']))")
OUTPUT_DIR=$(python3 -c "import json,os; c=json.load(open(os.path.expanduser('~/.config/lkml-analysis/config.json'))); print(os.path.expanduser(c['output_dir']))")
SUBSYSTEM="<子系统名>"
MAILDIR="$MAIL_BASE/$SUBSYSTEM"
DAYS=<天数>
LORE_URL="<从上表查到的 lore URL>"

if [ -d "$MAILDIR" ]; then
    # 邮件目录已存在，只更新当前子系统的邮件列表
    echo "更新 $SUBSYSTEM 邮件列表..."
    lei up "$MAILDIR"
else
    # 邮件目录不存在，首次用 lei q --only 从 lore 拉取
    echo "邮件目录不存在，首次从 lore.kernel.org 拉取 $SUBSYSTEM 邮件列表（可能需要几分钟）..."
    lei q --only="$LORE_URL" \
          --output="$MAILDIR" \
          "rt:${DAYS}.days.ago.."
    echo "拉取完成，共获取邮件：$(find "$MAILDIR" -type f | wc -l) 封"
fi
```

**注意：**
- `sched` 子系统的 lore URL 为 lkml（邮件量大），首次拉取耗时较长
- 拉取完成后，后续可用 `lei up "$MAILDIR"` 增量更新，无需重新拉取

---

## 第三步：建立轻量索引

```bash
python3 <skill_dir>/scripts/extract_patches.py \
  --days <天数> \
  --maildir "$MAILDIR" \
  > /tmp/${SUBSYSTEM}_index.json

python3 -c "import json; d=json.load(open('/tmp/${SUBSYSTEM}_index.json')); print(f'共 {d[\"total\"]} 条系列')"
```

---

## 第四步（可选）：打 patch 深入分析

**首先自动检测当前目录是否为内核源码树：**

```bash
# 检测条件：当前目录存在 Makefile 且含有 LINUX_KERNEL_VERSION 或 Kbuild 标志
if [ -f "$(pwd)/Makefile" ] && grep -q "LINUX_KERNEL_VERSION\|^VERSION\s*=" "$(pwd)/Makefile" 2>/dev/null; then
    echo "KERNEL_TREE:$(pwd)"
elif [ -f "$(pwd)/Kbuild" ] || [ -f "$(pwd)/scripts/Kbuild.include" ]; then
    echo "KERNEL_TREE:$(pwd)"
else
    echo "NOT_KERNEL_TREE"
fi
```

**如果不是内核源码目录**：跳过本步骤，直接进入第五步生成报告。不提示用户，也不要求用户切换目录。

**如果是内核源码目录**：在分析某个 patch 系列时，若仅凭封面信和 diff 片段难以理解上下文（涉及复杂数据结构、调用链），可将 patch 应用到测试分支：

```bash
LINUX_DIR="$(pwd)"
MAILDIR="$MAILDIR" LINUX_DIR="$LINUX_DIR" \
  bash <skill_dir>/scripts/apply_patches.sh \
  "<Message-ID>" \
  "analysis/${SUBSYSTEM}-$(date +%Y-%m)"
```

打入后查看代码上下文（各子系统核心目录见 `references/subsystems.md`）：

```bash
# 查看该子系统改动
git log -p origin/master..HEAD -- <子系统核心目录>

# 查看某具体文件改动
git diff origin/master..HEAD -- <文件路径>

# 按 patch 逐个查看
git log --oneline origin/master..HEAD
```

分析完成后清理测试分支：

```bash
git checkout master && git branch -D "analysis/${SUBSYSTEM}-$(date +%Y-%m)"
```

---

## 第五步：生成 Markdown 报告

过滤和分析策略见 `references/filter_rules.md`，报告格式**必须严格遵循** `references/report_template.md`。

**三档过滤：**

| hint | 策略 |
|------|------|
| `interesting` | 直接读邮件，深度分析 |
| `maybe` | 先读封面信（seq=0），判断是否值得分析 |
| `skip` | 跳过，不读邮件 |

**按需读取邮件内容：**

```bash
python3 <skill_dir>/scripts/extract_patches.py --read <filepath>
```

**分析原则：**
1. `files['0']`：最新版封面（动机、背景、benchmark）
2. 若封面只写 changelog，读 `prev_covers[0]['file']` 获取完整背景
3. `files['1']`, `files['2']`...：关键 patch 文件（代码改动）

**收益格式：**
- 有数据：直接列出作者提供的数字和测试环境
- 无数据：写「作者未提供性能数据，[推断的预期收益]」
- 性能数据判定：完整阅读封面信 + 所有 patch 提交日志正文

**报告排序：** 新接口/新机制 > 性能优化 > 重要 bug fix > 内部重构

**保存报告：**

```bash
REPORT_FILE="$OUTPUT_DIR/${SUBSYSTEM}-report-$(date +%Y-%m-%d).md"
```

如有 NACK，在对应 feature 末尾标注 ⚠️。

---

## 第六步：转换为 PDF（可选，用户要求时才执行）

```javascript
const { mdToPdf } = require('md-to-pdf');
const cssPath = '<skill_dir>/assets/pdf_style.css';
const reportMd = process.env.REPORT_FILE;
const reportPdf = reportMd.replace('.md', '.pdf');

await mdToPdf(
  { path: reportMd },
  {
    dest: reportPdf,
    pdf_options: { format: 'A4', margin: { top: '18mm', bottom: '18mm', left: '18mm', right: '18mm' } },
    stylesheet: [cssPath],
  }
);
console.log('PDF saved to:', reportPdf);
```

---

## 关键注意事项

- 用邮件 `Date:` 头过滤时间，不用文件时间戳
- 只取封面信（Subject 含 `0/N`）或单个 patch，避免重复分析同一系列
- 正文截取到 `---` / `diff --git` 之前，过滤 `>` 引用行
- 索引字段：`d['series']`，读邮件内容用 `--read <filepath>`
