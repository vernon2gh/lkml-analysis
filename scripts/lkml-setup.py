#!/usr/bin/env python3
"""
首次配置或更新 lkml-analysis 配置文件。

Usage:
  python3 lkml-setup.py
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _shared import CONFIG_PATH as CONFIG


def main():
    if os.path.exists(CONFIG):
        with open(CONFIG) as f:
            cfg = json.load(f)
        print(f"当前配置（{CONFIG}）：")
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
        ans = input("是否更新？[y/N] ").strip().lower()
        if ans != 'y':
            print("配置未修改。")
            return

    mail_base = input("邮件基础目录 [~/Mail/lei]：").strip() or "~/Mail/lei"
    output_dir = input("报告输出目录 [~/kernel-reports]：").strip() or "~/kernel-reports"

    cfg = {"mail_base_dir": mail_base, "output_dir": output_dir}
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    os.makedirs(os.path.expanduser(output_dir), exist_ok=True)

    with open(CONFIG, 'w') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"配置已保存：{CONFIG}")


if __name__ == '__main__':
    main()
