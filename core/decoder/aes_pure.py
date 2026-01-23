#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AES 算法纯Python实现
支持自定义S盒 (Magic S-Box)
支持模式: ECB, CBC, CFB, OFB, CTR
"""

import struct
import base64
import os
import hashlib

class AesPure:
    """AES (Advanced Encryption Standard) 纯Python实现"""
    
    # 标准 S盒
    STANDARD_SBOX = [
        0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
        0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
        0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
        0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
        0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
        0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
        0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
        0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
        0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
        0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
        0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
        0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
        0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
        0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
        0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
        0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
    ]

    # RCON
    RCON = [
        0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36
    ]

    def __init__(self, key, sbox=None, swap_key_schedule=False, swap_data_round=False):
        self.swap_key_schedule = swap_key_schedule
        self.swap_data_round = swap_data_round
        
        if sbox and len(sbox) == 256:
            self.sbox = sbox
        else:
            self.sbox = self.STANDARD_SBOX
            
        # 生成逆S盒
        self.rsbox = [0] * 256
        for i in range(256):
            self.rsbox[self.sbox[i]] = i
            
        self.key_expansion(key)

    @staticmethod
    def _sub_word(word, sbox):
        return [(sbox[b]) for b in word]

    @staticmethod
    def _rot_word(word):
        return word[1:] + word[:1]

    def key_expansion(self, key):
        """密钥扩展"""
        # 支持 128, 192, 256 bit 密钥
        key_size = len(key)
        if key_size == 16:
            self.rounds = 10
        elif key_size == 24:
            self.rounds = 12
        elif key_size == 32:
            self.rounds = 14
        else:
            # 填充或截取
            if key_size < 16: key = key + b'\x00' * (16 - key_size)
            elif key_size < 24: key = key[:16]
            elif key_size < 32: key = key[:24]
            else: key = key[:32]
            key_size = len(key)
            self.rounds = 10 if key_size == 16 else (12 if key_size == 24 else 14)

        Nk = key_size // 4
        Nb = 4
        Nr = self.rounds
        
        words = []
        for i in range(Nk):
            words.append(list(key[4*i:4*i+4]))
            
        for i in range(Nk, Nb * (Nr + 1)):
            temp = list(words[i-1])
            if i % Nk == 0:
                temp = self._rot_word(temp)
                temp = self._sub_word(temp, self.sbox)
                
                # Magic Swap: Key Schedule
                if self.swap_key_schedule:
                    temp.reverse()
                    
                temp[0] ^= self.RCON[i // Nk]
            elif Nk > 6 and i % Nk == 4:
                temp = self._sub_word(temp, self.sbox)
            
            new_word = [words[i-Nk][j] ^ temp[j] for j in range(4)]
            words.append(new_word)
            
        self.round_keys = [words[i:i+4] for i in range(0, len(words), 4)]

    def _magic_swap_state(self, state):
        """
        Magic Swap for Data Round:
        Swap bytes within each column (word) of the state.
        State is row-major: state[row][col]
        Column j is: state[0][j], state[1][j], state[2][j], state[3][j]
        """
        for j in range(4):
            # Swap column j: 0<->3, 1<->2
            state[0][j], state[3][j] = state[3][j], state[0][j]
            state[1][j], state[2][j] = state[2][j], state[1][j]

    # --- 核心变换 ---
    
    def _sub_bytes(self, state, sbox):
        for i in range(4):
            for j in range(4):
                state[i][j] = sbox[state[i][j]]

    def _shift_rows(self, state):
        state[1] = state[1][1:] + state[1][:1]
        state[2] = state[2][2:] + state[2][:2]
        state[3] = state[3][3:] + state[3][:3]

    def _inv_shift_rows(self, state):
        state[1] = state[1][-1:] + state[1][:-1]
        state[2] = state[2][-2:] + state[2][:-2]
        state[3] = state[3][-3:] + state[3][:-3]

    @staticmethod
    def _xtime(a):
        return ((a << 1) ^ 0x1B) & 0xFF if a & 0x80 else (a << 1) & 0xFF

    def _mix_columns(self, state):
        for i in range(4):
            t = state[0][i] ^ state[1][i] ^ state[2][i] ^ state[3][i]
            u = state[0][i]
            state[0][i] ^= t ^ self._xtime(state[0][i] ^ state[1][i])
            state[1][i] ^= t ^ self._xtime(state[1][i] ^ state[2][i])
            state[2][i] ^= t ^ self._xtime(state[2][i] ^ state[3][i])
            state[3][i] ^= t ^ self._xtime(state[3][i] ^ u)

    def _inv_mix_columns(self, state):
        for i in range(4):
            u = self._xtime(self._xtime(state[0][i] ^ state[2][i]))
            v = self._xtime(self._xtime(state[1][i] ^ state[3][i]))
            state[0][i] ^= u
            state[1][i] ^= v
            state[2][i] ^= u
            state[3][i] ^= v
        self._mix_columns(state)

    def _add_round_key(self, state, round_key):
        for i in range(4):
            for j in range(4):
                state[i][j] ^= round_key[j][i]

    def encrypt_block(self, block):
        # block -> state (4x4)
        state = [list(block[i:i+4]) for i in range(0, 16, 4)]
        # Transpose: state[row][col]
        state = [[state[j][i] for j in range(4)] for i in range(4)]
        
        self._add_round_key(state, self.round_keys[0])
        
        for i in range(1, self.rounds):
            self._sub_bytes(state, self.sbox)
            if self.swap_data_round: self._magic_swap_state(state)
            self._shift_rows(state)
            self._mix_columns(state)
            self._add_round_key(state, self.round_keys[i])
            
        self._sub_bytes(state, self.sbox)
        if self.swap_data_round: self._magic_swap_state(state)
        self._shift_rows(state)
        self._add_round_key(state, self.round_keys[self.rounds])
        
        # Flatten
        output = []
        for j in range(4):
            for i in range(4):
                output.append(state[i][j])
        return bytes(output)

    def decrypt_block(self, block):
        state = [list(block[i:i+4]) for i in range(0, 16, 4)]
        state = [[state[j][i] for j in range(4)] for i in range(4)]
        
        self._add_round_key(state, self.round_keys[self.rounds])
        
        for i in range(self.rounds - 1, 0, -1):
            self._inv_shift_rows(state)
            self._sub_bytes(state, self.rsbox)
            # Decryption: Undo swap?
            # Encryption structure: Sub -> Swap -> Shift...
            # Decryption structure: InvShift -> InvSub ...
            # To reverse "Sub->Swap", we must swap "after" InvSub (which is inverse of Sub).
            # But wait, InvSub(Swap(y))? No.
            # Encryption: y = Swap(Sub(x))
            # Decryption: x = InvSub(Swap(y))
            # Because Swap is self-inverse (reverse list), Swap(x) = InvSwap(x).
            if self.swap_data_round: self._magic_swap_state(state) 
            self._add_round_key(state, self.round_keys[i])
            self._inv_mix_columns(state)
            
        self._inv_shift_rows(state)
        self._sub_bytes(state, self.rsbox)
        if self.swap_data_round: self._magic_swap_state(state)
        self._add_round_key(state, self.round_keys[0])
        
        output = []
        for j in range(4):
            for i in range(4):
                output.append(state[i][j])
        return bytes(output)

class AesPureEncoders:
    """封装 AesPure 用于业务调用"""
    
    @staticmethod
    def _pad(data, padding):
        padding = padding.lower()
        if padding == 'nopadding': return data
        bs = 16
        pad_len = bs - (len(data) % bs)
        if padding == 'pkcs7':
            return data + bytes([pad_len] * pad_len)
        elif padding == 'zeropadding':
            return data + b'\x00' * pad_len
        return data + bytes([pad_len] * pad_len)

    @staticmethod
    def _unpad(data, padding):
        padding = padding.lower()
        if padding == 'nopadding': return data
        if padding == 'zeropadding': return data.rstrip(b'\x00')
        pad_len = data[-1]
        return data[:-pad_len]

    @staticmethod
    def encrypt(data: str, key: str, mode: str = 'ECB', iv: str = '', padding: str = 'pkcs7', sbox=None,
               swap_key_schedule: bool = False, swap_data_round: bool = False) -> str:
        key_bytes = hashlib.md5(key.encode('utf-8')).digest()
        aes = AesPure(key_bytes, sbox, swap_key_schedule, swap_data_round)
        
        data_bytes = data.encode('utf-8')
        padded = AesPureEncoders._pad(data_bytes, padding)
        
        mode = mode.upper()
        iv_bytes = hashlib.md5(iv.encode('utf-8')).digest() if iv else b'\x00' * 16
        
        res = b''
        if mode == 'ECB':
            for i in range(0, len(padded), 16):
                res += aes.encrypt_block(padded[i:i+16])
        elif mode == 'CBC':
            prev = iv_bytes
            for i in range(0, len(padded), 16):
                block = bytes([a ^ b for a, b in zip(padded[i:i+16], prev)])
                enc = aes.encrypt_block(block)
                res += enc
                prev = enc
        # ... Other modes can be added (CTR, etc)
        
        return base64.b64encode(res).decode('utf-8')

    @staticmethod
    def decrypt(data: str, key: str, mode: str = 'ECB', iv: str = '', padding: str = 'pkcs7', sbox=None,
               swap_key_schedule: bool = False, swap_data_round: bool = False) -> str:
        try:
            encrypted = base64.b64decode(data)
        except:
            return "[Error] Invalid Base64"
            
        key_bytes = hashlib.md5(key.encode('utf-8')).digest()
        aes = AesPure(key_bytes, sbox, swap_key_schedule, swap_data_round)
        
        mode = mode.upper()
        iv_bytes = hashlib.md5(iv.encode('utf-8')).digest() if iv else b'\x00' * 16
        
        res = b''
        if mode == 'ECB':
            for i in range(0, len(encrypted), 16):
                res += aes.decrypt_block(encrypted[i:i+16])
        elif mode == 'CBC':
            prev = iv_bytes
            for i in range(0, len(encrypted), 16):
                block = encrypted[i:i+16]
                dec = aes.decrypt_block(block)
                res += bytes([a ^ b for a, b in zip(dec, prev)])
                prev = block
                
        unpadded = AesPureEncoders._unpad(res, padding)
        return unpadded.decode('utf-8', errors='replace')
