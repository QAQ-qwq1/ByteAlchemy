#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unicode转义编码解码器实现
"""
import re

class UnicodeEncoders:
    @staticmethod
    def unicode_encode(data: str) -> str:
        try:
            result = []
            for char in data:
                code = ord(char)
                if code <= 0xFFFF:
                    result.append(f'\\u{code:04x}')
                else:
                    result.append(f'\\U{code:08x}')
            return ''.join(result)
        except Exception as e:
            raise ValueError(f"Unicode转义编码失败: {str(e)}")

    @staticmethod
    def unicode_decode(data: str) -> str:
        try:
            def replace_unicode(match):
                code = match.group(1)
                if len(code) == 4:
                    return chr(int(code, 16))
                elif len(code) == 8:
                    return chr(int(code, 16))
                return match.group(0)
            result = re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode, data)
            result = re.sub(r'\\U([0-9a-fA-F]{8})', replace_unicode, result)
            return result
        except Exception as e:
            raise ValueError(f"Unicode转义解码失败: {str(e)}")
