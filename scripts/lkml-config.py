#!/usr/bin/env python3
"""
读取 lkml-analysis 配置值，或检测当前目录是否为内核源码树。

Usage:
  python3 lkml-config.py                        # 打印完整配置 JSON
  python3 lkml-config.py output_dir             # 打印 output_dir
  python3 lkml-config.py mail_base_dir          # 打印 mail_base_dir
  python3 lkml-config.py check-kernel           # 输出 KERNEL_TREE:<path> 或 NOT_KERNEL_TREE
  python3 lkml-config.py report-path <subsys>   # 打印报告文件路径（含日期）
"""
import datetime
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _shared import CONFIG_PATH, load_config as load


def check_kernel():
    cwd = os.getcwd()
    mk = os.path.join(cwd, 'Makefile')
    if os.path.isfile(mk):
        try:
            content = open(mk).read(4096)
            if 'LINUX_KERNEL_VERSION' in content or 'VERSION =' in content:
                print(f'KERNEL_TREE:{cwd}')
                return
        except Exception:
            pass
    if os.path.isfile(os.path.join(cwd, 'scripts/Kbuild.include')):
        print(f'KERNEL_TREE:{cwd}')
        return
    print('NOT_KERNEL_TREE')


def report_path(subsystem):
    cfg = load()
    today = datetime.date.today().strftime('%Y-%m-%d')  # noqa: keep datetime import
    print(os.path.join(cfg['output_dir'], f'{subsystem}-report-{today}.md'))


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else None
    if key == 'check-kernel':
        check_kernel()
        return
    if key == 'report-path':
        if len(sys.argv) < 3:
            print('Usage: lkml-config.py report-path <subsystem>', file=sys.stderr)
            sys.exit(1)
        report_path(sys.argv[2])
        return
    cfg = load()
    if key:
        print(cfg[key])
    else:
        print(json.dumps(cfg, indent=2))


if __name__ == '__main__':
    main()
