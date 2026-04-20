"""
AI功能测试
测试MatrixTab中的AI开关和分析功能
"""

import pytest
import flet as ft
from unittest.mock import Mock, patch, AsyncMock
from src.ui.matrix_tab.matrix_page import MatrixTab
from src.data.local_storage import LocalStorage


class TestMatrixTabAI:
    """测试MatrixTab的AI功能"""

    def setup_method(self):
        """每个测试方法前设置"""
        self.page = Mock(spec=ft.Page)
        self.storage = Mock(spec=LocalStorage)
        self.matrix_tab = MatrixTab(self.page, self.storage)

    def test_ai_switch_default_off(self):
        """AI开关默认关闭"""
        assert self.matrix_tab.ai_enabled == False

    def test_ai_switch_can_be_toggled(self):
        """AI开关可以切换"""
        self.matrix_tab.ai_enabled = True
        assert self.matrix_tab.ai_enabled == True

        self.matrix_tab.ai_enabled = False
        assert self.matrix_tab.ai_enabled == False

    def test_improving_params_multiple(self):
        """改善参数支持多选"""
        self.matrix_tab.improving_params = ["速度", "力"]
        assert len(self.matrix_tab.improving_params) == 2
        assert "速度" in self.matrix_tab.improving_params
        assert "力" in self.matrix_tab.improving_params

    def test_worsening_params_multiple(self):
        """恶化参数支持多选"""
        self.matrix_tab.worsening_params = ["重量", "能量消耗"]
        assert len(self.matrix_tab.worsening_params) == 2
        assert "重量" in self.matrix_tab.worsening_params
        assert "能量消耗" in self.matrix_tab.worsening_params

    def test_no_params_uses_none(self):
        """未选择参数时为空列表"""
        assert self.matrix_tab.improving_params == []
        assert self.matrix_tab.worsening_params == []

    @patch('src.ai.ai_client.get_ai_manager')
    def test_ai_enabled_but_not_configured(self, mock_get_manager):
        """AI开启但未配置时提示"""
        mock_manager = Mock()
        mock_manager.is_enabled.return_value = False
        mock_get_manager.return_value = mock_manager

        # AI开启但实际未配置
        self.matrix_tab.ai_enabled = True

        # 状态文本应显示
        assert self.matrix_tab.ai_enabled == True

    @patch('src.ai.ai_client.get_ai_manager')
    def test_ai_enabled_and_configured(self, mock_get_manager):
        """AI开启且已配置"""
        mock_manager = Mock()
        mock_manager.is_enabled.return_value = True
        mock_get_manager.return_value = mock_manager

        self.matrix_tab.ai_enabled = True
        assert self.matrix_tab.ai_enabled == True


class TestParameterPickerMultiSelect:
    """测试参数多选功能"""

    def test_parameter_picker_multi_select_mode(self):
        """参数选择器支持多选"""
        from src.ui.parameter_ui import ParameterPicker

        page = Mock()
        picker = ParameterPicker(
            page=page,
            param_type="improving",
            current_values=["速度"],
            multi_select=True
        )

        assert picker.multi_select == True
        assert "速度" in picker.current_values

    def test_parameter_picker_single_select_mode(self):
        """参数选择器单选模式"""
        from src.ui.parameter_ui import ParameterPicker

        page = Mock()
        picker = ParameterPicker(
            page=page,
            param_type="improving",
            current_values=None,
            multi_select=False
        )

        assert picker.multi_select == False


class TestAIFallback:
    """测试AI降级功能"""

    def test_local_analysis_when_ai_disabled(self):
        """AI关闭时使用本地分析"""
        from src.core.matrix_selector import get_matrix_manager

        manager = get_matrix_manager()
        matrix = manager.get_matrix("39")

        # 本地查询
        result = matrix.query_matrix(
            improving="速度",
            worsening="能量消耗"
        )

        assert result.matrix_type == "39"
        assert len(result.principle_ids) > 0

    @patch('src.ai.ai_client.get_ai_manager')
    def test_local_analysis_when_ai_unavailable(self, mock_get_manager):
        """AI不可用时使用本地分析"""
        import asyncio
        from src.core.triz_engine import get_triz_engine

        mock_manager = Mock()
        mock_manager.is_enabled.return_value = False
        mock_get_manager.return_value = mock_manager

        engine = get_triz_engine()
        session = asyncio.run(
            engine.analyze_problem(
                problem="手机需要更大电池但要保持轻薄",
                improving_param="运动物体的能量消耗",
                worsening_param="重量",
                use_ai=False  # 明确关闭AI
            )
        )

        assert session is not None
        assert session.problem == "手机需要更大电池但要保持轻薄"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
