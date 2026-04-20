"""
全局应用状态管理
"""

from typing import Optional


class AppState:
    """全局应用状态（单例）"""

    _instance: Optional["AppState"] = None

    def __init__(self):
        self.current_tab: str = "matrix"
        self.storage: Optional[object] = None
        self.settings: Optional[object] = None

    @classmethod
    def get_instance(cls) -> "AppState":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# 全局访问函数
def get_app_state() -> AppState:
    return AppState.get_instance()
