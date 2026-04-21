"""
设置Tab页面
提供全局应用设置和管理功能
"""

import flet as ft
import logging
from typing import TYPE_CHECKING, Optional, Callable

from ..app_shell import TabContent
from ...config.constants import COLORS
from ...data.local_storage import LocalStorage
from ...data.models import AnalysisSession

if TYPE_CHECKING:
    from ..ai_settings_dialog import AISettingsDialog

logger = logging.getLogger(__name__)


class SettingsTab(TabContent):
    """设置Tab"""

    def __init__(
        self,
        page: ft.Page,
        storage: LocalStorage,
        on_view_detail: Optional[Callable] = None,
    ):
        """
        初始化设置Tab

        Args:
            page: Flet页面对象
            storage: 本地存储
            on_view_detail: 查看详情的回调
        """
        self._page = page
        self.storage = storage
        self.on_view_detail = on_view_detail

        # 分页状态
        self._offset = 0
        self._limit = 20
        self._has_more = True

        # 选中状态
        self._selected_histories: set = set()

        # UI组件引用
        self.history_list: Optional[ft.ListView] = None
        self.load_more_btn: Optional[ft.Button] = None
        self.empty_msg: Optional[ft.Container] = None
        self.delete_btn: Optional[ft.Button] = None
        self.select_all_cb: Optional[ft.Checkbox] = None
        self._ai_settings_dialog: Optional["AISettingsDialog"] = None
        # 动态文本引用
        self._delete_btn_text: Optional[ft.Text] = None
        self._load_more_btn_text: Optional[ft.Text] = None

        super().__init__("settings")

    def on_show(self):
        """当Tab显示时调用"""
        try:
            logger.info("SettingsTab on_show 被调用")
            # 首次显示时构建UI
            is_first_show = not self.history_list
            if is_first_show:
                logger.info("SettingsTab 首次显示，构建UI")
                self._build_ui()
            self._load_history()
        except Exception as e:
            logger.error(f"SettingsTab on_show error: {e}", exc_info=True)

    def _reset_and_load(self):
        """重置并加载"""
        self._offset = 0
        self._has_more = True
        self._build_ui()
        self._load_history()

    def _build_ui(self):
        """构建UI"""
        self.controls.clear()
        self._selected_histories.clear()

        # 历史列表 - 必须先创建，供回调使用
        self.history_list = ft.ListView(expand=True, spacing=10, padding=10)

        # 空消息
        self.empty_msg = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.icons.Icons.HISTORY, size=48, color=ft.Colors.GREY_400),
                    ft.Text("暂无历史记录", size=16, color=ft.Colors.GREY),
                    ft.Text(
                        "开始分析问题后会保存在这里", size=12, color=ft.Colors.GREY_400
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.alignment.Alignment(0.5, 0.5),
            padding=30,
        )

        # 加载更多按钮
        self._load_more_btn_text = ft.Text("加载更多")
        self.load_more_btn = ft.Button(
            content=self._load_more_btn_text,
            icon=ft.icons.Icons.EXPAND_MORE,
            on_click=self._on_load_more,
            style=ft.ButtonStyle(color=COLORS["primary"], bgcolor=ft.Colors.GREY_100),
        )

        # 全选复选框 - 在history_list创建后定义回调
        def on_select_all_changed(e):
            if e.control.value and self.history_list:
                for ctrl in self.history_list.controls:
                    if hasattr(ctrl, "key") and ctrl.key:
                        self._selected_histories.add(ctrl.key)
            else:
                self._selected_histories.clear()
            self._update_delete_button()

        def close_dlg(_):
            self._page.pop_dialog()

        def confirm_delete(_):
            for session_id in list(self._selected_histories):
                self.storage.delete_session(session_id)
            self._show_snack_bar(f"已删除 {len(self._selected_histories)} 条记录")
            self._selected_histories.clear()
            self._offset = 0
            self._build_ui()
            self._load_history()
            self._page.pop_dialog()

        def on_delete_click():
            if not self._selected_histories:
                self._show_snack_bar("请先选择要删除的记录")
                return

            dlg = ft.AlertDialog(
                title=ft.Text("确认删除"),
                content=ft.Text(
                    f"确定要删除选中的 {len(self._selected_histories)} 条历史记录吗？"
                ),
                actions=[
                    ft.TextButton("取消", on_click=close_dlg),
                    ft.TextButton(
                        "删除",
                        on_click=confirm_delete,
                        style=ft.ButtonStyle(color=ft.Colors.RED),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self._page.show_dialog(dlg)

        self.select_all_cb = ft.Checkbox(
            label="全选", value=False, on_change=on_select_all_changed
        )

        # 删除选中按钮
        self._delete_btn_text = ft.Text("删除选中")
        self.delete_btn = ft.Button(
            content=self._delete_btn_text,
            icon=ft.icons.Icons.DELETE,
            on_click=on_delete_click,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.RED),
        )

        # 标题
        title = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.Icons.SETTINGS, color=COLORS["primary"], size=28),
                    ft.Text("全局设置", size=20, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=15,
        )

        # AI设置区域
        ai_settings_card = self._create_ai_settings_card()

        # 历史记录标题栏
        history_header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.Icons.HISTORY, color=COLORS["primary"], size=20),
                    ft.Text("分析历史", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    self.select_all_cb,
                    self.delete_btn,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(top=15, left=15, right=15, bottom=5),
        )

        # 管理操作按钮
        self.manage_buttons = ft.Row(
            controls=[
                ft.TextButton(
                    content=ft.Text("导出JSON"),
                    icon=ft.icons.Icons.DOWNLOAD,
                    on_click=lambda _: self._export_sessions("json"),
                ),
                ft.TextButton(
                    content=ft.Text("导出TXT"),
                    icon=ft.icons.Icons.DOWNLOAD,
                    on_click=lambda _: self._export_sessions("txt"),
                ),
                ft.TextButton(
                    content=ft.Text("查看日志"),
                    icon=ft.icons.Icons.DESCRIPTION,
                    on_click=self._show_log_viewer,
                ),
                ft.TextButton(
                    content=ft.Text("清空全部"),
                    icon=ft.icons.Icons.DELETE_FOREVER,
                    on_click=self._confirm_clear_all,
                    style=ft.ButtonStyle(color=ft.Colors.RED),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

        footer = ft.Container(
            content=self.load_more_btn,
            alignment=ft.alignment.Alignment(0.5, 0.5),
            padding=10,
        )

        # 组装
        self.controls.extend(
            [
                title,
                ft.Divider(),
                ai_settings_card,
                history_header,
                ft.Divider(),
                self.manage_buttons,
                ft.Divider(),
                self.empty_msg,
                self.history_list,
                footer,
            ]
        )

    def _update_delete_button(self):
        """更新删除按钮状态"""
        if self._delete_btn_text and self.delete_btn:
            count = len(self._selected_histories)
            if count > 0:
                self._delete_btn_text.value = f"删除选中({count})"
                self.delete_btn.disabled = False
            else:
                self._delete_btn_text.value = "删除选中"
                self.delete_btn.disabled = True

    def _create_ai_settings_card(self) -> ft.Card:
        """创建AI设置卡片"""
        # AI设置按钮
        ai_settings_btn = ft.TextButton(
            content=ft.Text("AI设置"),
            icon=ft.icons.Icons.SETTINGS,
            on_click=self._show_ai_settings,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLORS["primary"]),
        )

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("AI智能增强", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Text(
                            "配置AI API密钥以启用智能分析和头脑风暴功能",
                            size=12,
                            color=ft.Colors.GREY,
                        ),
                        ft.Container(height=10),
                        ai_settings_btn,
                    ],
                    spacing=5,
                ),
                padding=15,
            ),
            elevation=1,
        )

    def _show_snack_bar(self, message: str, _duration: int = 3000):
        """显示弹窗提示消息"""
        dlg = ft.AlertDialog(
            modal=True,
            content=ft.Text(message),
            actions=[ft.TextButton("确定", on_click=lambda _: self._page.pop_dialog())],
        )
        self._page.show_dialog(dlg)

    def _show_ai_settings(self, _: Optional[ft.ControlEvent] = None):
        """显示AI设置对话框"""
        logger.info("_show_ai_settings 被调用")
        if self._ai_settings_dialog is None:
            from ..ai_settings_dialog import AISettingsDialog

            self._ai_settings_dialog = AISettingsDialog(self._page)
        self._ai_settings_dialog.show()

    def _show_log_viewer(self, _: Optional[ft.ControlEvent] = None):
        """显示日志查看器"""
        from pathlib import Path

        log_file = Path("logs/triz_app.log")
        log_content = ""

        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    log_content = "".join(lines[-100:])
                if not log_content:
                    log_content = "日志文件为空"
            except Exception as ex:
                log_content = f"读取日志失败: {ex}"
        else:
            log_content = "日志文件不存在\n请检查 logs/triz_app.log"

        # 刷新按钮
        refresh_btn = ft.TextButton(
            content=ft.Text("刷新"),
            icon=ft.icons.Icons.REFRESH,
            on_click=self._show_log_viewer,
        )

        # 日志内容区域（可滚动）
        log_display = ft.Container(
            content=ft.Text(
                log_content, size=10, font_family="monospace", selectable=True
            ),
            padding=10,
            bgcolor=ft.Colors.GREY_100,
            border_radius=5,
            expand=1,
        )

        # 弹窗内容
        dialog_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        [
                            ft.Icon(
                                ft.icons.Icons.DESCRIPTION, color=COLORS["primary"]
                            ),
                            ft.Text("日志查看器", size=18, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            refresh_btn,
                        ]
                    ),
                    ft.Divider(),
                    ft.Text(f"文件: {log_file}", size=11, color=ft.Colors.GREY),
                    ft.Container(height=5),
                    log_display,
                ],
                spacing=10,
                expand=1,
            ),
            width=550,
            height=500,
        )

        dialog = ft.AlertDialog(
            content=dialog_content,
            actions=[ft.TextButton("关闭", on_click=lambda _: self._close_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.show_dialog(dialog)

    def _export_sessions(self, format: str):
        """导出会话"""
        content = self.storage.export_all_sessions(format)
        if not content:
            self._show_snack_bar("没有可导出的历史记录")
            return

        # 保存到应用私有存储目录
        import os
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"triz_history_{timestamp}.{format}"

        # 使用 FLET_APP_STORAGE_DATA 路径（Android 专用存储）
        app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
        if app_data_path:
            exports_dir = os.path.join(app_data_path, "exports")
        else:
            # 回退到相对路径（桌面模式）
            exports_dir = "exports"

        os.makedirs(exports_dir, exist_ok=True)
        filepath = os.path.join(exports_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self._show_snack_bar(f"已导出到 {filepath}")
        except Exception as ex:
            logger.error(f"导出失败: {ex}")
            self._show_snack_bar(f"导出失败: {ex}")

    def _confirm_clear_all(self, _: Optional[ft.ControlEvent] = None):
        """确认清空所有历史"""

        def handle_confirm(confirmed: bool):
            if confirmed:
                self._do_clear_all()

        dialog = ft.AlertDialog(
            title=ft.Text("确认清空", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Text("确定要删除所有历史记录吗？此操作不可恢复。"),
            actions=[
                ft.TextButton("取消", on_click=lambda _: self._close_dialog()),
                ft.TextButton(
                    "确定",
                    on_click=lambda _: handle_confirm(True),
                    style=ft.ButtonStyle(color=ft.Colors.RED),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.show_dialog(dialog)

    def _do_clear_all(self):
        """执行清空所有历史"""
        count = self.storage.delete_all_sessions()
        self._close_dialog()
        self._reset_and_load()
        self._show_snack_bar(f"已删除 {count} 条历史记录")

    def _load_history(self):
        """加载历史记录"""
        # 确保UI已构建
        if (
            not self.history_list
            or not self.empty_msg
            or not self.load_more_btn
            or not self._load_more_btn_text
        ):
            return

        sessions = self.storage.get_session_summaries(
            limit=self._limit, offset=self._offset
        )

        logger.info(
            f"SettingsTab _load_history: offset={self._offset}, sessions_count={len(sessions)}"
        )

        # 每次加载时清空列表，防止重复添加
        if self._offset == 0:
            self.history_list.controls.clear()

        if self._offset == 0 and not sessions:
            self.empty_msg.visible = True
            self.history_list.visible = False
            self.load_more_btn.visible = False
        else:
            self.empty_msg.visible = False
            self.history_list.visible = True

            # 添加历史项
            for summary in sessions:
                item = self._create_history_item(summary)
                self.history_list.controls.append(item)

            # 检查是否还有更多
            total = self.storage.get_session_count()
            self._has_more = (self._offset + len(sessions)) < total

            if self._has_more:
                self.load_more_btn.visible = True
                self._load_more_btn_text.value = "加载更多"
                self.load_more_btn.disabled = False
            else:
                self.load_more_btn.visible = True
                self._load_more_btn_text.value = "没有更多了"
                self.load_more_btn.disabled = True

        self._page.update()

    def _on_load_more(self, _: Optional[ft.ControlEvent] = None):
        """加载更多"""
        if not self._has_more or not self._load_more_btn_text or not self.load_more_btn:
            return

        self._load_more_btn_text.value = "加载中..."
        self.load_more_btn.disabled = True
        self._page.update()

        self._offset += self._limit
        self._load_history()

    def _create_history_item(self, summary: dict) -> ft.Card:
        """创建历史记录卡片"""
        session_id = summary.get("id", "")
        time_text = summary.get("created_at", "")
        problem_preview = summary.get("problem_preview", "")
        solution_count = summary.get("solution_count", 0)
        ai_enabled = summary.get("ai_enabled", False)
        matrix_type = summary.get("matrix_type", "39")
        improving = summary.get("improving_param", "")
        worsening = summary.get("worsening_param", "")

        status_color = ft.Colors.GREEN if ai_enabled else ft.Colors.GREY
        status_text = "AI" if ai_enabled else "本地"

        # 复选框切换选中状态
        def on_checkbox_changed(_):
            if session_id in self._selected_histories:
                self._selected_histories.discard(session_id)
            else:
                self._selected_histories.add(session_id)
            self._update_delete_button()
            # 更新全选状态
            if self.history_list and self.select_all_cb:
                all_ids = {
                    str(ctrl.key)
                    for ctrl in self.history_list.controls
                    if hasattr(ctrl, "key") and ctrl.key
                }
                self.select_all_cb.value = bool(
                    all_ids and self._selected_histories == all_ids
                )

        checkbox = ft.Checkbox(
            value=session_id in self._selected_histories, on_change=on_checkbox_changed
        )

        return ft.Card(
            key=session_id,
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                checkbox,
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            time_text, size=12, color=ft.Colors.GREY
                                        ),
                                        ft.Text(
                                            problem_preview,
                                            size=14,
                                            max_lines=2,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                    ],
                                    spacing=2,
                                ),
                                ft.Container(expand=True),
                                ft.Container(
                                    content=ft.Text(
                                        status_text, size=10, color=status_color
                                    ),
                                    padding=5,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        f"{matrix_type}矩阵",
                                        size=10,
                                        color=ft.Colors.GREY,
                                    ),
                                    padding=5,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Divider(),
                        ft.Row(
                            controls=[
                                (
                                    ft.Text(
                                        f"改善: {improving or '自动'}",
                                        size=11,
                                        color=ft.Colors.GREY,
                                    )
                                    if improving
                                    else ft.Text("")
                                ),
                                (
                                    ft.Text(
                                        f"恶化: {worsening or '自动'}",
                                        size=11,
                                        color=ft.Colors.GREY,
                                    )
                                    if worsening
                                    else ft.Text("")
                                ),
                                ft.Container(expand=True),
                                ft.Text(
                                    f"{solution_count}个方案",
                                    size=11,
                                    color=COLORS["primary"],
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.Container(height=5),
                        ft.Row(
                            controls=[
                                ft.Container(expand=True),
                                ft.TextButton(
                                    content=ft.Text("查看详情"),
                                    icon=ft.icons.Icons.VISIBILITY,
                                    on_click=lambda _, s=summary: self._on_view_detail(
                                        s
                                    ),
                                ),
                            ]
                        ),
                    ],
                    spacing=5,
                ),
                padding=15,
            ),
            elevation=2,
        )

    def _on_view_detail(self, summary: dict):
        """查看详情"""
        if self.on_view_detail:
            self.on_view_detail(summary)
        else:
            session_id = summary.get("id")
            if session_id:
                session = self.storage.get_session(session_id)
                if session:
                    self._show_session_detail(session)
                else:
                    self._show_snack_bar("无法加载会话详情")
            else:
                self._show_snack_bar("会话ID无效")

    def _show_session_detail(self, session: AnalysisSession):
        """显示会话详情（卡片形式）"""
        # 头部信息
        header = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("问题:", size=13, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.Text(
                                "🤖 AI" if session.ai_enabled else "📦 本地",
                                size=11,
                                color=(
                                    ft.Colors.GREEN
                                    if session.ai_enabled
                                    else ft.Colors.GREY
                                ),
                            ),
                        ]
                    ),
                    ft.Text(
                        session.problem,
                        size=12,
                        max_lines=3,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Divider(),
                    ft.Row(
                        [
                            ft.Text(
                                f"改善: {session.improving_param or '自动'}",
                                size=11,
                                color=ft.Colors.GREY,
                            ),
                            ft.Text(
                                f"恶化: {session.worsening_param or '自动'}",
                                size=11,
                                color=ft.Colors.GREY,
                            ),
                        ]
                    ),
                    ft.Text(
                        f"{session.matrix_type}矩阵 | {len(session.solutions)}个方案",
                        size=11,
                        color=ft.Colors.GREY,
                    ),
                    ft.Text(
                        f"时间: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                        size=10,
                        color=ft.Colors.GREY_400,
                    ),
                ],
                spacing=5,
            ),
            padding=10,
            bgcolor=ft.Colors.GREY_100,
            border_radius=5,
        )

        # 解决方案卡片列表
        solutions = []
        for s in session.solutions:
            is_ai_generated = getattr(s, "is_ai_generated", False)
            confidence = getattr(s, "confidence", None)
            conf_text = f"{int(confidence * 100)}%" if confidence else ""

            card = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Container(
                                        content=ft.Text(
                                            f"#{s.principle_id}",
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        padding=5,
                                        bgcolor=COLORS["primary"],
                                        border_radius=3,
                                    ),
                                    ft.Text(
                                        s.principle_name,
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        expand=True,
                                    ),
                                    ft.Text(
                                        "🤖 AI" if is_ai_generated else "📦 本地",
                                        size=10,
                                        color=(
                                            ft.Colors.GREEN
                                            if is_ai_generated
                                            else ft.Colors.GREY
                                        ),
                                    ),
                                ]
                            ),
                            ft.Text(
                                s.description or "",
                                size=11,
                                max_lines=4,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Divider(),
                            ft.Row(
                                [
                                    ft.Text(
                                        getattr(s, "category", "物理"),
                                        size=10,
                                        color=ft.Colors.GREY,
                                    ),
                                    ft.Container(expand=True),
                                    (
                                        ft.Text(
                                            conf_text, size=10, color=COLORS["primary"]
                                        )
                                        if conf_text
                                        else ft.Text("")
                                    ),
                                ]
                            ),
                        ],
                        spacing=3,
                    ),
                    padding=10,
                ),
                elevation=1,
            )
            solutions.append(card)

        solutions_view = ft.ListView(
            controls=(
                solutions
                if solutions
                else [ft.Text("无解决方案", size=12, color=ft.Colors.GREY)]
            ),
            expand=True,
            spacing=8,
            padding=5,
        )

        dialog = ft.AlertDialog(
            title=ft.Text("会话详情", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        header,
                        ft.Container(height=10),
                        ft.Text("解决方案", size=14, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        solutions_view,
                    ],
                    spacing=5,
                ),
                width=450,
                height=500,
                padding=10,
            ),
            actions=[ft.TextButton("关闭", on_click=lambda _: self._close_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.show_dialog(dialog)

    def _close_dialog(self):
        """关闭弹窗"""
        self._page.pop_dialog()
