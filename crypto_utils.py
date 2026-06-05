# -*- coding: utf-8 -*-
"""
网易云音乐 API 加密工具模块
实现 params 和 encSecKey 的生成逻辑
"""

import random
import base64
import codecs
import json

from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5


# ------ 常量定义 ------

# 第一层 AES 密钥（固定值）
FIRST_AES_KEY = "0CoJUm6Qyw8W8jud"
# AES IV（固定值）
AES_IV = "0102030405060708"
# RSA 公钥（网易云固定）
RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDgtQn2JZ34KIPnQBJi1a5A9YLn
R+/6eM0pBwd3KfKb0o0Tz3jPEGtD82H2wEOdZ5RmU5iCq0OV/Tj7pJgFVNkC2HBs
o7RPi5/3zP5CqE8/GpjgLxY9LCj+CJfM7i4jkRR9bCQfB7scG0eYRxWXqw4O6KGa
I0iLj7K3UxOQp3QWOQIDAQAB
-----END PUBLIC KEY-----"""


# ------ 辅助函数 ------

def _generate_random_str(length=16):
    """
    生成指定长度的随机字符串（包含大小写字母和数字）
    用于第二层 AES 加密的密钥
    """
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(random.choice(chars) for _ in range(length))


def _pkcs7_pad(text):
    """
    PKCS7 填充
    AES 要求明文长度是 16 的倍数，不足部分进行填充
    即使已经是 16 的倍数，也要补充一整个 block（16 字节）
    """
    block_size = 16
    # 计算需要的填充字节数（1~16）
    padding = block_size - (len(text) % block_size)
    # 填充字节的值等于填充字节的数量
    padding_char = chr(padding)
    return text + padding_char * padding


def _aes_encrypt(text, key):
    """
    AES-CBC 加密
    :param text: 待加密文本（明文）
    :param key: 密钥
    :return: Base64 编码后的密文
    """
    # 先 PKCS7 填充
    padded_text = _pkcs7_pad(text)
    # 创建 AES-CBC 密码器
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, AES_IV.encode("utf-8"))
    # 加密
    encrypted = cipher.encrypt(padded_text.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def _rsa_encrypt(text):
    """
    RSA 加密（网易云特殊版本）
    重要：网易云要求明文先倒序再加密
    :param text: 待加密文本（16位随机字符串）
    :return: 十六进制格式的 256 字符密文
    """
    # 将明文倒序
    reversed_text = text[::-1]
    # 导入 RSA 公钥
    key = RSA.import_key(RSA_PUBLIC_KEY)
    cipher = PKCS1_v1_5.new(key)
    # 加密并转为十六进制字符串
    encrypted = cipher.encrypt(reversed_text.encode("utf-8"))
    return codecs.encode(encrypted, "hex").decode("utf-8")


# ------ 主要接口 ------

def encrypt_request(data):
    """
    加密请求数据，生成 params 和 encSecKey
    :param data: 字典形式的请求数据，如 {"id": 2126, "limit": 30, "offset": 0, "csrf_token": ""}
    :return: (params, encSecKey) 元组
    """
    # 将字典转为 JSON 字符串（不使用空格，与网易云官方一致）
    text = json.dumps(data, separators=(",", ":"))

    # 第一层 AES 加密：使用固定密钥 "0CoJUm6Qyw8W8jud"
    first_encrypted = _aes_encrypt(text, FIRST_AES_KEY)

    # 生成 16 位随机字符串，用作第二层密钥
    random_key = _generate_random_str(16)

    # 第二层 AES 加密：使用随机字符串作为密钥
    params = _aes_encrypt(first_encrypted, random_key)

    # RSA 加密随机字符串（网易云特殊：先倒序再加密）
    enc_sec_key = _rsa_encrypt(random_key)

    return params, enc_sec_key
