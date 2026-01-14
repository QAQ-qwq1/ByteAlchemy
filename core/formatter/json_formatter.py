import json

class JsonFormatter:
    """json格式化工具"""
    
    @staticmethod
    def format_json(text: str, indent: int = 4, sort_keys: bool = False, compact: bool = False) -> str:
        """
        格式化JSON字符串
        
        Args:
            text: 输入的JSON字符串
            indent: 缩进空格数
            sort_keys: 是否按键排序
            compact: 是否压缩输出 (去除空白)
        Returns:
            格式化后的JSON字符串，如果失败则返回以[错误]开头的描述
        """
        if not text:
            return ""
            
        try:
            # 尝试解析JSON
            parsed = json.loads(text)
            
            # 重新序列化为格式化的字符串
            if compact:
                formatted = json.dumps(parsed, separators=(',', ':'), sort_keys=sort_keys, ensure_ascii=False)
            else:
                formatted = json.dumps(parsed, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
                
            return formatted
        except json.JSONDecodeError as e:
            return f"[错误] JSON解析失败: {str(e)}"
        except Exception as e:
            return f"[错误] 格式化发生异常: {str(e)}"
