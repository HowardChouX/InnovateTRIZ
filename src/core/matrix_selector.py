"""
矛盾矩阵选择器和查询器
支持39矛盾矩阵，48矩阵为预留接口
"""

import logging
from typing import TYPE_CHECKING

from config.constants import INVENTIVE_PRINCIPLES
from data.models import MatrixQueryResult, PrincipleQueryResult
from data.triz_constants import get_triz_data_loader

if TYPE_CHECKING:
    from data.triz_constants import TRIZDataLoader

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
        self.parameters: list[str] = []
        self.matrix: dict[tuple[str, str], list[int]] = {}
        self._triz_loader: TRIZDataLoader | None = None
        self._init_matrix()

    def _init_matrix(self) -> None:
        """初始化矩阵数据"""
        if self.matrix_type == "39":
            self._init_39_matrix()
        elif self.matrix_type == "48":
            self._init_48_matrix()
        else:
            raise ValueError(f"不支持的矩阵类型: {self.matrix_type}")

    def _init_39_matrix(self) -> None:
        """初始化39矛盾矩阵"""
        # 从内置数据加载完整矩阵数据
        loader = get_triz_data_loader()
        self._triz_loader = loader
        self.matrix = loader.get_contradiction_matrix()
        self.parameters = loader.get_all_params()

        logger.info(
            f"加载39矛盾矩阵，包含{len(self.parameters)}个参数和{len(self.matrix)}个组合"
        )

    def _init_48_matrix(self) -> None:
        """初始化48矛盾矩阵（预留）"""
        self.parameters = []
        self.matrix = {}
        logger.warning("48矛盾矩阵暂未实现，使用空矩阵")

    def find_solutions(self, improving: str, worsening: str) -> list[int]:
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
                    logger.info(
                        f"找到部分匹配: {improving} vs {worsening} -> {principles}"
                    )
                    return principles

        # 参数名称标准化匹配
        normalized_improving = self._normalize_param(improving)
        normalized_worsening = self._normalize_param(worsening)

        # 尝试标准化后的精确匹配
        for (imp, wors), principles in self.matrix.items():
            norm_imp = self._normalize_param(imp)
            norm_wors = self._normalize_param(wors)
            if norm_imp == normalized_improving or normalized_improving in norm_imp:
                if (
                    norm_wors == normalized_worsening
                    or normalized_worsening in norm_wors
                ):
                    logger.info(
                        f"找到标准化匹配: {improving} vs {worsening} -> {principles}"
                    )
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
        # 移除"移动物体的"和"静止物体的"前缀进行对比
        normalized_no_prefix = normalized.replace("移动物体的", "").replace(
            "静止物体的", ""
        )
        return normalized_no_prefix

    def query_matrix(
        self, improving: str | None = None, worsening: str | None = None
    ) -> MatrixQueryResult:
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

        logger.info(
            f"矩阵查询结果: {improving} vs {worsening} -> {principle_ids} ({principle_names})"
        )

        return MatrixQueryResult(
            improving_param=improving,
            worsening_param=worsening,
            principle_ids=principle_ids,
            matrix_type=self.matrix_type,
            is_auto_detected=is_auto_detected,
        )

    def query_with_result(
        self, improving: str | None = None, worsening: str | None = None
    ) -> PrincipleQueryResult:
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
            confidence="高" if len(result.principle_ids) > 0 else "低",
        )



class MatrixManager:
    """矩阵管理器"""

    def __init__(self) -> None:
        self.matrices: dict[str, ContradictionMatrix] = {}
        self.current_matrix_type = "39"

    def get_matrix(self, matrix_type: str | None = None) -> ContradictionMatrix:
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

    def set_current_matrix(self, matrix_type: str) -> None:
        """设置当前矩阵类型"""
        if matrix_type not in ["39", "48"]:
            raise ValueError(f"不支持的矩阵类型: {matrix_type}")

        self.current_matrix_type = matrix_type
        logger.info(f"切换矩阵类型为: {matrix_type}")

    def get_current_matrix(self) -> ContradictionMatrix:
        """获取当前矩阵"""
        return self.get_matrix(self.current_matrix_type)

    def get_available_matrix_types(self) -> list[dict[str, str | bool]]:
        """获取可用的矩阵类型"""
        return [
            {
                "type": "39",
                "name": "39矛盾矩阵",
                "description": "标准39参数矛盾矩阵",
                "enabled": True,
            },
            {
                "type": "48",
                "name": "48矛盾矩阵",
                "description": "扩展48参数矛盾矩阵（规划中）",
                "enabled": False,
            },
        ]


# 全局矩阵管理器实例
matrix_manager = MatrixManager()


def get_matrix_manager() -> MatrixManager:
    """获取全局矩阵管理器"""
    return matrix_manager
