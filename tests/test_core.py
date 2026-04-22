"""
核心模块测试

测试 LocalTRIZEngine、ContradictionMatrix 等核心逻辑
"""

from src.core.matrix_selector import get_matrix_manager
from src.core.triz_engine import LocalTRIZEngine


class TestLocalTRIZEngine:
    """本地 TRIZ 引擎测试"""

    def setup_method(self):
        self.engine = LocalTRIZEngine()

    def test_detect_parameters_speed_energy(self):
        """测试参数检测：速度与能耗"""
        result = self.engine.detect_parameters("增加速度但减少能耗")
        assert isinstance(result, dict)

    def test_detect_parameters_weight_strength(self):
        """测试参数检测：重量与强度"""
        result = self.engine.detect_parameters("减轻重量但增加强度")
        assert isinstance(result, dict)

    def test_generate_solutions_basic(self):
        """测试基本解决方案生成"""
        solutions = self.engine.generate_solutions(
            principle_ids=[1, 15, 19], problem="测试问题", count=3
        )
        assert len(solutions) > 0

    def test_generate_solutions_with_principles(self):
        """测试指定原理生成方案"""
        solutions = self.engine.generate_solutions(
            principle_ids=[1, 2, 3, 4, 5], problem="如何改进车辆性能", count=5
        )
        assert len(solutions) <= 5

    def test_generate_solutions_empty_principles(self):
        """测试空原理列表"""
        solutions = self.engine.generate_solutions(principle_ids=[], problem="测试问题")
        assert len(solutions) == 0

    def test_categorize_solutions(self):
        """测试解决方案分类"""
        solutions = self.engine.generate_solutions(
            principle_ids=[1, 2, 15, 35], problem="测试问题"
        )
        categorized = self.engine.categorize_solutions(solutions)
        assert isinstance(categorized, dict)
        assert len(categorized) > 0

    def test_get_solution_statistics(self):
        """测试解决方案统计"""
        solutions = self.engine.generate_solutions(
            principle_ids=[1, 15, 19, 35], problem="测试问题"
        )
        stats = self.engine.get_solution_statistics(solutions)
        assert isinstance(stats, dict)
        assert "total" in stats or "count" in stats


class TestContradictionMatrix:
    """矛盾矩阵测试"""

    def setup_method(self):
        self.manager = get_matrix_manager()
        self.matrix = self.manager.get_matrix("39")

    def test_matrix_singleton(self):
        """测试矩阵单例"""
        matrix1 = self.manager.get_matrix("39")
        matrix2 = self.manager.get_matrix("39")
        assert matrix1 is matrix2

    def test_find_solutions_speed_energy(self):
        """测试速度-能耗解决方案"""
        principles = self.matrix.find_solutions("速度", "能耗")
        assert len(principles) > 0
        assert all(isinstance(p, int) for p in principles)

    def test_find_solutions_weight_strength(self):
        """测试重量-强度解决方案"""
        principles = self.matrix.find_solutions("重量", "强度")
        assert len(principles) > 0

    def test_find_solutions_with_valid_combination(self):
        """测试有效参数组合"""
        principles = self.matrix.find_solutions("速度", "能耗")
        assert isinstance(principles, list)
        assert len(principles) > 0

    def test_query_matrix(self):
        """测试矩阵直接查询"""
        result = self.matrix.query_matrix("重量", "强度")
        assert result is not None
        assert result.matrix_type == "39"

    def test_query_matrix_default_params(self):
        """测试默认参数查询"""
        result = self.matrix.query_matrix()
        assert result is not None

    def test_get_parameters(self):
        """测试获取所有参数"""
        params = self.matrix.get_improving_params()
        assert len(params) == 39
        assert "速度" in params
        assert "移动物体用的能源" in params


class TestMatrixManager:
    """矩阵管理器测试"""

    def setup_method(self):
        self.manager = get_matrix_manager()

    def test_get_39_matrix(self):
        """测试获取39矩阵"""
        matrix = self.manager.get_matrix("39")
        assert matrix is not None
        assert matrix.matrix_type == "39"

    def test_get_48_matrix_returns_empty_matrix(self):
        """测试获取48矩阵返回空矩阵对象"""
        matrix = self.manager.get_matrix("48")
        assert matrix is not None
        assert matrix.matrix_type == "48"
        assert len(matrix.matrix) == 0

    def test_get_available_matrix_types(self):
        """测试获取可用矩阵类型"""
        matrices = self.manager.get_available_matrix_types()
        assert isinstance(matrices, list)
        assert len(matrices) == 2
        assert matrices[0]["type"] == "39"
        assert matrices[1]["type"] == "48"
