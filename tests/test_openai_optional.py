"""
openai 可选导入测试

验证 openai 模块缺失时的降级行为
"""

import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestOpenAIOptional:
    """测试 openai 模块可选时的行为"""

    def test_ai_client_imports_without_openai(self):
        """验证 ai_client 模块在 openai 缺失时仍可导入"""
        # 这个测试检查 ai_client 模块是否正确处理 openai 缺失
        from src.ai import ai_client
        assert hasattr(ai_client, '_OPENAI_AVAILABLE')
        # _OPENAI_AVAILABLE 应该是 False（因为当前环境没有 openai）
        # 或者如果有 openai 则为 True

    def test_aimanager_without_openai(self):
        """测试 AIManager 在 openai 缺失时的行为"""
        from src.ai.ai_client import AIManager, _OPENAI_AVAILABLE

        manager = AIManager()

        # 无论 openai 是否可用，AIManager 都应该能初始化
        manager.initialize(provider="deepseek")

        # 没有 api_key 时应该 is_enabled() 返回 False
        assert manager.is_enabled() is False
        assert manager.is_connected() is False

    def test_aiclient_disabled_without_openai(self):
        """测试 AIClient 在 openai 缺失时是否正确禁用"""
        from src.ai.ai_client import AIClient, _OPENAI_AVAILABLE

        # 如果 openai 不可用，即使有 api_key 也应该无法初始化客户端
        client = AIClient(api_key="test_key", provider="deepseek")

        if not _OPENAI_AVAILABLE:
            # 没有 openai 时，客户端应该被禁用
            assert client.enabled is False, "openai 不可用时客户端应该禁用"
            assert client.client is None, "openai 不可用时 client 应该为 None"
