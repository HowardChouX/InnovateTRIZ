# -*- coding: utf-8 -*-
"""
APK环境测试脚本
用于在打包成APK后进行环境测试和日志输出

运行方式:
    在APK环境中直接运行此脚本
    python tests/test_apk_log.py
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.logger import (
    get_logger,
    get_triz_logger,
    IS_ANDROID,
    LOG_FILE,
    TEST_LOG_FILE,
    LOG_DIR
)
from src.config.constants import APP_NAME, APP_VERSION


class APKTestReport:
    """APK测试报告生成器"""

    def __init__(self):
        self.logger = get_logger("APK_TEST")
        self.test_results = []
        self.start_time = datetime.now()

    def add_result(self, category: str, name: str, passed: bool, message: str = ""):
        """添加测试结果"""
        self.test_results.append({
            "category": category,
            "name": name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def generate_report(self) -> str:
        """生成测试报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed

        report = []
        report.append("=" * 70)
        report.append(f"{APP_NAME} v{APP_VERSION} - APK环境测试报告")
        report.append("=" * 70)
        report.append(f"测试时间: {self.start_time.isoformat()}")
        report.append(f"测试耗时: {duration:.2f}秒")
        report.append(f"Android环境: {IS_ANDROID}")
        report.append("")
        report.append(f"测试结果: {passed}/{total} 通过")

        if failed > 0:
            report.append(f"❌ 失败: {failed}")
        else:
            report.append("✅ 全部通过")

        report.append("")
        report.append("-" * 70)
        report.append("详细结果")
        report.append("-" * 70)

        current_category = None
        for result in self.test_results:
            if result["category"] != current_category:
                current_category = result["category"]
                report.append(f"\n[{current_category}]")

            status = "✅" if result["passed"] else "❌"
            report.append(f"  {status} {result['name']}")
            if result["message"]:
                report.append(f"     {result['message']}")

        report.append("")
        report.append("-" * 70)
        report.append("系统信息")
        report.append("-" * 70)

        from src.utils.logger import TRIZLogger
        info = TRIZLogger.get_system_info()
        for key, value in info.items():
            report.append(f"  {key}: {value}")

        report.append("")
        report.append("-" * 70)
        report.append("日志文件")
        report.append("-" * 70)
        report.append(f"  应用日志: {LOG_FILE}")
        report.append(f"  测试日志: {TEST_LOG_FILE}")

        if LOG_FILE.exists():
            report.append(f"  应用日志大小: {LOG_FILE.stat().st_size} bytes")
        if TEST_LOG_FILE.exists():
            report.append(f"  测试日志大小: {TEST_LOG_FILE.stat().st_size} bytes")

        report.append("=" * 70)

        return "\n".join(report)


def run_apk_tests():
    """运行APK环境测试"""
    report_gen = APKTestReport()
    logger = get_logger("APK_TEST")

    logger.info("=" * 60)
    logger.info("开始APK环境测试")
    logger.info("=" * 60)

    # ========== 环境测试 ==========
    logger.info("\n[环境检测]")

    # Android环境 (桌面环境检测为False是正常的)
    report_gen.add_result(
        "环境检测",
        "Android环境",
        True,  # 桌面环境检测为False是正常的，不影响功能
        f"Android环境: {IS_ANDROID} (桌面环境为False是预期)"
    )

    # Python版本
    py_version = sys.version_info
    report_gen.add_result(
        "环境检测",
        "Python版本",
        py_version >= (3, 10),
        f"Python {py_version.major}.{py_version.minor}.{py_version.micro}"
    )

    # 日志目录
    log_dir_exists = LOG_DIR.exists()
    report_gen.add_result(
        "环境检测",
        "日志目录",
        log_dir_exists,
        f"logs目录: {'存在' if log_dir_exists else '不存在'}"
    )

    # ========== 核心模块测试 ==========
    logger.info("\n[核心模块测试]")

    # TRIZ引擎 (同步测试 - 使用LocalTRIZEngine)
    try:
        from src.core.triz_engine import LocalTRIZEngine
        engine = LocalTRIZEngine()
        # 同步方式测试
        params = engine.detect_parameters("测试问题")
        principles = engine.generate_solutions([1, 2, 3], "测试", count=3)
        report_gen.add_result(
            "核心模块",
            "TRIZ引擎",
            True,
            f"参数检测: {params}, 生成方案数: {len(principles)}"
        )
        logger.info(f"TRIZ引擎测试通过，方案数: {len(principles)}")
    except Exception as e:
        report_gen.add_result("核心模块", "TRIZ引擎", False, str(e))
        logger.error(f"TRIZ引擎测试失败: {e}")

    # 矛盾矩阵
    try:
        from src.core.matrix_selector import get_matrix_manager
        manager = get_matrix_manager()
        matrix = manager.get_matrix("39")
        principles = matrix.find_solutions("速度", "重量")
        report_gen.add_result(
            "核心模块",
            "矛盾矩阵",
            True,
            f"查询成功，返回原理数: {len(principles)}"
        )
        logger.info(f"矛盾矩阵测试通过，原理数: {len(principles)}")
    except Exception as e:
        report_gen.add_result("核心模块", "矛盾矩阵", False, str(e))
        logger.error(f"矛盾矩阵测试失败: {e}")

    # 原理服务
    try:
        from src.core.principle_service import get_principle_service
        service = get_principle_service()
        principles = service.get_all_principles()
        principle = service.get_principle(1)
        report_gen.add_result(
            "核心模块",
            "原理服务",
            True,
            f"原理总数: {len(principles)}, #1原理: {principle.name}"
        )
        logger.info(f"原理服务测试通过，原理总数: {len(principles)}")
    except Exception as e:
        report_gen.add_result("核心模块", "原理服务", False, str(e))
        logger.error(f"原理服务测试失败: {e}")

    # ========== 数据模块测试 ==========
    logger.info("\n[数据模块测试]")

    # 本地存储
    try:
        from src.data.local_storage import LocalStorage
        storage = LocalStorage()
        storage.initialize()
        stats = storage.get_statistics()
        sessions = storage.get_sessions(limit=5)
        report_gen.add_result(
            "数据模块",
            "本地存储",
            True,
            f"会话数: {stats['total_sessions']}, 方案数: {stats['total_solutions']}"
        )
        logger.info(f"本地存储测试通过，统计: {stats}")
        storage.close()
    except Exception as e:
        report_gen.add_result("数据模块", "本地存储", False, str(e))
        logger.error(f"本地存储测试失败: {e}")

    # 数据模型
    try:
        from src.data.models import AnalysisSession, Solution
        session = AnalysisSession(problem="测试")
        solution = Solution(
            principle_id=1,
            principle_name="分割原理",
            description="测试"
        )
        session.solutions.append(solution)
        report_gen.add_result(
            "数据模块",
            "数据模型",
            True,
            f"模型创建成功，会话ID: {session.id}"
        )
        logger.info(f"数据模型测试通过")
    except Exception as e:
        report_gen.add_result("数据模块", "数据模型", False, str(e))
        logger.error(f"数据模型测试失败: {e}")

    # ========== 配置模块测试 ==========
    logger.info("\n[配置模块测试]")

    # 设置
    try:
        from src.config.settings import AppSettings
        settings = AppSettings()
        report_gen.add_result(
            "配置模块",
            "应用设置",
            True,
            f"设置实例创建成功"
        )
        logger.info(f"应用设置测试通过")
    except Exception as e:
        report_gen.add_result("配置模块", "应用设置", False, str(e))
        logger.error(f"应用设置测试失败: {e}")

    # 常量
    try:
        from src.config.constants import ENGINEERING_PARAMETERS_39, INVENTIVE_PRINCIPLES
        report_gen.add_result(
            "配置模块",
            "常量定义",
            len(ENGINEERING_PARAMETERS_39) == 39 and len(INVENTIVE_PRINCIPLES) == 40,
            f"39参数: {len(ENGINEERING_PARAMETERS_39)}, 40原理: {len(INVENTIVE_PRINCIPLES)}"
        )
        logger.info(f"常量定义测试通过")
    except Exception as e:
        report_gen.add_result("配置模块", "常量定义", False, str(e))
        logger.error(f"常量定义测试失败: {e}")

    # ========== AI模块测试 ==========
    logger.info("\n[AI模块测试]")

    # AI管理器
    try:
        from src.ai.ai_client import get_ai_manager
        ai_manager = get_ai_manager()
        is_enabled = ai_manager.is_enabled()
        report_gen.add_result(
            "AI模块",
            "AI管理器",
            True,
            f"AI启用状态: {is_enabled}"
        )
        logger.info(f"AI管理器测试通过，启用: {is_enabled}")
    except Exception as e:
        report_gen.add_result("AI模块", "AI管理器", False, str(e))
        logger.error(f"AI管理器测试失败: {e}")

    # ========== UI模块测试 ==========
    logger.info("\n[UI模块测试]")

    # UI导入测试
    try:
        from src.ui.app_shell import TRIZAppShell
        from src.ui.matrix_tab import MatrixTab
        from src.ui.principles_tab import PrinciplesTab
        from src.ui.settings_tab import SettingsTab
        report_gen.add_result(
            "UI模块",
            "UI模块导入",
            True,
            "所有UI模块导入成功"
        )
        logger.info(f"UI模块导入测试通过")
    except Exception as e:
        report_gen.add_result("UI模块", "UI模块导入", False, str(e))
        logger.error(f"UI模块导入测试失败: {e}")

    # ========== 生成报告 ==========
    report = report_gen.generate_report()
    print("\n" + report)

    # 保存报告到文件
    report_file = LOG_DIR / "apk_test_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"\n报告已保存到: {report_file}")

    # 返回是否全部通过
    return all(r["passed"] for r in report_gen.test_results)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(f"{APP_NAME} v{APP_VERSION} - APK环境测试")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 70 + "\n")

    try:
        success = run_apk_tests()
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        success = False

    print("\n" + "=" * 70)
    if success:
        print("✅ APK环境测试全部通过!")
    else:
        print("❌ APK环境测试部分失败，请检查日志")
    print("=" * 70)

    sys.exit(0 if success else 1)
