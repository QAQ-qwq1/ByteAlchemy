import re

class HtmlFormatter:
    """HTML格式化工具 (Simple Regex Based)"""
    
    @staticmethod
    def format_html(text: str, indent: int = 4) -> str:
        """
        简单的HTML格式化，不依赖bs4
        """
        if not text:
            return ""
        
        # Simple indentation logic
        # 1. Split tags
        # very basic approach
        try:
            # Remove existing whitespace between tags?
            # Regex to match tags
            # <tag ...> or </tag> or <tag ... />
            
            # A very naive HTML prettifier
            # In a real app we'd want bs4. Without it, we do best effort.
            
            formatted = ""
            pad = 0
            
            # Normalize structure: put tags on newlines
            clean_text = re.sub(r'>\s*<', '>\n<', text)
            
            lines = clean_text.split('\n')
            
            # List of tags that don't increase depth (void elements)
            void_elements = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr']
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check closing tag first
                if re.match(r'^</\w+', line):
                    pad = max(0, pad - 1)
                
                formatted += (" " * (pad * indent)) + line + "\n"
                
                # Check opening tag (and not self-closing, and not void)
                # <div ...> but not </div> and not <div ... />
                if re.match(r'^<[\w]+', line) and not re.match(r'^</', line) and not line.endswith('/>'):
                    tag_name = re.match(r'^<([\w-]+)', line).group(1).lower()
                    if tag_name not in void_elements:
                         pad += 1
            
            return formatted.strip()
        except Exception as e:
            return f"[错误] HTML格式化失败: {str(e)}"
