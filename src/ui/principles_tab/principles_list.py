"""
发明原理列表和详情页面
提供40发明原理的浏览和详情查看
"""

import logging
from collections.abc import Callable

import flet as ft

from ...config.constants import CATEGORY_COLORS, COLORS, PRINCIPLE_CATEGORIES
from ...core.principle_service import get_principle_service
from ...data.models import InventivePrinciple
from ..app_shell import TabContent

logger = logging.getLogger(__name__)


class PrinciplesTab(TabContent):
    """发明原理Tab"""

    def __init__(self, page: ft.Page, on_principle_detail: Callable | None = None):
        """
        初始化发明原理Tab

        Args:
            page: Flet页面对象
            on_principle_detail: 查看原理详情的回调
        """
        self._page = page
        self.on_principle_detail = on_principle_detail
        self._principle_service = get_principle_service()

        # 状态
        self.selected_category = "全部"
        self.search_query = ""
        self._filtered_principles: list[InventivePrinciple] = []

        # UI组件引用
        self.principles_grid: ft.GridView | None = None
        self.category_chips: ft.Row | None = None
        self._ui_built: bool = False  # UI是否已构建

        super().__init__("principles")

    def on_show(self) -> None:
        """当Tab显示时调用"""
        try:
            if not self._ui_built:
                self._build_ui()
                self._ui_built = True
            self._apply_filters()
        except Exception as e:
            logger.error(f"PrinciplesTab on_show 错误: {e}", exc_info=True)

    def _build_ui(self) -> None:
        """构建UI"""
        self.controls.clear()

        # 标题
        title = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.Icons.LIGHTBULB, color=COLORS["primary"], size=28),
                    ft.Text("40发明原理", size=20, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=15,
        )

        # 分类筛选
        categories = ["全部"] + list(PRINCIPLE_CATEGORIES.keys())
        self.category_chips = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(c, size=13, weight=ft.FontWeight.W_500),
                    padding=ft.Padding.symmetric(vertical=8, horizontal=14),
                    border_radius=16,
                    border=ft.Border.all(1.5, ft.Colors.GREY_400),
                    bgcolor=(
                        COLORS["primary"]
                        if c == self.selected_category
                        else ft.Colors.GREY_100
                    ),
                    on_click=lambda _, cat=c: self._on_category_selected(cat),
                )
                for c in categories
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

        filter_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("分类筛选", size=14, weight=ft.FontWeight.BOLD),
                    self.category_chips,
                ],
                spacing=5,
            ),
            padding=15,
        )

        # 原理网格
        self.principles_grid = ft.GridView(
            expand=True, runs_count=2, spacing=10, child_aspect_ratio=1.8, padding=10
        )

        # 组装
        self.controls.extend(
            [title, ft.Divider(), filter_section, ft.Divider(), self.principles_grid]
        )

    def _on_category_selected(self, category: str) -> None:
        """分类选择"""
        self.selected_category = category

        # 更新按钮状态
        if not self.category_chips:
            return
        for container in self.category_chips.controls:
            if isinstance(container, ft.Container) and isinstance(
                container.content, ft.Text
            ):
                text = container.content.value
                is_selected = text == category
                container.bgcolor = (
                    COLORS["primary"] if is_selected else ft.Colors.GREY_100
                )
                container.content.color = (
                    ft.Colors.WHITE if is_selected else ft.Colors.BLACK
                )

        self._apply_filters()
        self._page.update()

    def _apply_filters(self) -> None:
        """应用筛选"""
        all_principles = self._principle_service.get_all_principles()

        # 分类筛选
        if self.selected_category == "全部":
            filtered = all_principles
        else:
            filtered = [
                p for p in all_principles if p.category == self.selected_category
            ]

        # 搜索筛选
        if self.search_query:
            query = self.search_query.lower()
            filtered = [
                p
                for p in filtered
                if query in p.name.lower() or query in p.definition.lower()
            ]

        self._filtered_principles = filtered
        self._update_grid()

    def _update_grid(self) -> None:
        """更新原理网格"""
        if not self.principles_grid:
            return

        self.principles_grid.controls.clear()

        for principle in self._filtered_principles:
            card = self._create_principle_tile(principle)
            self.principles_grid.controls.append(card)

        self._page.update()

    def _create_principle_tile(self, principle: InventivePrinciple) -> ft.Container:
        """创建原理卡片"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    f"#{principle.id}",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                                padding=ft.Padding.all(6),
                                border_radius=6,
                                bgcolor=self._get_category_color(principle.category),
                            ),
                            ft.Text(
                                principle.name,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                expand=True,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Container(height=5),
                    ft.Text(
                        (
                            principle.definition[:50] + "..."
                            if len(principle.definition) > 50
                            else principle.definition
                        ),
                        size=11,
                        color=ft.Colors.GREY_600,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Container(height=5),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    principle.category, size=9, color=COLORS["primary"]
                                ),
                                padding=3,
                            ),
                            ft.Container(expand=True),
                            ft.Icon(
                                ft.icons.Icons.CHEVRON_RIGHT,
                                size=16,
                                color=ft.Colors.GREY,
                            ),
                        ]
                    ),
                ],
                spacing=3,
            ),
            padding=12,
            border_radius=8,
            bgcolor=ft.Colors.GREY_100,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            on_click=lambda _, p=principle: self._on_principle_click(p),
        )

    def _get_category_color(self, category: str) -> str:
        """获取分类颜色"""
        return CATEGORY_COLORS.get(category, "#2196F3")

    def _on_principle_click(self, principle: InventivePrinciple) -> None:
        """原理点击"""
        if self.on_principle_detail:
            self.on_principle_detail(principle)
        else:
            # 默认显示详情弹窗
            self._show_principle_detail_dialog(principle)

    def _show_principle_detail_dialog(self, principle: InventivePrinciple) -> None:
        """显示原理详情弹窗"""
        dialog = ft.AlertDialog(
            open=True,
            title=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            f"#{principle.id}",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        padding=8,
                        border_radius=8,
                        bgcolor=COLORS["primary"],
                    ),
                    ft.Text(principle.name, size=18, weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        # 核心定义
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        "核心定义",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=COLORS["primary"],
                                    ),
                                    ft.Text(principle.definition, size=13),
                                ],
                                spacing=5,
                            ),
                            padding=10,
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=8,
                        ),
                        # 分类标签
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Text(
                                        "分类:", size=12, weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            principle.category,
                                            size=11,
                                            color=ft.Colors.WHITE,
                                        ),
                                        padding=5,
                                        border_radius=5,
                                        bgcolor=self._get_category_color(
                                            principle.category
                                        ),
                                    ),
                                    ft.Container(expand=True),
                                    ft.Text(
                                        f"标签: {', '.join(principle.tags)}",
                                        size=11,
                                        color=ft.Colors.GREY,
                                    ),
                                ],
                                spacing=10,
                            ),
                            padding=10,
                        ),
                        ft.Divider(),
                        # 示例
                        ft.Text("示例", size=14, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Column(
                                controls=(
                                    [
                                        ft.Text(f"• {ex}", size=12)
                                        for ex in principle.examples
                                    ]
                                    if principle.examples
                                    else [
                                        ft.Text("暂无", size=12, color=ft.Colors.GREY)
                                    ]
                                ),
                                spacing=3,
                            ),
                            padding=5,
                        ),
                        ft.Divider(),
                        # 应用案例
                        ft.Text("应用案例", size=14, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Column(
                                controls=(
                                    [
                                        ft.Text(f"• {uc}", size=12)
                                        for uc in principle.use_cases
                                    ]
                                    if principle.use_cases
                                    else [
                                        ft.Text("暂无", size=12, color=ft.Colors.GREY)
                                    ]
                                ),
                                spacing=3,
                            ),
                            padding=5,
                        ),
                        ft.Divider(),
                        # 详细说明
                        ft.Text("详细说明", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text(principle.explanation, size=12),
                        ft.Divider(),
                        # 实施步骤
                        ft.Text("实施步骤", size=14, weight=ft.FontWeight.BOLD),
                        ft.Column(
                            controls=(
                                [
                                    ft.Text(step, size=12)
                                    for step in principle.implementation_steps
                                ]
                                if principle.implementation_steps
                                else [ft.Text("暂无", size=12, color=ft.Colors.GREY)]
                            ),
                            spacing=3,
                        ),
                        ft.Divider(),
                        # 应用效益
                        ft.Text("应用效益", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text(principle.benefits, size=12),
                    ],
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=400,
                height=500,
                padding=10,
            ),
            actions=[ft.TextButton("关闭", on_click=lambda _: self._close_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.show_dialog(dialog)

    def _close_dialog(self) -> None:
        """关闭弹窗"""
        self._page.pop_dialog()
