import re

class SqlFormatter:
    """SQL格式化工具 (Simple Regex Based)"""
    
    @staticmethod
    def format_sql(text: str, indent: int = 4) -> str:
        """
        简单的SQL格式化
        """
        if not text:
            return ""
        try:
            # Keywords to put on new line
            keywords = [
                "SELECT", "FROM", "WHERE", "AND", "OR", "GROUP BY", "ORDER BY", 
                "HAVING", "LIMIT", "INSERT INTO", "VALUES", "UPDATE", "SET", 
                "DELETE FROM", "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", 
                "OUTER JOIN", "UNION", "CREATE TABLE", "DROP TABLE", "ALTER TABLE"
            ]
            
            formatted = text
            # Normalize whitespace
            formatted = " ".join(formatted.split())
            
            # Add newlines before keywords
            for kw in keywords:
                # Case insensitive replace? keywords usually UPCASE in format
                # We assume input might be mixed.
                # Regex replace with ignore case
                pattern = re.compile(r'\b(' + kw.replace(' ', r'\s+') + r')\b', re.IGNORECASE)
                formatted = pattern.sub(r'\n\1', formatted)
            
            # Indent?
            # Simple approach: split by newline, trim
            lines = formatted.split('\n')
            final_res = ""
            for line in lines:
                line = line.strip()
                if not line: 
                    continue
                final_res += line + "\n"
                
            return final_res.strip()
        except Exception as e:
            return f"[错误] SQL格式化失败: {str(e)}"
