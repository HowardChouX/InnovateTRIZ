"""
分类颜色标签组件
统一分类颜色显示，避免重复定义_get_category_color
"""

import flet as ft
from ...config.constants import CATEGORY_COLORS


class CategoryBadge(ft.Container):
    """分类标签组件"""

    def __init__(self, category: str, size: int = 9):
        """
        初始化分类标签

        Args:
            category: 分类名称（物理/化学/几何/时间/系统）
            size: 字体大小
        """
        color = CATEGORY_COLORS.get(category, "#2196F3")
        super().__init__(
            content=ft.Text(category, size=size, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
            bgcolor=color,
            padding=3,
            border_radius=5,
        )


def get_category_color(category: str) -> str:
    """
    获取分类对应的颜色

    Args:
        category: 分类名称

    Returns:
        颜色的十六进制字符串
    """
    return CATEGORY_COLORS.get(category, "#2196F3")
