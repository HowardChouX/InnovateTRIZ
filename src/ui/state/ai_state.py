"""
AI状态管理器（订阅-发布模式）
替代手动设置 matrix_tab._settings_tab 的方式
"""

from collections.abc import Callable
from typing import Optional


class AIStateManager:
    """AI状态管理器（单例）"""

    _instance: Optional["AIStateManager"] = None

    def __init__(self) -> None:
        self._is_enabled: bool = False
        self._is_connected: bool = False
        self._subscribers: list[Callable[[bool, bool], None]] = []

    @classmethod
    def get_instance(cls) -> "AIStateManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, callback: Callable[[bool, bool], None]) -> None:
        """
        订阅AI状态变化

        Args:
            callback: 回调函数，签名为 (is_enabled: bool, is_connected: bool) -> None
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[bool, bool], None]) -> None:
        """取消订阅"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def update_status(self, is_enabled: bool, is_connected: bool) -> None:
        """
        更新AI状态并通知所有订阅者

        Args:
            is_enabled: AI是否启用
            is_connected: AI是否已连接
        """
        self._is_enabled = is_enabled
        self._is_connected = is_connected
        self._notify_subscribers()

    def _notify_subscribers(self) -> None:
        """通知所有订阅者"""
        for callback in self._subscribers:
            try:
                callback(self._is_enabled, self._is_connected)
            except Exception:
                pass

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    @property
    def is_connected(self) -> bool:
        return self._is_connected


# 全局访问函数
def get_ai_state_manager() -> AIStateManager:
    return AIStateManager.get_instance()
