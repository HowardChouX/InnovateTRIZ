"""
数据模型定义
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Solution:
    """解决方案"""

    principle_id: int  # 发明原理编号（1-40）
    principle_name: str  # 原理名称
    description: str = ""  # 兼容旧字段，保留为空或沿用
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    confidence: float = 0.8  # 置信度（0-1）
    is_ai_generated: bool = False  # 是否AI生成
    category: str = "物理"  # 分类
    examples: list[str] = field(default_factory=list)  # 应用示例（兼容旧字段）
    created_at: datetime = field(default_factory=datetime.now)
    # 4字段结构化输出（头脑风暴专用）
    technical_solution: str = ""  # 技术方案（100-200字）
    innovation_point: str = ""  # 创新点（20-50字）
    cross_domain_cases: list[str] = field(default_factory=list)  # 跨领域案例
    expected_effect: str = ""  # 预期效果

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = {
            "id": self.id,
            "principle_id": self.principle_id,
            "principle_name": self.principle_name,
            "description": self.description,
            "confidence": self.confidence,
            "is_ai_generated": self.is_ai_generated,
            "category": self.category,
            "examples": self.examples,
            "created_at": self.created_at.isoformat(),
            # 4字段结构化输出
            "technical_solution": self.technical_solution,
            "innovation_point": self.innovation_point,
            "cross_domain_cases": self.cross_domain_cases,
            "expected_effect": self.expected_effect,
        }
        return data

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Solution":
        """从字典创建实例"""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        # 处理新字段的默认值
        data.setdefault("technical_solution", "")
        data.setdefault("innovation_point", "")
        data.setdefault("cross_domain_cases", [])
        data.setdefault("expected_effect", "")
        return cls(**data)


@dataclass
class AnalysisSession:
    """分析会话记录"""

    problem: str  # 问题描述
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    matrix_type: str = "39"  # 矩阵类型（39/48）
    improving_param: str | None = None  # 改善参数
    worsening_param: str | None = None  # 恶化参数
    ai_enabled: bool = False  # AI是否启用
    solution_count: int = 0  # 解决方案数量
    solutions: list[Solution] = field(default_factory=list)  # 生成的解决方案
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["solutions"] = [sol.to_dict() for sol in self.solutions]
        return data

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisSession":
        """从字典创建实例"""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])

        # 转换解决方案列表
        if "solutions" in data and isinstance(data["solutions"], list):
            solutions = []
            for sol_data in data["solutions"]:
                solutions.append(Solution.from_dict(sol_data))
            data["solutions"] = solutions

        return cls(**data)

    def get_summary(self) -> dict[str, Any]:
        """获取会话摘要"""
        return {
            "id": self.id,
            "problem_preview": self.problem[:50]
            + ("..." if len(self.problem) > 50 else ""),
            "matrix_type": self.matrix_type,
            "ai_enabled": self.ai_enabled,
            "solution_count": len(self.solutions),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
            "improving_param": self.improving_param,
            "worsening_param": self.worsening_param,
        }


@dataclass
class ProviderConfig:
    """AI供应商配置"""

    api_key: str | None = None  # API密钥
    base_url: str = "https://api.deepseek.com/v1"  # Base URL
    model: str = "deepseek-chat"  # 模型

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderConfig":
        """从字典创建实例"""
        return cls(**data)


# 默认供应商配置
DEFAULT_PROVIDER_CONFIGS = {
    "deepseek": ProviderConfig(
        api_key=None, base_url="https://api.deepseek.com/v1", model="deepseek-chat"
    ),
    "openrouter": ProviderConfig(
        api_key=None,
        base_url="https://openrouter.ai/api/v1",
        model="deepseek/deepseek-chat",
    ),
    "openai-format": ProviderConfig(
        api_key=None, base_url="https://api.openai.com/v1", model="gpt-4"
    ),
}


@dataclass
class AppConfig:
    """应用配置"""

    ai_provider: str = "deepseek"  # 当前AI提供商
    ai_providers_config: dict[str, ProviderConfig] = field(
        default_factory=lambda: DEFAULT_PROVIDER_CONFIGS.copy()
    )
    default_matrix_type: str = "39"  # 默认矩阵类型
    default_solution_count: int = 5  # 默认解决方案数量
    enable_history: bool = True  # 启用历史记录
    enable_cache: bool = True  # 启用缓存
    language: str = "zh"  # 界面语言
    theme: str = "light"  # 主题模式

    # 兼容旧字段（从旧配置迁移时使用）
    ai_api_key: str | None = None
    ai_base_url: str = "https://api.deepseek.com"
    ai_model: str = "deepseek-chat"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 将 providers_config 转换为普通字典
        data["ai_providers_config"] = {
            k: v.to_dict() if isinstance(v, ProviderConfig) else v
            for k, v in self.ai_providers_config.items()
        }
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        """从字典创建实例"""
        # 迁移旧格式配置
        if "ai_providers_config" not in data:
            providers_config = DEFAULT_PROVIDER_CONFIGS.copy()
            current_provider = data.get("ai_provider", "deepseek")

            # 迁移旧格式到新格式
            if current_provider in providers_config:
                old_config = providers_config[current_provider]
                if data.get("ai_api_key"):
                    old_config.api_key = data["ai_api_key"]
                if data.get("ai_base_url"):
                    old_config.base_url = data["ai_base_url"]
                if data.get("ai_model"):
                    old_config.model = data["ai_model"]

            data["ai_providers_config"] = {
                k: v.to_dict() if isinstance(v, ProviderConfig) else v
                for k, v in providers_config.items()
            }

        # 确保 providers_config 是 ProviderConfig 对象
        if "ai_providers_config" in data and isinstance(
            data["ai_providers_config"], dict
        ):
            data["ai_providers_config"] = {
                k: ProviderConfig.from_dict(v) if isinstance(v, dict) else v
                for k, v in data["ai_providers_config"].items()
            }

        return cls(**data)

    def get_current_provider_config(self) -> ProviderConfig:
        """获取当前供应商配置"""
        return self.ai_providers_config.get(
            self.ai_provider,
            DEFAULT_PROVIDER_CONFIGS.get(self.ai_provider, ProviderConfig()),
        )

    def set_provider_config(self, provider: str, config: ProviderConfig) -> None:
        """设置指定供应商的配置"""
        self.ai_providers_config[provider] = config


@dataclass
class MatrixQueryResult:
    """矩阵查询结果"""

    improving_param: str
    worsening_param: str
    principle_ids: list[int]  # 找到的发明原理编号
    matrix_type: str
    is_auto_detected: bool = False  # 参数是否自动检测

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class AIAnalysisRequest:
    """AI分析请求"""

    problem: str
    improving_param: str | None = None
    worsening_param: str | None = None
    principle_ids: list[int] | None = None
    solution_count: int = 5
    language: str = "zh"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class AIAnalysisResponse:
    """AI分析响应"""

    success: bool
    solutions: list[Solution]
    error_message: str | None = None
    processing_time: float | None = None  # 处理时间（秒）

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["solutions"] = [sol.to_dict() for sol in self.solutions]
        return data


# 导出相关的数据模型
@dataclass
class ExportOptions:
    """导出选项"""

    format: str = "json"  # json, txt, csv
    include_problem: bool = True
    include_parameters: bool = True
    include_solutions: bool = True
    include_timestamp: bool = True

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class ExportResult:
    """导出结果"""

    success: bool
    file_path: str | None = None
    file_size: int | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class InventivePrinciple:
    """40发明原理完整信息"""

    id: int  # 1-40
    name: str  # 原理名称
    definition: str = ""  # 核心定义
    category: str = ""  # 分类 (物理/化学/几何/时间/系统)
    tags: list[str] = field(default_factory=list)  # 标签列表
    examples: list[str] = field(default_factory=list)  # 示例
    use_cases: list[str] = field(default_factory=list)  # 应用案例
    explanation: str = ""  # 详细说明
    implementation_steps: list[str] = field(default_factory=list)  # 实施步骤
    benefits: str = ""  # 应用效益

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InventivePrinciple":
        """从字典创建实例"""
        return cls(**data)


@dataclass
class PrincipleQueryResult:
    """原理查询结果"""

    principle_ids: list[int]  # 原理编号列表
    improving_param: str  # 改善参数
    worsening_param: str  # 恶化参数
    source: str = "matrix"  # 数据来源 (matrix/excel)
    confidence: str = ""  # 置信度说明

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)
