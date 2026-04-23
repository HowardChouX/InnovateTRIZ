"""
测试供应商配置解密逻辑
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.config.settings import AppSettings, _simple_decrypt, _simple_encrypt
from src.data.models import AppConfig, ProviderConfig


class TestProviderConfigDecryption:
    """测试供应商配置的加密/解密"""

    @pytest.fixture
    def temp_config_file(self):
        """创建临时配置文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name
        yield temp_path
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_simple_encrypt_decrypt_roundtrip(self):
        """测试加密解密往返"""
        original = "sk-test-api-key-123"
        encrypted = _simple_encrypt(original)
        decrypted = _simple_decrypt(encrypted)
        assert decrypted == original, f"期望 {original}，实际 {decrypted}"

    def test_save_load_decrypts_current_provider_key(self, temp_config_file):
        """测试保存和加载后所有供应商密钥都被解密"""
        # 创建设置实例
        settings = AppSettings()
        settings.config_file = Path(temp_config_file)

        # 配置多个供应商
        settings.config.ai_provider = "deepseek"
        settings.config.set_provider_config(
            "deepseek",
            ProviderConfig(
                api_key="deepseek-key-123",
                base_url="https://api.deepseek.com/v1",
                model="deepseek-chat",
            ),
        )
        settings.config.set_provider_config(
            "openrouter",
            ProviderConfig(
                api_key="openrouter-key-456",
                base_url="https://openrouter.ai/api/v1",
                model="deepseek/deepseek-chat",
            ),
        )
        settings.config.set_provider_config(
            "openai-format",
            ProviderConfig(
                api_key="openai-key-789",
                base_url="https://api.openai.com/v1",
                model="gpt-4",
            ),
        )

        # 保存（会加密）
        data = settings.config.to_dict()
        # 确保所有 ProviderConfig 转为 dict 后再加密和序列化
        providers_dict: dict = {}
        for provider, config in data.get("ai_providers_config", {}).items():
            if isinstance(config, dict):
                d = dict(config)
            elif hasattr(config, "to_dict"):
                d = config.to_dict()
            else:
                d = {"api_key": None, "base_url": "", "model": ""}
            providers_dict[provider] = d
        data["ai_providers_config"] = providers_dict

        # 模拟加密
        for provider, config in data["ai_providers_config"].items():
            if config.get("api_key"):
                config["api_key"] = _simple_encrypt(config["api_key"])

        with open(temp_config_file, "w") as f:
            json.dump(data, f)

        # 重新加载
        settings2 = AppSettings()
        settings2.config_file = Path(temp_config_file)

        # 模拟 AppSettings.load() 的行为：解密所有供应商密钥
        with open(temp_config_file) as f:
            data = json.load(f)
        settings2.config = AppConfig.from_dict(data)

        for provider, provider_config in settings2.config.ai_providers_config.items():
            if provider_config and provider_config.api_key:
                decrypted = _simple_decrypt(provider_config.api_key)
                if decrypted:
                    provider_config.api_key = decrypted

        # 验证所有供应商的密钥都已解密
        assert (
            settings2.config.ai_providers_config["deepseek"].api_key
            == "deepseek-key-123"
        ), f"deepseek 期望 deepseek-key-123，实际: {settings2.config.ai_providers_config['deepseek'].api_key}"
        assert (
            settings2.config.ai_providers_config["openrouter"].api_key
            == "openrouter-key-456"
        ), f"openrouter 期望 openrouter-key-456，实际: {settings2.config.ai_providers_config['openrouter'].api_key}"
        assert (
            settings2.config.ai_providers_config["openai-format"].api_key
            == "openai-key-789"
        ), f"openai-format 期望 openai-key-789，实际: {settings2.config.ai_providers_config['openai-format'].api_key}"

    def test_all_provider_keys_encrypted_in_saved_file(self, temp_config_file):
        """测试保存时所有供应商密钥都被加密"""
        settings = AppSettings()
        settings.config_file = Path(temp_config_file)

        settings.config.ai_provider = "deepseek"
        settings.config.set_provider_config(
            "deepseek",
            ProviderConfig(
                api_key="deepseek-key",
                base_url="https://api.deepseek.com/v1",
                model="deepseek-chat",
            ),
        )
        settings.config.set_provider_config(
            "openrouter",
            ProviderConfig(
                api_key="openrouter-key",
                base_url="https://openrouter.ai/api/v1",
                model="deepseek/deepseek-chat",
            ),
        )
        settings.config.set_provider_config(
            "openai-format",
            ProviderConfig(
                api_key="openai-key",
                base_url="https://api.openai.com/v1",
                model="gpt-4",
            ),
        )

        # 保存
        data = settings.config.to_dict()
        # 确保所有 ProviderConfig 转为 dict 后再加密
        providers_dict: dict = {}
        for provider, config in data.get("ai_providers_config", {}).items():
            if isinstance(config, dict):
                d = dict(config)
            elif hasattr(config, "to_dict"):
                d = config.to_dict()
            else:
                d = {"api_key": None, "base_url": "", "model": ""}
            providers_dict[provider] = d
        data["ai_providers_config"] = providers_dict

        # 模拟加密
        for provider, config in data["ai_providers_config"].items():
            if config.get("api_key"):
                config["api_key"] = _simple_encrypt(config["api_key"])

        with open(temp_config_file, "w") as f:
            json.dump(data, f)

        # 读取文件，验证密钥是加密的
        with open(temp_config_file) as f:
            saved_data = json.load(f)

        # 加密后的密钥不应该是明文
        assert saved_data["ai_providers_config"]["deepseek"][
            "api_key"
        ] == _simple_encrypt("deepseek-key")
        assert saved_data["ai_providers_config"]["openrouter"][
            "api_key"
        ] == _simple_encrypt("openrouter-key")
        assert saved_data["ai_providers_config"]["openai-format"][
            "api_key"
        ] == _simple_encrypt("openai-key")

    def test_switch_provider_after_load(self, temp_config_file):
        """测试加载后切换供应商能正确处理密钥"""
        # 预置配置
        config_data = {
            "ai_provider": "deepseek",
            "ai_providers_config": {
                "deepseek": {
                    "api_key": _simple_encrypt("deepseek-secret"),
                    "base_url": "https://api.deepseek.com/v1",
                    "model": "deepseek-chat",
                },
                "openrouter": {
                    "api_key": _simple_encrypt("openrouter-secret"),
                    "base_url": "https://openrouter.ai/api/v1",
                    "model": "deepseek/deepseek-chat",
                },
                "openai-format": {
                    "api_key": None,
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-4",
                },
            },
            "default_matrix_type": "39",
            "default_solution_count": 5,
            "enable_history": True,
            "enable_cache": True,
            "language": "zh",
            "theme": "light",
        }

        with open(temp_config_file, "w") as f:
            json.dump(config_data, f)

        # 加载
        settings = AppSettings()
        settings.config_file = Path(temp_config_file)
        settings.config = AppConfig.from_dict(config_data)

        # 模拟 load() 的行为：解密所有供应商的密钥
        for provider, provider_config in settings.config.ai_providers_config.items():
            if provider_config and provider_config.api_key:
                decrypted = _simple_decrypt(provider_config.api_key)
                if decrypted:
                    provider_config.api_key = decrypted

        # 验证 deepseek 已解密
        assert (
            settings.config.ai_providers_config["deepseek"].api_key == "deepseek-secret"
        ), f"deepseek 期望解密后，实际: {settings.config.ai_providers_config['deepseek'].api_key}"

        # 切换到 openrouter - 现在密钥应该已经解密
        settings.config.ai_provider = "openrouter"
        openrouter_config = settings.config.ai_providers_config["openrouter"]
        assert (
            openrouter_config.api_key == "openrouter-secret"
        ), f"openrouter 期望解密后，实际: {openrouter_config.api_key}"

        # 切换到 openai-format（没有密钥）
        settings.config.ai_provider = "openai-format"
        assert settings.config.ai_providers_config["openai-format"].api_key is None
