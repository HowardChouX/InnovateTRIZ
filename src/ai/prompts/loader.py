"""
TRIZ提示词加载器
从Python代码加载提示词模板
"""

from typing import Optional, List, Dict
from .templates import (
    CONTRADICTION_SOLVER_TEMPLATE,
    ENGINEERING_PARAMETERS_39,
    ALTSHULLER_SOLVING_STEPS,
    FUNCTION_ANALYSIS_TEMPLATE,
    STANDARD_SOLUTIONS_76,
    SUFIELD_ANALYSIS_TEMPLATE
)
from ...config.constants import INVENTIVE_PRINCIPLES as CN_INVENTIVE_PRINCIPLES


class PromptLoader:
    """提示词加载器"""

    @staticmethod
    def get_principle(principle_number: int) -> Optional[Dict]:
        """
        获取指定编号的发明原理详情

        Args:
            principle_number: 原理编号 (1-40)

        Returns:
            包含name, synonyms, sub_principles的字典，或None
        """
        name = CN_INVENTIVE_PRINCIPLES.get(principle_number)
        if name:
            return {"name": name, "synonyms": "", "sub_principles": []}
        return None

    @staticmethod
    def get_all_principles() -> Dict[int, Dict]:
        """获取所有40个发明原理"""
        return {
            pid: {"name": name, "synonyms": "", "sub_principles": []}
            for pid, name in CN_INVENTIVE_PRINCIPLES.items()
        }

    @staticmethod
    def get_principle_name(principle_number: int) -> str:
        """获取原理名称"""
        return CN_INVENTIVE_PRINCIPLES.get(principle_number, "")

    @staticmethod
    def get_principle_synonyms(principle_number: int) -> str:
        """获取原理同义词"""
        return ""

    @staticmethod
    def get_principle_sub_principles(principle_number: int) -> List[str]:
        """获取原理子原则列表"""
        return []

    @staticmethod
    def get_contradiction_solver_template() -> str:
        """获取矛盾求解器模板"""
        return CONTRADICTION_SOLVER_TEMPLATE

    @staticmethod
    def get_39_parameters() -> Dict[int, str]:
        """获取39个标准工程参数"""
        return ENGINEERING_PARAMETERS_39.copy()

    @staticmethod
    def get_parameter_name(parameter_number: int) -> str:
        """获取指定编号的工程参数名称"""
        return ENGINEERING_PARAMETERS_39.get(parameter_number, "")

    @staticmethod
    def get_39_parameters_text() -> str:
        """获取39参数的可读文本"""
        lines = ["## 39 Standard Altshuller Parameters"]
        for num, name in sorted(ENGINEERING_PARAMETERS_39.items()):
            lines.append(f"{num:2d}. {name}")
        return "\n".join(lines)

    @staticmethod
    def get_altshuller_solving_steps() -> str:
        """获取7步求解流程"""
        return ALTSHULLER_SOLVING_STEPS

    @staticmethod
    def get_function_analysis_template() -> str:
        """获取功能分析模板"""
        return FUNCTION_ANALYSIS_TEMPLATE

    @staticmethod
    def get_standard_solution(class_num: int, group: int, standard: int) -> Optional[Dict]:
        """获取指定的标准解"""
        return STANDARD_SOLUTIONS_76.get((class_num, group, standard))

    @staticmethod
    def get_all_standard_solutions() -> Dict:
        """获取所有标准解"""
        return STANDARD_SOLUTIONS_76.copy()

    @staticmethod
    def get_standard_solutions_by_class(class_num: int) -> List[Dict]:
        """获取指定类别的所有标准解"""
        return {
            k: v for k, v in STANDARD_SOLUTIONS_76.items()
            if k[0] == class_num
        }

    @staticmethod
    def get_subfield_analysis_template() -> str:
        """获取物质-场分析模板"""
        return SUFIELD_ANALYSIS_TEMPLATE

    @staticmethod
    def build_principle_detail(principle_number: int) -> str:
        """
        构建单个原理的详细描述

        Args:
            principle_number: 原理编号

        Returns:
            格式化的原理详情字符串
        """
        name = CN_INVENTIVE_PRINCIPLES.get(principle_number)
        if not name:
            return ""

        return f"**#{principle_number} {name}**"

    @staticmethod
    def build_principles_text(principle_numbers: List[int]) -> str:
        """
        构建多个原理的详细信息

        Args:
            principle_numbers: 原理编号列表

        Returns:
            多个原理的格式化字符串
        """
        if not principle_numbers:
            return "No specific principles identified yet."

        lines = []
        for pid in principle_numbers:
            lines.append(PromptLoader.build_principle_detail(pid))
            lines.append("")

        return "\n".join(lines)
