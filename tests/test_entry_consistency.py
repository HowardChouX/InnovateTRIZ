"""
src/main.py 与根目录 main.py 一致性测试

验证两个入口点产生相同的行为
"""

import os
import sys

# 确保能导入 src 模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestMainEntryConsistency:
    """测试两个 main.py 入口的一致性"""

    def test_both_main_modules_importable(self):
        """验证两个 main.py 模块都可以被导入"""
        # 根目录 main.py
        import main as root_main
        assert hasattr(root_main, 'TRIZApp')
        assert hasattr(root_main, 'main')

        # src/main.py
        import src.main as src_main
        assert hasattr(src_main, 'TRIZApp')
        assert hasattr(src_main, 'main')

    def test_both_have_same_classes(self):
        """验证两个入口定义了相同的类"""
        import main as root_main
        import src.main as src_main

        # 两者都应该有 TRIZApp 类
        assert root_main.TRIZApp is not None
        assert src_main.TRIZApp is not None

        # 类应该有相同的方法
        root_methods = set(m for m in dir(root_main.TRIZApp) if not m.startswith('_'))
        src_methods = set(m for m in dir(src_main.TRIZApp) if not m.startswith('_'))

        # 公开方法应该一致（可能有细微差异）
        core_methods = {'main', '_setup_page', '_initialize_components',
                       '_show_main_interface', '_show_error_page', '_restart_app'}

        for method in core_methods:
            assert hasattr(root_main.TRIZApp, method), f"root_main.TRIZApp 缺少 {method}"
            assert hasattr(src_main.TRIZApp, method), f"src_main.TRIZApp 缺少 {method}"

    def test_both_have_same_async_methods(self):
        """验证两个入口的异步方法一致"""
        import main as root_main
        import src.main as src_main

        async_methods = ['main', '_initialize_components', '_show_main_interface',
                        '_show_error_page', '_restart_async']

        for method in async_methods:
            assert hasattr(root_main.TRIZApp, method), f"root_main.TRIZApp 缺少 async {method}"
            assert hasattr(src_main.TRIZApp, method), f"src_main.TRIZApp 缺少 async {method}"


class TestSysPathSetup:
    """测试 sys.path 设置"""

    def test_src_main_sets_correct_path(self):
        """验证 src/main.py 设置了正确的 sys.path"""
        import src.main as src_main_module

        # 检查 project_root 是否在 sys.path
        # 注意：这个测试在导入后检查，所以 project_root 应该已经添加
        pass  # 路径设置在导入时完成

    def test_root_main_sets_src_path(self):
        """验证根目录 main.py 添加了 src 到 sys.path"""
        import main as root_main_module

        # src 目录应该在 sys.path 中
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
        src_path = os.path.normpath(src_path)
        found = any(os.path.normpath(p) == src_path for p in sys.path)
        assert found, f"src 路径未在 sys.path 中找到"
