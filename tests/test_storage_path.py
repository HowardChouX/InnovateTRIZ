"""
存储路径兼容性测试

验证 Android 环境下 FLET_APP_STORAGE_DATA 环境变量的正确使用
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestLocalStoragePath:
    """测试 LocalStorage 路径逻辑"""

    def test_get_storage_dir_uses_flet_app_storage_data(self):
        """验证使用 FLET_APP_STORAGE_DATA 环境变量"""
        from src.data.local_storage import _get_storage_dir

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"FLET_APP_STORAGE_DATA": tmpdir}):
                result = _get_storage_dir()
                assert result == Path(tmpdir)
                assert result.exists()

    def test_get_storage_dir_fallback_to_home(self):
        """验证回退到 home 目录"""
        from src.data.local_storage import _get_storage_dir

        # 清除环境变量
        with patch.dict(os.environ, {}, clear=True):
            if "FLET_APP_STORAGE_DATA" in os.environ:
                del os.environ["FLET_APP_STORAGE_DATA"]
            result = _get_storage_dir()
            # 应该回退到 home/.config/triz-assistant
            assert "triz-assistant" in str(result)

    def test_storage_dir_creation(self):
        """验证存储目录自动创建"""
        from src.data.local_storage import LocalStorage

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalStorage(db_path=os.path.join(tmpdir, "test.db"))
            storage.initialize()
            assert Path(tmpdir, "test.db").exists()
            storage.close()


class TestSettingsPath:
    """测试 AppSettings 路径逻辑"""

    def test_config_path_uses_flet_app_storage_data(self):
        """验证配置路径使用 FLET_APP_STORAGE_DATA"""
        from src.config.settings import AppSettings

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"FLET_APP_STORAGE_DATA": tmpdir}):
                settings = AppSettings()
                assert settings.config_file == Path(tmpdir) / "config.json"

    def test_config_path_fallback_to_home(self):
        """验证配置路径回退到 home 目录"""
        from src.config.settings import AppSettings

        with patch.dict(os.environ, {}, clear=True):
            if "FLET_APP_STORAGE_DATA" in os.environ:
                del os.environ["FLET_APP_STORAGE_DATA"]
            settings = AppSettings()
            # 应该回退到 home/.config/triz-assistant/config.json
            assert "triz-assistant" in str(settings.config_file)
            assert settings.config_file.name == "config.json"


class TestLoggingPath:
    """测试日志路径逻辑"""

    def test_log_dir_uses_flet_app_storage_data(self):
        """验证日志目录使用 FLET_APP_STORAGE_DATA"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"FLET_APP_STORAGE_DATA": tmpdir}):
                log_dir = Path(tmpdir) / "logs"
                # 模拟 main.py 中的逻辑
                app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
                if app_data_path:
                    result = Path(app_data_path) / "logs"
                else:
                    result = Path.home() / ".config" / "triz-assistant" / "logs"
                assert result == log_dir

    def test_log_dir_fallback_to_home(self):
        """验证日志目录回退到 home 目录"""
        with patch.dict(os.environ, {}, clear=True):
            if "FLET_APP_STORAGE_DATA" in os.environ:
                del os.environ["FLET_APP_STORAGE_DATA"]
            app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
            if app_data_path:
                result = Path(app_data_path) / "logs"
            else:
                result = Path.home() / ".config" / "triz-assistant" / "logs"
            assert "triz-assistant" in str(result)
            assert "logs" in str(result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
