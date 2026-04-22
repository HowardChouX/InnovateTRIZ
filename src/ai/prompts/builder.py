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

    def build_contradiction_prompt(
        self,
        problem: str,
        improving_param: str = "",
        worsening_param: str = "",
        principles: list[int] | None = None,
    ) -> str:
        """
        构建矛盾求解提示词

        Args:
            problem: 问题描述
            improving_param: 改善参数
            worsening_param: 恶化参数
            principles: 推荐原理编号列表

        Returns:
            完整的提示词字符串
        """
        principles = principles or []

        # 获取原理详细信息
        principles_text = self.loader.build_principles_text(principles)

        # 构建原理名称列表
        principle_names = []
        for pid in principles:
            name = self.loader.get_principle_name(pid)
            if name:
                principle_names.append(f"#{pid} {name}")

        principles_name_text = (
            ", ".join(principle_names) if principle_names else "待确定"
        )

        # 获取矛盾求解模板
        solver_template = self.loader.get_contradiction_solver_template()

        prompt = f"""{solver_template}

## Current Problem Analysis

**Problem Description:**
{problem}

**Identified Contradiction:**
- Improving parameter: {improving_param or 'Not specified'}
- Worsening parameter: {worsening_param or 'Not specified'}

**Recommended Inventive Principles ({len(principles)}):**
{principles_name_text}

## Detailed Principle Information

{principles_text}

Please analyze the problem and provide innovative solutions using the recommended TRIZ principles.
"""
        return prompt

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

    def build_parameter_detection_prompt(self, problem: str) -> str:
        """
        构建参数检测提示词

        Args:
            problem: 问题描述

        Returns:
            用于检测参数的提示词
        """
        return f"""作为TRIZ专家，请分析以下技术问题并识别核心技术矛盾：

问题：{problem}

请完成以下任务：
1. 识别需要改善的技术参数（从39个工程参数中选择）
2. 识别可能恶化的技术参数（从39个工程参数中选择）
3. 用中文返回，格式为JSON：
{{
    "improving": "改善参数名称",
    "worsening": "恶化参数名称",
    "explanation": "矛盾解释"
}}

只返回JSON，不要其他文字。

## 39个工程参数参考
1. 运动物体的重量
2. 静止物体的重量
3. 运动物体的长度
4. 静止物体的长度
5. 运动物体的面积
6. 静止物体的面积
7. 运动物体的体积
8. 静止物体的体积
9. 速度
10. 力
11. 张力/压力
12. 形状
13. 稳定性
14. 强度
15. 运动物体的耐久性
16. 静止物体的耐久性
17. 温度
18. 亮度
19. 功率
20. 能源的浪费
21. 物质的浪费
22. 信息的流失
23. 时间的浪费
24. 物质数量
25. 信息数量
26. 可靠性
27. 测量的准度
28. 制造的准度
29. 复杂性
30. 制造性
31. 使用的便利性
32. 修复性
33. 适应性
34. 可变性
35. 自动化程度
36. 产能/生产力
37. 装置复杂性
38. 成本
39. 测量难度
"""

    def get_contradiction_format_guide(self) -> str:
        """获取矛盾格式指南"""
        return """
## 工程矛盾格式 (Engineering Contradiction)
**IF** [改善条件], **THEN** [期望结果], **BUT** [恶化结果]

示例: "如果发动机更强劲，那么汽车可以更快，但油耗会增加"

## 物理矛盾格式 (Physical Contradiction)
[参数] 必须是 [值1] **TO** [好处], **AND** [参数] 必须是 [值2] **TO** [好处]

示例: "船必须宽 **TO** 防止倾覆, **AND** 船必须窄 **TO** 快速航行"
"""

    def build_function_analysis_prompt(self, system: str = "") -> str:
        """
        构建功能分析提示词

        Args:
            system: 技术系统名称（可选）

        Returns:
            功能分析提示词
        """
        template = self.loader.get_function_analysis_template()

        if system:
            return f"""{template}

## Current System to Analyze
**System:** {system}

Please guide the user through Function Analysis of this system.
"""
        return template

    def build_subfield_analysis_prompt(self, problem: str = "") -> str:
        """
        构建物质-场分析提示词

        Args:
            problem: 问题描述（可选）

        Returns:
            物质-场分析提示词
        """
        template = self.loader.get_subfield_analysis_template()

        if problem:
            return f"""{template}

## Current Problem
**Problem:** {problem}

Please guide the user through Substance-Field Analysis of this problem.
1. Identify the substances (S1, S2) and field (F)
2. Create the substance-field model
3. Select appropriate standard solution
4. Apply the solution
"""
        return template

    def build_standard_solutions_prompt(
        self, problem: str = "", solution_class: int = 0
    ) -> str:
        """
        构建76标准解提示词

        Args:
            problem: 问题描述
            solution_class: 优先使用的类别 (1-5)

        Returns:
            标准解应用提示词
        """
        loader = self.loader
        subfield_template = loader.get_subfield_analysis_template()

        # 获取指定类别的标准解
        if solution_class > 0:
            solutions = loader.get_standard_solutions_by_class(solution_class)
            solutions_text = "\n".join(
                [
                    f"- Class {k[0]}.{k[1]}.{k[2]}: {v['name']}"
                    for k, v in solutions.items()
                ]
            )
        else:
            solutions_text = "All 76 Standard Solutions available"

        prompt = f"""{subfield_template}

## Available Standard Solutions
{solutions_text}

## Problem to Solve
**Problem:** {problem or 'Please describe your problem.'}

Please analyze the problem and suggest appropriate standard solutions.
"""
        return prompt
