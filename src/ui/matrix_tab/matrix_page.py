"""
矛盾矩阵Tab页面
提供39矛盾矩阵分析的主界面
"""

import logging
from collections.abc import Callable
from typing import Any

import flet as ft

from config.constants import COLORS
from core.matrix_selector import get_matrix_manager
from core.principle_service import get_principle_service
from data.local_storage import LocalStorage
from data.models import AnalysisSession, Solution
from ui.app_shell import TabContent
from ui.parameter_ui import ParameterPicker

logger = logging.getLogger(__name__)


class MatrixTab(TabContent):
    """矛盾矩阵Tab"""

    def __init__(
        self,
        page: ft.Page,
        storage: LocalStorage,
        on_navigate_to_principle: Callable | None = None,
    ):
        """
        初始化矛盾矩阵Tab

        Args:
            page: Flet页面对象
            storage: 本地存储
            on_navigate_to_principle: 跳转到原理详情的回调
        """
        self._page = page
        self.storage = storage
        self.on_navigate_to_principle = on_navigate_to_principle
        self._principle_service = get_principle_service()
        self._matrix_manager = get_matrix_manager()

        # 订阅AI状态变化
        from ui.state import get_ai_state_manager

        ai_state = get_ai_state_manager()
        ai_state.subscribe(self._on_ai_state_changed)

        # 状态
        self.ai_enabled = False
        self.improving_params: list[str] = []
        self.worsening_params: list[str] = []
        self.solution_count = 5
        self.problem_text = ""

        # UI组件引用
        self.problem_input: ft.TextField | None = None
        self.improving_btn: ft.Button | None = None
        self.worsening_btn: ft.Button | None = None
        self.improving_text: ft.Text | None = None
        self.worsening_text: ft.Text | None = None
        self.analyze_btn: ft.Button | None = None
        self.loading_indicator: ft.ProgressBar | None = None
        self.result_container: ft.Container | None = None
        self.brainstorm_loading: ft.Container
        self.ai_analysis_result_container: ft.Container | None = None

        # 当前会话
        self._current_matrix_session: AnalysisSession | None = None
        self._current_brainstorm_session: AnalysisSession | None = None
        # 矩阵查询的原理数据（用于同步到头脑风暴）
        self._current_matrix_principles: list = []

        # 选中的解决方案（用于批量保存）
        self._selected_solutions: list[int] = []  # 存储选中的 solution index

        # Overlay弹窗引用
        self._solutions_overlay: ft.Container | None = None
        self._detail_overlay: ft.Container | None = None

        super().__init__("matrix")

    def _show_snack_bar(
        self, message: str, duration: int = 3000  # noqa: ARG002
    ) -> None:
        """显示弹窗提示消息"""
        dlg = ft.AlertDialog(
            modal=True,
            content=ft.Text(message),
            actions=[ft.TextButton("确定", on_click=lambda _: self._page.pop_dialog())],
        )
        self._page.show_dialog(dlg)

    def on_show(self) -> None:
        """当Tab显示时调用"""
        try:
            # 只在首次显示时构建UI
            if not self.problem_input:
                self._build_ui()
            # 更新AI按钮状态
            self._update_ai_buttons()
        except Exception as e:
            logger.error(f"MatrixTab on_show error: {e}", exc_info=True)

    def _mark_ai_disconnected(self) -> None:
        """标记AI为未连接状态，并通知AI状态变化"""
        from ai.ai_client import get_ai_manager

        from ui.state import get_ai_state_manager

        ai_manager = get_ai_manager()
        ai_manager.set_connected(False)

        # 通过AIStateManager通知订阅者
        ai_state = get_ai_state_manager()
        ai_state.update_status(ai_manager.is_enabled(), False)

    def _on_ai_state_changed(self, is_enabled: bool, is_connected: bool) -> None:
        """AI状态变化回调"""
        logger.info(
            f"MatrixTab收到AI状态变化: enabled={is_enabled}, connected={is_connected}"
        )
        try:
            self._update_ai_buttons()
        except Exception as e:
            logger.error(f"_on_ai_state_changed error: {e}", exc_info=True)

    def _update_ai_buttons(self) -> None:
        """根据AI连接状态启用/禁用AI相关按钮"""
        from ai.ai_client import get_ai_manager

        ai_manager = get_ai_manager()
        # 使用实际连接状态，而非仅配置状态
        is_ai_connected = ai_manager.is_enabled() and ai_manager.is_connected()

        # 安全访问属性，避免在UI构建前被调用时出错
        analyze_btn = getattr(self, 'analyze_params_btn', None)
        brainstorm_btn = getattr(self, 'brainstorm_btn', None)

        if analyze_btn:
            analyze_btn.disabled = not is_ai_connected
        if brainstorm_btn:
            brainstorm_btn.disabled = not is_ai_connected

    def _build_ui(self) -> None:
        """构建UI"""
        self.controls.clear()

        # 标题
        title = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.Icons.GRID_ON, color=COLORS["primary"], size=28),
                    ft.Text("39矛盾矩阵分析", size=20, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=15,
        )

        # AI分析结果展示区域（必须在problem_section之前创建）
        self.ai_analysis_result_container = ft.Container(
            content=ft.Column(scroll=ft.ScrollMode.AUTO), padding=10, visible=False
        )

        # 问题输入区
        self.problem_input = ft.TextField(
            label="问题描述",
            hint_text="请输入您要解决的TRIZ问题，例如：如何让新能源汽车在保持续航里程的同时缩短充电时间",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_color=COLORS["primary"],
            expand=True,
            on_change=self._on_problem_changed,
        )

        self.analyze_params_btn = ft.Button(
            content=ft.Text(" AI分析参数"),
            icon=ft.icons.Icons.AUTO_AWESOME,
            on_click=self._on_ai_analyze_params,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLORS["primary"]),
            scale=0.9,
        )

        self.ai_analyze_loading = ft.ProgressBar(visible=False, width=150)

        self.improving_text = ft.Text("未选择", color=ft.Colors.GREY, size=14)
        self.worsening_text = ft.Text("未选择", color=ft.Colors.GREY, size=14)

        self.improving_btn = ft.Button(
            content=ft.Text("选择改善参数"),
            icon=ft.icons.Icons.TRENDING_UP,
            on_click=lambda _: self._show_param_picker("improving"),
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLORS["primary"]),
            scale=0.85,
        )

        self.worsening_btn = ft.Button(
            content=ft.Text("选择恶化参数"),
            icon=ft.icons.Icons.TRENDING_DOWN,
            on_click=lambda _: self._show_param_picker("worsening"),
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLORS["secondary"]),
            scale=0.85,
        )

        problem_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("问题描述", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(content=self.problem_input, expand=True),
                    ft.Container(height=5),
                    ft.Row(
                        controls=[self.analyze_params_btn, self.ai_analyze_loading],
                        spacing=10,
                    ),
                    # AI分析结果展示（在AI分析参数按钮下方）
                    ft.Container(height=5),
                    self.ai_analysis_result_container,
                    ft.Container(height=5),
                    ft.Text("参数选择", size=14, weight=ft.FontWeight.BOLD),
                    ft.Container(height=3),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("改善:", width=50, size=12),
                                    self.improving_btn,
                                ],
                                spacing=5,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                content=self.improving_text,
                                padding=ft.Padding.only(left=50),
                            ),
                            ft.Container(height=5),
                            ft.Row(
                                controls=[
                                    ft.Text("恶化:", width=50, size=12),
                                    self.worsening_btn,
                                ],
                                spacing=5,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                content=self.worsening_text,
                                padding=ft.Padding.only(left=50),
                            ),
                        ],
                        spacing=3,
                    ),
                ],
                spacing=8,
            ),
            padding=15,
        )

        # 分析按钮
        self.analyze_btn = ft.Button(
            content=ft.Text("查询发明原理"),
            icon=ft.icons.Icons.SEARCH,
            on_click=self._on_analyze,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE, bgcolor=COLORS["primary"], padding=10
            ),
            scale=0.95,
        )

        # 头脑风暴按钮
        self.brainstorm_btn = ft.Button(
            content=ft.Text("头脑风暴"),
            icon=ft.icons.Icons.LIGHTBULB,
            on_click=self._on_brainstorm,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE, bgcolor=COLORS["secondary"], padding=10
            ),
            scale=0.95,
        )

        self.loading_indicator = ft.ProgressBar(visible=False, width=200)

        button_section = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(content=self.analyze_btn, expand=True),
                    ft.Container(width=10),
                    ft.Container(content=self.brainstorm_btn, expand=True),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=15,
        )

        # 结果区域 - 左栏（矩阵查询）右栏（头脑风暴）
        self.matrix_result_container = ft.Container(
            content=ft.Column(scroll=ft.ScrollMode.AUTO), padding=5, height=300
        )

        # 头脑风暴加载指示器（嵌入到结果区域）
        self.brainstorm_progress_text = ft.Text(
            "准备开始...", size=12, color=ft.Colors.GREY_600
        )
        self.brainstorm_loading = ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(width=40, height=40),
                    ft.Container(height=10),
                    ft.Text("AI正在思考...", size=14, color=ft.Colors.GREY),
                    ft.Text(
                        "正在基于TRIZ原理生成创新解决方案...",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Container(height=5),
                    self.brainstorm_progress_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            visible=False,
            padding=20,
        )

        self.brainstorm_result_container = ft.Container(
            content=ft.Column(scroll=ft.ScrollMode.AUTO), padding=5, height=300
        )

        # 组合
        self.controls.extend(
            [
                title,
                ft.Divider(),
                problem_section,
                ft.Divider(),
                button_section,
                ft.Divider(),
                # 左右分栏显示结果
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        " 矩阵查询结果",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Container(height=5),
                                    self.matrix_result_container,
                                ],
                                spacing=5,
                            ),
                            expand=1,
                            border=ft.Border.all(1, ft.Colors.GREY_300),
                            border_radius=10,
                            padding=5,
                        ),
                        ft.Container(width=10),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text(
                                        " AI头脑风暴",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Container(height=5),
                                    self.brainstorm_result_container,
                                ],
                                spacing=5,
                            ),
                            expand=1,
                            border=ft.Border.all(1, ft.Colors.GREY_300),
                            border_radius=10,
                            padding=5,
                        ),
                    ],
                    spacing=10,
                ),
            ]
        )

    def _on_problem_changed(self, e: ft.Event) -> None:
        """问题描述变化"""
        self.problem_text = e.control.value.strip()

    async def _on_ai_analyze_params(self, e: ft.Event) -> None:  # noqa: ARG002
        """AI分析参数按钮点击"""
        # Guard: ensure UI components are initialized
        if not self.improving_text or not self.worsening_text:
            self._show_snack_bar("界面未就绪，请重试")
            return

        problem = self.problem_input.value.strip() if self.problem_input else ""

        if not problem:
            self._show_snack_bar("请先输入问题描述")
            return

        # 检查AI是否可用
        from ai.ai_client import get_ai_manager

        ai_manager = get_ai_manager()
        if not ai_manager.is_enabled():
            self._show_snack_bar("请先在设置中配置AI")
            return

        # 显示加载状态
        self.ai_analyze_loading.visible = True
        self.analyze_params_btn.disabled = True
        self._page.update()

        try:
            client = ai_manager.get_client()
            if not client:
                raise RuntimeError("AI客户端未初始化")
            result = await client.detect_parameters(problem)

            # 检查是否有错误
            if result.get("error"):
                logger.error(f"AI参数检测返回错误: {result.get('error')}")
                self._mark_ai_disconnected()
                self._show_snack_bar(f"AI分析失败: {result.get('error')}")
                return

            # AI调用成功，标记为已连接
            ai_manager.set_connected(True)

            logger.info(f"AI参数检测结果: {result}")

            improving = result.get("improving", [])
            worsening = result.get("worsening", [])

            # 确保是列表格式
            if isinstance(improving, str):
                improving = [improving] if improving else []
            if isinstance(worsening, str):
                worsening = [worsening] if worsening else []

            logger.info(f"AI返回改善参数: {improving}, 恶化参数: {worsening}")

            if improving:
                self.improving_params = improving
                display = ", ".join(improving[:2])
                if len(improving) > 2:
                    display += f"...(+{len(improving)-2})"
                self.improving_text.value = f"已选: {display}"
                self.improving_text.color = ft.Colors.GREEN
                logger.info(f"设置改善参数: {improving}")
            else:
                self.improving_params = []
                logger.info("AI未返回改善参数")

            if worsening:
                self.worsening_params = worsening
                display = ", ".join(worsening[:2])
                if len(worsening) > 2:
                    display += f"...(+{len(worsening)-2})"
                self.worsening_text.value = f"已选: {display}"
                self.worsening_text.color = ft.Colors.GREEN
                logger.info(f"设置恶化参数: {worsening}")
            else:
                self.worsening_params = []
                logger.info("AI未返回恶化参数")

            explanation = result.get("explanation", "")

            # 更新AI分析结果展示
            assert self.ai_analysis_result_container is not None
            self.ai_analysis_result_container.content = ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.icons.Icons.LIGHTBULB,
                                color=COLORS["secondary"],
                                size=20,
                            ),
                            ft.Text(
                                " AI参数分析结果",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=COLORS["secondary"],
                            ),
                        ],
                        spacing=5,
                    ),
                    ft.Container(height=5),
                    ft.Container(
                        content=ft.Text(
                            f"改善参数: {', '.join(improving) if improving else '未识别'}",
                            size=12,
                            color=ft.Colors.GREEN if improving else ft.Colors.GREY,
                        )
                    ),
                    ft.Container(
                        content=ft.Text(
                            f"恶化参数: {', '.join(worsening) if worsening else '未识别'}",
                            size=12,
                            color=ft.Colors.ORANGE if worsening else ft.Colors.GREY,
                        )
                    ),
                ]
                + (
                    [
                        ft.Container(height=5),
                        ft.Container(
                            content=ft.Text(
                                explanation, size=11, color=ft.Colors.GREY_600
                            ),
                            padding=8,
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=5,
                        ),
                    ]
                    if explanation
                    else []
                ),
                spacing=3,
            )
            self.ai_analysis_result_container.visible = True

        except Exception as ex:
            logger.error(f"AI参数分析失败: {ex}")
            # AI调用失败，标记为未连接
            self._mark_ai_disconnected()
            self._show_snack_bar(f"AI分析失败: {str(ex)}")
        finally:
            self.ai_analyze_loading.visible = False
            self.analyze_params_btn.disabled = False
            self._page.update()

    def _show_param_picker(self, param_type: str) -> None:
        """显示参数选择器"""
        current = (
            self.improving_params
            if param_type == "improving"
            else self.worsening_params
        )
        picker = ParameterPicker(
            page=self._page,
            param_type=param_type,
            current_values=current,
            on_selected=self._on_param_selected,
            multi_select=True,
        )
        picker.show()

    def _on_param_selected(
        self, param_type: str, param_values: list[str] | None
    ) -> None:
        """参数选中回调"""
        logger.info(f"_on_param_selected: type={param_type}, values={param_values}")
        assert self.improving_text is not None
        assert self.worsening_text is not None
        if param_type == "improving":
            self.improving_params = param_values or []
            if self.improving_params:
                display = ", ".join(self.improving_params[:2])
                if len(self.improving_params) > 2:
                    display += f"...(+{len(self.improving_params)-2})"
                self.improving_text.value = f"已选: {display}"
                self.improving_text.color = ft.Colors.GREEN
            else:
                self.improving_text.value = "未选择"
                self.improving_text.color = ft.Colors.GREY
        else:
            self.worsening_params = param_values or []
            if self.worsening_params:
                display = ", ".join(self.worsening_params[:2])
                if len(self.worsening_params) > 2:
                    display += f"...(+{len(self.worsening_params)-2})"
                self.worsening_text.value = f"已选: {display}"
                self.worsening_text.color = ft.Colors.GREEN
            else:
                self.worsening_text.value = "未选择"
                self.worsening_text.color = ft.Colors.GREY

        self._page.update()

    async def _on_analyze(self, e: ft.Event) -> None:  # noqa: ARG002
        """开始分析"""
        assert self.loading_indicator is not None
        assert self.analyze_btn is not None
        problem = self.problem_input.value.strip() if self.problem_input else ""

        logger.info(f"_on_analyze开始: improving_params={self.improving_params}, worsening_params={self.worsening_params}")

        # 至少需要问题描述或参数选择之一
        if not problem and not self.improving_params and not self.worsening_params:
            self._show_snack_bar("请输入问题描述或选择参数")
            return

        # 显示加载状态
        self.loading_indicator.visible = True
        self.analyze_btn.disabled = True
        self._page.update()

        try:
            # 纯本地矩阵查询
            matrix = self._matrix_manager.get_matrix("39")

            all_principle_ids = []
            improving_list = self.improving_params if self.improving_params else [None]
            worsening_list = self.worsening_params if self.worsening_params else [None]

            for imp in improving_list:
                for wors in worsening_list:
                    query_result = matrix.query_matrix(improving=imp, worsening=wors)
                    all_principle_ids.extend(query_result.principle_ids)

            unique_principle_ids = list(dict.fromkeys(all_principle_ids))
            principles = self._principle_service.get_principles_by_ids(
                unique_principle_ids
            )

            # 保存矩阵原理数据，供头脑风暴使用
            self._current_matrix_principles = principles

            # 保持 principles 为 InventivePrinciple 对象用于显示
            solutions = []
            for p in principles:
                solutions.append(
                    Solution(
                        principle_id=p.id,
                        principle_name=p.name,
                        description=p.definition,
                        category=p.category,
                        examples=p.examples,
                        is_ai_generated=False,
                        confidence=0.8,
                    )
                )

            session = AnalysisSession(
                problem=problem,
                matrix_type="39",
                improving_param=(
                    ", ".join(self.improving_params)
                    if self.improving_params
                    else "自动"
                ),
                worsening_param=(
                    ", ".join(self.worsening_params)
                    if self.worsening_params
                    else "自动"
                ),
                ai_enabled=False,
                solutions=solutions,
            )

            # 传入 InventivePrinciple 对象用于显示详情
            self._show_principles_result(
                session, principles, self.matrix_result_container
            )
            # 不自动保存，等待用户手动添加到历史

        except Exception as ex:
            logger.error(f"分析失败: {ex}")
            self._show_snack_bar(f"分析失败: {str(ex)}")
        finally:
            self.loading_indicator.visible = False
            self.analyze_btn.disabled = False
            self._page.update()

    async def _on_brainstorm(self, e: ft.Event) -> None:  # noqa: ARG002
        """头脑风暴按钮点击处理"""
        assert self.loading_indicator is not None
        assert self.brainstorm_btn is not None
        # 检查AI是否可用
        from ai.ai_client import get_ai_manager

        ai_manager = get_ai_manager()
        if not ai_manager.is_enabled():
            self._show_snack_bar("请先开启AI并配置API密钥")
            return

        problem = self.problem_input.value.strip() if self.problem_input else ""

        if not problem:
            self._show_snack_bar("请先输入问题描述")
            return

        # 显示嵌入的加载指示器
        self._show_brainstorm_loading()

        # 显示加载状态
        self.loading_indicator.visible = True
        self.brainstorm_btn.disabled = True
        self._page.update()

        try:
            from core.triz_engine import get_triz_engine

            engine = get_triz_engine()

            # 收集所有原理ID（去重）
            all_principle_ids = []
            matrix = self._matrix_manager.get_matrix("39")

            improving_list = self.improving_params if self.improving_params else [None]
            worsening_list = self.worsening_params if self.worsening_params else [None]

            for imp in improving_list:
                for wors in worsening_list:
                    query_result = matrix.query_matrix(improving=imp, worsening=wors)
                    all_principle_ids.extend(query_result.principle_ids)

            unique_principle_ids = list(dict.fromkeys(all_principle_ids))

            # 使用AI分析
            improving = self.improving_params[0] if self.improving_params else None
            worsening = self.worsening_params[0] if self.worsening_params else None

            # 使用遍历注入模式生成解决方案
            # 定义进度回调函数
            def update_progress(current: int, total: int) -> None:
                # 更新进度显示
                if hasattr(self, "brainstorm_progress_text"):
                    self.brainstorm_progress_text.value = (
                        f"正在分析原理 {current}/{total}..."
                    )
                    self._page.update()

            # 调用遍历生成方法
            solutions = await engine.generate_solutions_iterative(
                problem=problem,
                improving_param=improving,
                worsening_param=worsening,
                principle_ids=unique_principle_ids,
                progress_callback=update_progress,
            )

            # 创建会话
            from data.models import AnalysisSession

            session = AnalysisSession(
                problem=problem,
                improving_param=improving,
                worsening_param=worsening,
                ai_enabled=True,
                matrix_type="39",
                solutions=solutions,
                solution_count=len(solutions),
            )

            # 用矩阵查询的原理数据同步解决方案的原理信息
            if self._current_matrix_principles and session.solutions:
                principle_map = {p.id: p for p in self._current_matrix_principles}
                for sol in session.solutions:
                    if sol.principle_id in principle_map:
                        p = principle_map[sol.principle_id]
                        sol.principle_name = p.name
                        sol.category = p.category

            # 检查AI是否返回了有效的结构化解决方案
            has_structured_solutions = (
                any(
                    getattr(s, "technical_solution", "")
                    or getattr(s, "innovation_point", "")
                    or getattr(s, "cross_domain_cases", [])
                    for s in session.solutions
                )
                if session.solutions
                else False
            )

            if not session.solutions or not has_structured_solutions:
                # AI未返回有效结果，提示用户
                logger.warning("AI未返回有效解决方案")
                self._show_snack_bar("AI未返回有效解决方案，请检查网络或API配置")
                return

            # 头脑风暴成功，标记AI为已连接
            ai_manager.set_connected(True)

            self._show_solutions_result(
                session, session.solutions, self.brainstorm_result_container
            )

            self._show_snack_bar(f"头脑风暴完成！生成 {len(session.solutions)} 个方案")

        except Exception as ex:
            logger.error(f"头脑风暴失败: {ex}")
            # AI调用失败，标记为未连接
            self._mark_ai_disconnected()
            self._show_snack_bar(f"头脑风暴失败: {str(ex)}")
        finally:
            self.loading_indicator.visible = False
            self.brainstorm_btn.disabled = False
            self._hide_brainstorm_loading()
            self._page.update()

    def _show_brainstorm_loading(self) -> None:
        """显示嵌入的头脑风暴加载指示器"""
        self.brainstorm_result_container.content = self.brainstorm_loading
        self.brainstorm_loading.visible = True

    def _hide_brainstorm_loading(self) -> None:
        """隐藏嵌入的头脑风暴加载指示器"""
        self.brainstorm_loading.visible = False

    def _show_principles_result(
        self,
        session: AnalysisSession,
        principles: list,
        target_container: ft.Container | None = None,
    ) -> None:
        """显示矩阵查询结果（原理）"""
        self._current_matrix_session = session
        container = target_container or self.matrix_result_container
        card_controls: list[ft.Control] = [
            self._create_principle_card(p) for p in principles
        ]
        if principles:
            card_controls.append(ft.Container(height=10))
        else:
            card_controls.append(ft.Text("暂无结果", size=12, color=ft.Colors.GREY))
        container.content = ft.ListView(controls=card_controls, spacing=8, expand=True)
        self._page.update()

    def _show_solutions_result(
        self,
        session: AnalysisSession,
        solutions: list,
        target_container: ft.Container | None = None,
    ) -> None:
        """显示头脑风暴结果（解决方案）"""
        logger.info(f"_show_solutions_result called with {len(solutions)} solutions")
        self._current_brainstorm_session = session
        self._selected_solutions.clear()  # 清空选中状态
        container = target_container or self.brainstorm_result_container

        card_controls: list[ft.Control] = []
        if solutions:
            card_controls = [
                self._create_solution_card(s, idx, is_brainstorm=True)
                for idx, s in enumerate(solutions)
            ]
            card_controls.append(ft.Container(height=10))
            card_controls.append(self._create_save_selected_button())
        else:
            card_controls = [ft.Text("暂无结果", size=12, color=ft.Colors.GREY)]

        container.content = ft.ListView(controls=card_controls, spacing=8, expand=True)
        self._page.update()

    def _create_save_selected_button(self) -> ft.Container:
        """创建保存选中按钮"""

        def save_selected(e: ft.Event[Any]) -> None:  # noqa: ARG002
            logger.info(f"save_selected called, selected: {self._selected_solutions}")

            if not self._selected_solutions:
                self._show_snack_bar("请先选择要保存的方案")
                return

            session = self._current_brainstorm_session
            if not session:
                logger.error("session is None")
                self._show_snack_bar("会话数据不存在")
                return

            if not session.solutions:
                logger.error("session.solutions is empty")
                self._show_snack_bar("暂无解决方案")
                return

            # 获取选中的解决方案
            selected = [
                session.solutions[i]
                for i in self._selected_solutions
                if i < len(session.solutions)
            ]
            logger.info(f"Selected solutions count: {len(selected)}")

            if not selected:
                self._show_snack_bar("选中的方案无效")
                return

            try:
                # 检查是否已存在相同问题的会话
                existing_id = self.storage.find_session_by_problem(session.problem)
                logger.info(f"Existing session id: {existing_id}")

                if existing_id:
                    success = self.storage.append_solutions(existing_id, selected)
                    if success:
                        self._show_snack_bar(f"已追加 {len(selected)} 个方案到历史记录")
                    else:
                        self._show_snack_bar("追加失败，请查看日志")
                else:
                    from data.models import AnalysisSession as NewSession

                    new_session = NewSession(
                        problem=session.problem,
                        matrix_type=session.matrix_type,
                        improving_param=session.improving_param,
                        worsening_param=session.worsening_param,
                        ai_enabled=session.ai_enabled,
                        solutions=selected,
                    )
                    success = self.storage.save_session(new_session)
                    if success:
                        self._show_snack_bar(f"已保存 {len(selected)} 个方案到历史记录")
                    else:
                        self._show_snack_bar("保存失败，请查看日志")
            except Exception as ex:
                logger.error(f"保存失败: {ex}")
                self._show_snack_bar(f"保存异常: {str(ex)[:50]}")

            # 清空选择
            self._selected_solutions.clear()

        return ft.Container(
            content=ft.Button(
                content=ft.Text("保存选中"),
                icon=ft.icons.Icons.SAVE,
                on_click=save_selected,
                style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLORS["primary"]),
            ),
            padding=10,
            alignment=ft.alignment.Alignment(0, 0),
        )

    def _create_principle_card(self, principle: Any) -> ft.Container:
        """创建原理卡片（与原理库样式一致）"""
        from data.models import InventivePrinciple

        # 支持 Solution 和 InventivePrinciple 两种对象
        principle_id = getattr(principle, "principle_id", None) or getattr(
            principle, "id", 0
        )
        principle_name = getattr(principle, "name", "") or getattr(
            principle, "principle_name", ""
        )
        principle_category = getattr(principle, "category", "物理") or "物理"
        principle_definition = getattr(principle, "definition", "") or getattr(
            principle, "description", ""
        )

        # 点击处理：获取完整详情并显示弹窗
        def show_detail(e: ft.Event[Any]) -> None:  # noqa: ARG002
            # 如果传入的是Solution，需要通过principle_id获取完整详情
            if isinstance(principle, InventivePrinciple):
                full_principle: InventivePrinciple | None = principle
            else:
                pid = int(principle_id) if principle_id else 0
                full_principle = self._principle_service.get_principle(pid)
            if full_principle:
                self._show_principle_detail_dialog(full_principle)
            else:
                # 兜底：使用原始数据
                self._show_simple_detail_dialog(
                    int(principle_id) if principle_id else 0,
                    principle_name,
                    principle_definition,
                    getattr(principle, "examples", []) or [],
                    principle_category,
                )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    f"#{principle_id}",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                                padding=ft.Padding.all(6),
                                border_radius=6,
                                bgcolor=self._get_category_color(principle_category),
                            ),
                            ft.Text(
                                principle_name,
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
                            principle_definition[:50] + "..."
                            if len(principle_definition) > 50
                            else principle_definition
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
                                    principle_category, size=9, color=COLORS["primary"]
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
            on_click=show_detail,
        )

    def _create_solution_card(
        self, solution: Any, solution_index: int, is_brainstorm: bool = False
    ) -> ft.Container:
        """创建解决方案卡片（头脑风暴结果）"""
        solution_id = getattr(solution, "principle_id", 0)
        solution_name = getattr(solution, "principle_name", "")
        solution_description = getattr(solution, "description", "")
        solution_category = getattr(solution, "category", "物理")
        solution_examples = getattr(solution, "examples", []) or []
        solution_confidence = getattr(solution, "confidence", None)
        is_ai_generated = getattr(solution, "is_ai_generated", False)

        # 4字段结构化数据（头脑风暴专用）
        technical_solution = getattr(solution, "technical_solution", "")
        innovation_point = getattr(solution, "innovation_point", "")
        cross_domain_cases = getattr(solution, "cross_domain_cases", []) or []
        expected_effect = getattr(solution, "expected_effect", "")

        # 复选框切换选中状态
        def toggle_selection(e: ft.Event[Any]) -> None:  # noqa: ARG002
            if solution_index in self._selected_solutions:
                self._selected_solutions.remove(solution_index)
            else:
                self._selected_solutions.append(solution_index)

        # 点击显示解决方案详情弹窗
        def show_solution_detail(e: ft.Event[Any]) -> None:  # noqa: ARG002
            self._show_solution_detail_dialog(
                principle_id=solution_id,
                principle_name=solution_name,
                category=solution_category,
                technical_solution=technical_solution,
                innovation_point=innovation_point,
                cross_domain_cases=cross_domain_cases,
                examples=solution_examples,
            )

        # 复选框
        checkbox = ft.Checkbox(
            value=solution_index in self._selected_solutions,
            on_change=toggle_selection,
            tooltip="选择保存",
        )

        # AI标签
        ai_label = "🤖 AI生成" if is_ai_generated else "📦 本地"
        # 置信度显示
        conf_text = f"{int(solution_confidence * 100)}%" if solution_confidence else ""

        # AI标签
        ai_label = "🤖 AI生成" if is_ai_generated else "📦 本地"
        # 置信度显示
        conf_text = f"{int(solution_confidence * 100)}%" if solution_confidence else ""

        # 头脑风暴模式：4字段结构化卡片
        if is_brainstorm and (
            technical_solution
            or innovation_point
            or cross_domain_cases
            or expected_effect
        ):
            card_content = self._build_structured_card_content(
                checkbox,
                solution_id,
                solution_name,
                solution_category,
                technical_solution,
                innovation_point,
                cross_domain_cases,
                expected_effect,
                ai_label,
                conf_text,
            )
        else:
            # 原有模式
            card_content = ft.Column(
                controls=[
                    # 头部：checkbox + 原理编号 + 名称
                    ft.Row(
                        controls=[
                            checkbox,
                            ft.Container(
                                content=ft.Text(
                                    f"#{solution_id}",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                                padding=ft.Padding.all(6),
                                border_radius=6,
                                bgcolor=self._get_category_color(solution_category),
                            ),
                            ft.Text(
                                solution_name,
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
                            solution_description[:60] + "..."
                            if len(solution_description) > 60
                            else solution_description
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
                                    solution_category, size=9, color=COLORS["primary"]
                                ),
                                padding=3,
                            ),
                            ft.Container(
                                content=ft.Text(ai_label, size=9, color=ft.Colors.GREY),
                                padding=3,
                            ),
                            ft.Container(expand=True),
                            (
                                ft.Text(conf_text, size=9, color=COLORS["primary"])
                                if conf_text
                                else ft.Container()
                            ),
                            ft.Icon(
                                ft.icons.Icons.CHEVRON_RIGHT,
                                size=16,
                                color=ft.Colors.GREY,
                            ),
                        ]
                    ),
                    # 保存按钮
                    ft.Container(height=5),
                    ft.Row(
                        controls=[
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
            )

        return ft.Container(
            content=card_content,
            padding=12,
            border_radius=8,
            bgcolor=ft.Colors.GREY_100,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            on_click=show_solution_detail,
        )

    def _build_structured_card_content(
        self,
        checkbox: ft.Checkbox,
        solution_id: int,
        solution_name: str,
        solution_category: str,
        technical_solution: str,
        innovation_point: str,
        cross_domain_cases: list[str],
        expected_effect: str,  # noqa: ARG002
        ai_label: str,
        conf_text: str,
    ) -> ft.Column:
        """构建4字段结构化卡片内容"""
        # 技术方案
        tech_text = (
            technical_solution[:80] + "..."
            if len(technical_solution) > 80
            else technical_solution
        )
        # 创新点
        innov_text = (
            innovation_point[:50] + "..."
            if len(innovation_point) > 50
            else innovation_point
        )
        # 案例
        cases_text = " | ".join(cross_domain_cases[:2]) if cross_domain_cases else ""

        return ft.Column(
            controls=[
                # 头部：checkbox + 原理编号+名称
                ft.Row(
                    controls=[
                        checkbox,
                        ft.Container(
                            content=ft.Text(
                                f"#{solution_id}",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                            ),
                            padding=ft.Padding.all(6),
                            border_radius=6,
                            bgcolor=self._get_category_color(solution_category),
                        ),
                        ft.Text(
                            solution_name,
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            expand=True,
                        ),
                    ],
                    spacing=8,
                ),
                ft.Container(height=8),
                # 技术方案字段
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                "📋 技术方案",
                                size=10,
                                weight=ft.FontWeight.BOLD,
                                color=COLORS["primary"],
                            ),
                            padding=0,
                        )
                    ]
                ),
                ft.Text(
                    tech_text or "未提供",
                    size=11,
                    color=ft.Colors.GREY_700,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Container(height=5),
                # 创新点字段
                ft.Row(
                    controls=[
                        ft.Text(
                            "💡 创新点",
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=COLORS["secondary"],
                        )
                    ]
                ),
                ft.Text(
                    innov_text or "未提供",
                    size=11,
                    color=ft.Colors.GREY_700,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Container(height=5),
                # 跨领域案例
                ft.Row(
                    controls=[
                        ft.Text(
                            "🌏 案例",
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ORANGE,
                        )
                    ]
                ),
                ft.Text(
                    cases_text or "未提供",
                    size=10,
                    color=ft.Colors.GREY_600,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Container(height=5),
                # 底部：分类标签+AI标签+置信度
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                solution_category, size=9, color=COLORS["primary"]
                            ),
                            padding=3,
                        ),
                        ft.Container(
                            content=ft.Text(ai_label, size=9, color=ft.Colors.GREY),
                            padding=3,
                        ),
                        ft.Container(expand=True),
                        (
                            ft.Text(conf_text, size=9, color=COLORS["primary"])
                            if conf_text
                            else ft.Container()
                        ),
                        ft.Icon(
                            ft.icons.Icons.CHEVRON_RIGHT, size=16, color=ft.Colors.GREY
                        ),
                    ]
                ),
            ],
            spacing=2,
        )

    def _show_principle_detail_dialog(self, principle: Any) -> None:
        """显示原理详情弹窗"""
        from data.models import InventivePrinciple

        if not isinstance(principle, InventivePrinciple):
            # 如果不是 InventivePrinciple 类型，调用简化版
            self._show_simple_detail_dialog(
                principle.id if hasattr(principle, "id") else 0,
                principle.name if hasattr(principle, "name") else "",
                principle.definition if hasattr(principle, "definition") else "",
                principle.examples if hasattr(principle, "examples") else [],
                principle.category if hasattr(principle, "category") else "",
            )
            return

        dialog = ft.AlertDialog(
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
                                    (
                                        ft.Text(
                                            f"标签: {', '.join(principle.tags)}",
                                            size=11,
                                            color=ft.Colors.GREY,
                                        )
                                        if principle.tags
                                        else ft.Container()
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
                        # 底部留白，防止内容被遮挡
                        ft.Container(height=40),
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

    def _show_simple_detail_dialog(
        self,
        principle_id: int,
        principle_name: str,
        definition: str,
        examples: list[str],
        category: str,
    ) -> None:
        """显示简化版详情弹窗（用于Solution对象）"""
        dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            f"#{principle_id}",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        padding=8,
                        border_radius=8,
                        bgcolor=COLORS["primary"],
                    ),
                    ft.Text(principle_name, size=18, weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        # 分类
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Text(
                                        "分类:", size=12, weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            category, size=11, color=ft.Colors.WHITE
                                        ),
                                        padding=5,
                                        border_radius=5,
                                        bgcolor=self._get_category_color(category),
                                    ),
                                ],
                                spacing=10,
                            ),
                            padding=10,
                        ),
                        ft.Divider(),
                        # 核心定义
                        ft.Text("核心定义", size=14, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text(definition, size=13),
                            padding=10,
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=8,
                        ),
                        ft.Divider(),
                        # 示例
                        ft.Text("应用示例", size=14, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Column(
                                controls=(
                                    [ft.Text(f"• {ex}", size=12) for ex in examples]
                                    if examples
                                    else [
                                        ft.Text(
                                            "暂无示例", size=12, color=ft.Colors.GREY
                                        )
                                    ]
                                ),
                                spacing=3,
                            ),
                            padding=5,
                        ),
                    ],
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=400,
                height=350,
                padding=10,
            ),
            actions=[ft.TextButton("关闭", on_click=lambda _: self._close_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.show_dialog(dialog)

    def _show_solution_detail_dialog(
        self,
        principle_id: int,
        principle_name: str,
        category: str,
        technical_solution: str = "",
        innovation_point: str = "",
        cross_domain_cases: list[str] | None = None,
        examples: list[str] | None = None,
    ) -> None:
        """显示头脑风暴解决方案详情弹窗"""
        if cross_domain_cases is None:
            cross_domain_cases = []
        if examples is None:
            examples = []

        # 构建内容控件
        content_controls = []

        # 分类
        content_controls.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text("分类:", size=12, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text(category, size=11, color=ft.Colors.WHITE),
                            padding=5,
                            border_radius=5,
                            bgcolor=self._get_category_color(category),
                        ),
                    ],
                    spacing=10,
                ),
                padding=10,
            )
        )

        content_controls.append(ft.Divider())

        # 技术方向（原核心定义）
        if technical_solution:
            content_controls.append(
                ft.Text("技术方向", size=14, weight=ft.FontWeight.BOLD)
            )
            content_controls.append(
                ft.Container(
                    content=ft.Text(technical_solution, size=13),
                    padding=10,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=8,
                )
            )
            content_controls.append(ft.Container(height=5))

        # 创新点
        if innovation_point:
            content_controls.append(
                ft.Text("创新点", size=14, weight=ft.FontWeight.BOLD)
            )
            content_controls.append(
                ft.Container(
                    content=ft.Text(innovation_point, size=13),
                    padding=10,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=8,
                )
            )
            content_controls.append(ft.Container(height=5))

        # 案例（原应用示例）
        if cross_domain_cases:
            cases_text = "\n".join([f"• {c}" for c in cross_domain_cases])
            content_controls.append(ft.Text("案例", size=14, weight=ft.FontWeight.BOLD))
            content_controls.append(
                ft.Container(
                    content=ft.Text(cases_text, size=12),
                    padding=10,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=8,
                )
            )
            content_controls.append(ft.Container(height=5))

        # 如果没有技术方向和创新点，显示原有的定义和示例
        if not technical_solution and not innovation_point and examples:
            content_controls.append(
                ft.Text("核心定义", size=14, weight=ft.FontWeight.BOLD)
            )
            content_controls.append(
                ft.Container(
                    content=ft.Text(
                        getattr(self, "_current_solution", {}).get("description", ""),
                        size=13,
                    ),
                    padding=10,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=8,
                )
            )
            content_controls.append(ft.Container(height=5))
            content_controls.append(
                ft.Text("应用示例", size=14, weight=ft.FontWeight.BOLD)
            )
            content_controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=(
                            [ft.Text(f"• {ex}", size=12) for ex in examples]
                            if examples
                            else [ft.Text("暂无示例", size=12, color=ft.Colors.GREY)]
                        ),
                        spacing=3,
                    ),
                    padding=5,
                )
            )

        # 底部留白，防止内容被遮挡
        content_controls.append(ft.Container(height=40))

        dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            f"#{principle_id}",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        padding=8,
                        border_radius=8,
                        bgcolor=COLORS["primary"],
                    ),
                    ft.Text(principle_name, size=18, weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=content_controls, spacing=8, scroll=ft.ScrollMode.AUTO
                ),
                width=400,
                height=450,
                padding=10,
            ),
            actions=[ft.TextButton("关闭", on_click=lambda _: self._close_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.show_dialog(dialog)

    def _close_dialog(self) -> None:
        """关闭弹窗"""
        # 关闭overlay弹窗
        if hasattr(self, "_solutions_overlay") and self._solutions_overlay:
            try:
                self._page.remove(self._solutions_overlay)
            except Exception:
                pass
            self._solutions_overlay = None
        if hasattr(self, "_detail_overlay") and self._detail_overlay:
            try:
                self._page.remove(self._detail_overlay)
            except Exception:
                pass
            self._detail_overlay = None
        # 关闭AlertDialog
        try:
            self._page.pop_dialog()
        except Exception:
            pass

    def _get_category_color(self, category: str) -> str:
        """获取分类颜色"""
        from config.constants import CATEGORY_COLORS

        return CATEGORY_COLORS.get(category, "#2196F3")
