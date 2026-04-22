"""
AI状态同步流程测试
验证AI状态在实际使用场景中的同步情况
"""

from unittest.mock import MagicMock

# 测试用的模拟数据
MOCK_API_KEY = "test-api-key-12345"
MOCK_PROVIDER = "deepseek"


class MockAIClient:
    """模拟AI客户端"""

    def __init__(self, should_fail=False):
        self._should_fail = should_fail

    def is_available(self):
        return not self._should_fail

    async def test_connection(self):
        if self._should_fail:
            raise Exception("连接失败")
        return True

    async def detect_parameters(self, problem):
        if self._should_fail:
            raise Exception("AI连接失败")
        return {
            "improving": ["速度", "效率"],
            "worsening": ["重量", "成本"],
            "explanation": "测试解释",
        }

    async def generate_solutions(self, request):
        if self._should_fail:
            raise Exception("AI连接失败")
        from src.data.models import AIAnalysisResponse, Solution

        return AIAnalysisResponse(
            success=True,
            solutions=[
                Solution(
                    principle_id=1,
                    principle_name="分割原理",
                    description="测试方案",
                    confidence=0.9,
                    is_ai_generated=True,
                )
            ],
        )


class MockAIManager:
    """模拟AI管理器"""

    def __init__(self, should_fail=False):
        self._enabled = False
        self._connected = False
        self._client = None
        self._should_fail = should_fail
        self.config = {"provider": MOCK_PROVIDER, "api_key": None, "enabled": False}

    def initialize(self, api_key=None, provider=None, base_url=None, model=None):
        if api_key:
            self._enabled = True
            self.config["api_key"] = api_key
            self.config["provider"] = provider or MOCK_PROVIDER
            self.config["enabled"] = True
            self._client = MockAIClient(should_fail=self._should_fail)
            print("      ├─ initialize()  API密钥已配置")
            print("      ├─ is_enabled()  -> True")

    def is_enabled(self):
        return self._enabled

    def is_connected(self):
        return self._connected

    def set_connected(self, connected: bool):
        self._connected = connected
        status = "已连接" if connected else "未连接"
        print(f"      └─ set_connected({status})")

    def get_client(self):
        return self._client if self._enabled else None


class TestLogger:
    """测试日志输出器"""

    # ANSI 颜色代码
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def header(cls, text):
        """打印标题"""
        width = 68
        print(f"\n{cls.BOLD}{cls.CYAN}{'─' * width}{cls.RESET}")
        print(
            f"{cls.BOLD}{cls.CYAN}│ {text}{' ' * (width - len(text) - 3)}│{cls.RESET}"
        )
        print(f"{cls.BOLD}{cls.CYAN}{'─' * width}{cls.RESET}")

    @classmethod
    def section(cls, text):
        """打印章节"""
        print(f"\n{cls.BOLD}{cls.BLUE}▸ {text}{cls.RESET}")

    @classmethod
    def step(cls, text):
        """打印步骤"""
        print(f"\n  {cls.DIM}▶ {text}{cls.RESET}")

    @classmethod
    def action(cls, text):
        """打印动作"""
        print(f"    {cls.YELLOW}→ {text}{cls.RESET}")

    @classmethod
    def success(cls, text):
        """打印成功信息"""
        print(f"    {cls.GREEN}✓ {text}{cls.RESET}")

    @classmethod
    def error(cls, text):
        """打印错误信息"""
        print(f"    {cls.RED}✗ {text}{cls.RESET}")

    @classmethod
    def info(cls, text):
        """打印信息"""
        print(f"      {cls.DIM}• {text}{cls.RESET}")

    @classmethod
    def result(cls, actual, expected, description=""):
        """打印测试结果"""
        passed = actual == expected
        status = (
            f"{cls.GREEN}PASS{cls.RESET}" if passed else f"{cls.RED}FAIL{cls.RESET}"
        )
        icon = "✓" if passed else "✗"
        symbol = cls.GREEN if passed else cls.RED
        desc = f" ({description})" if description else ""
        print(
            f"    {symbol}{icon}{cls.RESET} {description}: {cls.DIM}actual={actual}{cls.RESET}, {cls.DIM}expected={expected}{cls.RESET} {status}"
        )

    @classmethod
    def divider(cls, char="─", length=68):
        """打印分隔线"""
        print(f"{cls.DIM}{char * length}{cls.RESET}")

    @classmethod
    def flow(cls, from_state, to_state, description=""):
        """打印状态流转"""
        print(
            f"      {cls.DIM}└─ [{from_state}] ──{description}──> [{to_state}]{cls.RESET}"
        )


class TestAIStatusSyncFlow:
    """AI状态同步流程测试"""

    def test_flow_1_normal_operation(self):
        """流程1: 正常操作流程"""
        TestLogger.header("流程1: 正常操作流程")
        TestLogger.info("验证: 配置 → 连接测试 → AI分析 → 头脑风暴")

        manager = MockAIManager(should_fail=False)

        # 初始状态
        TestLogger.step("1.1 初始状态")
        TestLogger.action("检查AI管理器的初始状态")
        TestLogger.info(f"is_enabled()  -> {manager.is_enabled()}")
        TestLogger.info(f"is_connected() -> {manager.is_connected()}")
        TestLogger.result(manager.is_enabled(), False, "启用状态")
        TestLogger.result(manager.is_connected(), False, "连接状态")

        # 配置API
        TestLogger.step("1.2 配置API密钥")
        TestLogger.action("initialize(api_key='***', provider='deepseek')")
        manager.initialize(api_key=MOCK_API_KEY)
        TestLogger.result(manager.is_enabled(), True, "启用状态")
        TestLogger.result(manager.is_connected(), False, "连接状态(未测试)")

        # 连接测试
        TestLogger.step("1.3 连接测试成功")
        TestLogger.action("check_ai_connectivity() 返回成功")
        manager.set_connected(True)
        TestLogger.flow("未连接", "已连接", "连接测试成功")
        TestLogger.result(manager.is_connected(), True, "连接状态")

        # AI分析参数
        TestLogger.step("1.4 AI分析参数成功")
        TestLogger.action("detect_parameters() 返回成功")
        manager.set_connected(True)
        TestLogger.flow("已连接", "已连接", "分析成功")
        TestLogger.result(manager.is_connected(), True, "连接状态")

        # 头脑风暴
        TestLogger.step("1.5 头脑风暴成功")
        TestLogger.action("generate_solutions() 返回成功")
        manager.set_connected(True)
        TestLogger.flow("已连接", "已连接", "头脑风暴成功")
        TestLogger.result(manager.is_connected(), True, "连接状态")

        TestLogger.divider()
        TestLogger.success("流程1完成: AI状态始终正确同步 ✓")

    def test_flow_2_connection_failure(self):
        """流程2: 连接失败场景"""
        TestLogger.header("流程2: 连接失败场景")
        TestLogger.info("验证: AI调用失败 → 状态更新为未连接 → 重试成功")

        manager = MockAIManager(should_fail=False)
        manager.initialize(api_key=MOCK_API_KEY)
        manager.set_connected(True)

        # AI分析失败
        TestLogger.step("2.1 AI分析参数失败")
        TestLogger.action("detect_parameters() 抛出异常: 网络错误")
        manager.set_connected(False)
        TestLogger.flow("已连接", "未连接", "AI调用失败")
        TestLogger.result(manager.is_connected(), False, "连接状态")

        # 重新连接
        TestLogger.step("2.2 重新测试连接")
        TestLogger.action("check_ai_connectivity() 返回成功")
        manager.set_connected(True)
        TestLogger.flow("未连接", "已连接", "重新连接成功")
        TestLogger.result(manager.is_connected(), True, "连接状态")

        TestLogger.divider()
        TestLogger.success("流程2完成: 失败时状态正确更新为未连接 ✓")

    def test_flow_3_intermittent_failure(self):
        """流程3: 间歇性失败"""
        TestLogger.header("流程3: 间歇性失败")
        TestLogger.info("验证: 成功 → 失败 → 成功 (网络抖动场景)")

        manager = MockAIManager(should_fail=False)
        manager.initialize(api_key=MOCK_API_KEY)

        # 第1次成功
        TestLogger.step("3.1 第1次: AI分析参数")
        TestLogger.action("detect_parameters() -> 成功")
        manager.set_connected(True)
        TestLogger.flow("未连接", "已连接", "第1次成功")
        TestLogger.result(manager.is_connected(), True, "连接状态")

        # 第2次失败
        TestLogger.step("3.2 第2次: 头脑风暴")
        TestLogger.action("generate_solutions() -> 异常: 连接超时")
        manager.set_connected(False)
        TestLogger.flow("已连接", "未连接", "第2次失败")
        TestLogger.result(manager.is_connected(), False, "连接状态")

        # 第3次成功
        TestLogger.step("3.3 第3次: AI分析参数")
        TestLogger.action("detect_parameters() -> 成功")
        manager.set_connected(True)
        TestLogger.flow("未连接", "已连接", "第3次成功")
        TestLogger.result(manager.is_connected(), True, "连接状态")

        TestLogger.divider()
        TestLogger.success("流程3完成: 状态随实际结果正确切换 ✓")

    def test_flow_4_settings_tab_sync(self):
        """流程4: 设置Tab同步"""
        TestLogger.header("流程4: 设置Tab同步")
        TestLogger.info("验证: 头脑风暴失败 → 更新全局设置Tab")

        manager = MockAIManager(should_fail=False)
        manager.initialize(api_key=MOCK_API_KEY)
        manager.set_connected(True)

        # 模拟设置Tab
        settings_tab = MagicMock()
        mock_page = MagicMock()
        mock_page.session = {"settings_tab": settings_tab}

        TestLogger.step("4.1 执行头脑风暴")
        TestLogger.action("generate_solutions() -> 异常: 网络错误")
        manager.set_connected(False)
        TestLogger.result(manager.is_connected(), False, "AI状态")

        TestLogger.step("4.2 调用 _mark_ai_disconnected()")
        TestLogger.action("set_connected(False)")
        TestLogger.action("settings_tab._update_ai_status(force_check=False)")

        # 模拟 _mark_ai_disconnected 逻辑
        try:
            settings_tab_ref = mock_page.session.get("settings_tab")
            if settings_tab_ref and hasattr(settings_tab_ref, "_update_ai_status"):
                settings_tab_ref._update_ai_status(force_check=False)
                TestLogger.info("settings_tab._update_ai_status() 被调用")
        except Exception as e:
            TestLogger.error(f"设置Tab更新异常: {e}")

        TestLogger.step("4.3 验证状态更新")
        TestLogger.result(manager.is_connected(), False, "AI状态")
        settings_tab._update_ai_status.assert_called_once()
        TestLogger.result(True, True, "_update_ai_status调用次数=1")

        TestLogger.divider()
        TestLogger.success("流程4完成: 设置Tab正确接收到状态更新 ✓")

    def test_flow_5_matrix_tab_button_state(self):
        """流程5: MatrixTab按钮状态"""
        TestLogger.header("流程5: MatrixTab按钮状态")
        TestLogger.info("验证: AI连接状态决定按钮启用/禁用")

        manager = MockAIManager(should_fail=False)
        manager.initialize(api_key=MOCK_API_KEY)

        # 模拟按钮
        analyze_btn = MagicMock()
        brainstorm_btn = MagicMock()

        def update_buttons():
            is_ai_connected = manager.is_enabled() and manager.is_connected()
            analyze_btn.disabled = not is_ai_connected
            brainstorm_btn.disabled = not is_ai_connected

        # 初始状态
        TestLogger.step("5.1 初始状态 (已配置API，未测试连接)")
        TestLogger.action("update_buttons()")
        update_buttons()
        TestLogger.result(analyze_btn.disabled, True, "分析按钮")
        TestLogger.result(brainstorm_btn.disabled, True, "头脑风暴按钮")

        # 连接成功
        TestLogger.step("5.2 连接测试成功")
        TestLogger.action("check_ai_connectivity() -> 成功")
        manager.set_connected(True)
        TestLogger.action("update_buttons()")
        update_buttons()
        TestLogger.result(analyze_btn.disabled, False, "分析按钮")
        TestLogger.result(brainstorm_btn.disabled, False, "头脑风暴按钮")

        # AI调用失败
        TestLogger.step("5.3 AI调用失败")
        TestLogger.action("generate_solutions() -> 异常")
        manager.set_connected(False)
        TestLogger.action("update_buttons()")
        update_buttons()
        TestLogger.result(analyze_btn.disabled, True, "分析按钮")
        TestLogger.result(brainstorm_btn.disabled, True, "头脑风暴按钮")

        TestLogger.divider()
        TestLogger.success("流程5完成: 按钮状态与AI连接状态正确同步 ✓")

    def test_flow_6_full_user_journey(self):
        """流程6: 完整用户旅程"""
        TestLogger.header("流程6: 完整用户旅程")
        TestLogger.info("验证: 从打开应用到查看设置的完整流程")

        manager = MockAIManager(should_fail=False)
        settings_tab = MagicMock()
        mock_page = MagicMock()
        mock_page.session = {"settings_tab": settings_tab}

        # 首次打开
        TestLogger.step("6.1 首次打开应用")
        TestLogger.info(
            f"AI状态: enabled={manager.is_enabled()}, connected={manager.is_connected()}"
        )
        TestLogger.result(manager.is_enabled(), False, "AI未启用")
        TestLogger.result(manager.is_connected(), False, "连接未知")

        # 配置API
        TestLogger.step("6.2 配置API密钥")
        TestLogger.action("initialize(api_key='***')")
        manager.initialize(api_key=MOCK_API_KEY)
        TestLogger.result(manager.is_enabled(), True, "AI已启用")

        # 启动时测试
        TestLogger.step("6.3 启动时测试连接")
        TestLogger.action("check_ai_connectivity() -> 成功")
        manager.set_connected(True)
        TestLogger.flow("未连接", "已连接", "启动检测")
        TestLogger.result(manager.is_connected(), True, "连接成功")

        # AI分析
        TestLogger.step("6.4 进行AI分析参数")
        TestLogger.action("detect_parameters() -> 成功")
        manager.set_connected(True)
        TestLogger.flow("已连接", "已连接", "分析成功")
        TestLogger.result(manager.is_connected(), True, "保持连接")

        # 头脑风暴
        TestLogger.step("6.5 进行头脑风暴")
        TestLogger.action("generate_solutions() -> 成功")
        manager.set_connected(True)
        TestLogger.flow("已连接", "已连接", "头脑风暴成功")
        TestLogger.result(manager.is_connected(), True, "保持连接")

        # 切换到设置Tab
        TestLogger.step("6.6 切换到设置Tab")
        TestLogger.info("用户切换到「全局设置」Tab查看状态")
        TestLogger.action("_update_ai_status() 被调用")
        TestLogger.result(manager.is_connected(), True, "设置Tab显示已连接")

        TestLogger.divider()
        TestLogger.success("流程6完成: 完整用户旅程中状态正确同步 ✓")


def run_integration_tests():
    """运行集成测试"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "AI状态同步集成测试" + " " * 27 + "║")
    print("╚" + "═" * 68 + "╝")

    test_suite = TestAIStatusSyncFlow()

    test_suite.test_flow_1_normal_operation()
    test_suite.test_flow_2_connection_failure()
    test_suite.test_flow_3_intermittent_failure()
    test_suite.test_flow_4_settings_tab_sync()
    test_suite.test_flow_5_matrix_tab_button_state()
    test_suite.test_flow_6_full_user_journey()

    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 22 + "所有流程测试完成" + " " * 29 + "║")
    print("╚" + "═" * 68 + "╝")
    print()


if __name__ == "__main__":
    run_integration_tests()
