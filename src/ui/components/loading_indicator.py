"""
加载指示器组件
统一加载状态显示
"""

import flet as ft


class LoadingIndicator(ft.ProgressBar):
    """统一的加载指示器"""

    def __init__(self, visible: bool = False, width: int = 200):
        super().__init__(
            visible=visible,
            width=width,
        )
