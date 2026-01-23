#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AES加解密工具，支持多种密钥长度、加密模式和填充方式
"""
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    from Crypto.Util import Counter
    from Crypto.Random import get_random_bytes
    PYCRYPTO_AVAILABLE = True
except ImportError:
    PYCRYPTO_AVAILABLE = False
    # Mocking for type hint or simple path execution avoidance
    AES = None

import base64
import hashlib
import os

class AesEncoders:
    
    @staticmethod
    def _check_available():
        if not PYCRYPTO_AVAILABLE:
            raise ImportError("PyCryptodome library not found. Please install it with: pip install pycryptodome")

    @staticmethod
    def _derive_key(key: str, key_type: str = 'utf-8', key_size: int = 32) -> bytes:
        """
        处理密钥
        """
        if not key:
            raise ValueError("密钥不能为空")
        
        if key_type.lower() == 'hex':
            try:
                # 去除可能的空格
                key = key.replace(' ', '')
                key_bytes = bytes.fromhex(key)
                # 如果长度超过需要的长度，截断；如果不足... 通常AES Key是定长的 (16/24/32)
                # 这里为了兼容性，如果用户输入Hex，尽量保持原样，但Crypto.Cipher需要特定长度
                # 我们假设用户知道自己在做什么，或者我们截取/补零？
                # 按照通常逻辑，Hex Key应该是精确的。但为了稳健，我们可以截取或补0到最近的合法长度(16, 24, 32)
                # 或者直接返回，交给AES.new去报错
                return key_bytes
            except ValueError:
                raise ValueError("密钥不是有效的Hex字符串")
        else:
            # UTF-8: 使用SHA-256派生
            key_hash = hashlib.sha256(key.encode('utf-8')).digest()
            return key_hash[:key_size]
    
    @staticmethod
    def _prepare_iv(iv: str, iv_type: str, mode: str) -> bytes:
        """
        准备初始化向量（IV）
        """
        mode = mode.upper()
        if mode == 'ECB':
            return None
        
        if not iv:
            # 自动生成随机IV
            if PYCRYPTO_AVAILABLE:
                return get_random_bytes(16)
            else:
                 return os.urandom(16)
        
        if iv_type.lower() == 'hex':
            try:
                iv = iv.replace(' ', '')
                iv_bytes = bytes.fromhex(iv)
                if len(iv_bytes) != 16:
                   raise ValueError(f"IV Hex长度必须为16字节 (当前: {len(iv_bytes)})")
                return iv_bytes
            except ValueError as e:
                if "IV Hex" in str(e): raise e
                raise ValueError("IV不是有效的Hex字符串")
        else:
            # UTF-8 Logic
            iv_bytes = iv.encode('utf-8')
            if len(iv_bytes) == 16:
                return iv_bytes
            else:
                # 使用MD5派生到16字节
                return hashlib.md5(iv_bytes).digest()

    @staticmethod
    def _pad_data(data: bytes, padding: str, block_size: int = 16) -> bytes:
        """
        数据填充
        """
        padding = padding.lower()
        if padding == 'pkcs7':
            return pad(data, block_size, style='pkcs7')
        elif padding == 'iso10126':
            return pad(data, block_size, style='iso10126')
        elif padding == 'ansix923':
            return pad(data, block_size, style='x923')
        elif padding == 'zeropadding':
            pad_len = block_size - len(data) % block_size
            if pad_len == 0:
                pad_len = block_size
            return data + b'\x00' * pad_len
        elif padding == 'nopadding':
            if len(data) % block_size != 0:
                raise ValueError("NoPadding模式下数据长度必须是块大小的倍数")
            return data
        else:
            raise ValueError(f"不支持的填充方式: {padding}")

    @staticmethod
    def _unpad_data(data: bytes, padding: str, block_size: int = 16) -> bytes:
        """
        去除填充
        """
        padding = padding.lower()
        if padding == 'pkcs7':
            return unpad(data, block_size, style='pkcs7')
        elif padding == 'iso10126':
            return unpad(data, block_size, style='iso10126')
        elif padding == 'ansix923':
            return unpad(data, block_size, style='x923')
        elif padding == 'zeropadding':
            # 移除末尾的所有\x00
            return data.rstrip(b'\x00')
        elif padding == 'nopadding':
            return data
        else:
            raise ValueError(f"不支持的填充方式: {padding}")

    @staticmethod
    def aes_encrypt(data: str, key: str, mode: str = 'CBC', iv: str = '', padding: str = 'pkcs7', 
                   key_type: str = 'utf-8', iv_type: str = 'utf-8', data_type: str = None) -> str:
        """
        AES加密
        """
        AesEncoders._check_available()
        if not data:
            raise ValueError("数据不能为空")
        
        # 派生密钥
        key_bytes = AesEncoders._derive_key(key, key_type, 32)
        
        # 准备IV
        iv_bytes = AesEncoders._prepare_iv(iv, iv_type, mode)
        
        # 编码数据
        data_bytes = data.encode('utf-8')
        
        mode = mode.upper()
        
        # 创建加密器
        if mode == 'ECB':
            cipher = AES.new(key_bytes, AES.MODE_ECB)
        elif mode == 'CBC':
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv=iv_bytes)
        elif mode == 'CFB':
            cipher = AES.new(key_bytes, AES.MODE_CFB, iv=iv_bytes, segment_size=128)
        elif mode == 'OFB':
            cipher = AES.new(key_bytes, AES.MODE_OFB, iv=iv_bytes)
        elif mode == 'CTR':
            # CTR模式特殊处理
            counter = Counter.new(128, initial_value=int.from_bytes(iv_bytes, byteorder='big'))
            cipher = AES.new(key_bytes, AES.MODE_CTR, counter=counter)
        else:
            raise ValueError(f'不支持的模式: {mode}')
        
        # 填充
        # 流模式（CTR, CFB, OFB）不需要填充，但如果用户选了填充，我们也可以做，或者忽略
        # 这里逻辑是：如果用户选了 NoPadding，就不填；否则按用户选的填
        is_stream = mode in ['CTR', 'CFB', 'OFB']
        if is_stream and padding.lower() == 'nopadding':
            padded = data_bytes
        else:
            padded = AesEncoders._pad_data(data_bytes, padding)
        
        # 加密
        encrypted = cipher.encrypt(padded)
        
        # 返回结果 (携带IV)
        # 仅当IV是自动生成（入参iv为空）且非ECB模式时，才携带IV
        if not iv and iv_bytes and mode != 'ECB':
            result = base64.b64encode(iv_bytes + encrypted).decode('utf-8')
        else:
            result = base64.b64encode(encrypted).decode('utf-8')
        
        return result

    @staticmethod
    def aes_decrypt(data: str, key: str, mode: str = 'CBC', iv: str = '', padding: str = 'pkcs7',
                   key_type: str = 'utf-8', iv_type: str = 'utf-8', data_type: str = None) -> str:
        """
        AES解密
        """
        AesEncoders._check_available()
        if not data:
            raise ValueError("数据不能为空")
        
        key_bytes = AesEncoders._derive_key(key, key_type, 32)
        
        try:
            encrypted_data = base64.b64decode(data)
        except Exception:
             raise ValueError("Base64解码失败，输入不是有效的Base64字符串")

        mode = mode.upper()
        
        # 处理IV
        if mode == 'ECB':
            iv_bytes = None
            encrypted_bytes = encrypted_data
        else:
            if iv:
                iv_bytes = AesEncoders._prepare_iv(iv, iv_type, mode)
                encrypted_bytes = encrypted_data
            else:
                if len(encrypted_data) < 16:
                    raise ValueError("加密数据太短，无法提取IV")
                iv_bytes = encrypted_data[:16]
                encrypted_bytes = encrypted_data[16:]

        # 创建解密器
        if mode == 'ECB':
            cipher = AES.new(key_bytes, AES.MODE_ECB)
        elif mode == 'CBC':
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv=iv_bytes)
        elif mode == 'CFB':
            cipher = AES.new(key_bytes, AES.MODE_CFB, iv=iv_bytes, segment_size=128)
        elif mode == 'OFB':
            cipher = AES.new(key_bytes, AES.MODE_OFB, iv=iv_bytes)
        elif mode == 'CTR':
            counter = Counter.new(128, initial_value=int.from_bytes(iv_bytes, byteorder='big'))
            cipher = AES.new(key_bytes, AES.MODE_CTR, counter=counter)
        else:
            raise ValueError(f'不支持的模式: {mode}')
        
        # 解密
        decrypted = cipher.decrypt(encrypted_bytes)
        
        # 去填充
        is_stream = mode in ['CTR', 'CFB', 'OFB']
        if is_stream and padding.lower() == 'nopadding':
            unpadded = decrypted
        else:
            unpadded = AesEncoders._unpad_data(decrypted, padding)
        
        return unpadded.decode('utf-8')
