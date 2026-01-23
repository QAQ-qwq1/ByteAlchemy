#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base家族编码解码器实现
支持Base16, Base32, Base64, Base85的编码和解码
"""

import base64

class BaseEncoders:
    """Base家族编码解码器"""
    @staticmethod
    def base16_encode(data: str) -> str:
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            return base64.b16encode(data).decode('ascii')
        except Exception as e:
            raise ValueError(f"Base16编码失败: {str(e)}")

    @staticmethod
    def base16_decode(data: str) -> str:
        try:
            data = data.strip().replace(' ', '').replace('\n', '').replace('\r', '')
            decoded = base64.b16decode(data.upper())
            return decoded.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Base16解码失败: {str(e)}")

    @staticmethod
    def base32_encode(data: str) -> str:
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            return base64.b32encode(data).decode('ascii')
        except Exception as e:
            raise ValueError(f"Base32编码失败: {str(e)}")

    @staticmethod
    def base32_decode(data: str) -> str:
        try:
            data = data.strip().replace(' ', '').replace('\n', '').replace('\r', '').replace('=', '')
            padding = len(data) % 8
            if padding != 0:
                data += '=' * (8 - padding)
            decoded = base64.b32decode(data)
            return decoded.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Base32解码失败: {str(e)}")

    @staticmethod
    def base64_encode(data: str, url_safe: bool = False) -> str:
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            if url_safe:
                return base64.urlsafe_b64encode(data).decode('ascii')
            else:
                return base64.b64encode(data).decode('ascii')
        except Exception as e:
            raise ValueError(f"Base64编码失败: {str(e)}")

    @staticmethod
    def base64_decode(data: str, url_safe: bool = False) -> str:
        try:
            data = data.strip().replace(' ', '').replace('\n', '').replace('\r', '')
            if url_safe:
                decoded = base64.urlsafe_b64decode(data)
            else:
                padding = len(data) % 4
                if padding != 0:
                    data += '=' * (4 - padding)
                decoded = base64.b64decode(data)
            return decoded.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Base64解码失败: {str(e)}")

    @staticmethod
    def base85_encode(data: str, variant: str = 'ascii85') -> str:
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            if variant == 'ascii85':
                return base64.a85encode(data).decode('ascii')
            elif variant == 'z85':
                return BaseEncoders._z85_encode(data)
            else:
                raise ValueError(f"不支持的Base85变体: {variant}")
        except Exception as e:
            raise ValueError(f"Base85编码失败: {str(e)}")

    @staticmethod
    def base85_decode(data: str, variant: str = 'ascii85') -> str:
        try:
            data = data.strip().replace(' ', '').replace('\n', '').replace('\r', '')
            if variant == 'ascii85':
                if data.startswith('<~') and data.endswith('~>'):
                    data = data[2:-2]
                decoded = base64.a85decode(data)
            elif variant == 'z85':
                decoded = BaseEncoders._z85_decode(data)
            else:
                raise ValueError(f"不支持的Base85变体: {variant}")
            return decoded.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Base85解码失败: {str(e)}")

    @staticmethod
    def _z85_encode(data: bytes) -> str:
        alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-:+=^!/*?&<>()[]{}@%$#"
        original_len = len(data)
        
        # 添加填充到4的倍数
        if len(data) % 4 != 0:
            padding = 4 - (len(data) % 4)
            data += b'\x00' * padding
        
        result = []
        for i in range(0, len(data), 4):
            chunk = data[i:i+4]
            value = int.from_bytes(chunk, 'big')
            temp = []
            for _ in range(5):
                temp.append(alphabet[value % 85])
                value //= 85
            result.extend(reversed(temp))
        
        # 在结果末尾编码原始长度（使用特殊标记）
        encoded = ''.join(result)
        # 添加长度信息作为后缀（format: |length|）
        return f"{encoded}|{original_len}|"

    @staticmethod
    def _z85_decode(data: str) -> bytes:
        alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-:+=^!/*?&<>()[]{}@%$#"
        table = {c: i for i, c in enumerate(alphabet)}
        
        # 提取原始长度信息
        if '|' in data:
            parts = data.rsplit('|', 2)
            if len(parts) == 3:
                data = parts[0]
                try:
                    original_len = int(parts[1])
                except ValueError:
                    original_len = None
            else:
                original_len = None
        else:
            original_len = None
        
        if len(data) % 5 != 0:
            raise ValueError("Z85数据长度必须是5的倍数")
        
        result = []
        for i in range(0, len(data), 5):
            chunk = data[i:i+5]
            value = 0
            for c in chunk:
                if c not in table:
                    raise ValueError(f"无效的Z85字符: {c}")
                value = value * 85 + table[c]
            temp = value.to_bytes(4, 'big')
            result.extend(temp)
        
        decoded = bytes(result)
        
        # 如果有原始长度信息，截断到正确长度
        if original_len is not None:
            decoded = decoded[:original_len]
        
        return decoded
