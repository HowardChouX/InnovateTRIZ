"""
参数选择器模块
提供39个工程参数的可视化选择界面
"""

import logging
from collections.abc import Callable

import flet as ft

from ..config.constants import COLORS

logger = logging.getLogger(__name__)


def _hex_to_flet_color(hex_color: str, alpha: int = 255) -> str:
    """将 #RRGGBB 格式的 hex 颜色转换为 Flet 颜色（带透明度）

    Args:
        hex_color: 颜色值如 "#2196F3"
        alpha: 透明度 0-255，默认为 255（不透明）

    Returns:
        Flet 颜色字符串，格式为 #AARRGGBB
    """
    if hex_color.startswith("#"):
        hex_color = hex_color[1:]
    return f"#{alpha:02X}{hex_color}"


class ParameterPicker:
    """参数选择器类"""

    # 参数分类
    PARAM_CATEGORIES = {
        "几何参数": [
            "移动物体的重量",
            "静止物体的重量",
            "移动物体的长度",
            "静止物体的长度",
            "移动物体的面积",
            "静止物体的面积",
            "移动物体的体积",
            "静止物体的体积",
        ],
        "力学参数": [
            "速度",
            "力",
            "张力/压力",
            "形状",
            "物体的稳定性",
            "强度",
            "移动物体的持久性",
            "静止物体的持久性",
            "温度",
            "亮度",
        ],
        "能量参数": ["移动物体用的能源", "非移动物体用的能源", "功率", "能源的浪费"],
        "物质参数": ["物质的浪费", "信息的流失", "时间的浪费", "物质的总量", "可靠性"],
        "测量参数": ["测量的准度", "制造的准度"],
        "有害因素参数": ["作用于物体的有害因素", "有害的副作用"],
        "制造参数": [
            "制造性",
            "使用的便利性",
            "修复性",
            "适应性",
            "设备的复杂性",
            "控制的复杂性",
            "自动化程度",
            "产能/生产力",
        ],
    }

    def __init__(
        self,
        page: ft.Page,
        param_type: str,
        current_values: list[str] | None = None,
        on_selected: Callable | None = None,
        multi_select: bool = True,
    ):
        """
        初始化参数选择器

        Args:
            page: Flet页面对象
            param_type: 参数类型 ("improving" 或 "worsening")
            current_values: 当前已选值列表
            on_selected: 选择后的回调函数
            multi_select: 是否支持多选
        """
        self.page = page
        self.param_type = param_type
        self.current_values = list(current_values) if current_values else []
        self.on_selected = on_selected
        self.multi_select = multi_select

        self.dialog: ft.AlertDialog | None = None
        self.search_field: ft.TextField | None = None
        self.content_column: ft.Column | None = None
        self.filtered_params: dict[str, list[str]] = self.PARAM_CATEGORIES.copy()

        logger.info(
            f"ParameterPicker初始化: type={param_type}, current={current_values}, multi={multi_select}"
        )

    def show(self) -> None:
        """显示参数选择弹窗"""
        self._create_dialog()
        assert self.dialog is not None
        self.page.show_dialog(self.dialog)

    def _create_dialog(self) -> None:
        """创建弹窗"""
        # 标题
        title = "选择改善参数" if self.param_type == "improving" else "选择恶化参数"
        title_icon = (
            ft.icons.Icons.ARROW_UPWARD
            if self.param_type == "improving"
            else ft.icons.Icons.ARROW_DOWNWARD
        )

        # 搜索框
        self.search_field = ft.TextField(
            hint_text="搜索参数...",
            prefix_icon=ft.icons.Icons.SEARCH,
            on_change=self._on_search_input,  # type: ignore[reportArgumentType]
        )

        # 清除按钮
        clear_btn = ft.TextButton("清除选择", on_click=self._on_clear_click)

        # 内容区域
        self.content_column = ft.Column(
            controls=[], scroll=ft.ScrollMode.AUTO, spacing=10, expand=1
        )

        # 初始化参数列表
        self._update_param_list()

        # 弹窗内容
        dialog_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(title_icon, color=COLORS["primary"]),
                            ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            clear_btn,
                        ]
                    ),
                    ft.Divider(),
                    self.search_field,
                    self.content_column,
                ],
                spacing=15,
            ),
            width=400,
            height=500,
        )

        self.dialog = ft.AlertDialog(
            title=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.Icons.SETTINGS, color=COLORS["primary"]),
                        ft.Text(title, weight=ft.FontWeight.BOLD),
                    ]
                ),
                padding=10,
            ),
            content=dialog_content,
            actions=[
                ft.TextButton("确认", on_click=self._on_confirm_click),
                ft.TextButton("取消", on_click=self._on_cancel_click),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _on_search_input(self, e: ft.ControlEvent) -> None:
        """搜索框输入处理（实时搜索）"""
        assert isinstance(e.control, ft.TextField)
        query = e.control.value.strip().lower()
        self._filter_params(query)
        self._update_param_list()
        self.page.update()

    def _filter_params(self, query: str) -> None:
        """过滤参数"""
        if not query:
            self.filtered_params = self.PARAM_CATEGORIES.copy()
            return

        self.filtered_params = {}
        for category, params in self.PARAM_CATEGORIES.items():
            # 使用更精确的匹配
            filtered = [p for p in params if query in p.lower()]
            if filtered:
                self.filtered_params[category] = filtered

    def _update_param_list(self) -> None:
        """更新参数列表"""
        assert self.content_column is not None
        self.content_column.controls.clear()

        for category, params in self.filtered_params.items():
            if not params:
                continue

            # 分类标题
            category_header = ft.Container(
                content=ft.Text(
                    category,
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=COLORS["primary"],
                ),
                padding=ft.Padding.only(top=12, bottom=6),
            )
            self.content_column.controls.append(category_header)

            # 参数按钮
            for param in params:
                is_selected = param in self.current_values
                btn = self._create_param_button(param, is_selected)
                self.content_column.controls.append(btn)
                # 参数按钮之间添加间距
                self.content_column.controls.append(ft.Container(height=4))

    def _create_param_button(self, param: str, is_selected: bool) -> ft.Container:
        """创建参数按钮"""
        bg_color = (
            _hex_to_flet_color(COLORS["primary"], 32)
            if is_selected
            else ft.Colors.GREY_100
        )
        border_color = COLORS["primary"] if is_selected else ft.Colors.TRANSPARENT

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        (
                            ft.icons.Icons.CHECK_BOX
                            if is_selected
                            else ft.icons.Icons.CHECK_BOX_OUTLINE_BLANK
                        ),
                        color=COLORS["primary"] if is_selected else ft.Colors.GREY,
                        size=20,
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        param,
                        size=14,
                        color=(
                            COLORS["text_primary"]
                            if is_selected
                            else ft.Colors.GREY_700
                        ),
                    ),
                ],
                spacing=10,
            ),
            padding=12,
            border_radius=8,
            bgcolor=bg_color,
            border=ft.Border.all(1, border_color),
            on_click=lambda _, p=param: self._on_param_click(p),
        )

    def _on_param_click(self, param: str) -> None:
        """参数点击处理"""
        logger.info(f"点击参数: {param}")

        if self.multi_select:
            # 多选模式：切换选中状态
            if param in self.current_values:
                self.current_values.remove(param)
            else:
                self.current_values.append(param)
            # 刷新列表显示
            self._update_param_list()
            self.page.update()
        else:
            # 单选模式：直接选中并关闭
            self.page.pop_dialog()
            if self.on_selected:
                self.on_selected(self.param_type, param)

    def _on_clear_click(self, _):  # type: ignore
        """清除选择"""
        logger.info("清除参数选择")
        self.current_values = []
        self._update_param_list()
        self.page.update()

        if self.on_selected:
            self.on_selected(self.param_type, [])

    def _on_confirm_click(self, _):  # type: ignore
        """确认按钮点击"""
        logger.info(f"确认选择: {self.current_values}")
        self.page.pop_dialog()

        if self.on_selected:
            self.on_selected(self.param_type, self.current_values)

    def _on_cancel_click(self, _):  # type: ignore
        """取消按钮点击"""
        self.page.pop_dialog()
