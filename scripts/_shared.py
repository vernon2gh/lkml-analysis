"""lkml-analysis 共享配置工具，供其他脚本 import。"""
import json
import os

CONFIG_PATH = os.path.expanduser('~/.config/lkml-analysis/config.json')


def load_config():
    with open(CONFIG_PATH) as f:
        c = json.load(f)
    return {k: os.path.expanduser(v) for k, v in c.items()}
