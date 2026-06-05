# -*- coding: utf-8 -*-
"""
网易云音乐爬虫模块
使用网易云音乐公开 API，负责专辑列表获取、图片下载等核心逻辑
"""

import os
import re
import time
import random
import requests


# ------ 常量定义 ------

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://music.163.com/",
}

ALBUM_LIST_API = "https://music.163.com/api/artist/albums/{artist_id}"
SEARCH_API = "https://music.163.com/api/search/get"

PAGE_SIZE = 50
MAX_RETRIES = 3
MIN_DELAY = 0.5
MAX_DELAY = 1.0


# ------ 辅助函数 ------

def _clean_filename(name):
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/:*?"<>|]', "_", name)


def _get_year_from_publish_time(publish_time):
    """
    从毫秒级时间戳中提取年份
    """
    if not publish_time:
        return "未知"
    try:
        t = int(publish_time)
        if t > 10**12:
            t = t // 1000
        return str(time.localtime(t).tm_year)
    except (ValueError, TypeError, OSError):
        return "未知"


def _remove_size_suffix(url):
    """
    去掉封面 URL 尺寸参数获取原图
    如 https://p1.music.126.net/xxx.jpg?param=640x640 -> https://p1.music.126.net/xxx.jpg
    """
    if not url:
        return url
    idx = url.find("?")
    return url[:idx] if idx != -1 else url


def _request_get(url, params=None, cookie_str=""):
    """带重试的 GET 请求"""
    headers = HEADERS.copy()
    if cookie_str:
        headers["Cookie"] = cookie_str

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            raise Exception(f"请求失败（已重试 {MAX_RETRIES} 次）: {e}")


# ------ 主要接口 ------

def search_artist(keyword, cookie_str=""):
    """
    通过名称搜索歌手
    :return: 歌手列表 [{"id": int, "name": str}, ...]
    """
    params = {"s": keyword, "type": 100, "limit": 20}
    result = _request_get(SEARCH_API, params, cookie_str)

    artists = []
    try:
        for a in result.get("result", {}).get("artists", []):
            artists.append({"id": a["id"], "name": a["name"]})
    except (KeyError, TypeError):
        pass
    return artists


def get_all_albums(artist_id, cookie_str=""):
    """
    获取歌手所有专辑（自动处理分页）
    :return: 专辑列表
    """
    all_albums = []
    offset = 0

    while True:
        url = ALBUM_LIST_API.format(artist_id=artist_id)
        params = {"limit": PAGE_SIZE, "offset": offset}
        result = _request_get(url, params, cookie_str)

        albums = result.get("hotAlbums", [])
        if not albums:
            break

        for album in albums:
            all_albums.append({
                "id": album["id"],
                "name": album["name"],
                "pic_url": album.get("picUrl", ""),
                "publish_time": album.get("publishTime", 0),
                "size": album.get("size", 0),
            })

        if len(albums) < PAGE_SIZE:
            break

        offset += PAGE_SIZE
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    return all_albums


def download_image(url, save_path, cookie_str=""):
    """下载单张图片，失败返回 False"""
    raw_url = _remove_size_suffix(url)
    headers = HEADERS.copy()
    if cookie_str:
        headers["Cookie"] = cookie_str

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(raw_url, headers=headers, timeout=15)
            resp.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(resp.content)
            return True
        except requests.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
    return False


def download_albums(artist_id, save_dir, cookie_str="", progress_callback=None):
    """
    下载歌手所有专辑封面
    :param progress_callback: (current, total, message)
    :return: (成功数, 失败数, 失败列表)
    """
    if progress_callback:
        progress_callback(0, 1, "正在获取专辑列表...")

    albums = get_all_albums(artist_id, cookie_str)
    total = len(albums)
    if total == 0:
        return 0, 0, []

    os.makedirs(save_dir, exist_ok=True)

    success = 0
    fail = 0
    failed_list = []

    for idx, album in enumerate(albums):
        year = _get_year_from_publish_time(album.get("publish_time"))
        name = _clean_filename(album["name"])
        filepath = os.path.join(save_dir, f"{name}_{year}.jpg")

        # 文件已存在则跳过
        if os.path.exists(filepath):
            msg = f"[跳过] {album['name']} ({year}) - 文件已存在"
            if progress_callback:
                progress_callback(idx + 1, total, msg)
            success += 1
            continue

        if album["pic_url"]:
            ok = download_image(album["pic_url"], filepath, cookie_str)
            if ok:
                msg = f"[成功] {album['name']} ({year})"
                success += 1
            else:
                msg = f"[失败] {album['name']} ({year}) - 下载失败"
                fail += 1
                failed_list.append(album["name"])
        else:
            msg = f"[失败] {album['name']} ({year}) - 无封面地址"
            fail += 1
            failed_list.append(album["name"])

        if progress_callback:
            progress_callback(idx + 1, total, msg)

        if idx < total - 1:
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    return success, fail, failed_list
