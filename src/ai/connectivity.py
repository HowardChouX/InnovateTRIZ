"""
AI联通性检测模块
在应用启动和设置保存后检测AI API连接状态
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectivityStatus(Enum):
    """联通状态枚举"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class ConnectivityResult:
    """联通性检测结果"""
    status: ConnectivityStatus
    message: str
    latency_ms: Optional[float] = None
    provider: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self.status == ConnectivityStatus.CONNECTED

    def to_notification_text(self) -> str:
        """转换为通知文本"""
        if self.is_connected:
            return f"✅ AI已连接 ({self.provider})"
        else:
            return f"❌ AI连接失败: {self.message}"


class AIConnectivityDetector:
    """AI联通性检测器"""

    def __init__(self, timeout: float = 10.0):
        """
        初始化检测器

        Args:
            timeout: 超时时间（秒）
        """
        self.timeout = timeout

    async def check_connectivity(self, ai_manager) -> ConnectivityResult:
        """
        检测AI联通性

        Args:
            ai_manager: AIManager实例

        Returns:
            联通性检测结果
        """
        from src.ai.ai_client import get_ai_manager

        # 如果没有传入ai_manager，获取全局实例
        if ai_manager is None:
            ai_manager = get_ai_manager()

        # 检查AI是否启用
        if not ai_manager.is_enabled():
            return ConnectivityResult(
                status=ConnectivityStatus.DISCONNECTED,
                message="AI未启用（无API密钥）"
            )

        provider = ai_manager.config.get("provider", "unknown")

        try:
            # 使用超时进行连接测试
            client = ai_manager.get_client()
            if client is None:
                return ConnectivityResult(
                    status=ConnectivityStatus.DISCONNECTED,
                    message="无法获取AI客户端",
                    provider=provider
                )

            # 测试连接（带超时）
            import time
            start_time = time.time()

            result = await asyncio.wait_for(
                client.test_connection(),
                timeout=self.timeout
            )

            latency_ms = (time.time() - start_time) * 1000

            if result:
                logger.info(f"AI联通性检测成功: {provider}, 延迟: {latency_ms:.0f}ms")
                return ConnectivityResult(
                    status=ConnectivityStatus.CONNECTED,
                    message="连接成功",
                    latency_ms=latency_ms,
                    provider=provider
                )
            else:
                logger.warning(f"AI联通性检测失败: {provider}")
                return ConnectivityResult(
                    status=ConnectivityStatus.DISCONNECTED,
                    message="AI响应异常",
                    provider=provider
                )

        except asyncio.TimeoutError:
            logger.warning(f"AI联通性检测超时: {provider}")
            return ConnectivityResult(
                status=ConnectivityStatus.TIMEOUT,
                message="连接超时",
                provider=provider
            )

        except Exception as e:
            logger.error(f"AI联通性检测错误: {provider}, {e}")
            return ConnectivityResult(
                status=ConnectivityStatus.ERROR,
                message=str(e),
                provider=provider
            )

    def check_connectivity_sync(self, ai_manager=None) -> ConnectivityResult:
        """
        同步检测AI联通性（适用于非async上下文）

        Args:
            ai_manager: AIManager实例

        Returns:
            联通性检测结果
        """
        try:
            # 先检查AI是否启用（快速失败路径）
            if ai_manager is None:
                from src.ai.ai_client import get_ai_manager
                ai_manager = get_ai_manager()

            if not ai_manager.is_enabled():
                return ConnectivityResult(
                    status=ConnectivityStatus.DISCONNECTED,
                    message="AI未启用（无API密钥）"
                )

            # 使用线程池在后台运行异步检查
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    asyncio.run,
                    self.check_connectivity(ai_manager)
                )
                return future.result(timeout=self.timeout + 5)

        except Exception as e:
            logger.error(f"同步AI联通性检测错误: {e}")
            return ConnectivityResult(
                status=ConnectivityStatus.ERROR,
                message=str(e)
            )


# 全局检测器实例
_connectivity_detector: Optional[AIConnectivityDetector] = None


def get_connectivity_detector() -> AIConnectivityDetector:
    """获取全局联通性检测器"""
    global _connectivity_detector
    if _connectivity_detector is None:
        _connectivity_detector = AIConnectivityDetector()
    return _connectivity_detector


async def check_ai_connectivity() -> ConnectivityResult:
    """
    快捷函数：检测AI联通性

    Returns:
        联通性检测结果
    """
    detector = get_connectivity_detector()
    from src.ai.ai_client import get_ai_manager
    ai_manager = get_ai_manager()
    return await detector.check_connectivity(ai_manager)


def check_ai_connectivity_sync() -> ConnectivityResult:
    """
    快捷函数：同步检测AI联通性

    Returns:
        联通性检测结果
    """
    detector = get_connectivity_detector()
    return detector.check_connectivity_sync()
