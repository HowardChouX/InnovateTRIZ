"""
AI设置对话框
"""

import flet as ft
import logging
from typing import Optional

from ..ai.connectivity import check_ai_connectivity_sync

logger = logging.getLogger(__name__)


class AISettingsDialog:
    """AI设置对话框"""

    def __init__(self, page: ft.Page, on_settings_changed=None):
        self.page = page
        self.on_settings_changed = on_settings_changed

        # 当前设置
        self.settings = {
            "provider": "deepseek",
            "api_key": "",
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat"
        }

        # UI组件
        self.dialog: Optional[ft.AlertDialog] = None
        self.providerDropdown: Optional[ft.Dropdown] = None
        self.apiKeyField: Optional[ft.TextField] = None
        self.baseUrlField: Optional[ft.TextField] = None
        self.modelField: Optional[ft.TextField] = None

    def show(self):
        """显示设置对话框"""
        self._load_current_settings()
        self._create_dialog()
        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()

    def _load_current_settings(self):
        """加载当前设置"""
        from src.ai.ai_client import get_ai_manager

        ai_manager = get_ai_manager()

        # 从 AI 管理器获取当前配置
        if ai_manager.is_enabled():
            self.settings["provider"] = ai_manager.config.get("provider", "deepseek")
            self.settings["api_key"] = ai_manager.config.get("api_key", "")
            self.settings["base_url"] = ai_manager.config.get("base_url", "https://api.deepseek.com/v1")
            self.settings["model"] = ai_manager.config.get("model", "deepseek-chat")
        else:
            # 使用默认值
            self.settings = {
                "provider": "deepseek",
                "api_key": "",
                "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat"
            }

    def _create_dialog(self):
        """创建对话框"""
        self.providerDropdown = ft.Dropdown(
            label="AI提供商",
            value=self.settings["provider"],
            options=[
                ft.dropdown.Option("openrouter", "OpenRouter"),
                ft.dropdown.Option("deepseek", "DeepSeek"),
                ft.dropdown.Option("openai", "OpenAI"),
            ],
            on_change=self._on_provider_changed
        )

        self.apiKeyField = ft.TextField(
            label="API密钥",
            value=self.settings["api_key"],
            hint_text="sk-...",
            password=True,
            can_reveal_password=True,
            expand=True
        )

        self.baseUrlField = ft.TextField(
            label="Base URL",
            value=self.settings["base_url"],
            hint_text="https://api.openrouter.ai/api/v1",
            expand=True
        )

        self.modelField = ft.TextField(
            label="模型",
            value=self.settings["model"],
            hint_text="deepseek/deepseek-chat",
            expand=True
        )

        content = ft.Column(
            controls=[
                ft.Text("配置AI API设置", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.providerDropdown,
                self.apiKeyField,
                self.baseUrlField,
                self.modelField,
                ft.Container(height=10),
                ft.Text("提示: API密钥将安全存储在本地", size=12, color=ft.colors.GREY)
            ],
            spacing=15,
            scroll=ft.ScrollMode.AUTO
        )

        self.dialog = ft.AlertDialog(
            title=ft.Text("AI设置"),
            content=content,
            actions=[
                ft.TextButton("保存", on_click=self._on_save),
                ft.TextButton("取消", on_click=self._on_cancel)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

    def _on_provider_changed(self, e: ft.ControlEvent):
        """提供商变更"""
        provider = e.control.value
        if provider == "deepseek":
            self.baseUrlField.value = "https://api.deepseek.com/v1"
            self.modelField.value = "deepseek-chat"
        elif provider == "openrouter":
            self.baseUrlField.value = "https://openrouter.ai/api/v1"
            self.modelField.value = "deepseek/deepseek-chat"
        elif provider == "openai":
            self.baseUrlField.value = "https://api.openai.com/v1"
            self.modelField.value = "gpt-4"
        self.page.update()

    def _on_save(self, e: ft.ControlEvent):
        """保存设置"""
        provider = self.providerDropdown.value
        api_key = self.apiKeyField.value.strip()
        base_url = self.baseUrlField.value.strip()
        model = self.modelField.value.strip()

        if not api_key:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("请输入API密钥"), duration=3000)
            )
            return

        # 使用 AppSettings 标准流程保存（自动加密）
        import asyncio
        from src.config.settings import get_app_settings

        async def _do_save():
            settings = get_app_settings()
            await settings.load()  # 先加载现有配置

            # 更新AI相关配置
            settings.ai_api_key = api_key
            settings.ai_provider = provider
            settings.ai_base_url = base_url
            settings.ai_model = model

            # 保存（会自动加密api_key）
            success = await settings.save()
            if not success:
                raise Exception("保存失败")

            return settings.config_file

        try:
            config_file = asyncio.run(_do_save())
            logger.info(f"AI设置已保存到: {config_file}")
        except Exception as ex:
            logger.error(f"保存设置失败: {ex}")
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"保存失败: {ex}"), duration=3000)
            )
            return

        # 重新初始化AI管理器
        from src.ai.ai_client import get_ai_manager
        ai_manager = get_ai_manager()
        ai_manager.initialize(
            api_key=api_key,
            provider=provider,
            base_url=base_url,
            model=model
        )

        logger.info(f"AI设置已保存: provider={provider}, model={model}")

        self.dialog.open = False
        self.page.update()

        # 测试AI联通性
        connectivity = check_ai_connectivity_sync()
        if connectivity.is_connected:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"✅ AI设置已保存并连接成功 ({connectivity.provider}, 延迟: {connectivity.latency_ms:.0f}ms)"),
                    duration=4000
                )
            )
        else:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"⚠️  AI设置已保存但连接失败: {connectivity.message}"),
                    duration=4000
                )
            )

        if self.on_settings_changed:
            self.on_settings_changed()

    def _on_cancel(self, e: ft.ControlEvent):
        """取消"""
        self.dialog.open = False
        self.page.update()
