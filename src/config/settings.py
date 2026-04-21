"""
应用设置管理
"""

import os
import sys
import json
import logging
import base64
from typing import Optional, Dict, Any
from pathlib import Path

from ..data.models import AppConfig, ProviderConfig

logger = logging.getLogger(__name__)

# 简单的加密密钥（实际生产应使用更安全的方式）
_SETTINGS_ENC_KEY = b"triz-app-secure-key-2024"


def _simple_encrypt(data: str) -> str:
    """简单加密API密钥"""
    if not data:
        return ""
    encoded = base64.b64encode(data.encode()).decode()
    return encoded


def _simple_decrypt(data: str) -> str:
    """简单解密API密钥"""
    if not data or data == "[REDACTED]":
        return ""
    try:
        decoded = base64.b64decode(data.encode()).decode()
        return decoded
    except Exception:
        return ""


def _is_android() -> bool:
    """检测是否运行在Android环境"""
    # 优先检测 platform
    if sys.platform == "android":
        return True
    # 回退检测 ANDROID_ROOT 环境变量
    if "ANDROID" in os.environ.get("ANDROID_ROOT", ""):
        return True
    return False


class AppSettings:
    """应用设置管理器"""

    def __init__(self):
        self.config = AppConfig()
        self.config_file = self._get_config_path()
        self._ensure_directories()

    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        # 方法1: 使用 FLET_APP_STORAGE_DATA 环境变量（最推荐）
        app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
        if app_data_path:
            config_path = Path(app_data_path) / "config.json"
            return config_path

        # 方法2: 非 Android 路径
        if os.name == "nt":  # Windows
            config_dir = Path(os.environ.get("APPDATA", "")) / "TRIZAssistant"
        else:  # Linux/Mac
            config_dir = Path.home() / ".config" / "triz-assistant"

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.config_file.parent,  # 配置目录
        ]

        if not _is_android():
            # 非Android环境添加相对路径目录
            directories.extend([
                Path("exports"),  # 导出目录
                Path("cache"),  # 缓存目录
                Path("logs"),  # 日志目录
            ])

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except:
                pass  # Android上某些目录可能无法创建

    async def load(self):
        """加载设置（不解密，密钥在打开设置对话框时解密）"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config = AppConfig.from_dict(data)

                logger.info(f"设置已从 {self.config_file} 加载")
            else:
                # 尝试从环境变量加载
                await self._load_from_env()
                logger.info("使用默认设置")

        except Exception as e:
            logger.error(f"加载设置失败: {e}")
            # 使用默认设置

    async def _load_from_env(self):
        """从环境变量加载设置"""
        # AI配置 - 从环境变量加载到当前供应商配置
        current_provider = self.config.ai_provider
        provider_config = self.config.ai_providers_config.get(current_provider)
        if not provider_config:
            provider_config = ProviderConfig()
            self.config.ai_providers_config[current_provider] = provider_config

        if os.environ.get("DEEPSEEK_API_KEY"):
            self.config.ai_provider = "deepseek"
            self.config.ai_providers_config["deepseek"].api_key = os.environ.get("DEEPSEEK_API_KEY")
        elif os.environ.get("OPENROUTER_API_KEY"):
            self.config.ai_provider = "openrouter"
            self.config.ai_providers_config["openrouter"].api_key = os.environ.get("OPENROUTER_API_KEY")

        # 应用配置
        language = os.environ.get("APP_LANGUAGE")
        if language in ["zh", "en"]:
            self.config.language = language

        theme = os.environ.get("THEME_MODE")
        if theme in ["light", "dark", "auto"]:
            self.config.theme = theme

    async def save(self):
        """保存设置"""
        try:
            data = self.config.to_dict()

            # 加密所有供应商的API密钥
            for provider, config in data.get("ai_providers_config", {}).items():
                if config.get("api_key"):
                    config["api_key"] = _simple_encrypt(config["api_key"])

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"设置已保存到 {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            return False

    def decrypt_all_provider_keys(self):
        """解密所有供应商的API密钥（仅在打开设置对话框时调用一次）"""
        for provider, provider_config in self.config.ai_providers_config.items():
            if provider_config and provider_config.api_key:
                decrypted = _simple_decrypt(provider_config.api_key)
                if decrypted:
                    provider_config.api_key = decrypted
                else:
                    # 如果解密失败，保留原值（可能是明文）
                    pass

    def get(self, key: str, default=None) -> Any:
        """获取设置值"""
        return getattr(self.config, key, default)

    def set(self, key: str, value: Any):
        """设置值"""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            logger.info(f"设置更新: {key} = {value}")
        else:
            logger.warning(f"尝试设置不存在的配置项: {key}")

    def update(self, updates: Dict[str, Any]):
        """批量更新设置"""
        for key, value in updates.items():
            self.set(key, value)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于日志等，显示时隐藏敏感信息）"""
        data = self.config.to_dict()

        # 隐藏敏感信息用于显示
        sensitive_keys = ["ai_api_key", "password", "token"]
        for key in sensitive_keys:
            if key in data and data[key]:
                data[key] = "[ENCRYPTED]"

        return data

    def reset_to_defaults(self):
        """重置为默认设置"""
        self.config = AppConfig()
        logger.info("设置已重置为默认值")

    # 便捷属性访问
    @property
    def ai_api_key(self) -> Optional[str]:
        """获取当前供应商的AI API密钥"""
        return self.config.get_current_provider_config().api_key

    @ai_api_key.setter
    def ai_api_key(self, value: str):
        """设置当前供应商的AI API密钥"""
        provider = self.config.ai_provider
        if provider not in self.config.ai_providers_config:
            self.config.ai_providers_config[provider] = ProviderConfig()
        self.config.ai_providers_config[provider].api_key = value

    @property
    def ai_provider(self) -> str:
        """获取AI提供商"""
        return self.config.ai_provider

    @ai_provider.setter
    def ai_provider(self, value: str):
        """设置AI提供商"""
        if value in ["deepseek", "openrouter", "openai-format"]:
            self.config.ai_provider = value

    @property
    def ai_base_url(self) -> str:
        """获取当前供应商的AI Base URL"""
        return self.config.get_current_provider_config().base_url

    @ai_base_url.setter
    def ai_base_url(self, value: str):
        """设置当前供应商的AI Base URL"""
        provider = self.config.ai_provider
        if provider not in self.config.ai_providers_config:
            self.config.ai_providers_config[provider] = ProviderConfig()
        self.config.ai_providers_config[provider].base_url = value

    @property
    def ai_model(self) -> str:
        """获取当前供应商的AI模型"""
        return self.config.get_current_provider_config().model

    @ai_model.setter
    def ai_model(self, value: str):
        """设置当前供应商的AI模型"""
        provider = self.config.ai_provider
        if provider not in self.config.ai_providers_config:
            self.config.ai_providers_config[provider] = ProviderConfig()
        self.config.ai_providers_config[provider].model = value

    @property
    def language(self) -> str:
        """获取界面语言"""
        return self.config.language

    @language.setter
    def language(self, value: str):
        """设置界面语言"""
        if value in ["zh", "en"]:
            self.config.language = value

    @property
    def theme(self) -> str:
        """获取主题模式"""
        return self.config.theme

    @theme.setter
    def theme(self, value: str):
        """设置主题模式"""
        if value in ["light", "dark", "auto"]:
            self.config.theme = value

    @property
    def default_solution_count(self) -> int:
        """获取默认解决方案数量"""
        return self.config.default_solution_count

    @default_solution_count.setter
    def default_solution_count(self, value: int):
        """设置默认解决方案数量"""
        if 0 <= value <= 20:
            self.config.default_solution_count = value

    @property
    def enable_history(self) -> bool:
        """获取历史记录启用状态"""
        return self.config.enable_history

    @enable_history.setter
    def enable_history(self, value: bool):
        """设置历史记录启用状态"""
        self.config.enable_history = value

    def is_ai_configured(self) -> bool:
        """检查AI是否已配置"""
        return bool(self.ai_api_key)

    def get_ai_config_summary(self) -> Dict[str, Any]:
        """获取AI配置摘要"""
        return {
            "configured": self.is_ai_configured(),
            "provider": self.config.ai_provider,
            "has_api_key": bool(self.ai_api_key)
        }


# 全局设置实例
_app_settings: Optional[AppSettings] = None
_settings_loaded: bool = False


def get_app_settings() -> AppSettings:
    """获取全局设置实例（已加载）"""
    global _app_settings, _settings_loaded
    if _app_settings is None:
        _app_settings = AppSettings()
    return _app_settings


async def initialize_settings():
    """初始化设置"""
    settings = get_app_settings()
    await settings.load()
    return settings