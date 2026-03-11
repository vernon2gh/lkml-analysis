#!/usr/bin/env python3
"""
建立子系统 patch 系列索引，保存到 /tmp/<subsystem>_index.json。

Usage:
  python3 lkml-index.py <subsystem> [--days N]

Output:
  /tmp/<subsystem>_index.json
  打印：总数 + hint 分布（interesting / maybe / skip）

Examples:
  python3 lkml-index.py mm --days 1
  python3 lkml-index.py net --days 7
"""
import argparse
import json
import os
import subprocess
import sys

CONFIG_FILE = os.path.expanduser('~/.config/lkml-analysis/config.json')
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))


def load_mail_base():
    with open(CONFIG_FILE) as f:
        c = json.load(f)
    return os.path.expanduser(c['mail_base_dir'])


def main():
    parser = argparse.ArgumentParser(description='建立 patch 系列轻量索引')
    parser.add_argument('subsystem')
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('--maildir', help='直接指定 maildir 路径（自定义子系统时使用）')
    args = parser.parse_args()

    if args.maildir:
        maildir = os.path.expanduser(args.maildir)
    else:
        mail_base = load_mail_base()
        maildir   = os.path.join(mail_base, args.subsystem)
    index_file = f'/tmp/{args.subsystem}_index.json'
    extract_py = os.path.join(SCRIPT_DIR, 'extract_patches.py')

    result = subprocess.run(
        ['python3', extract_py, '--days', str(args.days), '--maildir', maildir],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    with open(index_file, 'w') as f:
        f.write(result.stdout)

    data  = json.loads(result.stdout)
    total = data['total']
    hints = {'interesting': 0, 'maybe': 0, 'skip': 0}
    for s in data['series']:
        hints[s.get('hint', 'skip')] += 1

    print(f"索引已保存：{index_file}")
    print(
        f"共 {total} 条系列  |  "
        f"interesting={hints['interesting']}  "
        f"maybe={hints['maybe']}  "
        f"skip={hints['skip']}"
    )


if __name__ == '__main__':
    main()
