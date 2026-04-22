"""
TRIZ提示词模块
将XML提示词资源转化为Python内置格式
"""

from .builder import PromptBuilder
from .loader import PromptLoader

__all__ = ["PromptLoader", "PromptBuilder"]
