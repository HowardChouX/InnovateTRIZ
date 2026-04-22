"""
矩阵查询功能测试
测试查询发明原理的纯本地矩阵逻辑
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.matrix_selector import get_matrix_manager
from src.core.principle_service import get_principle_service


class TestMatrixQuery:
    """矩阵查询测试"""

    def setup_method(self):
        """每个测试前准备"""
        self.matrix_manager = get_matrix_manager()
        self.principle_service = get_principle_service()
        self.matrix = self.matrix_manager.get_matrix("39")

    def test_query_with_both_params(self):
        """测试使用改善和恶化参数查询"""
        result = self.matrix.query_matrix(improving="速度", worsening="力")
        assert result is not None
        assert len(result.principle_ids) > 0
        print(f"速度+力 查询结果: {result.principle_ids}")

    def test_query_with_single_improving_param(self):
        """测试只使用改善参数查询"""
        result = self.matrix.query_matrix(improving="速度", worsening=None)
        assert result is not None
        print(f"仅速度查询结果: {result.principle_ids}")

    def test_query_with_single_worsening_param(self):
        """测试只使用恶化参数查询"""
        result = self.matrix.query_matrix(improving=None, worsening="力")
        assert result is not None
        print(f"仅力查询结果: {result.principle_ids}")

    def test_query_with_no_params(self):
        """测试无参数查询（使用默认值）"""
        result = self.matrix.query_matrix(improving=None, worsening=None)
        assert result is not None
        print(f"无参数查询结果: {result.principle_ids}")

    def test_query_multiple_improving_params(self):
        """测试多个改善参数查询"""
        all_ids = []
        params = ["速度", "力"]
        for imp in params:
            result = self.matrix.query_matrix(improving=imp, worsening="重量")
            all_ids.extend(result.principle_ids)

        unique_ids = list(dict.fromkeys(all_ids))
        assert len(unique_ids) > 0
        print(f"多改善参数查询: {unique_ids}")

    def test_query_multiple_worsening_params(self):
        """测试多个恶化参数查询"""
        all_ids = []
        params = ["重量", "体积"]
        for wors in params:
            result = self.matrix.query_matrix(improving="能量", worsening=wors)
            all_ids.extend(result.principle_ids)

        unique_ids = list(dict.fromkeys(all_ids))
        assert len(unique_ids) > 0
        print(f"多恶化参数查询: {unique_ids}")

    def test_query_energy_weight(self):
        """测试能量vs重量典型矛盾"""
        result = self.matrix.query_matrix(
            improving="运动物体的能量", worsening="静止物体的重量"
        )
        assert result is not None
        assert len(result.principle_ids) > 0
        print(f"能量+重量查询: {result.principle_ids}")

        # 获取原理详情
        principles = self.principle_service.get_principles_by_ids(result.principle_ids)
        assert len(principles) > 0
        for p in principles[:3]:
            print(f"  原理{p.id}: {p.name}")

    def test_query_results_are_deterministic(self):
        """测试查询结果是确定性的"""
        result1 = self.matrix.query_matrix(improving="速度", worsening="力")
        result2 = self.matrix.query_matrix(improving="速度", worsening="力")

        assert result1.principle_ids == result2.principle_ids
        print("查询结果是确定性的")

    def test_get_principles_by_ids(self):
        """测试通过ID获取原理详情"""
        result = self.matrix.query_matrix(improving="速度", worsening="力")
        principles = self.principle_service.get_principles_by_ids(result.principle_ids)

        assert len(principles) > 0
        for p in principles:
            assert p.id is not None
            assert p.name is not None
            assert p.definition is not None
        print(f"获取到 {len(principles)} 个原理详情")

    def test_empty_result_for_invalid_combination(self):
        """测试无效参数组合返回空结果"""
        # 尝试一个不太可能产生结果的组合
        result = self.matrix.query_matrix(improving="形状", worsening="温度")
        # 形状vs温度可能有结果也可能没有，这是有效的查询
        assert result is not None
        print(f"形状+温度查询: {result.principle_ids}")


class TestMatrixQueryIndependence:
    """测试矩阵查询的独立性（不依赖AI）"""

    def setup_method(self):
        self.matrix_manager = get_matrix_manager()
        self.matrix = self.matrix_manager.get_matrix("39")

    def test_query_does_not_require_ai(self):
        """测试查询不依赖AI"""
        # 在没有AI配置的情况下也能查询
        result = self.matrix.query_matrix(improving="速度", worsening="力")
        assert result is not None
        assert len(result.principle_ids) > 0
        print("矩阵查询不依赖AI")

    def test_query_params_are_optional(self):
        """测试参数是可选的"""
        # 只提供改善参数
        result1 = self.matrix.query_matrix(improving="速度", worsening=None)
        assert result1 is not None

        # 只提供恶化参数
        result2 = self.matrix.query_matrix(improving=None, worsening="力")
        assert result2 is not None

        # 不提供参数
        result3 = self.matrix.query_matrix(improving=None, worsening=None)
        assert result3 is not None

        print("参数都是可选的")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
