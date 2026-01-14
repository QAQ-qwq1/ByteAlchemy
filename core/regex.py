import re
import string

class RegexUtils:
    """正则工具类"""
    
    @staticmethod
    def escape_text(text: str) -> str:
        """转义字符串为正则安全格式"""
        if not text:
            return ""
        return re.escape(text)

class RegexGenerator:
    """正则生成器"""
    
    @staticmethod
    def generate_pattern(include_digits: bool, include_lower: bool, include_upper: bool, 
                        custom_chars: str = "", exclude_chars: str = "") -> str:
        """生成正则表达式模式"""
        allowed_chars = set()
        
        if include_digits:
            allowed_chars.update(string.digits)
        if include_lower:
            allowed_chars.update(string.ascii_lowercase)
        if include_upper:
            allowed_chars.update(string.ascii_uppercase)
            
        if custom_chars:
            allowed_chars.update(custom_chars)
            
        if exclude_chars:
            allowed_chars.difference_update(exclude_chars)
            
        if not allowed_chars:
            return ""
            
        # Optimize ranges
        sorted_chars = sorted(list(allowed_chars))
        optimized_pattern = RegexGenerator._optimize_ranges(sorted_chars)
        
        return f"[{optimized_pattern}]+"

    @staticmethod
    def _optimize_ranges(chars: list) -> str:
        """优化字符列表为正则范围 (e.g. ['a', 'b', 'c'] -> a-c)"""
        if not chars:
            return ""
            
        # 1. 尝试寻找连续区间
        ranges = []
        if not chars:
            return ""
            
        # ASCII values
        ords = [ord(c) for c in chars]
        
        start = ords[0]
        end = ords[0]
        
        for i in range(1, len(ords)):
            if ords[i] == end + 1:
                end = ords[i]
            else:
                ranges.append((start, end))
                start = ords[i]
                end = ords[i]
        ranges.append((start, end))
        
        # 2. 构建字符串
        result = []
        for start, end in ranges:
            count = end - start + 1
            if count >= 3:
                # 3个以上连续才用横杠，例如 0-2 (012)
                # 特殊处理：如果start/end是特殊正则字符需要转义？
                # 在 [] 内大部分不需要，除了 \ ] ^ -
                s_char = chr(start)
                e_char = chr(end)
                result.append(f"{re.escape(s_char)}-{re.escape(e_char)}")
            else:
                for code in range(start, end + 1):
                    result.append(re.escape(chr(code)))
                    
        return "".join(result)
