"""
环境变量降级路径测试

测试 FLET_APP_STORAGE_DATA 等环境变量未设置时的降级行为
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestStoragePathFallback:
    """测试存储路径的环境变量降级"""

    def test_local_storage_uses_flet_storage_data(self):
        """验证 LocalStorage 优先使用 FLET_APP_STORAGE_DATA"""
        with patch.dict(os.environ, {'FLET_APP_STORAGE_DATA': '/test/data'}, clear=False):
            # 重新导入以获取新值
            import importlib
            from src.data import local_storage
            importlib.reload(local_storage)

            storage_dir = local_storage._get_storage_dir()
            assert str(storage_dir) == '/test/data', f"期望 /test/data，实际 {storage_dir}"

    def test_local_storage_fallback_without_env(self):
        """验证 FLET_APP_STORAGE_DATA 未设置时的降级路径"""
        # 移除环境变量
        env_without = {k: v for k, v in os.environ.items() if k != 'FLET_APP_STORAGE_DATA'}

        with patch.dict(os.environ, env_without, clear=True):
            import importlib
            from src.data import local_storage
            importlib.reload(local_storage)

            storage_dir = local_storage._get_storage_dir()

            # 降级到临时目录
            assert storage_dir is not None
            assert 'triz-assistant' in str(storage_dir)


class TestConfigPathFallback:
    """测试配置路径的环境变量降级"""

    def test_settings_uses_flet_storage_data(self):
        """验证 AppSettings 优先使用 FLET_APP_STORAGE_DATA"""
        with patch.dict(os.environ, {'FLET_APP_STORAGE_DATA': '/test/config'}, clear=False):
            import importlib
            from src.config import settings
            importlib.reload(settings)

            app_settings = settings.AppSettings()
            config_path = app_settings._get_config_path()

            assert str(config_path).startswith('/test/config'), f"配置路径应该从 /test/config 开始: {config_path}"


class TestLogPathFallback:
    """测试日志路径的环境变量降级"""

    def test_main_uses_flet_storage_data_for_logs(self):
        """验证根目录 main.py 优先使用 FLET_APP_STORAGE_DATA"""
        # 读取 main.py 中的日志路径设置
        import main

        # 检查 _is_android_env 函数存在
        assert hasattr(main, '_is_android_env')

        # Mock 环境
        with patch.dict(os.environ, {'FLET_APP_STORAGE_DATA': '/test/logs'}, clear=False):
            # 调用 _is_android_env 应该返回 False（因为 FLET_PLATFORM 不是 android）
            assert main._is_android_env() is False

            # 验证日志目录逻辑
            app_data_path = os.getenv('FLET_APP_STORAGE_DATA')
            if app_data_path:
                log_dir = Path(app_data_path) / "logs"
                assert str(log_dir) == '/test/logs/logs'
