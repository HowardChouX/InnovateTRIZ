"""
发明原理卡片组件
统一原理展示卡片
"""

from collections.abc import Callable

import flet as ft

from .category_badge import CategoryBadge, get_category_color


class PrincipleCard(ft.Container):
    """发明原理卡片组件"""

    def __init__(
        self,
        principle_id: int,
        name: str,
        definition: str,
        category: str = "物理",
        on_click: Callable | None = None,
    ):
        """
        初始化原理卡片

        Args:
            principle_id: 原理编号
            name: 原理名称
            definition: 原理定义
            category: 分类
            on_click: 点击回调
        """
        self.principle_id = principle_id
        self.name = name
        self.definition = definition
        self.category = category
        self.on_click_handler = on_click

        # 截断过长的定义
        display_def = definition[:60] + "..." if len(definition) > 60 else definition

        super().__init__(
            content=self._build_content(display_def),
            padding=12,
            border_radius=8,
            bgcolor=ft.Colors.GREY_100,
            on_click=self._handle_click,
        )

    def _build_content(self, display_def: str) -> ft.Column:
        """构建卡片内容"""
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                f"#{self.principle_id}",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                            ),
                            padding=6,
                            border_radius=6,
                            bgcolor=get_category_color(self.category),
                        ),
                        ft.Text(
                            self.name, size=14, weight=ft.FontWeight.BOLD, expand=True
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(display_def, size=11, color=ft.Colors.GREY_700),
                ft.Row(
                    controls=[
                        CategoryBadge(category=self.category),
                        ft.Container(expand=True),
                        ft.Icon(
                            ft.icons.Icons.ARROW_FORWARD,
                            size=16,
                            color=ft.Colors.GREY_600,
                        ),
                    ],
                ),
            ],
            spacing=6,
        )

    def _handle_click(self) -> None:
        """处理点击事件"""
        if self.on_click_handler:
            self.on_click_handler(self.principle_id)
