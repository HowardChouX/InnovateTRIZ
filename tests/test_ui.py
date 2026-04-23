"""
UI模块测试
测试参数选择器和解决方案展示
"""

import os
import sys

import pytest

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data.local_storage import LocalStorage
from src.data.models import AnalysisSession, Solution
from src.ui import ParameterPicker, SolutionListView
from src.ui.matrix_tab import MatrixTab


class MockPage:
    """模拟Flet页面对象"""

    def __init__(self):
        self.controls = []
        self.dialog = None
        self.snack_bar = None

    def clean(self):
        self.controls = []

    def add(self, *controls):
        for control in controls:
            self.controls.append(control)

    def update(self):
        pass

    async def update_async(self):
        pass

    def show_snack_bar(self, snack_bar):
        self.snack_bar = snack_bar


class TestMatrixTab:
    """MatrixTab测试"""

    def setup_method(self):
        """每个测试方法前准备"""
        self.page = MockPage()
        self.storage = LocalStorage()
        self.storage.initialize()
        self.tab = MatrixTab(self.page, self.storage)

    def test_tab_initialization(self):
        """测试Tab初始化"""
        assert self.tab is not None
        assert self.tab.storage is not None
        assert self.tab.ai_enabled == False

    def test_tab_has_empty_params_initially(self):
        """测试初始状态下参数为空"""
        assert self.tab.improving_params == []
        assert self.tab.worsening_params == []


class TestParameterPicker:
    """参数选择器测试"""

    def setup_method(self):
        """每个测试方法前准备"""
        self.page = MockPage()
        self.selected_param = None

    def test_parameter_categories_defined(self):
        """测试参数分类是否定义"""
        from src.ui.parameter_ui import get_param_categories
        categories = get_param_categories("39")
        assert "几何参数" in categories
        assert "力学参数" in categories
        assert "能量参数" in categories

    def test_all_39_params_covered(self):
        """测试39个参数是否都被覆盖"""
        from src.config.constants import ENGINEERING_PARAMETERS_39
        from src.ui.parameter_ui import get_param_categories

        all_params = []
        for category, params in get_param_categories("39").items():
            all_params.extend(params)

        for param in ENGINEERING_PARAMETERS_39:
            assert param in all_params, f"参数 {param} 未被覆盖"

    def test_parameter_picker_initialization(self):
        """测试参数选择器初始化"""
        picker = ParameterPicker(
            page=self.page,
            param_type="improving",
            current_values=None,
            on_selected=None,
        )

        assert picker is not None
        assert picker.param_type == "improving"
        assert picker.current_values == []

    def test_parameter_picker_worsening_type(self):
        """测试恶化参数类型"""
        picker = ParameterPicker(
            page=self.page,
            param_type="worsening",
            current_values=["成本"],
            on_selected=None,
        )

        assert picker.param_type == "worsening"
        assert picker.current_values == ["成本"]


class TestSolutionListView:
    """解决方案展示测试"""

    def setup_method(self):
        """每个测试方法前准备"""
        self.page = MockPage()

    def test_categorize_by_principle(self):
        """测试按原理分类"""
        view = SolutionListView(self.page)

        # 创建测试解决方案
        solutions = [
            Solution(principle_id=1, principle_name="分割原理", description="测试1"),
            Solution(principle_id=15, principle_name="动态性原理", description="测试2"),
            Solution(
                principle_id=35,
                principle_name="物理或化学参数改变原理",
                description="测试3",
            ),
        ]

        categorized = view._categorize_by_principle(solutions)

        assert "物理" in categorized
        assert "化学" in categorized
        assert len(categorized["物理"]) == 2  # 原理1和15是物理类
        assert len(categorized["化学"]) == 1  # 原理35是化学类

    def test_solution_view_initialization(self):
        """测试解决方案视图初始化"""
        view = SolutionListView(page=self.page)

        assert view is not None
        assert len(view.solutions) == 0
        assert len(view.categorized_solutions) == 0

    def test_empty_solutions_handling(self):
        """测试空解决方案列表处理"""
        view = SolutionListView(self.page)

        solutions = []
        categorized = view._categorize_by_principle(solutions)

        assert len(categorized) == 0


class TestSolutionModel:
    """解决方案模型测试"""

    def test_solution_creation(self):
        """测试解决方案创建"""
        solution = Solution(
            principle_id=1,
            principle_name="分割原理",
            description="将整体分割为独立模块",
        )

        assert solution.principle_id == 1
        assert solution.principle_name == "分割原理"
        assert solution.confidence == 0.8  # 默认值
        assert solution.is_ai_generated == False  # 默认值
        assert solution.category == "物理"  # 默认值

    def test_solution_to_dict(self):
        """测试解决方案转字典"""
        solution = Solution(
            principle_id=1,
            principle_name="分割原理",
            description="测试描述",
            confidence=0.9,
        )

        data = solution.to_dict()

        assert data["principle_id"] == 1
        assert data["principle_name"] == "分割原理"
        assert data["confidence"] == 0.9
        assert "id" in data
        assert "created_at" in data

    def test_solution_from_dict(self):
        """测试从字典创建解决方案"""
        data = {
            "id": "test-id-123",
            "principle_id": 2,
            "principle_name": "抽取原理",
            "description": "抽取关键部分",
            "confidence": 0.85,
            "is_ai_generated": True,
            "category": "物理",
            "examples": ["例1", "例2"],
            "created_at": "2024-01-01T12:00:00",
        }

        solution = Solution.from_dict(data)

        assert solution.id == "test-id-123"
        assert solution.principle_id == 2
        assert solution.confidence == 0.85
        assert solution.is_ai_generated == True


class TestAnalysisSessionModel:
    """分析会话模型测试"""

    def test_session_creation(self):
        """测试会话创建"""
        session = AnalysisSession(problem="手机需要更大电池但要保持轻薄")

        assert session.problem == "手机需要更大电池但要保持轻薄"
        assert session.matrix_type == "39"  # 默认值
        assert session.ai_enabled == False  # 默认值
        assert len(session.solutions) == 0  # 默认值

    def test_session_with_solutions(self):
        """测试带解决方案的会话"""
        solutions = [
            Solution(principle_id=1, principle_name="分割原理", description="测试")
        ]
        session = AnalysisSession(problem="测试问题", solutions=solutions)

        assert len(session.solutions) == 1
        assert session.solutions[0].principle_id == 1

    def test_session_get_summary(self):
        """测试获取会话摘要"""
        session = AnalysisSession(problem="这是一个测试问题，用于验证摘要功能")

        summary = session.get_summary()

        assert "id" in summary
        assert "problem_preview" in summary
        assert len(summary["problem_preview"]) > 0
        assert summary["solution_count"] == 0


class TestConstants:
    """常量测试"""

    def test_engineering_parameters_count(self):
        """测试39个工程参数"""
        from src.config.constants import ENGINEERING_PARAMETERS_39

        assert len(ENGINEERING_PARAMETERS_39) == 39

    def test_inventive_principles_count(self):
        """测试40个发明原理"""
        from src.config.constants import INVENTIVE_PRINCIPLES

        assert len(INVENTIVE_PRINCIPLES) == 40
        assert 1 in INVENTIVE_PRINCIPLES
        assert 40 in INVENTIVE_PRINCIPLES

    def test_principle_categories(self):
        """测试原理分类"""
        from src.config.constants import PRINCIPLE_CATEGORIES

        assert "物理" in PRINCIPLE_CATEGORIES
        assert "化学" in PRINCIPLE_CATEGORIES
        assert "几何" in PRINCIPLE_CATEGORIES
        assert "时间" in PRINCIPLE_CATEGORIES
        assert "系统" in PRINCIPLE_CATEGORIES

    def test_colors_defined(self):
        """测试颜色定义"""
        from src.config.constants import COLORS

        assert "primary" in COLORS
        assert "secondary" in COLORS
        assert "background" in COLORS
        assert "surface" in COLORS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
