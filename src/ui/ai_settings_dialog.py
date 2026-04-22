"""
AI设置对话框
"""

import logging
from collections.abc import Callable
from typing import Any

import flet as ft

from config.constants import COLORS

logger = logging.getLogger(__name__)


class AISettingsDialog:
    """AI设置对话框"""

    def __init__(
        self,
        page: ft.Page,
        on_settings_changed: Callable | None = None,
    ) -> None:
        self.page = page
        self.on_settings_changed = on_settings_changed

        # 当前设置
        self.settings: dict[str, Any] = {
            "provider": "deepseek",
            "api_key": "",
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
        }

        # UI组件
        self.dialog: ft.AlertDialog | None = None
        self.providerDropdown: ft.Dropdown | None = None
        self.apiKeyField: ft.TextField | None = None
        self.baseUrlField: ft.TextField | None = None
        self.modelField: ft.TextField | None = None
        self.testConnectionBtn: ft.Button | None = None
        self.connectionStatusText: ft.Text | None = None
        self.testLoading: ft.ProgressRing | None = None

    def _show_snack_bar(self, message: str) -> None:
        """显示提示消息（使用 AlertDialog 模拟 SnackBar）"""
        dlg = ft.AlertDialog(
            modal=False,
            content=ft.Text(message),
        )
        self.page.show_dialog(dlg)
        # 使用 run_task 自动关闭对话框
        self.page.run_task(self._auto_close_dialog, dlg)

    async def _auto_close_dialog(self, dlg: ft.AlertDialog) -> None:
        """自动关闭对话框"""
        import asyncio

        await asyncio.sleep(2)
        dlg.open = False
        self.page.update()

    def show(self) -> None:
        """显示设置对话框"""
        logger.info("AISettingsDialog.show() 被调用")
        if self.dialog is None:
            self._load_current_settings()
            self._create_dialog()
        else:
            self._load_current_settings()
        assert self.dialog is not None
        self.page.show_dialog(self.dialog)

    def _load_current_settings(self) -> None:
        """加载当前设置（在打开对话框时调用，解密所有供应商密钥到内存字典）"""
        from config.settings import _simple_decrypt, get_app_settings

        # AppSettings 是单例
        settings = get_app_settings()

        def try_decrypt(api_key: str) -> str:
            """循环解密直到得到明文（处理双重或多重编码）"""
            if not api_key:
                return api_key
            for _ in range(10):
                decrypted = _simple_decrypt(api_key)
                if not decrypted:
                    break
                # 检查解密结果是否像 API key（sk- 开头）
                if decrypted.startswith("sk-") or decrypted.startswith("api-"):
                    return decrypted
                # 如果不是 sk- 格式，尝试再次解密
                api_key = decrypted
            return api_key

        # 解密所有供应商的API密钥，存到 self.settings["providers_data"] 字典
        providers_data = {}
        for provider, provider_config in settings.config.ai_providers_config.items():
            if provider_config:
                api_key = provider_config.api_key or ""
                if api_key:
                    api_key = try_decrypt(api_key)
                providers_data[provider] = {
                    "api_key": api_key,
                    "base_url": provider_config.base_url,
                    "model": provider_config.model,
                }
            else:
                providers_data[provider] = {"api_key": "", "base_url": "", "model": ""}

        self.settings["providers_data"] = providers_data

        # 使用当前供应商的配置
        current_provider = settings.config.ai_provider
        self.settings["provider"] = current_provider
        if current_provider in providers_data:
            self.settings["api_key"] = providers_data[current_provider]["api_key"]
            self.settings["base_url"] = providers_data[current_provider]["base_url"]
            self.settings["model"] = providers_data[current_provider]["model"]
        else:
            self.settings["api_key"] = ""
            self.settings["base_url"] = "https://api.deepseek.com/v1"
            self.settings["model"] = "deepseek-chat"

        # 如果 UI 控件已创建，更新它们的值
        if self.providerDropdown is not None:
            self.providerDropdown.value = self.settings["provider"]
        if self.apiKeyField is not None:
            self.apiKeyField.value = self.settings["api_key"]
        if self.baseUrlField is not None:
            self.baseUrlField.value = self.settings["base_url"]
        if self.modelField is not None:
            self.modelField.value = self.settings["model"]

    def _create_dialog(self) -> None:
        """创建对话框"""
        self.providerDropdown = ft.Dropdown(
            label="AI提供商",
            value=self.settings["provider"],
            options=[
                ft.dropdown.Option("deepseek", "DeepSeek"),
                ft.dropdown.Option("openrouter", "OpenRouter"),
                ft.dropdown.Option("openai-format", "Openai-format"),
            ],
            on_select=self._on_provider_changed,
        )

        self.apiKeyField = ft.TextField(
            label="API密钥",
            value=self.settings["api_key"],
            hint_text="sk-...",
            password=True,
            can_reveal_password=True,
            expand=True,
        )

        self.baseUrlField = ft.TextField(
            label="Base URL",
            value=self.settings["base_url"],
            hint_text="https://api.openrouter.ai/api/v1",
            expand=True,
        )

        self.modelField = ft.TextField(
            label="模型",
            value=self.settings["model"],
            hint_text="deepseek/deepseek-chat",
            expand=True,
        )

        # 连接测试相关
        self.testConnectionBtn = ft.Button(
            content=ft.Text("测试连接"),
            icon=ft.icons.Icons.NETWORK_CHECK,
            on_click=self._on_test_connection,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE, bgcolor=COLORS.get("secondary", "#FF9800")
            ),
        )
        self.testLoading = ft.ProgressRing(width=20, height=20, visible=False)
        self.connectionStatusText = ft.Text("", size=12)

        content = ft.Column(
            controls=[
                self.providerDropdown,
                self.apiKeyField,
                self.baseUrlField,
                self.modelField,
                ft.Container(height=10),
                ft.Divider(),
                ft.Container(height=5),
                ft.Row(
                    controls=[
                        self.testConnectionBtn,
                        self.testLoading,
                        self.connectionStatusText,
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=5),
                ft.Text(
                    "密钥已使用算法加密安全的保存到本地", size=12, color=ft.Colors.GREY
                ),
            ],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("AI设置"),
            content=content,
            actions=[
                ft.TextButton("取消", on_click=self._on_cancel),
                ft.TextButton("保存", on_click=self._on_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _on_provider_changed(self, e: ft.Event[ft.Dropdown]) -> None:
        """提供商变更"""
        assert self.baseUrlField is not None and self.modelField is not None
        provider = e.control.value if e.control.value else "deepseek"

        # 从 providers_data 字典读取（切换时不解密）
        providers_data = self.settings.get("providers_data", {})
        if provider in providers_data:
            self.baseUrlField.value = providers_data[provider].get("base_url", "")
            self.modelField.value = providers_data[provider].get("model", "")
            if self.apiKeyField:
                self.apiKeyField.value = providers_data[provider].get("api_key", "")
        else:
            # 使用默认值
            if provider == "deepseek":
                self.baseUrlField.value = "https://api.deepseek.com/v1"
                self.modelField.value = "deepseek-chat"
            elif provider == "openrouter":
                self.baseUrlField.value = "https://openrouter.ai/api/v1"
                self.modelField.value = "deepseek/deepseek-chat"
            elif provider == "openai-format":
                self.baseUrlField.value = "https://api.openai.com/v1"
                self.modelField.value = "gpt-4"
        self.page.update()

    def _on_cancel(self, _: ft.Event[ft.TextButton]) -> None:
        """取消"""
        self.page.pop_dialog()

    def _on_save(self, _: ft.Event[ft.TextButton]) -> None:
        """保存设置"""
        assert self.providerDropdown is not None and self.apiKeyField is not None
        assert self.baseUrlField is not None and self.modelField is not None
        provider = self.providerDropdown.value if self.providerDropdown.value else ""
        api_key = self.apiKeyField.value.strip()
        base_url = self.baseUrlField.value.strip()
        model = self.modelField.value.strip()

        if not api_key:
            self._show_snack_bar("请输入API密钥")
            return

        # 关闭对话框
        self.page.pop_dialog()

        # 使用 page.run_task 执行异步保存
        self.page.run_task(
            self._save_settings_async, api_key, provider, base_url, model
        )

    async def _save_settings_async(
        self, api_key: str, provider: str, base_url: str, model: str
    ) -> None:
        """异步保存设置"""
        from ai.ai_client import get_ai_manager
        from config.settings import get_app_settings
        from data.models import ProviderConfig

        try:
            settings = get_app_settings()
            await settings.load()

            # 更新当前供应商
            settings.ai_provider = provider

            # 更新对应供应商的配置
            settings.config.set_provider_config(
                provider,
                ProviderConfig(api_key=api_key, base_url=base_url, model=model),
            )

            success = await settings.save()
            if not success:
                logger.error("保存AI设置失败")
                return

            logger.info("AI设置已保存")

            # 重新初始化AI管理器
            ai_manager = get_ai_manager()
            ai_manager.initialize(
                api_key=api_key, provider=provider, base_url=base_url, model=model
            )

            if self.on_settings_changed:
                self.on_settings_changed()

        except Exception as ex:
            logger.error(f"保存AI设置失败: {ex}")

    def _on_test_connection(self, _: ft.Event[ft.Button]) -> None:
        """手动测试AI连接"""
        assert self.apiKeyField is not None and self.baseUrlField is not None
        assert self.modelField is not None and self.providerDropdown is not None
        assert (
            self.connectionStatusText is not None and self.testConnectionBtn is not None
        )
        assert self.testLoading is not None

        api_key = self.apiKeyField.value.strip()
        if not api_key:
            self.connectionStatusText.value = "请先输入API密钥"
            self.connectionStatusText.color = ft.Colors.RED
            self.page.update()
            return

        # 显示加载状态
        self.testConnectionBtn.disabled = True
        self.testLoading.visible = True
        self.connectionStatusText.value = "正在测试..."
        self.connectionStatusText.color = ft.Colors.GREY
        self.page.update()

        # 使用 run_task 执行异步测试
        self.page.run_task(
            self._test_connection_async,
            api_key,
            self.providerDropdown.value or "deepseek",
            self.baseUrlField.value.strip(),
            self.modelField.value.strip(),
        )

    async def _test_connection_async(
        self, api_key: str, provider: str, base_url: str, model: str
    ) -> None:
        """异步测试AI连接"""
        import time

        from ai.ai_client import get_ai_manager

        assert (
            self.connectionStatusText is not None and self.testConnectionBtn is not None
        )
        assert self.testLoading is not None

        start_time = None
        try:
            start_time = time.time()

            # 临时初始化AI客户端进行测试
            ai_manager = get_ai_manager()
            ai_manager.initialize(
                api_key=api_key, provider=provider, base_url=base_url, model=model
            )

            # 尝试获取客户端并发送一个简单请求测试
            client = ai_manager.get_client()
            if client:
                # 发送一个简单的 chat completion 请求测试连接
                from openai import AsyncOpenAI  # type: ignore[import-not-found]

                test_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                await test_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5,
                )
                elapsed = (time.time() - start_time) * 1000

                # 测试成功
                self.connectionStatusText.value = f"连接成功 (延迟: {elapsed:.0f}ms)"
                self.connectionStatusText.color = ft.Colors.GREEN
                ai_manager.set_connected(True)
                logger.info(f"AI连接测试成功，延迟: {elapsed:.0f}ms")
            else:
                self.connectionStatusText.value = "连接失败: 无法获取客户端"
                self.connectionStatusText.color = ft.Colors.RED
                ai_manager.set_connected(False)

        except Exception as ex:
            elapsed = (time.time() - start_time) * 1000 if start_time is not None else 0
            error_msg = str(ex)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                self.connectionStatusText.value = "认证失败: API密钥无效"
            elif "403" in error_msg:
                self.connectionStatusText.value = "访问被拒绝: 请检查API权限"
            elif "404" in error_msg:
                self.connectionStatusText.value = "未找到: 请检查Base URL"
            elif "timeout" in error_msg.lower():
                self.connectionStatusText.value = "连接超时"
            elif "connection" in error_msg.lower():
                self.connectionStatusText.value = "连接失败: 请检查网络"
            else:
                self.connectionStatusText.value = "连接失败"
            self.connectionStatusText.color = ft.Colors.RED
            logger.error(f"AI连接测试失败: {ex}")
        finally:
            self.testConnectionBtn.disabled = False
            self.testLoading.visible = False
            self.page.update()
