"""
AI 客户端测试模块

测试 AIManager 和 AIClient 的初始化、配置和行为
使用 Mock 避免真实 API 调用
"""

from unittest.mock import patch

from src.ai.ai_client import AIClient, AIManager, get_ai_manager


class TestAIManager:
    """AI 管理器测试"""

    def setup_method(self):
        self.manager = AIManager()

    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = get_ai_manager()
        manager2 = get_ai_manager()
        assert manager1 is manager2

    def test_initialize_without_api_key(self):
        """测试无 API Key 初始化"""
        self.manager.initialize(provider="deepseek")
        assert self.manager.is_enabled() is False

    def test_initialize_with_empty_key(self):
        """测试空 API Key 初始化"""
        self.manager.initialize(api_key="", provider="deepseek")
        assert self.manager.is_enabled() is False

    def test_get_client_returns_none_when_disabled(self):
        """测试禁用时返回 None"""
        self.manager.initialize(provider="deepseek")
        client = self.manager.get_client()
        assert client is None

    def test_is_enabled_reflects_api_key(self):
        """测试 is_enabled 反映 API Key 状态"""
        self.manager.initialize(provider="deepseek")
        assert self.manager.is_enabled() is False


class TestAIClient:
    """AI 客户端测试 (Mock)"""

    def setup_method(self):
        self.client = AIClient(api_key="test_key", provider="deepseek")

    def test_initialization(self):
        """测试初始化"""
        assert self.client.api_key == "test_key"
        assert self.client.provider == "deepseek"

    def test_is_available_returns_bool(self):
        """测试 is_available 返回布尔值"""
        result = self.client.is_available()
        assert isinstance(result, bool)


class TestAIManagerMocked:
    """带 Mock 的 AI 管理器测试"""

    def setup_method(self):
        self.manager = AIManager()

    @patch.object(AIClient, "is_available", return_value=False)
    def test_ai_unavailable_when_client_returns_false(self, mock_is_available):
        """测试客户端返回 False 时 AI 不可用"""
        self.manager.initialize(api_key="fake_key", provider="deepseek")
        client = self.manager.get_client()
        if client:
            result = client.is_available()
            assert result is False

    def test_init_with_different_providers(self):
        """测试不同 provider 初始化"""
        client_deepseek = AIClient(api_key="key", provider="deepseek")
        assert client_deepseek.provider == "deepseek"
        assert client_deepseek.api_key == "key"
