#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL编码解码器实现
"""
from urllib.parse import quote, unquote

class UrlEncoders:
    @staticmethod
    def url_encode(data: str) -> str:
        try:
            return quote(data, safe='')
        except Exception as e:
            raise ValueError(f"URL编码失败: {str(e)}")

    @staticmethod
    def url_decode(data: str) -> str:
        try:
            return unquote(data)
        except Exception as e:
            raise ValueError(f"URL解码失败: {str(e)}")
