from abc import ABC, abstractmethod
from typing import Any, Dict

class IMainLogic(ABC):
    """主逻辑接口"""
    
    @abstractmethod
    def execute_operation(self, op_name: str, data: str, params: Dict[str, Any]) -> str:
        """执行单个操作"""
        pass
        
    @abstractmethod
    def run_process_chain(self, chain: list, input_text: str, params_provider_func) -> str:
        """执行操作链"""
        pass
    
    @abstractmethod
    def convert_format(self, text: str, from_fmt: str, to_fmt: str) -> str:
        """转换文本格式"""
        pass
