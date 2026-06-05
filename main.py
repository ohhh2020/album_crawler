# -*- coding: utf-8 -*-
"""
网易云音乐专辑封面爬虫 - 主程序入口
自动将 lib 目录添加到导入路径（打包部署用）
"""

import sys
import os


def _setup_path():
    """将 lib 目录添加到 sys.path，支持本地运行和打包后的路径"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    lib_dir = os.path.join(base_dir, "lib")
    if os.path.isdir(lib_dir):
        sys.path.insert(0, lib_dir)


def main():
    """程序入口"""
    _setup_path()
    from gui import AlbumCrawlerGUI
    app = AlbumCrawlerGUI()
    app.run()


if __name__ == "__main__":
    main()
