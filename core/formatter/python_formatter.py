import ast

class PythonFormatter:
    """Python代码格式化工具 (基于ast module)"""
    
    @staticmethod
    def format_python(text: str) -> str:
        """
        格式化Python代码
        
        Args:
            text: 输入的Python代码字符串
        Returns:
            格式化后的代码，如果失败则返回以[错误]开头的描述
        """
        if not text:
            return ""
            
        try:
            # 解析为AST
            tree = ast.parse(text)
            # 反解析为代码 (Python 3.9+ 支持 ast.unparse)
            if hasattr(ast, 'unparse'):
                formatted = ast.unparse(tree)
                return formatted
            else:
                return "[错误] 当前Python版本不支持ast.unparse (需要Python 3.9+)"
        except SyntaxError as e:
            return f"[错误] Python语法错误: {e.msg} (Line {e.lineno})"
        except Exception as e:
            return f"[错误] 格式化发生异常: {str(e)}"
