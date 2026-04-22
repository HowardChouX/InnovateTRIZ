"""
TRIZ提示词构建器
将TRIZ知识注入提示词
"""

from .loader import PromptLoader
from .templates import SINGLE_PRINCIPLE_TEMPLATE, SOLUTION_GENERATION_TEMPLATE


class PromptBuilder:
    """提示词构建器"""

    def __init__(self) -> None:
        self.loader = PromptLoader()

    def build_solution_prompt(
        self,
        problem: str,
        improving_param: str = "",
        worsening_param: str = "",
        principles: list[int] | None = None,
        solution_count: int = 5,
    ) -> str:
        """
        构建解决方案生成提示词（用于AI生成解决方案）

        Args:
            problem: 问题描述
            improving_param: 改善参数
            worsening_param: 恶化参数
            principles: 推荐原理编号列表
            solution_count: 解决方案数量

        Returns:
            用于生成解决方案的提示词
        """
        principles = principles or []

        # 获取原理详细信息
        principle_names = []
        principles_text_lines = []

        for pid in principles:
            name = self.loader.get_principle_name(pid)
            synonyms = self.loader.get_principle_synonyms(pid)
            sub_principles = self.loader.get_principle_sub_principles(pid)

            if name:
                principle_names.append(f"{pid}. {name}")
                principles_text_lines.append(f"**#{pid} {name}**")
                if synonyms:
                    principles_text_lines.append(f"  - Synonyms: {synonyms}")
                for i, sub in enumerate(sub_principles[:3], 1):  # 限制子原则数量
                    principles_text_lines.append(f"  {i}. {sub}")
                principles_text_lines.append("")

        principles_text = (
            "\n".join(principle_names) if principle_names else "未指定具体原理"
        )
        principles_detail = (
            "\n".join(principles_text_lines) if principles_text_lines else ""
        )

        prompt = SOLUTION_GENERATION_TEMPLATE.format(
            problem=problem,
            improving_param=improving_param or "未指定",
            worsening_param=worsening_param or "未指定",
            improving=improving_param or "未指定",
            worsening=worsening_param or "未指定",
            principles_text=principles_text,
            solution_count=solution_count,
        )

        # 追加原理详细信息
        if principles_detail:
            prompt += f"\n\n## 原理详解\n\n{principles_detail}"

        return prompt

    def build_single_principle_solution_prompt(
        self,
        problem: str,
        improving_param: str = "",
        worsening_param: str = "",
        principle_id: int = 1,
    ) -> str:
        """
        构建单个原理分析的提示词（用于遍历注入）

        Args:
            problem: 问题描述
            improving_param: 改善参数
            worsening_param: 恶化参数
            principle_id: 原理编号

        Returns:
            用于生成单个解决方案的提示词
        """
        principle_name = (
            self.loader.get_principle_name(principle_id) or f"原理{principle_id}"
        )
        synonyms = self.loader.get_principle_synonyms(principle_id) or ""
        sub_principles = self.loader.get_principle_sub_principles(principle_id) or []

        # 构建原理详情
        detail_parts = []
        if synonyms:
            detail_parts.append(f"同义词: {synonyms}")
        if sub_principles:
            sub_text = "; ".join(sub_principles[:3])
            detail_parts.append(f"子原理: {sub_text}")
        principle_detail = "\n".join(detail_parts) if detail_parts else "无详细信息"

        prompt = SINGLE_PRINCIPLE_TEMPLATE.format(
            problem=problem,
            improving_param=improving_param or "未指定",
            worsening_param=worsening_param or "未指定",
            principle_id=principle_id,
            principle_name=principle_name,
            principle_detail=principle_detail,
        )

        return prompt
