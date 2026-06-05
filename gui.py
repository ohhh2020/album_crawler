# -*- coding: utf-8 -*-
"""
网易云音乐专辑封面爬虫 - 图形界面模块
基于 tkinter 实现
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from crawler import search_artist, download_albums


# ------ 常量 ------

DEFAULT_SAVE_DIR = "album_covers"
WINDOW_TITLE = "网易云音乐专辑封面下载器 v1.0"
MODE_ID = "ID模式 - 直接输入歌手ID"
MODE_NAME = "名称模式 - 通过歌手名称搜索"


class AlbumCrawlerGUI:
    """网易云音乐专辑封面下载器图形界面"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry("680x580")
        self.root.resizable(False, False)

        # 运行状态标记
        self.is_running = False

        # 搜索模式
        self.search_mode = tk.StringVar(value=MODE_ID)

        # 控件
        self._build_ui()

    def _build_ui(self):
        """构建界面"""
        # ====== 输入区域 ======
        input_frame = ttk.LabelFrame(self.root, text="歌手信息", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        # 搜索模式单选按钮
        ttk.Radiobutton(
            input_frame,
            text=MODE_ID,
            variable=self.search_mode,
            value=MODE_ID,
        ).grid(row=0, column=0, sticky=tk.W, padx=5)

        ttk.Radiobutton(
            input_frame,
            text=MODE_NAME,
            variable=self.search_mode,
            value=MODE_NAME,
        ).grid(row=0, column=1, sticky=tk.W, padx=5)

        # 输入框
        ttk.Label(input_frame, text="歌手ID / 名称:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.entry_input = ttk.Entry(input_frame, width=50)
        self.entry_input.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # ====== Cookie 区域 ======
        cookie_frame = ttk.LabelFrame(self.root, text="Cookie 设置（可选）", padding=10)
        cookie_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(cookie_frame, text="Cookie:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=2
        )
        self.entry_cookie = ttk.Entry(cookie_frame, width=80)
        self.entry_cookie.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        ttk.Label(
            cookie_frame,
            text="从浏览器开发者工具中复制 Cookie（F12 → Network → 任意请求 → Request Headers → Cookie）",
            foreground="gray",
            font=("", 9),
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5)

        # ====== 保存路径 ======
        path_frame = ttk.LabelFrame(self.root, text="保存设置", padding=10)
        path_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(path_frame, text="保存路径:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.entry_path = ttk.Entry(path_frame, width=60)
        self.entry_path.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.entry_path.insert(0, DEFAULT_SAVE_DIR)

        ttk.Button(
            path_frame, text="浏览...", command=self._select_path, width=10
        ).grid(row=0, column=2, padx=5)

        # ====== 操作按钮 ======
        self.btn_frame = ttk.Frame(self.root)
        self.btn_frame.pack(fill=tk.X, padx=10, pady=5)

        self.btn_start = ttk.Button(
            self.btn_frame, text="开始下载", command=self._start_download, width=15
        )
        self.btn_start.pack(side=tk.LEFT, padx=5)

        # ====== 进度条 ======
        progress_frame = ttk.LabelFrame(self.root, text="下载进度", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=600,
        )
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)

        self.label_progress = ttk.Label(progress_frame, text="等待开始...")
        self.label_progress.pack(anchor=tk.W, padx=5)

        # ====== 状态信息 ======
        status_frame = ttk.LabelFrame(self.root, text="运行状态", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.text_status = tk.Text(status_frame, height=12, wrap=tk.WORD, state=tk.DISABLED)
        self.text_status.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 滚动条
        scrollbar = ttk.Scrollbar(self.text_status, command=self.text_status.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_status.config(yscrollcommand=scrollbar.set)

    def _select_path(self):
        """选择保存路径"""
        path = filedialog.askdirectory(title="选择保存目录")
        if path:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, path)

    def _log(self, message):
        """在状态框中添加日志"""
        self.text_status.config(state=tk.NORMAL)
        self.text_status.insert(tk.END, message + "\n")
        self.text_status.see(tk.END)
        self.text_status.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _update_progress(self, current, total, message):
        """更新进度条和状态"""
        if total > 0:
            percent = (current / total) * 100
            self.progress_var.set(percent)
            self.label_progress.config(
                text=f"进度: {current}/{total}  ({current * 100 // total}%)"
            )
        else:
            self.label_progress.config(text=message)
        self._log(message)

    def _reset_ui(self):
        """重置界面到初始状态"""
        self.is_running = False
        self.btn_start.config(text="开始下载", state=tk.NORMAL)
        self.progress_var.set(0)
        self.label_progress.config(text="等待开始...")

    def _start_download(self):
        """开始下载（启动后台线程）"""
        if self.is_running:
            return

        # 获取输入
        user_input = self.entry_input.get().strip()
        if not user_input:
            messagebox.showwarning("提示", "请输入歌手ID或歌手名称")
            return

        # 禁用按钮
        self.is_running = True
        self.btn_start.config(text="下载中...", state=tk.DISABLED)
        self.text_status.config(state=tk.NORMAL)
        self.text_status.delete(1.0, tk.END)
        self.text_status.config(state=tk.DISABLED)
        self.progress_var.set(0)

        # 启动后台线程
        thread = threading.Thread(
            target=self._download_worker,
            args=(user_input,),
            daemon=True,
        )
        thread.start()

    def _download_worker(self, user_input):
        """后台下载工作线程"""
        try:
            cookie_str = self.entry_cookie.get().strip()
            save_path = self.entry_path.get().strip() or DEFAULT_SAVE_DIR

            # 判断模式
            if self.search_mode.get() == MODE_ID:
                # ID 模式
                artist_id = int(user_input)
                self.root.after(
                    0, self._log, f"歌手ID: {artist_id}"
                )
                self.root.after(
                    0, self._log, f"保存路径: {os.path.abspath(save_path)}"
                )
                self._run_download(artist_id, save_path, cookie_str)
            else:
                # 名称模式：先搜索
                self.root.after(0, self._update_progress, 0, 1, "正在搜索歌手...")
                artists = search_artist(user_input, cookie_str)

                if not artists:
                    self.root.after(
                        0, messagebox.showwarning, "未找到", f"未找到歌手: {user_input}"
                    )
                    self.root.after(0, self._reset_ui)
                    return

                # 只有一个结果，直接使用
                if len(artists) == 1:
                    artist = artists[0]
                    self.root.after(
                        0, self._log, f"找到歌手: {artist['name']} (ID: {artist['id']})"
                    )
                    self._run_download(artist["id"], save_path, cookie_str)
                else:
                    # 多个结果，显示选择对话框
                    self.root.after(
                        0, self._show_artist_selection, artists, save_path, cookie_str
                    )

        except ValueError:
            self.root.after(
                0, messagebox.showerror, "输入错误", "歌手ID必须是数字！"
            )
            self.root.after(0, self._reset_ui)
        except Exception as e:
            self._log_error(f"发生错误: {e}")
            self.root.after(0, self._reset_ui)

    def _show_artist_selection(self, artists, save_path, cookie_str):
        """显示歌手选择窗口"""
        select_window = tk.Toplevel(self.root)
        select_window.title("选择歌手")
        select_window.geometry("400x300")
        select_window.transient(self.root)

        ttk.Label(select_window, text="找到多个匹配的歌手，请选择：").pack(pady=10)

        listbox = tk.Listbox(select_window, width=50, height=10)
        listbox.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        for artist in artists:
            listbox.insert(tk.END, f"{artist['name']} (ID: {artist['id']})")

        def on_select():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                artist = artists[idx]
                select_window.destroy()
                self._log(f"已选择: {artist['name']} (ID: {artist['id']})")
                self._run_download(artist["id"], save_path, cookie_str)
            else:
                messagebox.showwarning("提示", "请先选择一位歌手")

        ttk.Button(select_window, text="确认选择", command=on_select).pack(pady=10)

    def _run_download(self, artist_id, save_path, cookie_str):
        """执行下载任务"""
        try:
            success, fail, failed_list = download_albums(
                artist_id,
                save_path,
                cookie_str,
                progress_callback=lambda c, t, m: self.root.after(0, self._update_progress, c, t, m),
            )

            # 显示完成信息
            summary = (
                f"\n======= 下载完成 =======\n"
                f"总计: {success + fail} 张\n"
                f"成功: {success} 张\n"
                f"失败: {fail} 张\n"
                f"保存路径: {os.path.abspath(save_path)}"
            )
            self.root.after(0, self._log, summary)

            if fail > 0:
                self.root.after(
                    0, messagebox.showwarning,
                    "下载完成",
                    f"完成！成功 {success} 张，失败 {fail} 张\n"
                    f"失败的专辑: {', '.join(failed_list)}"
                )
            else:
                self.root.after(
                    0, messagebox.showinfo,
                    "下载完成",
                    f"全部 {success} 张专辑封面下载成功！\n保存路径: {os.path.abspath(save_path)}"
                )

        except Exception as e:
            self._log_error(f"下载过程中发生错误: {e}")
        finally:
            self.root.after(0, self._reset_ui)

    def _log_error(self, message):
        """记录错误到日志并弹出提示"""
        self.root.after(0, self._log, f"[错误] {message}")
        self.root.after(0, messagebox.showerror, "错误", message)

    def run(self):
        """启动主循环"""
        self.root.mainloop()
