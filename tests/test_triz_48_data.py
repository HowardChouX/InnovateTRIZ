"""
48矛盾矩阵数据准确性测试

验证从 triz48.xls 提取的48矩阵数据完整性
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data.triz_constants import ENGINEERING_PARAMETERS_48, MATRIX_48


# xls标准48参数
XLS_48_PARAMS = [
    "移动物体的重量", "静止物体的重量", "移动物体的长度", "静止物体的长度",
    "移动物体的面积", "静止物体的面积", "移动物体的体积", "静止物体的体积",
    "形状", "物质的数量", "信息的数量", "移动物体的耐久性", "静止物体的耐久性",
    "速度", "力", "移动物体消耗的能量", "静止物体消耗的能量", "功率",
    "张力/压力", "强度", "结构的稳定性", "温度", "明亮度", "运行效率",
    "物质的浪费", "时间的浪费", "能量的浪费", "信息的遗漏", "噪音",
    "有害的散发", "有害的副作用", "适应性", "兼容性/连通性", "使用的方便性",
    "可靠性", "易维护性", "安全性", "易受伤性", "美观", "外来有害因素",
    "可制造性", "制造的准确度", "自动化程度", "生产率", "装置的复杂性",
    "控制的复杂性", "测量的难度", "测量的准确度"
]


class TestTriz48Parameters:
    """48工程参数测试"""

    def test_parameter_count(self):
        """测试参数数量为48个"""
        assert len(ENGINEERING_PARAMETERS_48) == 48

    def test_parameter_names_match_xls(self):
        """测试参数名与xls标准完全一致"""
        assert ENGINEERING_PARAMETERS_48 == XLS_48_PARAMS

    def test_no_duplicate_parameters(self):
        """测试参数列表无重复"""
        assert len(ENGINEERING_PARAMETERS_48) == len(set(ENGINEERING_PARAMETERS_48))

    def test_all_parameters_are_strings(self):
        """测试所有参数都是非空字符串"""
        for param in ENGINEERING_PARAMETERS_48:
            assert isinstance(param, str)
            assert len(param) > 0


class TestTriz48MatrixSize:
    """48矛盾矩阵规模测试"""

    def test_matrix_record_count_full_48x48(self):
        """测试矩阵记录数为完整的48x48=2304条"""
        assert len(MATRIX_48) == 2304, f"期望2304条，实际{len(MATRIX_48)}条"

    def test_all_keys_are_tuples(self):
        """测试所有键都是正确的元组格式"""
        for key in MATRIX_48.keys():
            assert isinstance(key, tuple)
            assert len(key) == 2
            assert isinstance(key[0], str) and isinstance(key[1], str)

    def test_all_values_are_principle_lists(self):
        """测试所有值都是发明原理编号列表"""
        for key, principles in MATRIX_48.items():
            assert isinstance(principles, list)
            for pid in principles:
                assert isinstance(pid, int)
                assert 1 <= pid <= 40

    def test_no_empty_principle_lists(self):
        """测试不存在空的发明原理列表"""
        empty = [k for k, v in MATRIX_48.items() if len(v) == 0]
        assert len(empty) == 0, f"存在{len(empty)}个空原理列表"

    def test_all_48_params_have_entries(self):
        """测试所有48个参数都有条目"""
        params_set = set(ENGINEERING_PARAMETERS_48)
        params_with_data = set()
        for imp, wors in MATRIX_48.keys():
            params_with_data.add(imp)
            params_with_data.add(wors)
        missing = params_set - params_with_data
        assert len(missing) == 0, f"以下参数没有数据: {missing}"


class TestTriz48MatrixCompleteness:
    """48矛盾矩阵完整性测试"""

    def test_all_param_pairs_exist(self):
        """测试所有48x48参数组合都存在"""
        params = ENGINEERING_PARAMETERS_48
        missing = []
        for p1 in params:
            for p2 in params:
                if (p1, p2) not in MATRIX_48:
                    missing.append((p1, p2))
        assert len(missing) == 0, f"缺失{len(missing)}个组合: {missing[:5]}"

    def test_diagonal_entries_exist(self):
        """测试所有对角线条目(参数自身矛盾)都存在"""
        for param in ENGINEERING_PARAMETERS_48:
            assert (param, param) in MATRIX_48, f"缺少对角线条目: ({param}, {param})"


class TestTriz48MatrixAccuracy:
    """48矛盾矩阵数据准确性测试"""

    def test_weight_vs_weight_has_principles(self):
        """测试：移动物体的重量 vs 移动物体的重量"""
        key = ("移动物体的重量", "移动物体的重量")
        assert key in MATRIX_48
        assert len(MATRIX_48[key]) > 0
        # 参考值
        expected = [35, 28, 31, 8, 2, 3, 10]
        assert MATRIX_48[key] == expected

    def test_speed_vs_force(self):
        """测试：速度 vs 力"""
        key = ("速度", "力")
        assert key in MATRIX_48
        assert len(MATRIX_48[key]) > 0

    def test_shape_vs_strength(self):
        """测试：形状 vs 强度"""
        key = ("形状", "强度")
        assert key in MATRIX_48
        assert len(MATRIX_48[key]) > 0

    def test_extended_param_entry(self):
        """测试扩展参数(39-48)条目"""
        extended_params = ENGINEERING_PARAMETERS_48[39:]
        for p in extended_params:
            assert (p, p) in MATRIX_48 or any(
                (p, other) in MATRIX_48 or (other, p) in MATRIX_48
                for other in ENGINEERING_PARAMETERS_48
            ), f"扩展参数{p}没有任何数据"


class TestTriz48MatrixDataTypes:
    """48矛盾矩阵数据类型测试"""

    def test_principle_ids_are_integers(self):
        """测试所有发明原理编号都是整数"""
        for key, principles in MATRIX_48.items():
            for p in principles:
                assert isinstance(p, int), f"{key}包含非整数: {p}"

    def test_principle_ids_in_valid_range(self):
        """测试原理编号在1-40范围内"""
        for key, principles in MATRIX_48.items():
            for p in principles:
                assert 1 <= p <= 40, f"{key}包含无效原理编号: {p}"


class TestTriz48VsXls:
    """48矩阵与xls源文件对比测试（需要xlrd模块）"""

    @pytest.fixture
    def xls_data(self):
        """加载xls源数据"""
        try:
            import xlrd
        except ImportError:
            pytest.skip("xlrd not installed")

        xls_path = os.path.join(os.path.dirname(__file__), "..", "triz48.xls")
        if not os.path.exists(xls_path):
            pytest.skip("triz48.xls not found")

        wb = xlrd.open_workbook(xls_path)
        sh = wb.sheet_by_name('CM4')
        row_params = [sh.cell_value(i, 0) for i in range(2, sh.nrows)]

        xls_matrix = {}
        for i in range(2, sh.nrows):
            row_param_num = int(row_params[i-2])
            p1 = XLS_48_PARAMS[row_param_num - 1]
            for j in range(2, sh.ncols):
                col_xls_idx = j - 2
                p2 = XLS_48_PARAMS[col_xls_idx]
                val = sh.cell_value(i, j)
                if val != '' and val != 0:
                    if isinstance(val, float):
                        principles = [int(val)]
                    else:
                        parts = str(val).split(',')
                        principles = [int(x.strip()) for x in parts if x.strip()]
                    xls_matrix[(p1, p2)] = principles
        return xls_matrix

    def test_xls_record_count(self, xls_data):
        """测试xls源文件有2304条记录"""
        assert len(xls_data) == 2304

    def test_matrix_matches_xls(self, xls_data):
        """测试MATRIX_48与xls源数据一致"""
        mismatches = []
        for key, xls_principles in xls_data.items():
            if key in MATRIX_48:
                if MATRIX_48[key] != xls_principles:
                    mismatches.append((key, MATRIX_48[key], xls_principles))
            else:
                mismatches.append((key, "MISSING", xls_principles))

        assert len(mismatches) == 0, f"有{len(mismatches)}个不匹配: {mismatches[:3]}"

    def test_xls_and_matrix_same_count(self, xls_data):
        """测试xls和matrix记录数相同"""
        assert len(MATRIX_48) == len(xls_data)


class TestMatrixSelector48:
    """MatrixSelector 48矩阵测试"""

    def test_matrix_selector_can_load_48(self):
        """测试MatrixSelector可以加载48矩阵"""
        from src.core.matrix_selector import get_matrix_manager
        manager = get_matrix_manager()
        matrix = manager.get_matrix("48")
        assert matrix.matrix_type == "48"
        assert len(matrix.parameters) == 48

    def test_48_has_more_params_than_39(self):
        """测试48矩阵比39矩阵参数多"""
        from src.data.triz_constants import ENGINEERING_PARAMETERS
        assert len(ENGINEERING_PARAMETERS_48) > len(ENGINEERING_PARAMETERS)


class TestMatrix39Integrity:
    """39矩阵完整性测试"""

    def test_39_matrix_uses_correct_param_names(self):
        """测试39矩阵使用xls标准参数名"""
        from src.data.triz_constants import ENGINEERING_PARAMETERS, MATRIX_39

        # 验证MATRIX_39中的所有参数都在ENGINEERING_PARAMETERS中
        params_set = set(ENGINEERING_PARAMETERS)
        invalid = [(p1, p2) for (p1, p2) in MATRIX_39.keys()
                   if p1 not in params_set or p2 not in params_set]
        assert len(invalid) == 0, f"39矩阵有无效参数: {invalid[:3]}"

    def test_39_params_are_subset_of_48(self):
        """测试39参数是48参数的子集"""
        from src.data.triz_constants import ENGINEERING_PARAMETERS, ENGINEERING_PARAMETERS_48

        params_39_set = set(ENGINEERING_PARAMETERS)
        params_48_set = set(ENGINEERING_PARAMETERS_48)

        # 39参数应该是48参数的子集
        diff = params_39_set - params_48_set
        assert len(diff) == 0, f"39参数中有{len(diff)}个不在48参数中: {diff}"

    def test_39_params_no_duplicates(self):
        """测试39参数无重复"""
        from src.data.triz_constants import ENGINEERING_PARAMETERS
        assert len(ENGINEERING_PARAMETERS) == len(set(ENGINEERING_PARAMETERS))

    def test_39_matrix_record_count(self):
        """测试39矩阵记录数（稀疏矩阵，少于39*39=1521）"""
        from src.data.triz_constants import MATRIX_39
        # 39矩阵是稀疏的，原始数据有1189条
        assert len(MATRIX_39) == 1189, f"期望1189条，实际{len(MATRIX_39)}条"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
