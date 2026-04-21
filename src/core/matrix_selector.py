"""
矛盾矩阵选择器和查询器
支持39矛盾矩阵，48矩阵为预留接口
"""

from typing import List, Optional, Tuple, Dict
import logging
from ..data.models import MatrixQueryResult, PrincipleQueryResult
from ..data.excel_loader import get_triz_data_loader
from ..config.constants import INVENTIVE_PRINCIPLES

logger = logging.getLogger(__name__)


class ContradictionMatrix:
    """矛盾矩阵基类"""

    def __init__(self, matrix_type: str = "39"):
        """
        初始化矛盾矩阵

        Args:
            matrix_type: 矩阵类型，"39" 或 "48"
        """
        self.matrix_type = matrix_type
        self.parameters: List[str] = []
        self.matrix: Dict[Tuple[str, str], List[int]] = {}
        self._triz_loader = None
        self._init_matrix()

    def _init_matrix(self):
        """初始化矩阵数据"""
        if self.matrix_type == "39":
            self._init_39_matrix()
        elif self.matrix_type == "48":
            self._init_48_matrix()
        else:
            raise ValueError(f"不支持的矩阵类型: {self.matrix_type}")

    def _init_39_matrix(self):
        """初始化39矛盾矩阵"""
        # 从内置数据加载完整矩阵数据
        self._triz_loader = get_triz_data_loader()
        self.matrix = self._triz_loader.get_contradiction_matrix()
        self.parameters = self._triz_loader.get_all_params()

        logger.info(f"加载39矛盾矩阵，包含{len(self.parameters)}个参数和{len(self.matrix)}个组合")

    def _init_48_matrix(self):
        """初始化48矛盾矩阵（预留）"""
        self.parameters = []
        self.matrix = {}
        logger.warning("48矛盾矩阵暂未实现，使用空矩阵")

    def get_improving_params(self) -> List[str]:
        """获取所有可改善参数"""
        return self.parameters.copy()

    def get_worsening_params(self) -> List[str]:
        """获取所有可能恶化参数"""
        return self.parameters.copy()

    def find_solutions(self, improving: str, worsening: str) -> List[int]:
        """
        查找对应的发明原理编号

        Args:
            improving: 改善参数
            worsening: 恶化参数

        Returns:
            发明原理编号列表
        """
        if not improving or not worsening:
            logger.warning("改善参数或恶化参数为空")
            return [1, 10, 15, 19, 35]  # 默认原理

        # 精确匹配
        key = (improving, worsening)
        if key in self.matrix:
            principles = self.matrix[key]
            logger.info(f"找到精确匹配: {improving} vs {worsening} -> {principles}")
            return principles

        # 尝试反向匹配（交换改善和恶化参数）
        reverse_key = (worsening, improving)
        if reverse_key in self.matrix:
            principles = self.matrix[reverse_key]
            logger.info(f"找到反向匹配: {improving} vs {worsening} -> {principles}")
            return principles

        # 尝试部分匹配（参数包含关系）
        for (imp, wors), principles in self.matrix.items():
            if imp in improving or improving in imp:
                if wors in worsening or worsening in wors:
                    logger.info(f"找到部分匹配: {improving} vs {worsening} -> {principles}")
                    return principles

        # 参数名称标准化匹配
        normalized_improving = self._normalize_param(improving)
        normalized_worsening = self._normalize_param(worsening)

        # 尝试标准化后的精确匹配
        for (imp, wors), principles in self.matrix.items():
            norm_imp = self._normalize_param(imp)
            norm_wors = self._normalize_param(wors)
            if norm_imp == normalized_improving or normalized_improving in norm_imp:
                if norm_wors == normalized_worsening or normalized_worsening in norm_wors:
                    logger.info(f"找到标准化匹配: {improving} vs {worsening} -> {principles}")
                    return principles

        # 使用默认原理
        logger.info(f"未找到匹配，使用默认原理: {improving} vs {worsening}")
        return [1, 10, 15, 19, 35]

    def _normalize_param(self, param: str) -> str:
        """标准化参数名称"""
        if not param:
            return ""
        # 移除空格和特殊字符，转小写
        normalized = param.strip().lower()
        # 移除"运动物体的"和"静止物体的"前缀进行对比
        normalized_no_prefix = normalized.replace("运动物体的", "").replace("静止物体的", "")
        return normalized_no_prefix

    def query_matrix(self,
                    improving: Optional[str] = None,
                    worsening: Optional[str] = None) -> MatrixQueryResult:
        """
        查询矛盾矩阵

        Args:
            improving: 改善参数（可选）
            worsening: 恶化参数（可选）

        Returns:
            矩阵查询结果
        """
        is_auto_detected = False

        # 如果参数未提供，使用默认参数
        if not improving:
            improving = "速度"
            is_auto_detected = True

        if not worsening:
            worsening = "移动物体用的能源"
            is_auto_detected = True

        # 查找原理
        principle_ids = self.find_solutions(improving, worsening)

        # 获取原理名称
        principle_names = []
        for pid in principle_ids:
            if pid in INVENTIVE_PRINCIPLES:
                principle_names.append(INVENTIVE_PRINCIPLES[pid])

        logger.info(f"矩阵查询结果: {improving} vs {worsening} -> {principle_ids} ({principle_names})")

        return MatrixQueryResult(
            improving_param=improving,
            worsening_param=worsening,
            principle_ids=principle_ids,
            matrix_type=self.matrix_type,
            is_auto_detected=is_auto_detected
        )

    def query_with_result(self,
                         improving: Optional[str] = None,
                         worsening: Optional[str] = None) -> PrincipleQueryResult:
        """
        查询矛盾矩阵并返回完整结果

        Args:
            improving: 改善参数（可选）
            worsening: 恶化参数（可选）

        Returns:
            原理查询结果
        """
        result = self.query_matrix(improving, worsening)

        return PrincipleQueryResult(
            principle_ids=result.principle_ids,
            improving_param=result.improving_param,
            worsening_param=result.worsening_param,
            source="matrix",
            confidence="高" if len(result.principle_ids) > 0 else "低"
        )

    def suggest_worsening_params(self, improving: str) -> List[str]:
        """
        根据改善参数建议可能的恶化参数

        Args:
            improving: 改善参数

        Returns:
            建议的恶化参数列表
        """
        suggestions = []

        # 查找矩阵中与该改善参数相关的恶化参数
        for (imp, wors), _ in self.matrix.items():
            if imp == improving or imp in improving or improving in imp:
                suggestions.append(wors)

        # 去重并限制数量
        suggestions = list(set(suggestions))

        # 如果没有找到建议，返回一些常见参数
        if not suggestions:
            suggestions = ["移动物体用的能源", "重量", "成本", "设备的复杂性", "时间的浪费"]

        return suggestions[:10]  # 最多返回10个建议

    def validate_parameters(self, improving: str, worsening: str) -> Tuple[bool, str]:
        """
        验证参数是否有效

        Args:
            improving: 改善参数
            worsening: 恶化参数

        Returns:
            (是否有效, 错误消息)
        """
        if not improving or not improving.strip():
            return False, "改善参数不能为空"

        if not worsening or not worsening.strip():
            return False, "恶化参数不能为空"

        # 检查参数是否在列表中（宽松检查）
        improving_valid = any(
            improving in param or param in improving
            for param in self.parameters
        )
        worsening_valid = any(
            worsening in param or param in worsening
            for param in self.parameters
        )

        if not improving_valid:
            logger.warning(f"改善参数 '{improving}' 不在标准参数列表中")

        if not worsening_valid:
            logger.warning(f"恶化参数 '{worsening}' 不在标准参数列表中")

        return True, "参数有效"


class MatrixManager:
    """矩阵管理器"""

    def __init__(self):
        self.matrices: Dict[str, ContradictionMatrix] = {}
        self.current_matrix_type = "39"

    def get_matrix(self, matrix_type: Optional[str] = None) -> ContradictionMatrix:
        """
        获取指定类型的矛盾矩阵

        Args:
            matrix_type: 矩阵类型，默认为当前类型

        Returns:
            矛盾矩阵实例
        """
        if matrix_type is None:
            matrix_type = self.current_matrix_type

        if matrix_type not in self.matrices:
            self.matrices[matrix_type] = ContradictionMatrix(matrix_type)

        return self.matrices[matrix_type]

    def set_current_matrix(self, matrix_type: str):
        """设置当前矩阵类型"""
        if matrix_type not in ["39", "48"]:
            raise ValueError(f"不支持的矩阵类型: {matrix_type}")

        self.current_matrix_type = matrix_type
        logger.info(f"切换矩阵类型为: {matrix_type}")

    def get_current_matrix(self) -> ContradictionMatrix:
        """获取当前矩阵"""
        return self.get_matrix(self.current_matrix_type)

    def get_available_matrix_types(self) -> List[Dict[str, str | bool]]:
        """获取可用的矩阵类型"""
        return [
            {"type": "39", "name": "39矛盾矩阵", "description": "标准39参数矛盾矩阵", "enabled": True},
            {"type": "48", "name": "48矛盾矩阵", "description": "扩展48参数矛盾矩阵（规划中）", "enabled": False}
        ]


# 全局矩阵管理器实例
matrix_manager = MatrixManager()


def get_matrix_manager() -> MatrixManager:
    """获取全局矩阵管理器"""
    return matrix_manager