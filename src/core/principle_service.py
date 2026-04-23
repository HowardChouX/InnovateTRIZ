"""
40发明原理服务
提供40个发明原理的完整信息查询
"""

import logging
from typing import Any

from config.constants import INVENTIVE_PRINCIPLES, PRINCIPLE_CATEGORIES
from data.models import InventivePrinciple
from data.triz_constants import PRINCIPLE_DETAILS, get_triz_data_loader

logger = logging.getLogger(__name__)


class PrincipleService:
    """40发明原理服务类"""

    def __init__(self) -> None:
        self._principles: dict[int, InventivePrinciple] = {}
        self._load_principles()

    def _load_principles(self) -> None:
        """加载40个发明原理"""
        # 使用TRIZ数据加载器获取原理名称
        triz_loader = get_triz_data_loader()
        triz_principles = triz_loader.get_40_principles()
        triz_name_map = {p["id"]: p["name"] for p in triz_principles}

        # 使用详细信息填充原理
        for principle_id in range(1, 41):
            # 获取TRIZ数据中的名称（如果有）
            name = triz_name_map.get(
                principle_id,
                INVENTIVE_PRINCIPLES.get(principle_id, f"原理{principle_id}"),
            )

            # 获取详细信息（如果没有则使用默认信息）
            details = PRINCIPLE_DETAILS.get(principle_id, {})
            details["name"] = name

            principle = InventivePrinciple(
                id=principle_id,
                name=name,
                definition=details.get("definition", ""),
                category=details.get("category", ""),
                tags=details.get("tags", []),
                examples=details.get("examples", []),
                use_cases=details.get("use_cases", []),
                explanation=details.get("explanation", ""),
                implementation_steps=details.get("implementation_steps", []),
                benefits=details.get("benefits", ""),
            )
            self._principles[principle_id] = principle

        logger.info(f"加载了{len(self._principles)}个发明原理")

    def get_principle(self, principle_id: int) -> InventivePrinciple | None:
        """
        获取指定编号的发明原理

        Args:
            principle_id: 原理编号 (1-40)

        Returns:
            发明原理对象，如果不存在则返回None
        """
        return self._principles.get(principle_id)

    def get_all_principles(self) -> list[InventivePrinciple]:
        """
        获取所有40个发明原理

        Returns:
            发明原理列表
        """
        return list(self._principles.values())

    def get_principles_by_ids(
        self, principle_ids: list[int]
    ) -> list[InventivePrinciple]:
        """
        根据编号列表获取发明原理

        Args:
            principle_ids: 原理编号列表

        Returns:
            发明原理列表
        """
        return [
            self._principles[pid] for pid in principle_ids if pid in self._principles
        ]



# 全局单例
_principle_service: PrincipleService | None = None


def get_principle_service() -> PrincipleService:
    """获取全局原理服务实例"""
    global _principle_service
    if _principle_service is None:
        _principle_service = PrincipleService()
    return _principle_service
