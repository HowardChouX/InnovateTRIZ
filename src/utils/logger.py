"""
全局日志系统 - TRIZ Android应用
用于APK测试阶段的调试和状态追踪
"""

import logging
import os
import platform
import sys
import traceback
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional


def is_android() -> bool:
    """统一Android环境检测"""
    if sys.platform == "android":
        return True
    if os.getenv("FLET_PLATFORM") == "android":
        return True
    return False


# 保持向后兼容
IS_ANDROID = is_android()

# 日志级别
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# 默认日志级别
DEFAULT_LOG_LEVEL = "INFO"

# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志文件配置
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB
BACKUP_COUNT = 3


def _get_log_dir() -> Path:
    """获取日志目录路径（兼容Android）"""
    # 优先使用 FLET_APP_STORAGE_DATA
    app_data = os.getenv("FLET_APP_STORAGE_DATA")
    if app_data:
        log_dir = Path(app_data) / "logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            return log_dir
        except Exception:
            pass

    # 桌面环境回退
    config_dir = os.getenv("XDG_CONFIG_HOME") or os.path.join(Path.home(), ".config")
    log_dir = Path(config_dir) / "triz-assistant" / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return log_dir


def _get_log_file_path() -> Path:
    """获取日志文件路径"""
    return _get_log_dir() / "triz_app.log"


# 日志文件路径
LOG_DIR = _get_log_dir()
LOG_FILE = _get_log_file_path()
TEST_LOG_FILE = LOG_DIR / "test_log.txt"


class TRIZLogger:
    """TRIZ应用全局日志器"""

    _instance: Optional["TRIZLogger"] = None
    _initialized = False

    def __new__(cls) -> "TRIZLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self._loggers: dict[str, logging.Logger] = {}
        self._main_logger: logging.Logger = None  # type: ignore[assignment]
        self._test_logger: logging.Logger = None  # type: ignore[assignment]
        self._log_buffer: list = []
        self._max_buffer_size = 1000
        self._is_debug_mode = False

        # 初始化日志系统
        self._setup_logging()

    def _setup_logging(self) -> None:
        """设置日志系统"""
        # 确保日志目录存在
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"警告: 无法创建日志目录 {LOG_DIR}: {e}")

        # 配置根日志器（使所有logger都使用统一日志系统）
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # 抑制第三方库的DEBUG日志（uvicorn/flet_web/WebSocket等）
        for noisy_logger_name in [
            "uvicorn", "uvicorn.error", "uvicorn.access",
            "flet_web", "flet_desktop", "flet_controls", "flet_transport",
        ]:
            noisy_logger = logging.getLogger(noisy_logger_name)
            noisy_logger.setLevel(logging.WARNING)
            noisy_logger.handlers.clear()
            noisy_logger.propagate = False

        # 只添加不存在的处理器，避免重复或清除其他库设置的处理器
        existing_handler_types = {type(h) for h in root_logger.handlers}

        # 控制台处理器
        if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in root_logger.handlers):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
            root_logger.addHandler(console_handler)

        # 文件处理器（带轮转）
        if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
            try:
                file_handler = RotatingFileHandler(
                    LOG_FILE,
                    encoding="utf-8",
                    mode="a",
                    maxBytes=MAX_LOG_SIZE,
                    backupCount=BACKUP_COUNT,
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
                root_logger.addHandler(file_handler)
            except Exception as e:
                print(f"警告: 无法创建文件日志处理器: {e}")

        # 测试专用处理器
        if not any(isinstance(h, logging.FileHandler) and "test_log" in getattr(h, 'baseFilename', '') for h in root_logger.handlers):
            try:
                test_handler = logging.FileHandler(
                    TEST_LOG_FILE, encoding="utf-8", mode="w"
                )
                test_handler.setLevel(logging.DEBUG)
                test_handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
                        LOG_DATE_FORMAT,
                    )
                )
                root_logger.addHandler(test_handler)
            except Exception as e:
                print(f"警告: 无法创建测试日志处理器: {e}")

        # TRIZ专用日志器
        triz_logger = logging.getLogger("TRIZ")
        triz_logger.setLevel(logging.DEBUG)

        self._main_logger = triz_logger
        self._test_logger = logging.getLogger("TRIZ.TEST")

        # 记录初始化信息
        self._log_system_info()

    def _log_system_info(self) -> None:
        """记录系统信息"""
        info = self.get_system_info()
        self._main_logger.info("=" * 60)
        self._main_logger.info("TRIZ应用日志系统初始化")
        self._main_logger.info(f"平台: {info['platform']}")
        self._main_logger.info(f"Python: {info['python_version']}")
        self._main_logger.info(f"Android环境: {info['is_android']}")
        self._main_logger.info(f"日志文件: {LOG_FILE}")
        self._main_logger.info(f"测试日志: {TEST_LOG_FILE}")
        self._main_logger.info("=" * 60)

    @staticmethod
    def get_system_info() -> dict[str, Any]:
        """获取系统信息"""
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "is_android": IS_ANDROID,
            "hostname": platform.node(),
            "timestamp": datetime.now().isoformat(),
        }

    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器"""
        if name not in self._loggers:
            logger = logging.getLogger(f"TRIZ.{name}")
            logger.setLevel(logging.DEBUG)
            self._loggers[name] = logger
        return self._loggers[name]

    def set_log_level(self, level: str) -> None:
        """设置日志级别"""
        if level.upper() in LOG_LEVELS:
            if self._main_logger:
                self._main_logger.setLevel(LOG_LEVELS[level.upper()])
            self._is_debug_mode = level.upper() == "DEBUG"

    def log_function_call(self, func_name: str, params: dict | None = None) -> None:
        """记录函数调用"""
        if params:
            param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
            self._main_logger.debug(f"[CALL] {func_name}({param_str})")
        else:
            self._main_logger.debug(f"[CALL] {func_name}()")

    def log_function_result(
        self, func_name: str, result: Any, success: bool = True
    ) -> None:
        """记录函数返回"""
        status = "OK" if success else "FAIL"
        result_preview = str(result)[:100] if result else "None"
        self._main_logger.debug(f"[{status}] {func_name} -> {result_preview}")

    def log_exception(self, func_name: str, exc: Exception) -> None:
        """记录异常"""
        exc_info = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
        self._main_logger.error(f"[EXCEPTION] {func_name}: {exc}\n{exc_info}")

    def log_event(self, event: str, data: dict | None = None) -> None:
        """记录事件"""
        if data:
            self._main_logger.info(f"[EVENT] {event} | {data}")
        else:
            self._main_logger.info(f"[EVENT] {event}")

    def log_state_change(
        self, obj_name: str, state: str, old_state: str | None = None
    ) -> None:
        """记录状态变化"""
        if old_state:
            self._main_logger.info(f"[STATE] {obj_name}: {old_state} -> {state}")
        else:
            self._main_logger.info(f"[STATE] {obj_name}: {state}")

    def log_api_call(
        self,
        api_name: str,
        params: dict,
        result: Any = None,
        error: str | None = None,
    ) -> None:
        """记录API调用"""
        if error:
            self._main_logger.error(f"[API] {api_name} FAILED: {error}")
        else:
            self._main_logger.debug(f"[API] {api_name} called with {params}")
            if result:
                self._main_logger.debug(
                    f"[API] {api_name} returned: {str(result)[:100]}"
                )

    def log_test_result(self, test_name: str, passed: bool, message: str = "") -> None:
        """记录测试结果"""
        status = "PASS" if passed else "FAIL"
        self._test_logger.info(f"[{status}] {test_name}: {message}")

    def get_recent_logs(self, count: int = 100) -> list[str]:
        """获取最近的日志"""
        return self._log_buffer[-count:]

    def clear_logs(self) -> None:
        """清除日志文件"""
        for handler in self._main_logger.handlers if self._main_logger else []:
            handler.close()
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        if TEST_LOG_FILE.exists():
            TEST_LOG_FILE.unlink()


# 全局日志器实例
_triz_logger: TRIZLogger | None = None


def get_logger(name: str = "APP") -> logging.Logger:
    """获取TRIZ日志器的便捷函数"""
    global _triz_logger
    if _triz_logger is None:
        _triz_logger = TRIZLogger()
    return _triz_logger.get_logger(name)


def get_triz_logger() -> TRIZLogger:
    """获取TRIZLogger实例"""
    global _triz_logger
    if _triz_logger is None:
        _triz_logger = TRIZLogger()
    return _triz_logger


def log_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """函数调用日志装饰器"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = get_logger(func.__module__)
        func_name = f"{func.__module__}.{func.__name__}"
        logger.debug(
            f"[CALL] {func_name}(args={len(args)}, kwargs={list(kwargs.keys()) if kwargs else None})"
        )
        try:
            result = func(*args, **kwargs)
            logger.debug(
                f"[RETURN] {func_name} -> {str(result)[:50] if result else 'None'}"
            )
            return result
        except Exception as e:
            logger.error(f"[EXCEPTION] {func_name}: {e}")
            raise

    return wrapper


def log_async_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """异步函数调用日志装饰器"""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = get_logger(func.__module__)
        func_name = f"{func.__module__}.{func.__name__}"
        logger.debug(
            f"[CALL] {func_name}(args={len(args)}, kwargs={list(kwargs.keys()) if kwargs else None})"
        )
        try:
            result = await func(*args, **kwargs)
            logger.debug(
                f"[RETURN] {func_name} -> {str(result)[:50] if result else 'None'}"
            )
            return result
        except Exception as e:
            logger.error(f"[EXCEPTION] {func_name}: {e}")
            raise

    return wrapper


# 便捷日志函数
def log_info(message: str, **kwargs: Any) -> None:
    """记录INFO级别日志"""
    get_logger("APP").info(message, **kwargs)


def log_debug(message: str, **kwargs: Any) -> None:
    """记录DEBUG级别日志"""
    get_logger("APP").debug(message, **kwargs)


def log_warning(message: str, **kwargs: Any) -> None:
    """记录WARNING级别日志"""
    get_logger("APP").warning(message, **kwargs)


def log_error(message: str, **kwargs: Any) -> None:
    """记录ERROR级别日志"""
    get_logger("APP").error(message, **kwargs)


# 导出
__all__ = [
    "TRIZLogger",
    "get_logger",
    "get_triz_logger",
    "log_call",
    "log_async_call",
    "log_info",
    "log_debug",
    "log_warning",
    "log_error",
    "IS_ANDROID",
    "LOG_FILE",
    "TEST_LOG_FILE",
    "LOG_DIR",
]
