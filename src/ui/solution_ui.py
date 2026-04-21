"""
解决方案展示模块
提供解决方案列表和详情展示
"""

import flet as ft
import logging
from typing import Optional, Callable, List, Dict, Sequence

from ..data.models import Solution
from ..config.constants import (
    COLORS,
    PRINCIPLE_CATEGORIES
)

logger = logging.getLogger(__name__)


class SolutionListView:
    """解决方案展示类"""

    def __init__(
        self,
        page: ft.Page,
        on_back: Optional[Callable] = None
    ):
        self.page = page
        self.on_back = on_back
        self.solutions: List[Solution] = []
        self.categorized_solutions: Dict[str, List[Solution]] = {}

    def show(
        self,
        solutions: List[Solution],
        problem: str,
        improving_param: Optional[str] = None,
        worsening_param: Optional[str] = None,
        on_back: Optional[Callable] = None
    ):
        """
        显示解决方案列表

        Args:
            solutions: 解决方案列表
            problem: 问题描述
            improving_param: 改善参数
            worsening_param: 恶化参数
            on_back: 返回回调
        """
        self.solutions = solutions
        if on_back:
            self.on_back = on_back

        # 按原理分类
        self.categorized_solutions = self._categorize_by_principle(solutions)

        # 构建UI
        self._build_ui(problem, improving_param, worsening_param)

    def _categorize_by_principle(self, solutions: List[Solution]) -> Dict[str, List[Solution]]:
        """按原理分类解决方案"""
        categorized = {}

        for category in PRINCIPLE_CATEGORIES.keys():
            categorized[category] = []

        categorized["其他"] = []

        for solution in solutions:
            placed = False
            for category, principle_ids in PRINCIPLE_CATEGORIES.items():
                if solution.principle_id in principle_ids:
                    categorized[category].append(solution)
                    placed = True
                    break

            if not placed:
                categorized["其他"].append(solution)

        return {k: v for k, v in categorized.items() if v}

    def _build_ui(
        self,
        problem: str,
        improving_param: Optional[str],
        worsening_param: Optional[str]
    ):
        """构建UI"""
        self.page.clean()

        # 顶部导航
        top_bar = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.icons.Icons.ARROW_BACK,
                    on_click=self._on_back_click
                ),
                ft.Text("分析结果", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.icons.Icons.HOME,
                    on_click=self._on_home_click,
                    tooltip="返回主页"
                )
            ],
            alignment=ft.MainAxisAlignment.START
        )

        # 问题摘要卡片
        problem_card = self._create_problem_card(problem, improving_param, worsening_param)

        # 统计信息
        stats_row = self._create_stats_row()

        # 解决方案列表
        solutions_container = ft.ListView(
            controls=list(self._create_solution_cards()),
            expand=True,
            spacing=15,
            padding=10
        )

        # 组装页面 - 合并为一次添加，减少UI刷新
        self.page.add(
            top_bar,
            ft.Divider(),
            problem_card,
            stats_row,
            ft.Divider(),
            solutions_container
        )

    def _create_problem_card(
        self,
        problem: str,
        improving_param: Optional[str],
        worsening_param: Optional[str]
    ) -> ft.Card:
        """创建问题摘要卡片"""
        param_text = ""
        if improving_param or worsening_param:
            param_text = f"改善: {improving_param or '自动'} → 恶化: {worsening_param or '自动'}"

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.icons.Icons.LIGHTBULB, color=COLORS["accent"]),
                                ft.Text("问题摘要", size=16, weight=ft.FontWeight.BOLD)
                            ],
                            spacing=10
                        ),
                        ft.Container(
                            content=ft.Text(problem, size=14),
                            padding=ft.padding.only(top=5, bottom=10)
                        ),
                        ft.Divider(),
                        ft.Row(
                            controls=[
                                ft.Text(param_text, size=12, color=ft.Colors.GREY_600),
                                ft.Container(expand=True),
                                ft.Text(
                                    f"生成 {len(self.solutions)} 个方案",
                                    size=12,
                                    color=COLORS["primary"],
                                    weight=ft.FontWeight.BOLD
                                )
                            ]
                        )
                    ],
                    spacing=5
                ),
                padding=15
            ),
            elevation=3
        )

    def _create_stats_row(self) -> ft.Container:
        """创建统计信息行"""
        # 分类统计
        categories = list(self.categorized_solutions.keys())
        total = len(self.solutions)

        # 平均置信度
        avg_confidence = 0.0
        if self.solutions:
            avg_confidence = sum(s.confidence for s in self.solutions) / total

        # AI生成数量
        ai_count = sum(1 for s in self.solutions if s.is_ai_generated)

        stat_cards: list[ft.Container] = [
            self._create_stat_item("总方案数", str(total), ft.icons.Icons.LIST),
            self._create_stat_item("平均置信度", f"{avg_confidence:.1%}", ft.icons.Icons.ANALYTICS),
            self._create_stat_item("分类数", str(len(categories)), ft.icons.Icons.CATEGORY),
        ]

        if ai_count > 0:
            stat_cards.append(
                self._create_stat_item("AI生成", str(ai_count), ft.icons.Icons.AUTO_AWESOME)
            )

        return ft.Container(
            content=ft.Row(
                controls=list(stat_cards),
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                spacing=10
            ),
            padding=10
        )

    def _create_stat_item(self, label: str, value: str, icon: ft.IconData) -> ft.Container:
        """创建统计项"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icon, color=COLORS["primary"], size=20),
                    ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ft.Text(label, size=10, color=ft.Colors.GREY)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2
            ),
            padding=10,
            border_radius=10,
            bgcolor=COLORS["surface"]
        )

    def _create_solution_cards(self) -> Sequence[ft.Container]:
        """创建解决方案卡片列表"""
        cards = []

        for category, solutions in self.categorized_solutions.items():
            if not solutions:
                continue

            # 分类标题
            category_header = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(self._get_category_icon(category), color=COLORS["primary"]),
                        ft.Text(
                            f"{category}类原理",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=COLORS["primary"]
                        ),
                        ft.Container(
                            content=ft.Text(
                                f"({len(solutions)}个)",
                                size=12,
                                color=ft.Colors.GREY
                            )
                        )
                    ],
                    spacing=10
                ),
                padding=ft.padding.only(top=10, bottom=5)
            )
            cards.append(category_header)

            # 该分类下的解决方案卡片
            for solution in solutions:
                card = self._create_solution_card(solution)
                cards.append(card)

        return cards

    def _get_category_icon(self, category: str) -> ft.IconData:
        """获取分类图标"""
        icons = {
            "物理": ft.icons.Icons.SCIENCE,
            "化学": ft.icons.Icons.SCIENCE,
            "几何": ft.icons.Icons.STRAIGHTEN,
            "时间": ft.icons.Icons.SCHEDULE,
            "系统": ft.icons.Icons.SETTINGS_SYSTEM_DAYDREAM,
            "其他": ft.icons.Icons.MORE_HORIZ
        }
        return icons.get(category, ft.icons.Icons.LIGHTBULB)

    def _create_solution_card(self, solution: Solution) -> ft.Card:
        """创建解决方案卡片"""
        # 置信度颜色
        confidence = solution.confidence
        if confidence >= 0.8:
            conf_color = COLORS["success"]
        elif confidence >= 0.6:
            conf_color = COLORS["warning"]
        else:
            conf_color = COLORS["error"]

        # 置信度文本
        conf_text = f"{confidence:.0%}"

        # 原理信息
        # principle_text = f"原理{solution.principle_id}: {solution.principle_name}"  # noqa: ERA001

        # 示例列表
        examples_text = ""
        if solution.examples:
            examples_text = "应用示例:\n" + "\n".join(f"• {ex}" for ex in solution.examples[:3])

        card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        # 顶部行：原理编号和置信度
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(
                                        f"#{solution.principle_id}",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.WHITE
                                    ),
                                    padding=8,
                                    border_radius=8,
                                    bgcolor=COLORS["primary"]
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        solution.principle_name,
                                        size=14,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    expand=True
                                ),
                                ft.Container(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(ft.icons.Icons.VERIFIED, color=conf_color, size=16),
                                            ft.Text(conf_text, size=12, color=conf_color)
                                        ],
                                        spacing=2
                                    ),
                                    padding=5,
                                    border_radius=5,
                                    bgcolor=conf_color + "20"
                                )
                            ],
                            spacing=10,
                            alignment=ft.MainAxisAlignment.START
                        ),

                        ft.Divider(),

                        # 方案描述
                        ft.Container(
                            content=ft.Text(
                                solution.description,
                                size=13,
                                color=ft.Colors.GREY_800
                            ),
                            padding=ft.padding.only(bottom=10)
                        ),

                        # AI标签
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(
                                        "🤖 AI生成" if solution.is_ai_generated else "📦 本地生成",
                                        size=10,
                                        color=ft.Colors.GREY
                                    ),
                                    padding=3
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        solution.category,
                                        size=10,
                                        color=COLORS["primary"]
                                    ),
                                    padding=3
                                )
                            ],
                            spacing=5
                        ),

                        # 应用示例（如果有）
                        ft.Container(
                            content=ft.Text(
                                examples_text,
                                size=11,
                                color=ft.Colors.GREY_600,
                                italic=True
                            ),
                            padding=ft.padding.only(top=10),
                            visible=bool(examples_text)
                        )
                    ],
                    spacing=5
                ),
                padding=15
            ),
            elevation=2
        )

        return card

    def _on_back_click(self, e=None):
        """返回按钮点击"""
        if self.on_back:
            self.on_back(e)

    def _on_home_click(self, e=None):
        """主页按钮点击"""
        if self.on_back:
            self.on_back(e)
