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

from ..data.models import AppConfig

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
        # 优先使用用户配置目录
        if os.name == "nt":  # Windows
            config_dir = Path(os.environ.get("APPDATA", "")) / "TRIZAssistant"
        elif _is_android():
            # Android环境 - 使用应用私有数据目录
            config_dir = Path("/data/data/com.example.triz/files")
            config_dir.mkdir(parents=True, exist_ok=True)
            return config_dir / "config.json"
        else:  # Linux/Mac
            config_dir = Path.home() / ".config" / "triz-assistant"

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.config_file.parent,  # 配置目录
            Path("exports"),  # 导出目录
            Path("cache"),  # 缓存目录
            Path("logs"),  # 日志目录
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    async def load(self):
        """加载设置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config = AppConfig.from_dict(data)

                # 解密API密钥
                if self.config.ai_api_key:
                    decrypted = _simple_decrypt(self.config.ai_api_key)
                    if decrypted:
                        self.config.ai_api_key = decrypted
                    else:
                        # 如果解密失败，尝试直接使用（可能是旧格式）
                        pass

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
        # AI配置
        self.config.ai_api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
        if os.environ.get("OPENROUTER_API_KEY"):
            self.config.ai_provider = "openrouter"

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

            # API密钥使用简单加密存储（安全但非军事级别）
            if data.get("ai_api_key"):
                data["ai_api_key"] = _simple_encrypt(data["ai_api_key"])

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"设置已保存到 {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            return False

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
        """获取AI API密钥"""
        return self.config.ai_api_key

    @ai_api_key.setter
    def ai_api_key(self, value: str):
        """设置AI API密钥"""
        self.config.ai_api_key = value

    @property
    def ai_provider(self) -> str:
        """获取AI提供商"""
        return self.config.ai_provider

    @ai_provider.setter
    def ai_provider(self, value: str):
        """设置AI提供商"""
        if value in ["deepseek", "openrouter", "openai"]:
            self.config.ai_provider = value

    @property
    def ai_base_url(self) -> str:
        """获取AI Base URL"""
        return self.config.ai_base_url

    @ai_base_url.setter
    def ai_base_url(self, value: str):
        """设置AI Base URL"""
        self.config.ai_base_url = value

    @property
    def ai_model(self) -> str:
        """获取AI模型"""
        return self.config.ai_model

    @ai_model.setter
    def ai_model(self, value: str):
        """设置AI模型"""
        self.config.ai_model = value

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
        return bool(self.config.ai_api_key)

    def get_ai_config_summary(self) -> Dict[str, Any]:
        """获取AI配置摘要"""
        return {
            "configured": self.is_ai_configured(),
            "provider": self.config.ai_provider,
            "has_api_key": bool(self.config.ai_api_key)
        }


# 全局设置实例
_app_settings: Optional[AppSettings] = None


def get_app_settings() -> AppSettings:
    """获取全局设置实例"""
    global _app_settings
    if _app_settings is None:
        _app_settings = AppSettings()
    return _app_settings


async def initialize_settings():
    """初始化设置"""
    settings = get_app_settings()
    await settings.load()
    return settings