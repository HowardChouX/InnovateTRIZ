"""
AI参数检测测试
测试AI分析参数功能
"""

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ai.ai_client import AIClient
from src.config.constants import ENGINEERING_PARAMETERS_39
from src.config.settings import AppSettings


class TestAIClient:
    """AI客户端测试"""

    def setup_method(self):
        """每个测试前准备"""
        self.settings = AppSettings()

    def test_detect_parameters_returns_list(self):
        """测试参数检测返回列表格式"""
        # 需要API密钥才能测试
        if not self.settings.ai_api_key:
            pytest.skip("需要配置AI API密钥")

        client = AIClient(
            api_key=self.settings.ai_api_key,
            provider=self.settings.ai_provider,
            base_url=self.settings.ai_base_url,
            model=self.settings.ai_model,
        )

        if not client.is_available():
            pytest.skip("AI不可用")

        async def run_test():
            result = await client.detect_parameters("手机需要更大电池但要保持轻薄")

            # 验证返回格式
            assert isinstance(result, dict)
            assert "improving" in result
            assert "worsening" in result

            # 验证改善参数是列表
            improving = result.get("improving", [])
            if improving:
                assert isinstance(improving, list), "改善参数应该是列表"
                # 验证参数在39参数列表中
                for p in improving:
                    assert p in ENGINEERING_PARAMETERS_39, f"参数'{p}'不在39参数列表中"

            # 验证恶化参数是列表
            worsening = result.get("worsening", [])
            if worsening:
                assert isinstance(worsening, list), "恶化参数应该是列表"
                # 验证参数在39参数列表中
                for p in worsening:
                    assert p in ENGINEERING_PARAMETERS_39, f"参数'{p}'不在39参数列表中"

            print(f"改善参数: {improving}")
            print(f"恶化参数: {worsening}")

        asyncio.run(run_test())

    def test_detect_parameters_multiple(self):
        """测试返回多个参数"""
        if not self.settings.ai_api_key:
            pytest.skip("需要配置AI API密钥")

        client = AIClient(
            api_key=self.settings.ai_api_key,
            provider=self.settings.ai_provider,
            base_url=self.settings.ai_base_url,
            model=self.settings.ai_model,
        )

        if not client.is_available():
            pytest.skip("AI不可用")

        async def run_test():
            result = await client.detect_parameters("如何提高汽车速度同时降低油耗")

            improving = result.get("improving", [])
            worsening = result.get("worsening", [])

            print(f"改善参数: {improving} (共{len(improving)}个)")
            print(f"恶化参数: {worsening} (共{len(worsening)}个)")

            # 至少应该有一些参数
            assert len(improving) > 0 or len(worsening) > 0

        asyncio.run(run_test())

    def test_detect_parameters_explanation(self):
        """测试返回包含解释"""
        if not self.settings.ai_api_key:
            pytest.skip("需要配置AI API密钥")

        client = AIClient(
            api_key=self.settings.ai_api_key,
            provider=self.settings.ai_provider,
            base_url=self.settings.ai_base_url,
            model=self.settings.ai_model,
        )

        if not client.is_available():
            pytest.skip("AI不可用")

        async def run_test():
            result = await client.detect_parameters("手机需要更大电池但要保持轻薄")
            explanation = result.get("explanation", "")

            print(f"解释: {explanation}")
            # 解释应该非空
            assert explanation != ""

        asyncio.run(run_test())


class TestParameterValidation:
    """参数验证测试"""

    def test_engineering_params_39_count(self):
        """测试39参数数量"""
        assert len(ENGINEERING_PARAMETERS_39) == 39
        print(f"39参数列表共{len(ENGINEERING_PARAMETERS_39)}个参数")

    def test_engineering_params_include_energy(self):
        """测试能量参数存在"""
        energy_params = [
            p for p in ENGINEERING_PARAMETERS_39 if "能源" in p or "能量" in p
        ]
        assert len(energy_params) >= 2, "应该有多个能量相关参数"
        print(f"能量参数: {energy_params}")

    def test_engineering_params_include_weight(self):
        """测试重量参数存在"""
        weight_params = [p for p in ENGINEERING_PARAMETERS_39 if "重量" in p]
        assert len(weight_params) >= 2, "应该有多个重量相关参数"
        print(f"重量参数: {weight_params}")

    def test_engineering_params_no_duplicates(self):
        """测试参数无重复"""
        assert len(ENGINEERING_PARAMETERS_39) == len(set(ENGINEERING_PARAMETERS_39))
        print("参数列表无重复")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
