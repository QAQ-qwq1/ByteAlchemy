import re

class CssFormatter:
    """CSS格式化工具 (Simple Regex Based)"""
    
    @staticmethod
    def format_css(text: str, indent: int = 4) -> str:
        """
        简单的CSS格式化
        """
        if not text:
            return ""
        try:
            # Minify first to normalize
            s = re.sub(r'\s+', ' ', text).strip()
            
            # { -> {\n
            s = s.replace('{', ' {\n')
            # ; -> ;\n
            s = s.replace(';', ';\n')
            # } -> \n}\n
            s = s.replace('}', '\n}\n')
            
            # Clean up double newlines
            lines = s.split('\n')
            formatted = ""
            depth = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if '}' in line:
                    depth = max(0, depth - 1)
                
                formatted += (" " * (depth * indent)) + line + "\n"
                
                if '{' in line:
                    depth += 1
            
            return formatted.strip()
        except Exception as e:
            return f"[错误] CSS格式化失败: {str(e)}"
