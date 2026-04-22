"""
应用外壳模块
使用传统方式实现Tab切换，但保持页面隔离
"""

import logging
from collections.abc import Callable

import flet as ft

from ..config.constants import COLORS

logger = logging.getLogger(__name__)

# 路由常量
ROUTE_MATRIX = "matrix"
ROUTE_PRINCIPLES = "principles"
ROUTE_SETTINGS = "settings"


class TRIZAppShell:
    """
    TRIZ应用外壳管理器
    使用传统方式管理Tab切换
    """

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self._tab_registry: dict[str, ft.Container] = {}
        self._current_tab: str | None = None
        self._nav_bar: ft.NavigationBar | None = None
        self._settings_tab: object | None = None  # 存储settings_tab引用

        logger.info("TRIZAppShell初始化完成")

    def add_tab(self, tab_id: str, content: ft.Control) -> None:
        """注册Tab内容 - content是Tab实例"""
        # content 继承自 TabContent(ft.Column)，可以直接使用
        # 包装成Container便于控制显隐
        container = ft.Container(content=content, visible=False, expand=True)
        self._tab_registry[tab_id] = container
        # 存储settings_tab引用
        if tab_id == ROUTE_SETTINGS:
            self._settings_tab = content
        logger.info(f"注册Tab: {tab_id}")

    def get_settings_tab(self) -> object | None:
        """获取settings_tab实例"""
        return self._settings_tab

    def show(self) -> None:
        """显示应用外壳"""
        # 创建导航栏
        self._nav_bar = ft.NavigationBar(
            selected_index=0,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.icons.Icons.GRID_ON,
                    selected_icon=ft.icons.Icons.GRID_ON,
                    label="矛盾矩阵",
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.Icons.LIGHTBULB_OUTLINE,
                    selected_icon=ft.icons.Icons.LIGHTBULB,
                    label="发明原理",
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.Icons.SETTINGS,
                    selected_icon=ft.icons.Icons.SETTINGS,
                    label="全局设置",
                ),
            ],
            on_change=self._on_nav_change,
            bgcolor=COLORS.get("surface", "#F5F5F5"),
            indicator_color=COLORS.get("primary", "#2196F3"),
        )

        # 顶部状态栏占位（避免被Android状态栏遮挡）
        self._status_bar = ft.Container(height=38, bgcolor=COLORS.get("primary", "#2196F3"))

        # 添加顶部状态栏
        self.page.add(self._status_bar)

        # 将所有Tab添加到页面
        for container in self._tab_registry.values():
            self.page.add(container)

        # 添加导航栏到页面底部
        self.page.add(self._nav_bar)

        # 显示默认Tab
        self._switch_tab(ROUTE_MATRIX)

        logger.info("应用外壳显示完成")

    def _on_nav_change(self, _) -> None:  # type: ignore
        """导航栏切换处理"""
        index = self._nav_bar.selected_index if self._nav_bar else 0
        tab_map = {
            0: ROUTE_MATRIX,
            1: ROUTE_PRINCIPLES,
            2: ROUTE_SETTINGS,
        }
        new_tab = tab_map.get(index, ROUTE_MATRIX)
        self._switch_tab(new_tab)

    def _switch_tab(self, tab_id: str) -> None:
        """切换Tab"""
        logger.info(f"_switch_tab called with: {tab_id}")

        # 隐藏当前Tab
        if self._current_tab and self._current_tab in self._tab_registry:
            logger.info(f"Hiding current tab: {self._current_tab}")
            self._tab_registry[self._current_tab].visible = False

        # 显示新Tab
        if tab_id in self._tab_registry:
            logger.info(f"Showing tab: {tab_id}")
            self._tab_registry[tab_id].visible = True
            self._current_tab = tab_id
            logger.info(
                f"Switching to tab {tab_id}, container visible: {self._tab_registry[tab_id].visible}"
            )

            # 调用Tab的on_show方法
            container = self._tab_registry[tab_id]
            if isinstance(container.content, TabContent):
                logger.info(f"Calling on_show for {tab_id}")
                try:
                    container.content.on_show()
                    logger.info(f"on_show for {tab_id} completed")
                except Exception as e:
                    logger.error(f"on_show for {tab_id} failed: {e}", exc_info=True)

        # 更新导航栏
        if self._nav_bar:
            tab_to_index = {
                ROUTE_MATRIX: 0,
                ROUTE_PRINCIPLES: 1,
                ROUTE_SETTINGS: 2,
            }
            self._nav_bar.selected_index = tab_to_index.get(tab_id, 0)

        logger.info(f"About to call page.update() for {tab_id}")
        self.page.update()
        logger.info(f"page.update() completed for {tab_id}")
        logger.info(f"切换到Tab: {tab_id} 完成")

    def get_current_tab(self) -> str | None:
        """获取当前Tab标识"""
        return self._current_tab

    def refresh_current_tab(self) -> None:
        """刷新当前Tab内容"""
        if self._current_tab and self._current_tab in self._tab_registry:
            container = self._tab_registry[self._current_tab]
            if isinstance(container.content, TabContent):
                container.content.on_show()
            self.page.update()
            logger.info(f"刷新Tab: {self._current_tab}")


# 为了向后兼容，保留 TabContent 和 AppShell
class TabContent(ft.Column):
    """Tab内容基类"""

    def __init__(self, tab_id: str) -> None:
        self.tab_id = tab_id
        super().__init__(
            expand=True,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

    def on_show(self) -> None:
        """当Tab显示时调用"""
        pass

    def on_hide(self) -> None:
        """当Tab隐藏时调用"""
        pass


class AppShell(ft.NavigationBar):
    """应用外壳 - 底部导航栏（兼容旧代码）"""

    TAB_MATRIX = "matrix"
    TAB_PRINCIPLES = "principles"
    TAB_SETTINGS = "settings"

    def __init__(self, on_tab_change: Callable[[str], None]):
        self.on_tab_change = on_tab_change
        self.current_tab = self.TAB_MATRIX

        super().__init__(
            selected_index=0,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.icons.Icons.GRID_ON,
                    selected_icon=ft.icons.Icons.GRID_ON,
                    label="39矛盾矩阵",
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.Icons.LIGHTBULB_OUTLINE,
                    selected_icon=ft.icons.Icons.LIGHTBULB,
                    label="40发明原理",
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.Icons.SETTINGS,
                    selected_icon=ft.icons.Icons.SETTINGS,
                    label="全局设置",
                ),
            ],
            on_change=self._handle_tab_change,
            bgcolor=COLORS.get("surface", "#F5F5F5"),
            indicator_color=COLORS.get("primary", "#2196F3"),
        )

    def _handle_tab_change(self, _):  # type: ignore
        """处理Tab切换"""
        index = self.selected_index
        if index == 0:
            self.current_tab = self.TAB_MATRIX
        elif index == 1:
            self.current_tab = self.TAB_PRINCIPLES
        elif index == 2:
            self.current_tab = self.TAB_SETTINGS
        else:
            self.current_tab = self.TAB_MATRIX

        logger.info(f"切换到Tab: {self.current_tab}")

        if self.on_tab_change is not None:
            self.on_tab_change(self.current_tab)

    def set_tab(self, tab: str) -> None:
        """设置当前Tab"""
        self.current_tab = tab
        if tab == self.TAB_MATRIX:
            self.selected_index = 0
        elif tab == self.TAB_PRINCIPLES:
            self.selected_index = 1
        elif tab == self.TAB_SETTINGS:
            self.selected_index = 2
        logger.info(f"设置当前Tab: {self.current_tab}")
