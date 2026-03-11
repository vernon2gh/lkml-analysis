#!/usr/bin/env python3
"""
更新（或首次拉取）指定子系统的邮件列表。

Usage:
  python3 lkml-sync.py <subsystem> [--days N]

Examples:
  python3 lkml-sync.py mm
  python3 lkml-sync.py net --days 7
"""
import argparse
import os
import subprocess
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _shared import CONFIG_PATH, load_config

LORE_URLS = {
    'mm':       'https://lore.kernel.org/linux-mm',
    'sched':    'https://lore.kernel.org/lkml',
    'fs':       'https://lore.kernel.org/linux-fsdevel',
    'net':      'https://lore.kernel.org/netdev',
    'block':    'https://lore.kernel.org/linux-block',
    'io_uring': 'https://lore.kernel.org/io-uring',
    'bpf':      'https://lore.kernel.org/bpf',
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def ensure_config():
    if not os.path.exists(CONFIG_PATH):
        print("未找到配置，启动初始化向导...")
        result = subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, 'lkml-setup.py')])
        if result.returncode != 0 or not os.path.exists(CONFIG_PATH):
            print("配置未完成，退出。", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='更新子系统邮件列表')
    parser.add_argument('subsystem', choices=list(LORE_URLS))
    parser.add_argument('--days', type=int, default=30)
    args = parser.parse_args()

    ensure_config()
    mail_base = load_config()['mail_base_dir']
    maildir = os.path.join(mail_base, args.subsystem)
    lore_url = LORE_URLS[args.subsystem]

    if os.path.isdir(maildir):
        print(f"更新 {args.subsystem} 邮件列表...")
        result = subprocess.run(['lei', 'up', maildir])
    else:
        print(f"首次从 lore.kernel.org 拉取 {args.subsystem} 邮件（可能需要几分钟）...")
        result = subprocess.run([
            'lei', 'q', f'--only={lore_url}',
            f'--output={maildir}',
            f'rt:{args.days}.days.ago..',
        ])

    if result.returncode != 0:
        sys.exit(result.returncode)

    count = sum(
        len(os.listdir(os.path.join(maildir, d)))
        for d in ('cur', 'new')
        if os.path.isdir(os.path.join(maildir, d))
    )
    print(f"完成，maildir 共 {count} 封邮件：{maildir}")


if __name__ == '__main__':
    main()
