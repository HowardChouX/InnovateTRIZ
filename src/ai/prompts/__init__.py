"""
TRIZ提示词模块
将XML提示词资源转化为Python内置格式
"""

from .loader import PromptLoader
from .builder import PromptBuilder

__all__ = ["PromptLoader", "PromptBuilder"]
