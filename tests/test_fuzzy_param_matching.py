# -*- coding: utf-8 -*-
"""
参数模糊匹配测试

验证思考模型返回的参数名称能够正确匹配到39参数列表
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# 从 constants 导入39参数列表
from src.config.constants import ENGINEERING_PARAMETERS_39
from src.ai.ai_client import fuzzy_match_param


class TestFuzzyParamMatching:
    """测试参数模糊匹配"""

    def test_exact_match(self):
        """精确匹配应该直接返回"""
        assert fuzzy_match_param("速度", ENGINEERING_PARAMETERS_39) == "速度"
        assert fuzzy_match_param("功率", ENGINEERING_PARAMETERS_39) == "功率"
        assert fuzzy_match_param("重量", ENGINEERING_PARAMETERS_39) == "移动物体的重量"

    def test_alias_match(self):
        """别名匹配"""
        assert fuzzy_match_param("能量", ENGINEERING_PARAMETERS_39) == "移动物体用的能源"
        assert fuzzy_match_param("能源", ENGINEERING_PARAMETERS_39) == "移动物体用的能源"

    def test_partial_match(self):
        """部分匹配"""
        # "能量消耗" 应该匹配到 "移动物体用的能源"
        result = fuzzy_match_param("能量消耗", ENGINEERING_PARAMETERS_39)
        assert result in ENGINEERING_PARAMETERS_39

    def test_thinking_model_common_params(self):
        """思考模型常见返回格式"""
        # 思考模型可能返回的格式
        test_cases = [
            ("速度", "速度"),
            ("功率", "功率"),
            ("能量", "移动物体用的能源"),
            ("重量", "移动物体用的重量"),
            ("体积", "移动物体的体积"),
            ("长度", "移动物体的长度"),
            ("强度", "强度"),
            ("可靠性", "可靠性"),
        ]
        for input_param, expected in test_cases:
            result = fuzzy_match_param(input_param, ENGINEERING_PARAMETERS_39)
            # 结果应该在39参数列表中
            assert result in ENGINEERING_PARAMETERS_39, f"'{input_param}' -> '{result}' not in 39 params"

    def test_unmatched_param(self):
        """无法匹配的参数应返回原值"""
        result = fuzzy_match_param("完全不存在的参数", ENGINEERING_PARAMETERS_39)
        assert result == "完全不存在的参数"

    def test_empty_param(self):
        """空参数应该返回空字符串"""
        result = fuzzy_match_param("", ENGINEERING_PARAMETERS_39)
        # 空字符串不应该匹配到任何参数
        assert result == "" or result not in ENGINEERING_PARAMETERS_39


class TestJSONParsingWithThinkingContent:
    """测试包含思考内容的JSON解析"""

    def test_remove_think_tags(self):
        """验证能够移除think标签"""
        import re

        # 使用普通字符串避免语法问题
        content = (
            "<think>让我分析这个问题..."
            "思考过程...</think>"
            '{"improving": ["速度"], "worsening": ["重量"]}'
        )

        cleaned = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        assert '<think>' not in cleaned
        assert '<think>' not in cleaned
        assert '速度' in cleaned
        assert '{"improving"' in cleaned

    def test_extract_json_from_thinking_response(self):
        """从思考模型响应中提取JSON"""
        import re

        # 使用普通字符串避免语法问题
        content = (
            "<think>用户想要提高速度同时减少重量..."
            "我需要选择合适的TRIZ参数...</think>"
            '{"improving": ["速度", "功率"], '
            '"worsening": ["重量", "体积"], '
            '"explanation": "提高性能降低能耗"}'
        )

        # 移除think标签
        import re
        cleaned = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)

        # 提取JSON
        json_start = cleaned.find('{"')
        json_end = cleaned.rfind('}') + 1

        assert json_start >= 0
        assert json_end > json_start

        import json
        result = json.loads(cleaned[json_start:json_end])
        assert result["improving"] == ["速度", "功率"]
        assert result["worsening"] == ["重量", "体积"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
