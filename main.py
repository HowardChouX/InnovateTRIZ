#!/usr/bin/env python3
"""
TRIZ Android应用主入口
"""

import flet as ft
import asyncio
import logging
import sys
import os
from typing import Optional

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.config.constants import APP_NAME, APP_VERSION, COLORS
from src.data.local_storage import LocalStorage
from src.ai.ai_client import get_ai_manager
from src.ai.connectivity import check_ai_connectivity, AIConnectivityDetector
from src.config.settings import AppSettings
from src.ui.app_shell import TRIZAppShell
from src.ui.matrix_tab import MatrixTab
from src.ui.principles_tab import PrinciplesTab
from src.ui.settings_tab import SettingsTab

# 配置日志
import os
from pathlib import Path

# 确保日志目录存在
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 配置日志：同时输出到控制台和文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 控制台
        logging.FileHandler(log_dir / "triz_app.log", encoding="utf-8")  # 文件
    ]
)
logger = logging.getLogger(__name__)


class TRIZApp:
    """TRIZ应用主类"""

    def __init__(self):
        self.page: Optional[ft.Page] = None
        self.storage: Optional[LocalStorage] = None
        self.settings: Optional[AppSettings] = None
        self.app_shell: Optional[TRIZAppShell] = None

    async def main(self, page: ft.Page):
        """主函数"""
        self.page = page
        await self._setup_page()
        await self._initialize_components()
        await self._show_main_interface()

    async def _setup_page(self):
        """设置页面"""
        # 页面配置
        self.page.title = f"{APP_NAME} v{APP_VERSION}"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.spacing = 0

        # 设置主题颜色
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=COLORS["primary"],
                secondary=COLORS["secondary"],
                surface=COLORS["surface"],
            )
        )

        logger.info("页面设置完成")

    async def _initialize_components(self):
        """初始化组件"""
        try:
            # 初始化设置
            self.settings = AppSettings()
            await self.settings.load()

            # 初始化存储
            self.storage = LocalStorage()
            self.storage.initialize()

            # 初始化AI管理器
            ai_manager = get_ai_manager()
            if self.settings.ai_api_key:
                ai_manager.initialize(
                    api_key=self.settings.ai_api_key,
                    provider=self.settings.ai_provider,
                    base_url=self.settings.ai_base_url,
                    model=self.settings.ai_model
                )
                logger.info("AI管理器初始化完成")
            else:
                logger.info("AI管理器未初始化（无API密钥）")

            # 初始化AppShell
            self.app_shell = TRIZAppShell(self.page)

            # 添加三个Tab
            self.matrix_tab = MatrixTab(self.page, self.storage)
            principles_tab = PrinciplesTab(self.page)
            settings_tab = SettingsTab(self.page, self.storage)

            self.app_shell.add_tab("matrix", self.matrix_tab)
            self.app_shell.add_tab("principles", principles_tab)
            self.app_shell.add_tab("settings", settings_tab)

            logger.info("所有组件初始化完成")

        except Exception as e:
            logger.error(f"初始化组件失败: {e}")
            await self._show_error_page(f"初始化失败: {str(e)}")

    async def _show_main_interface(self):
        """显示主界面"""
        if not self.app_shell:
            await self._show_error_page("界面初始化失败")
            return

        try:
            # 显示AppShell
            self.app_shell.show()

            # 显示欢迎消息
            await self._show_welcome_message()

            logger.info("主界面显示完成")

        except Exception as e:
            logger.error(f"显示主界面失败: {e}")
            await self._show_error_page(f"界面加载失败: {str(e)}")

    async def _show_welcome_message(self):
        """显示欢迎消息"""
        welcome_text = f"欢迎使用{APP_NAME}！\n版本: {APP_VERSION}"

        # 检查AI状态并测试联通性
        ai_manager = get_ai_manager()
        if ai_manager.is_enabled():
            # 测试AI联通性
            connectivity = await check_ai_connectivity()
            # 更新全局连接状态
            ai_manager.set_connected(connectivity.is_connected)
            if connectivity.is_connected:
                welcome_text += f"\n\n✅ AI已连接 ({connectivity.provider})"
                if connectivity.latency_ms:
                    welcome_text += f" - 延迟: {connectivity.latency_ms:.0f}ms"
            else:
                welcome_text += f"\n\n⚠️  AI连接失败: {connectivity.message}"
                welcome_text += "\n请检查网络和API密钥设置"
        else:
            ai_manager.set_connected(False)
            welcome_text += "\n\n⚠️  AI智能增强未启用（需要配置API密钥）"

        # 刷新MatrixTab的AI按钮状态
        if hasattr(self, 'matrix_tab') and self.matrix_tab:
            self.matrix_tab._update_ai_buttons()

        # 显示snackbar消息
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(welcome_text),
            duration=4000
        )
        self.page.snack_bar.open = True
        self.page.update()

    async def _show_error_page(self, error_message: str):
        """显示错误页面"""
        self.page.clean()

        error_content = ft.Column(
            controls=[
                ft.Icon(ft.icons.Icons.WARNING_AMBER_ROUNDED, size=64, color=ft.Colors.RED),
                ft.Text("应用启动失败", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(error_message, size=16, color=ft.Colors.GREY),
                ft.Divider(),
                ft.Text("请尝试：", size=14),
                ft.Text("1. 检查网络连接", size=12),
                ft.Text("2. 重启应用", size=12),
                ft.Text("3. 联系技术支持", size=12),
                ft.Button(
                    "重试",
                    icon=ft.icons.Icons.REFRESH,
                    on_click=lambda e: self._restart_app()
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )

        self.page.add(
            ft.Container(
                content=error_content,
                alignment=ft.alignment.Alignment(0.5, 0.5),
                expand=True
            )
        )

        self.page.update()

    def _restart_app(self):
        """重启应用"""
        asyncio.create_task(self._restart_async())

    async def _restart_async(self):
        """异步重启"""
        self.page.clean()
        await self._initialize_components()
        await self._show_main_interface()


def main():
    """应用入口点"""
    import argparse

    # 命令行参数解析
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{APP_VERSION}")
    parser.add_argument(
        "--mode",
        choices=["web", "desktop", "apk"],
        default="web",
        help="运行模式: web(浏览器), desktop(桌面窗口), apk(移动应用)"
    )
    parser.add_argument("--port", type=int, default=8550, help="Web模式端口")
    args = parser.parse_args()

    # 检查Python版本
    if sys.version_info < (3, 10):
        print("错误: 需要Python 3.10或更高版本")
        sys.exit(1)

    print(f"🚀 启动 {APP_NAME} v{APP_VERSION}")
    print(f"📱 运行模式: {args.mode.upper()}")
    print("=" * 50)

    # 运行Flet应用
    try:
        if args.mode == "web":
            # Web模式（用于测试）
            ft.app(
                target=TRIZApp().main,
                view=ft.AppView.WEB_BROWSER,
                port=args.port,
                assets_dir="assets"
            )
        elif args.mode == "desktop":
            # 桌面模式
            ft.app(
                target=TRIZApp().main,
                view=ft.AppView.FLET_APP,
                assets_dir="assets"
            )
        else:
            # APK模式（移动应用）- 不需要指定view
            # 在Android/iOS上自动适配
            ft.app(
                target=TRIZApp().main,
                assets_dir="assets"
            )

    except KeyboardInterrupt:
        print("\n👋 应用已退出")
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")
        logger.error(f"应用启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()