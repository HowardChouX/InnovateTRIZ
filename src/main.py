#!/usr/bin/env python3
"""
TRIZ Android应用主入口
（与根目录 main.py 功能相同，作为 flet build 的入口点）
"""

import flet as ft
import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径（让 from src.xxx 能够正常工作）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config.constants import APP_NAME, APP_VERSION, COLORS
from src.data.local_storage import LocalStorage
from src.ai.ai_client import get_ai_manager
from src.config.settings import AppSettings, get_app_settings
from src.ui.app_shell import TRIZAppShell
from src.ui.matrix_tab import MatrixTab
from src.ui.principles_tab import PrinciplesTab
from src.ui.settings_tab import SettingsTab

# 配置日志（仅控制台，避免Android文件权限问题）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # 仅控制台
)


def _is_android_env() -> bool:
    """检测Android环境（Flet官方推荐方式）"""
    if os.getenv("FLET_PLATFORM") == "android":
        return True
    if sys.platform == "android":
        return True
    if "ANDROID" in os.environ.get("ANDROID_ROOT", ""):
        return True
    if "ANDROID_DATA" in os.environ:
        return True
    return False


try:
    app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
    if app_data_path:
        log_dir = Path(app_data_path) / "logs"
    elif _is_android_env():
        # Android 环境回退到当前目录
        log_dir = Path(".") / ".triz_logs"
    else:
        # 桌面环境
        config_home = os.getenv("XDG_CONFIG_HOME") or os.path.join(
            Path.home(), ".config"
        )
        log_dir = Path(config_home) / "triz-assistant" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "triz_app.log", encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logging.getLogger().addHandler(file_handler)
except Exception:
    pass  # Android上文件日志可能失败，使用控制台日志即可

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
        assert self.page is not None
        await self._setup_page()
        await self._initialize_components()
        await self._show_main_interface()

    async def _setup_page(self):
        """设置页面"""
        assert self.page is not None
        # 页面配置
        self.page.title = f"{APP_NAME} v{APP_VERSION}"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.spacing = 0
        self.page.bgcolor = COLORS.get("surface", "#F5F5F5")

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
        assert self.page is not None
        try:
            # 初始化设置（使用全局单例）
            self.settings = get_app_settings()
            await self.settings.load()

            # 初始化存储
            self.storage = LocalStorage()
            self.storage.initialize()

            # 初始化AI管理器 - 需要先解密密钥
            ai_manager = get_ai_manager()
            # 获取当前供应商的配置并解密
            current_provider = self.settings.ai_provider
            provider_config = self.settings.config.ai_providers_config.get(
                current_provider
            )
            if provider_config and provider_config.api_key:
                # 解密密钥
                from src.config.settings import _simple_decrypt

                api_key = (
                    _simple_decrypt(provider_config.api_key) or provider_config.api_key
                )
                if api_key:
                    ai_manager.initialize(
                        api_key=api_key,
                        provider=current_provider,
                        base_url=provider_config.base_url,
                        model=provider_config.model,
                    )
                    logger.info("AI管理器初始化完成")
                    # 静默测试AI连接
                    self.page.run_task(self._silent_test_ai_connection)
                else:
                    logger.info("AI管理器未初始化（密钥解密失败）")
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

    async def _silent_test_ai_connection(self):
        """静默测试AI连接"""
        import time
        from src.ai.ai_client import get_ai_manager
        from src.ui.state import get_ai_state_manager

        ai_manager = get_ai_manager()
        if not ai_manager.is_enabled():
            return

        try:
            start_time = time.time()
            is_connected = await ai_manager.test_ai_connection()
            elapsed_ms = (time.time() - start_time) * 1000

            ai_manager.set_connected(is_connected)
            logger.info(
                f"AI静默连接测试完成: {'成功' if is_connected else '失败'}, 延迟: {elapsed_ms:.0f}ms"
            )

            # 通知AI状态变化
            ai_state = get_ai_state_manager()
            ai_state.update_status(ai_manager.is_enabled(), is_connected)

        except Exception as e:
            logger.error(f"AI静默连接测试失败: {e}")
            ai_manager.set_connected(False)

    async def _show_main_interface(self):
        """显示主界面"""
        if not self.app_shell:
            await self._show_error_page("界面初始化失败")
            return

        try:
            # 显示AppShell
            self.app_shell.show()

            logger.info("主界面显示完成")

        except Exception as e:
            logger.error(f"显示主界面失败: {e}")
            await self._show_error_page(f"界面加载失败: {str(e)}")

    async def _show_error_page(self, error_message: str):
        """显示错误页面"""
        assert self.page is not None
        self.page.clean()

        error_content = ft.Column(
            controls=[
                ft.Icon(
                    ft.icons.Icons.WARNING_AMBER_ROUNDED, size=64, color=ft.Colors.RED
                ),
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
                    on_click=lambda e: self._restart_app(),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )

        self.page.add(
            ft.Container(
                content=error_content,
                alignment=ft.alignment.Alignment(0.5, 0.5),
                expand=True,
            )
        )

        self.page.update()

    def _restart_app(self):
        """重启应用"""
        asyncio.create_task(self._restart_async())

    async def _restart_async(self):
        """异步重启"""
        assert self.page is not None
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
        help="运行模式: web(浏览器), desktop(桌面窗口), apk(移动应用)",
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
            ft.run(
                TRIZApp().main,
                view=ft.AppView.WEB_BROWSER,
                port=args.port,
                assets_dir="assets",
            )
        else:
            # 桌面/APK模式 - Flet自动根据运行平台选择
            ft.run(TRIZApp().main, assets_dir="assets")

    except KeyboardInterrupt:
        print("\n👋 应用已退出")
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")
        logger.error(f"应用启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
