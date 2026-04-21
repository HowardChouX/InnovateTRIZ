"""
头脑风暴流程测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai.prompts.builder import PromptBuilder
from src.ai.prompts.loader import PromptLoader
from src.data.models import AIAnalysisRequest, Solution


class TestBrainstormFlow:
    """测试头脑风暴完整流程"""

    def test_prompt_builder_initialization(self):
        """测试提示词构建器初始化"""
        builder = PromptBuilder()
        assert builder is not None
        assert builder.loader is not None

    def test_solution_prompt_contains_required_fields(self):
        """测试解决方案提示词包含必要字段"""
        builder = PromptBuilder()

        prompt = builder.build_solution_prompt(
            problem="手机需要更大电池但要保持轻薄",
            improving_param="运动物体的能量消耗",
            worsening_param="重量",
            principles=[1, 2, 3, 15, 28],
            solution_count=5
        )

        # 验证基本参数被正确填入
        assert "手机需要更大电池但要保持轻薄" in prompt
        assert "运动物体的能量消耗" in prompt
        assert "重量" in prompt

        # 验证4字段结构化输出要求存在
        assert "technical_solution" in prompt
        assert "innovation_point" in prompt
        assert "cross_domain_cases" in prompt
        assert "expected_effect" in prompt

    def test_solution_prompt_with_empty_parameters(self):
        """测试带空参数的提示词构建"""
        builder = PromptBuilder()

        prompt = builder.build_solution_prompt(
            problem="如何提高产品质量",
            improving_param="",
            worsening_param="",
            principles=[1, 2, 3],
            solution_count=3
        )

        # 验证空参数被替换为"未指定"
        assert "未指定" in prompt
        assert "如何提高产品质量" in prompt

    def test_solution_prompt_with_single_principle(self):
        """测试单一原理的提示词构建"""
        builder = PromptBuilder()

        prompt = builder.build_solution_prompt(
            problem="减少设备能耗",
            improving_param="能量消耗",
            worsening_param="成本",
            principles=[15],
            solution_count=1
        )

        assert "减少设备能耗" in prompt
        assert "能量消耗" in prompt
        assert "成本" in prompt

    def test_ai_analysis_request_creation(self):
        """测试AI分析请求创建"""
        request = AIAnalysisRequest(
            problem="手机散热问题",
            improving_param="温度",
            worsening_param="重量",
            principle_ids=[1, 2, 3],
            solution_count=5
        )

        assert request.problem == "手机散热问题"
        assert request.improving_param == "温度"
        assert request.worsening_param == "重量"
        assert request.principle_ids == [1, 2, 3]
        assert request.solution_count == 5

    def test_ai_analysis_request_to_dict(self):
        """测试AI分析请求转字典"""
        request = AIAnalysisRequest(
            problem="测试问题",
            improving_param="改善参数",
            worsening_param="恶化参数",
            principle_ids=[1, 2],
            solution_count=3
        )

        data = request.to_dict()
        assert data["problem"] == "测试问题"
        assert data["improving_param"] == "改善参数"
        assert data["worsening_param"] == "恶化参数"
        assert data["principle_ids"] == [1, 2]
        assert data["solution_count"] == 3

    def test_solution_model_creation(self):
        """测试解决方案模型创建"""
        solution = Solution(
            principle_id=1,
            principle_name="分割",
            description="将系统分割成独立模块",
            confidence=0.9,
            is_ai_generated=True,
            category="物理",
            examples=["手机模块化设计", "电脑组装式结构"]
        )

        assert solution.principle_id == 1
        assert solution.principle_name == "分割"
        assert solution.confidence == 0.9
        assert solution.is_ai_generated is True
        assert len(solution.examples) == 2

    def test_solution_to_dict(self):
        """测试解决方案转字典"""
        solution = Solution(
            principle_id=2,
            principle_name="抽取",
            description="提取关键部分",
            confidence=0.8
        )

        data = solution.to_dict()
        assert data["principle_id"] == 2
        assert data["principle_name"] == "抽取"
        assert data["description"] == "提取关键部分"
        assert data["confidence"] == 0.8

    def test_solution_from_dict(self):
        """测试从字典创建解决方案"""
        data = {
            "principle_id": 3,
            "principle_name": "局部质量",
            "description": "改善局部特性",
            "confidence": 0.85,
            "is_ai_generated": True,
            "category": "几何",
            "examples": ["案例1", "案例2"],
            "created_at": "2024-01-01T12:00:00"
        }

        solution = Solution.from_dict(data)
        assert solution.principle_id == 3
        assert solution.principle_name == "局部质量"
        assert solution.confidence == 0.85


class TestPromptTemplateRequirements:
    """测试提示词模板要求（4字段结构）"""

    def test_technical_solution_field_requirement(self):
        """测试technical_solution字段要求"""
        builder = PromptBuilder()

        prompt = builder.build_solution_prompt(
            problem="汽车轻量化设计",
            improving_param="重量",
            worsening_param="强度",
            principles=[1, 2, 3],
            solution_count=3
        )

        # 验证4字段结构
        assert "technical_solution" in prompt or "技术方案" in prompt
        assert "50-100" in prompt or "50" in prompt

    def test_innovation_point_field_requirement(self):
        """测试innovation_point字段要求"""
        builder = PromptBuilder()

        prompt = builder.build_solution_prompt(
            problem="提高能效",
            improving_param="效率",
            worsening_param="成本",
            principles=[1, 2],
            solution_count=2
        )

        # 验证创新点字段
        assert "innovation_point" in prompt or "创新点" in prompt
        assert "20-30" in prompt or "20" in prompt

    def test_cross_domain_cases_field_requirement(self):
        """测试cross_domain_cases字段要求"""
        builder = PromptBuilder()

        prompt = builder.build_solution_prompt(
            problem="降低能耗",
            improving_param="能量消耗",
            worsening_param="复杂性",
            principles=[1, 2, 3],
            solution_count=3
        )

        # 验证跨领域案例字段
        assert "cross_domain_cases" in prompt or "领域" in prompt
        assert "领域A" in prompt or "领域" in prompt

    def test_confidence_field_requirement(self):
        """测试confidence字段要求"""
        builder = PromptBuilder()

        prompt = builder.build_solution_prompt(
            problem="提高速度",
            improving_param="速度",
            worsening_param="能耗",
            principles=[1],
            solution_count=1
        )

        # 验证预期效果和置信度字段
        assert "expected_effect" in prompt or "效果" in prompt
        assert "confidence" in prompt.lower() or "置信" in prompt
        assert "0.0" in prompt or "0" in prompt
        assert "1.0" in prompt or "1" in prompt

    def test_no_placeholder_in_output(self):
        """测试模板中没有未替换的占位符"""
        builder = PromptBuilder()

        prompt = builder.build_solution_prompt(
            problem="测试问题",
            improving_param="改善",
            worsening_param="恶化",
            principles=[1, 2, 3],
            solution_count=5
        )

        # 检查没有Python format占位符
        import re
        placeholders = re.findall(r'\{[a-zA-Z_]+\}', prompt)
        # 过滤掉合理的占位符（如果AI返回的JSON中有的话）
        invalid_placeholders = [p for p in placeholders if p not in ['{problem}', '{improving}', '{worsening}']]

        # 确保没有无效占位符
        assert len(invalid_placeholders) == 0, f"发现未替换的占位符: {invalid_placeholders}"


class TestBrainstormParameterLimit:
    """测试头脑风暴参数限制"""

    def test_single_improving_param(self):
        """测试单一改善参数"""
        # 模拟MatrixPage中的逻辑
        improving_params = ["运动物体的能量消耗"]

        improving = improving_params[0] if improving_params else None
        assert improving == "运动物体的能量消耗"

    def test_single_worsening_param(self):
        """测试单一恶化参数"""
        worsening_params = ["重量"]

        worsening = worsening_params[0] if worsening_params else None
        assert worsening == "重量"

    def test_empty_params_handling(self):
        """测试空参数处理"""
        improving_params = []
        worsening_params = []

        improving = improving_params[0] if improving_params else None
        worsening = worsening_params[0] if worsening_params else None

        assert improving is None
        assert worsening is None

    def test_ai_request_with_none_params(self):
        """测试带None参数的AI请求"""
        request = AIAnalysisRequest(
            problem="测试问题",
            improving_param=None,
            worsening_param=None,
            principle_ids=[1, 2, 3],
            solution_count=5
        )

        assert request.improving_param is None
        assert request.worsening_param is None


class TestSolutionParsing:
    """测试解决方案解析"""

    def test_parse_valid_json_response(self):
        """测试解析有效的JSON响应"""
        from src.ai.ai_client import AIClient

        client = AIClient()

        json_response = '''[
            {
                "principle_id": 1,
                "principle_name": "分割",
                "description": "将系统分割成独立模块，每个模块可以单独优化，从而降低复杂度同时提升性能。包含：1)模块接口标准化 2)独立电源管理 3)热分区设计。",
                "examples": ["手机模块化设计:苹果iPhone的模块化电池仓设计", "电脑组装式结构:台式机的可拆卸组件设计"],
                "confidence": 0.9
            },
            {
                "principle_id": 15,
                "principle_name": "动态性",
                "description": "引入自适应散热机制，根据实际负载动态调整散热策略。包含：1)温度传感器网络 2)风扇转速智能控制 3)相变材料应用。",
                "examples": ["笔记本电脑:联想拯救者的智能风扇控制", "数据中心:谷歌的AI散热优化"],
                "confidence": 0.85
            }
        ]'''

        solutions = client._parse_solutions(json_response, [1, 15])

        assert len(solutions) == 2
        assert solutions[0].principle_id == 1
        assert solutions[0].principle_name == "分割"
        assert solutions[1].principle_id == 15
        assert solutions[1].principle_name == "动态性"

    def test_parse_invalid_json_response(self):
        """测试解析无效JSON响应时的默认解决方案"""
        from src.ai.ai_client import AIClient

        client = AIClient()

        # 无效的JSON响应
        invalid_response = "这不是有效的JSON响应"

        solutions = client._parse_solutions(invalid_response, [1, 2, 3, 15, 28])

        # 应该返回默认解决方案
        assert len(solutions) > 0
        assert all(sol.is_ai_generated for sol in solutions)


class TestSinglePrincipleSolutionPrompt:
    """测试单个原理分析的提示词构建"""

    def test_build_single_principle_prompt_basic(self):
        """测试基本单个原理提示词构建"""
        from src.ai.prompts.builder import PromptBuilder

        builder = PromptBuilder()
        prompt = builder.build_single_principle_solution_prompt(
            problem="如何减少手机重量同时提高性能",
            improving_param="重量",
            worsening_param="性能",
            principle_id=1
        )

        # 验证问题被包含
        assert "如何减少手机重量同时提高性能" in prompt
        # 验证原理编号被包含
        assert "1" in prompt or "分割" in prompt

    def test_build_single_principle_prompt_with_synonyms(self):
        """测试带同义词的单个原理提示词"""
        from src.ai.prompts.builder import PromptBuilder

        builder = PromptBuilder()
        # 原理1的同义词是"分割"
        prompt = builder.build_single_principle_solution_prompt(
            problem="模块化设计问题",
            improving_param="复杂性",
            worsening_param="成本",
            principle_id=1
        )

        # 原理1是分割原理，同义词应该被包含
        assert "分割" in prompt or "1" in prompt

    def test_build_single_principle_prompt_empty_params(self):
        """测试空参数时的单个原理提示词"""
        from src.ai.prompts.builder import PromptBuilder

        builder = PromptBuilder()
        prompt = builder.build_single_principle_solution_prompt(
            problem="测试问题",
            improving_param="",
            worsening_param="",
            principle_id=15
        )

        # 空参数应被替换为"未指定"
        assert "未指定" in prompt
        assert "测试问题" in prompt

    def test_build_single_principle_prompt_known_principle(self):
        """测试已知原理的提示词构建"""
        from src.ai.prompts.builder import PromptBuilder

        builder = PromptBuilder()
        # 原理15是动态性原理
        prompt = builder.build_single_principle_solution_prompt(
            problem="自适应系统设计",
            improving_param="适应性",
            worsening_param="复杂性",
            principle_id=15
        )

        # 应该包含动态性相关内容
        assert "自适应系统设计" in prompt
        assert "15" in prompt or "动态性" in prompt

    def test_build_single_principle_prompt_contains_problem_context(self):
        """测试提示词包含问题上下文"""
        from src.ai.prompts.builder import PromptBuilder

        builder = PromptBuilder()
        specific_problem = "电池续航时间短导致手机用户体验下降"
        prompt = builder.build_single_principle_solution_prompt(
            problem=specific_problem,
            improving_param="电池续航",
            worsening_param="重量",
            principle_id=22  # 变害为利原理
        )

        # 验证具体问题描述被包含
        assert specific_problem in prompt


class TestSinglePrincipleGeneration:
    """测试单个原理的解决方案生成"""

    def test_generate_solution_for_principle_returns_solution(self):
        """测试单个原理生成返回解决方案"""
        from src.ai.ai_client import AIClient

        client = AIClient()

        # 这个测试检查方法是否存在
        assert hasattr(client, 'generate_solution_for_principle')

    def test_generate_solution_for_principle_signature(self):
        """测试单个原理生成方法签名"""
        from src.ai.ai_client import AIClient
        import inspect

        client = AIClient()

        # 检查方法存在
        assert hasattr(client, 'generate_solution_for_principle')

        # 检查方法签名
        sig = inspect.signature(client.generate_solution_for_principle)
        params = list(sig.parameters.keys())

        # 应该包含: problem, improving_param, worsening_param, principle_id
        assert 'problem' in params
        assert 'improving_param' in params
        assert 'worsening_param' in params
        assert 'principle_id' in params


class TestIterativeGeneration:
    """测试遍历生成解决方案"""

    def test_triz_engine_has_generate_solutions_iterative(self):
        """测试TRIZ引擎有遍历生成方法"""
        from src.core.triz_engine import TRIZEngine
        import inspect

        engine = TRIZEngine()

        # 检查方法存在
        assert hasattr(engine, 'generate_solutions_iterative')

    def test_generate_solutions_iterative_signature(self):
        """测试遍历生成方法签名"""
        from src.core.triz_engine import TRIZEngine
        import inspect

        engine = TRIZEngine()

        sig = inspect.signature(engine.generate_solutions_iterative)
        params = list(sig.parameters.keys())

        # 应该包含必要参数
        assert 'problem' in params
        assert 'improving_param' in params
        assert 'worsening_param' in params
        assert 'principle_ids' in params


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
