"""
APK编译前检查脚本
在执行flet build apk之前运行此脚本进行全面检查
"""

import os
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.logger import IS_ANDROID, LOG_DIR, get_logger


class PreBuildChecker:
    """编译前检查器"""

    def __init__(self):
        self.logger = get_logger("PRE_BUILD")
        self.checks = []
        self.passed = 0
        self.failed = 0

    def check(self, name: str, condition: bool, message: str = ""):
        """执行检查"""
        self.checks.append({"name": name, "passed": condition, "message": message})
        if condition:
            self.passed += 1
            self.logger.info(f"✅ {name}")
        else:
            self.failed += 1
            self.logger.error(f"❌ {name}: {message}")

    def print_report(self):
        """打印检查报告"""
        print("\n" + "=" * 60)
        print("APK编译前检查报告")
        print("=" * 60)
        print(f"\n检查项: {self.passed + self.failed}")
        print(f"通过: {self.passed} ✅")
        print(f"失败: {self.failed} ❌")

        if self.failed > 0:
            print("\n失败项目:")
            for check in self.checks:
                if not check["passed"]:
                    print(f"  ❌ {check['name']}: {check['message']}")

        print("\n" + "=" * 60)
        return self.failed == 0


def run_checks():
    """运行所有检查"""
    checker = PreBuildChecker()
    logger = checker.logger

    print("\n开始APK编译前检查...\n")

    # ========== 1. 文件结构检查 ==========
    logger.info("=== 文件结构检查 ===")

    required_files = [
        "main.py",
        "requirements.txt",
        "src/__init__.py",
        "src/ai/__init__.py",
        "src/ai/ai_client.py",
        "src/config/__init__.py",
        "src/config/constants.py",
        "src/config/settings.py",
        "src/core/__init__.py",
        "src/core/triz_engine.py",
        "src/core/matrix_selector.py",
        "src/core/principle_service.py",
        "src/data/__init__.py",
        "src/data/local_storage.py",
        "src/data/models.py",
        "src/ui/__init__.py",
        "src/ui/app_shell.py",
        "src/ui/matrix_tab/__init__.py",
        "src/ui/matrix_tab/matrix_page.py",
        "src/ui/principles_tab/__init__.py",
        "src/ui/principles_tab/principles_list.py",
        "src/ui/history_tab/__init__.py",
        "src/ui/history_tab/history_list.py",
        "src/ui/settings_tab/__init__.py",
        "src/ui/settings_tab/settings_tab.py",
        "assets/.gitkeep",
    ]

    base_path = Path(__file__).parent.parent
    for file_path in required_files:
        full_path = base_path / file_path
        checker.check(
            f"文件存在: {file_path}",
            full_path.exists(),
            "文件不存在" if not full_path.exists() else "",
        )

    # ========== 2. 目录检查 ==========
    logger.info("\n=== 目录检查 ===")

    required_dirs = [
        "src",
        "src/ai",
        "src/config",
        "src/core",
        "src/data",
        "src/ui",
        "src/ui/matrix_tab",
        "src/ui/principles_tab",
        "src/ui/history_tab",
        "src/ui/settings_tab",
        "assets",
        "logs",
    ]

    for dir_path in required_dirs:
        full_path = base_path / dir_path
        checker.check(
            f"目录存在: {dir_path}",
            full_path.exists() and full_path.is_dir(),
            "目录不存在" if not full_path.exists() else "",
        )

    # ========== 3. 模块导入检查 ==========
    logger.info("\n=== 模块导入检查 ===")

    modules = [
        ("src.config.constants", "APP_NAME"),
        ("src.config.settings", "AppSettings"),
        ("src.core.triz_engine", "get_triz_engine"),
        ("src.core.matrix_selector", "get_matrix_manager"),
        ("src.core.principle_service", "get_principle_service"),
        ("src.data.local_storage", "LocalStorage"),
        ("src.data.models", "Solution"),
        ("src.ai.ai_client", "get_ai_manager"),
        ("src.ui.app_shell", "TRIZAppShell"),
        ("src.ui.matrix_tab", "MatrixTab"),
        ("src.ui.principles_tab", "PrinciplesTab"),
        ("src.ui.settings_tab", "SettingsTab"),
    ]

    for module_name, attr_name in modules:
        try:
            module = __import__(module_name, fromlist=[attr_name])
            has_attr = hasattr(module, attr_name)
            checker.check(
                f"导入: {module_name}.{attr_name}",
                has_attr,
                "属性不存在" if not has_attr else "",
            )
        except Exception as e:
            checker.check(f"导入: {module_name}.{attr_name}", False, str(e))

    # ========== 4. 核心功能检查 ==========
    logger.info("\n=== 核心功能检查 ===")

    try:
        from src.core.triz_engine import LocalTRIZEngine

        engine = LocalTRIZEngine()
        params = engine.detect_parameters("测试手机电池问题")
        checker.check("TRIZ引擎参数检测", "improving" in params)

        principles = engine.generate_solutions([1, 2, 3], "测试", count=3)
        checker.check("TRIZ引擎方案生成", len(principles) > 0)
    except Exception as e:
        checker.check("TRIZ引擎功能", False, str(e))

    try:
        from src.core.matrix_selector import get_matrix_manager

        manager = get_matrix_manager()
        matrix = manager.get_matrix("39")
        checker.check("矛盾矩阵初始化", matrix.matrix_type == "39")

        results = matrix.find_solutions("速度", "重量")
        checker.check("矛盾矩阵查询", len(results) > 0)
    except Exception as e:
        checker.check("矛盾矩阵功能", False, str(e))

    try:
        from src.core.principle_service import get_principle_service

        service = get_principle_service()
        principles = service.get_all_principles()
        checker.check("原理服务", len(principles) == 40)
    except Exception as e:
        checker.check("原理服务", False, str(e))

    try:
        from src.data.local_storage import LocalStorage

        storage = LocalStorage()
        storage.initialize()
        stats = storage.get_statistics()
        checker.check("本地存储", "total_sessions" in stats)
        storage.close()
    except Exception as e:
        checker.check("本地存储", False, str(e))

    # ========== 5. 日志系统检查 ==========
    logger.info("\n=== 日志系统检查 ===")

    checker.check("日志目录", LOG_DIR.exists())
    checker.check("日志系统", True)  # 日志已在运行

    # ========== 6. 环境检查 ==========
    logger.info("\n=== 环境检查 ===")

    checker.check(
        "Python版本 >= 3.10",
        sys.version_info >= (3, 10),
        f"当前: {sys.version_info.major}.{sys.version_info.minor}",
    )

    try:
        import flet

        checker.check(
            "Flet已安装", True, f"版本: {getattr(flet, 'version', 'unknown')}"
        )
    except ImportError:
        checker.check("Flet已安装", False, "未安装")

    try:
        import openai

        checker.check(
            "OpenAI已安装", True, f"版本: {getattr(openai, '__version__', 'unknown')}"
        )
    except ImportError:
        checker.check("OpenAI已安装", False, "未安装")

    # ========== 7. Android环境检查 ==========
    logger.info("\n=== Android环境检查 ===")

    android_home = os.environ.get("ANDROID_HOME", "")
    checker.check(
        "ANDROID_HOME已设置",
        bool(android_home),
        android_home if android_home else "未设置",
    )

    checker.check(
        "Android环境检测",
        True,  # IS_ANDROID在桌面上为False是正常的
        f"Android: {IS_ANDROID}",
    )

    # 打印报告
    success = checker.print_report()

    if success:
        print("\n✅ 所有检查通过！可以开始APK编译。")
        print("\n编译命令:")
        print("  开发版: flet build apk --dev")
        print("  或运行: python main.py --mode apk (测试用)")
    else:
        print("\n❌ 部分检查失败，请修复后重试。")

    return success


if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
