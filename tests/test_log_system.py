"""
TRIZ应用日志测试脚本
用于APK打包后的环境测试和日志输出

使用方法:
    python tests/test_log_system.py
    # 或在APK中运行时自动执行
"""

import os
import sys
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.logger import (
    IS_ANDROID,
    LOG_DIR,
    LOG_FILE,
    TEST_LOG_FILE,
    get_logger,
    log_debug,
    log_error,
    log_info,
    log_warning,
)


class LogTestRunner:
    """日志测试运行器"""

    def __init__(self):
        self.results = []
        self.logger = get_logger("TEST")
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0

    def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        self.test_count += 1
        self.logger.info(f"{'='*60}")
        self.logger.info(f"测试: {test_name}")
        self.logger.info(f"{'='*60}")

        try:
            result = test_func()
            if result.get("passed", False):
                self.pass_count += 1
                status = "✅ PASS"
            else:
                self.fail_count += 1
                status = "❌ FAIL"

            self.logger.info(f"结果: {status}")
            if result.get("message"):
                self.logger.info(f"详情: {result['message']}")

            self.results.append(
                {
                    "name": test_name,
                    "passed": result.get("passed", False),
                    "message": result.get("message", ""),
                }
            )

        except Exception as e:
            self.fail_count += 1
            self.logger.error(f"测试异常: {e}")
            self.results.append(
                {"name": test_name, "passed": False, "message": f"异常: {str(e)}"}
            )

    def print_summary(self):
        """打印测试摘要"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info("测试摘要")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"总计: {self.test_count}")
        self.logger.info(f"通过: {self.pass_count} ✅")
        self.logger.info(f"失败: {self.fail_count} ❌")
        self.logger.info(f"通过率: {self.pass_count/self.test_count*100:.1f}%")
        self.logger.info("\n日志文件位置:")
        self.logger.info(f"  - 应用日志: {LOG_FILE}")
        self.logger.info(f"  - 测试日志: {TEST_LOG_FILE}")


def test_logger_initialization():
    """测试日志系统初始化"""
    try:
        logger = get_logger("TEST_INIT")
        assert logger is not None
        assert isinstance(logger.name, str)
        return {"passed": True, "message": "日志系统初始化成功"}
    except Exception as e:
        return {"passed": False, "message": str(e)}


def test_log_levels():
    """测试日志级别"""
    logger = get_logger("LEVEL_TEST")
    try:
        logger.debug("DEBUG级别测试")
        logger.info("INFO级别测试")
        logger.warning("WARNING级别测试")
        logger.error("ERROR级别测试")
        return {"passed": True, "message": "所有日志级别工作正常"}
    except Exception as e:
        return {"passed": False, "message": str(e)}


def test_log_file_creation():
    """测试日志文件创建"""
    try:
        assert LOG_DIR.exists(), "日志目录不存在"
        assert LOG_DIR.is_dir(), "日志路径不是目录"
        # 写入测试日志
        test_logger = get_logger("FILE_TEST")
        test_logger.info("这是测试日志写入")
        # 检查文件是否存在
        if LOG_FILE.exists():
            size = LOG_FILE.stat().st_size
            return {"passed": True, "message": f"日志文件已创建，大小: {size} bytes"}
        else:
            return {"passed": False, "message": "日志文件未创建"}
    except Exception as e:
        return {"passed": False, "message": str(e)}


def test_system_info():
    """测试系统信息获取"""
    try:
        from src.utils.logger import TRIZLogger

        info = TRIZLogger.get_system_info()
        assert "platform" in info
        assert "python_version" in info
        assert "is_android" in info
        return {"passed": True, "message": f"系统信息: {info}"}
    except Exception as e:
        return {"passed": False, "message": str(e)}


def test_module_loggers():
    """测试各模块日志器"""
    modules = ["CORE", "UI", "AI", "DATA", "CONFIG"]
    try:
        for module in modules:
            logger = get_logger(module)
            logger.info(f"{module}模块日志器测试")
        return {"passed": True, "message": f"所有{len(modules)}个模块日志器正常"}
    except Exception as e:
        return {"passed": False, "message": str(e)}


def test_convenience_functions():
    """测试便捷日志函数"""
    try:
        log_info("INFO便捷函数测试")
        log_debug("DEBUG便捷函数测试")
        log_warning("WARNING便捷函数测试")
        log_error("ERROR便捷函数测试")
        return {"passed": True, "message": "便捷日志函数正常工作"}
    except Exception as e:
        return {"passed": False, "message": str(e)}


def test_triz_engine_logging():
    """测试TRIZ引擎日志"""
    try:
        from src.core.triz_engine import get_triz_engine

        logger = get_logger("TRIZ_ENGINE")
        engine = get_triz_engine()
        logger.info(f"TRIZ引擎实例: {type(engine).__name__}")
        return {"passed": True, "message": "TRIZ引擎日志正常"}
    except Exception as e:
        return {"passed": False, "message": str(e)}


def test_matrix_selector_logging():
    """测试矛盾矩阵日志"""
    try:
        from src.core.matrix_selector import get_matrix_manager

        logger = get_logger("MATRIX")
        manager = get_matrix_manager()
        matrix = manager.get_matrix("39")
        logger.info(f"矛盾矩阵类型: {matrix.matrix_type}")
        logger.info(f"参数数量: {len(matrix.parameters)}")
        return {"passed": True, "message": "矛盾矩阵日志正常"}
    except Exception as e:
        return {"passed": False, "message": str(e)}


def test_principle_service_logging():
    """测试原理服务日志"""
    try:
        from src.core.principle_service import get_principle_service

        logger = get_logger("PRINCIPLE")
        service = get_principle_service()
        principles = service.get_all_principles()
        logger.info(f"发明原理数量: {len(principles)}")
        return {"passed": True, "message": "原理服务日志正常"}
    except Exception as e:
        return {"passed": False, "message": str(e)}


def test_storage_logging():
    """测试存储日志"""
    try:
        from src.data.local_storage import LocalStorage

        logger = get_logger("STORAGE")
        storage = LocalStorage()
        storage.initialize()
        stats = storage.get_statistics()
        logger.info(f"存储统计: {stats}")
        storage.close()
        return {"passed": True, "message": "存储日志正常"}
    except Exception as e:
        return {"passed": False, "message": str(e)}


def test_ai_client_logging():
    """测试AI客户端日志"""
    try:
        from src.ai.ai_client import get_ai_manager

        logger = get_logger("AI_CLIENT")
        ai_manager = get_ai_manager()
        logger.info(f"AI管理器启用状态: {ai_manager.is_enabled()}")
        return {"passed": True, "message": "AI客户端日志正常"}
    except Exception as e:
        return {"passed": False, "message": str(e)}


def test_settings_logging():
    """测试设置日志"""
    try:
        from src.config.settings import AppSettings

        logger = get_logger("SETTINGS")
        settings = AppSettings()
        logger.info(f"设置实例: {type(settings).__name__}")
        return {"passed": True, "message": "设置日志正常"}
    except Exception as e:
        return {"passed": False, "message": str(e)}


def run_all_tests():
    """运行所有日志测试"""
    runner = LogTestRunner()

    # 日志系统基础测试
    runner.run_test("日志系统初始化", test_logger_initialization)
    runner.run_test("日志级别测试", test_log_levels)
    runner.run_test("日志文件创建", test_log_file_creation)
    runner.run_test("系统信息获取", test_system_info)
    runner.run_test("模块日志器", test_module_loggers)
    runner.run_test("便捷日志函数", test_convenience_functions)

    # 核心模块日志测试
    runner.run_test("TRIZ引擎日志", test_triz_engine_logging)
    runner.run_test("矛盾矩阵日志", test_matrix_selector_logging)
    runner.run_test("原理服务日志", test_principle_service_logging)
    runner.run_test("存储日志", test_storage_logging)
    runner.run_test("AI客户端日志", test_ai_client_logging)
    runner.run_test("设置日志", test_settings_logging)

    # 打印摘要
    runner.print_summary()

    return runner.fail_count == 0


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TRIZ应用日志系统测试")
    print(f"时间: {datetime.now().isoformat()}")
    print(f"平台: {platform.platform() if 'platform' in dir() else 'unknown'}")
    print(f"Android: {IS_ANDROID}")
    print("=" * 60 + "\n")

    success = run_all_tests()

    print("\n" + "=" * 60)
    if success:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败，请检查日志文件")
    print("=" * 60)

    sys.exit(0 if success else 1)
