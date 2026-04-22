"""
本地TRIZ引擎（无AI版本）
提供基础的TRIZ分析功能
"""

import logging
import random
from collections.abc import Callable
from datetime import datetime
from functools import lru_cache
from typing import Any

from ..config.constants import (
    ENGINEERING_PARAMETERS_39,
    INVENTIVE_PRINCIPLES,
    PRINCIPLE_CATEGORIES,
)
from ..data.models import (
    AIAnalysisRequest,
    AIAnalysisResponse,
    AnalysisSession,
    Solution,
)

logger = logging.getLogger(__name__)


@lru_cache(maxsize=256)
def _cached_detect_parameters(problem: str) -> tuple:
    """
    带缓存的参数检测算法（纯函数，无副作用）

    Args:
        problem: 问题描述

    Returns:
        (improving_param, worsening_param, explanation) 元组
    """
    problem_lower = problem.lower()

    # 关键词数据结构
    class KeywordData:
        def __init__(self, kws: list[str], w: float):
            self.keywords = kws
            self.weight = w

    # 扩展的改善参数关键词映射（带权重）
    improving_keywords: dict[str, KeywordData] = {
        "速度": KeywordData(
            ["快", "速度", "效率", "响应", "延迟", "耗时", "快速", "加速"], 1.0
        ),
        "强度": KeywordData(
            ["强", "坚固", "耐用", "寿命", "可靠", "稳固", "牢固"], 1.0
        ),
        "精度": KeywordData(["精确", "准确", "误差", "偏差", "公差", "精密"], 1.0),
        "重量": KeywordData(["轻", "轻便", "轻量", "轻巧"], 1.2),
        "能耗": KeywordData(["省电", "节能", "低功耗", "省能"], 1.2),
        "成本": KeywordData(["便宜", "省钱", "经济", "廉价", "低成本"], 1.2),
        "安全性": KeywordData(["安全", "防护", "保险", "安心"], 1.0),
        "可靠性": KeywordData(["可靠", "稳定", "耐用", "持久", "长久"], 1.0),
        "功率": KeywordData(["功率", "动力", "强劲", "马力", "高性能"], 1.0),
        "温度": KeywordData(["冷却", "散热", "低温", "凉爽"], 1.0),
        "产能/生产力": KeywordData(["产能/生产力", "产量", "效率", "高产"], 1.0),
        "修复性": KeywordData(["维修", "保养", "易修", "维护"], 1.0),
        "适应性": KeywordData(["适应", "通用", "灵活", "多变"], 1.0),
        "使用的便利性": KeywordData(["易用", "简便", "简单", "操作方便"], 1.0),
        "自动化程度": KeywordData(["自动", "智能", "自动化", "无人"], 1.0),
        "制造的准度": KeywordData(["精密", "精细", "光洁", "平滑"], 1.0),
        "测量的准度": KeywordData(["测量", "检测", "传感", "精确"], 1.0),
    }

    # 恶化工况关键词映射（带权重）
    worsening_keywords: dict[str, KeywordData] = {
        "速度": KeywordData(["慢", "缓慢", "减速", "延迟"], 1.0),
        "重量": KeywordData(["重", "沉重", "笨重", "笨拙"], 1.0),
        "能耗": KeywordData(["耗电", "功耗", "费电", "高能耗", "能源消耗"], 1.0),
        "成本": KeywordData(["贵", "昂贵", "高成本", "费用高"], 1.0),
        "复杂性": KeywordData(["复杂", "繁琐", "难用", "麻烦", "复杂化"], 1.0),
        "可靠性": KeywordData(["故障", "失效", "损坏", "易坏", "不稳定"], 1.0),
        "强度": KeywordData(["弱", "脆弱", "易损", "不耐用"], 1.0),
        "温度": KeywordData(["热", "高温", "过热", "发烫"], 1.0),
        "移动物体用的能源": KeywordData(["耗能", "能耗高", "费电"], 1.2),
        "设备的复杂性": KeywordData(["复杂", "繁杂", "结构复杂"], 1.0),
        "控制的复杂性": KeywordData(["难检测", "难测量", "检测复杂"], 1.0),
        "有害的副作用": KeywordData(["污染", "危害", "有害", "危险"], 1.0),
        "时间的浪费": KeywordData(["耗时", "费时", "时间长", "延误"], 1.0),
        "物质的浪费": KeywordData(["损耗", "浪费", "消耗"], 1.0),
        "信息的流失": KeywordData(["丢失", "损失", "失真"], 1.0),
    }

    # 检测改善参数
    improving_param = "速度"
    improving_score = 0.0

    for param, data in improving_keywords.items():
        score = sum(1 for keyword in data.keywords if keyword in problem_lower)
        weighted_score = score * data.weight
        if weighted_score > improving_score:
            improving_score = weighted_score
            improving_param = param

    # 检测恶化参数
    worsening_param = "成本"
    worsening_score = 0.0

    for param, data in worsening_keywords.items():
        score = sum(1 for keyword in data.keywords if keyword in problem_lower)
        weighted_score = score * data.weight
        if weighted_score > worsening_score:
            worsening_score = weighted_score
            worsening_param = param

    # 避免改善和恶化参数相同
    if improving_param == worsening_param:
        for param in ENGINEERING_PARAMETERS_39:
            if param != improving_param and param != "速度" and param != "成本":
                worsening_param = param
                break
        else:
            worsening_param = "能耗" if improving_param != "能耗" else "设备的复杂性"

    return (improving_param, worsening_param, "本地算法自动检测")


class LocalTRIZEngine:
    """本地TRIZ引擎"""

    def __init__(self) -> None:
        self.solution_templates = self._init_solution_templates()
        self.example_database = self._init_example_database()
        logger.info("本地TRIZ引擎初始化完成")

    def _init_solution_templates(self) -> dict[int, list[str]]:
        """初始化解决方案模板"""
        templates = {}

        # 为每个原理创建多个模板
        for principle_id, principle_name in INVENTIVE_PRINCIPLES.items():
            templates[principle_id] = [
                f"应用{principle_name}，通过重新设计系统结构来解决问题",
                f"利用{principle_name}，改变物体或系统的某个属性",
                f"采用{principle_name}，引入新的元素或机制",
                f"基于{principle_name}，优化现有流程或方法",
                f"运用{principle_name}，创造性地组合不同功能",
            ]

        return templates

    def _init_example_database(self) -> dict[int, list[str]]:
        """初始化示例数据库"""
        examples = {}

        # 分割原理示例
        examples[1] = [
            "将整体分割为多个独立模块，便于维护和升级",
            "使用可拆卸设计，方便运输和安装",
            "将复杂功能分解为简单子功能",
        ]

        # 抽取原理示例
        examples[2] = [
            "提取关键部件单独优化",
            "分离有害部分或有用部分",
            "从复杂系统中提取核心功能",
        ]

        # 局部质量原理示例
        examples[3] = [
            "不同部位使用不同材料",
            "关键部位加强设计",
            "根据功能需求优化局部结构",
        ]

        # 动态性原理示例
        examples[15] = [
            "设计可调节部件适应不同需求",
            "使用柔性材料或结构",
            "实现系统的自适应调节",
        ]

        # 周期性作用原理示例
        examples[19] = [
            "使用脉冲代替连续作用",
            "周期性检查维护",
            "间歇性工作模式节省能源",
        ]

        # 变害为利原理示例
        examples[22] = ["利用废热发电", "将噪音转化为能源", "回收副产品创造价值"]

        # 为没有特定示例的原理提供通用示例
        for principle_id in INVENTIVE_PRINCIPLES.keys():
            if principle_id not in examples:
                examples[principle_id] = [
                    f"{INVENTIVE_PRINCIPLES[principle_id]}的典型工业应用",
                    f"使用{INVENTIVE_PRINCIPLES[principle_id]}解决类似问题的案例",
                    f"{INVENTIVE_PRINCIPLES[principle_id]}在产品设计中的应用",
                ]

        return examples

    def detect_parameters(self, problem: str) -> dict[str, str]:
        """
        本地算法检测技术参数（改进版，带缓存）

        Args:
            problem: 问题描述

        Returns:
            包含改善和恶化参数的字典
        """
        improving, worsening, explanation = _cached_detect_parameters(problem)
        logger.info(f"本地参数检测: 改善={improving}, 恶化={worsening}")
        return {
            "improving": improving,
            "worsening": worsening,
            "explanation": explanation,
        }

    def generate_solutions(
        self, principle_ids: list[int], problem: str, count: int = 5
    ) -> list[Solution]:
        """
        本地生成解决方案

        Args:
            principle_ids: 发明原理编号列表
            problem: 问题描述
            count: 需要生成的解决方案数量

        Returns:
            解决方案列表
        """
        if count <= 0:
            return []

        solutions: list[Solution] = []
        used_principles: set[int] = set()

        # 限制数量
        actual_count = min(count, len(principle_ids) * 2)

        for _ in range(actual_count):
            # 选择原理（优先使用提供的原理）
            if principle_ids:
                principle_id = random.choice(principle_ids)
            else:
                # 如果没有提供原理，随机选择一个
                principle_id = random.choice(list(INVENTIVE_PRINCIPLES.keys()))

            # 避免重复使用同一原理（除非原理不够）
            if principle_id in used_principles and len(used_principles) < len(
                principle_ids
            ):
                # 尝试选择未使用的原理
                unused = [pid for pid in principle_ids if pid not in used_principles]
                if unused:
                    principle_id = random.choice(unused)

            used_principles.add(principle_id)

            # 获取原理名称
            principle_name = INVENTIVE_PRINCIPLES.get(
                principle_id, f"原理{principle_id}"
            )

            # 确定分类
            category = "物理"
            for cat, pids in PRINCIPLE_CATEGORIES.items():
                if principle_id in pids:
                    category = cat
                    break

            # 选择模板
            templates = self.solution_templates.get(principle_id, [])
            if templates:
                template = random.choice(templates)
                description = template.replace("{problem}", problem)
            else:
                description = f"应用{principle_name}来解决{problem}"

            # 获取示例
            examples = self.example_database.get(principle_id, [])
            if examples:
                selected_examples = random.sample(examples, min(2, len(examples)))
            else:
                selected_examples = [f"{principle_name}的典型应用"]

            # 生成置信度（本地生成的置信度稍低）
            confidence = random.uniform(0.6, 0.85)

            solution = Solution(
                principle_id=principle_id,
                principle_name=principle_name,
                description=description,
                confidence=confidence,
                is_ai_generated=False,
                category=category,
                examples=selected_examples,
            )

            solutions.append(solution)

        logger.info(f"本地生成 {len(solutions)} 个解决方案")

        return solutions

    def generate_solutions_from_request(
        self, request: AIAnalysisRequest
    ) -> AIAnalysisResponse:
        """
        从请求生成解决方案（兼容AI接口）

        Args:
            request: 分析请求

        Returns:
            分析响应
        """
        start_time = datetime.now()

        try:
            # 生成解决方案
            solutions = self.generate_solutions(
                principle_ids=request.principle_ids or [],
                problem=request.problem,
                count=request.solution_count,
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            return AIAnalysisResponse(
                success=True, solutions=solutions, processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"本地生成解决方案失败: {e}")
            return AIAnalysisResponse(
                success=False,
                solutions=[],
                error_message=f"本地分析失败: {str(e)}",
                processing_time=0,
            )

    def categorize_solutions(
        self, solutions: list[Solution]
    ) -> dict[str, list[Solution]]:
        """
        按原理分类解决方案

        Args:
            solutions: 解决方案列表

        Returns:
            按分类组织的解决方案字典
        """
        categorized: dict[str, list[Solution]] = {}

        # 初始化分类
        for category in PRINCIPLE_CATEGORIES.keys():
            categorized[category] = []

        # 未分类的解决方案
        categorized["其他"] = []

        # 分类解决方案
        for solution in solutions:
            placed = False

            for category, principle_ids in PRINCIPLE_CATEGORIES.items():
                if solution.principle_id in principle_ids:
                    categorized[category].append(solution)
                    placed = True
                    break

            if not placed:
                categorized["其他"].append(solution)

        # 移除空分类
        result = {k: v for k, v in categorized.items() if v}

        logger.info(f"解决方案分类完成: {list(result.keys())}")

        return result

    def get_solution_statistics(self, solutions: list[Solution]) -> dict[str, Any]:
        """
        获取解决方案统计信息

        Args:
            solutions: 解决方案列表

        Returns:
            统计信息字典
        """
        if not solutions:
            return {
                "total": 0,
                "ai_generated": 0,
                "avg_confidence": 0,
                "categories": {},
            }

        total = len(solutions)
        ai_generated = sum(1 for s in solutions if s.is_ai_generated)
        avg_confidence = sum(s.confidence for s in solutions) / total

        # 分类统计
        categories = {}
        for solution in solutions:
            category = solution.category
            if category not in categories:
                categories[category] = 0
            categories[category] += 1

        # 原理分布
        principle_dist = {}
        for solution in solutions:
            principle_id = solution.principle_id
            if principle_id not in principle_dist:
                principle_dist[principle_id] = 0
            principle_dist[principle_id] += 1

        # 排序原理分布
        sorted_principles = sorted(
            principle_dist.items(), key=lambda x: x[1], reverse=True
        )[
            :10
        ]  # 只显示前10个

        return {
            "total": total,
            "ai_generated": ai_generated,
            "ai_percentage": ai_generated / total * 100 if total > 0 else 0,
            "avg_confidence": round(avg_confidence, 3),
            "categories": categories,
            "top_principles": sorted_principles,
        }

    def enhance_solution_descriptions(
        self, solutions: list[Solution], problem: str
    ) -> list[Solution]:
        """
        增强解决方案描述（使其更具体）

        Args:
            solutions: 原始解决方案
            problem: 问题描述

        Returns:
            增强后的解决方案
        """
        enhanced = []

        for solution in solutions:
            # 创建增强描述
            enhanced_desc = self._enhance_description(
                solution.description, solution.principle_name, problem
            )

            # 创建增强示例
            enhanced_examples = self._enhance_examples(
                solution.examples, solution.principle_name, problem
            )

            # 创建新解决方案（保持其他属性不变）
            enhanced_solution = Solution(
                id=solution.id,
                principle_id=solution.principle_id,
                principle_name=solution.principle_name,
                description=enhanced_desc,
                confidence=min(solution.confidence * 1.1, 0.95),  # 稍微提高置信度
                is_ai_generated=solution.is_ai_generated,
                category=solution.category,
                examples=enhanced_examples,
                created_at=solution.created_at,
            )

            enhanced.append(enhanced_solution)

        logger.info(f"增强 {len(enhanced)} 个解决方案描述")

        return enhanced

    def _enhance_description(
        self, description: str, _principle: str, problem: str
    ) -> str:
        """增强描述"""
        # 简单的增强逻辑
        enhancements = [
            f"针对'{problem}'，{description}",
            f"{description}，特别适用于解决类似'{problem}'的问题",
            f"在'{problem}'的背景下，{description}",
        ]

        return random.choice(enhancements)

    def _enhance_examples(
        self, examples: list[str], principle: str, problem: str
    ) -> list[str]:
        """增强示例"""
        enhanced = examples.copy()

        # 添加问题相关的示例
        problem_keywords = ["手机", "电池", "软件", "系统", "设计", "产品"]
        for keyword in problem_keywords:
            if keyword in problem and len(enhanced) < 5:
                enhanced.append(f"在{keyword}领域应用{principle}的案例")

        return enhanced[:3]  # 最多3个示例


class TRIZEngine:
    """统一的TRIZ引擎（整合本地和AI）"""

    def __init__(self) -> None:
        self.local_engine = LocalTRIZEngine()
        logger.info("TRIZ引擎初始化完成")

    async def analyze_problem(
        self,
        problem: str,
        improving_param: str | None = None,
        worsening_param: str | None = None,
        use_ai: bool = False,
        ai_request: AIAnalysisRequest | None = None,
    ) -> AnalysisSession:
        """
        分析问题（统一接口）

        Args:
            problem: 问题描述
            improving_param: 改善参数（可选）
            worsening_param: 恶化参数（可选）
            use_ai: 是否使用AI
            ai_request: AI请求参数（可选）

        Returns:
            分析会话
        """
        # 创建会话
        session = AnalysisSession(problem=problem, ai_enabled=use_ai)

        # 如果参数未提供，自动检测
        if not improving_param or not worsening_param:
            detected = self.local_engine.detect_parameters(problem)
            improving_param = detected["improving"]
            worsening_param = detected["worsening"]
            session.improving_param = improving_param
            session.worsening_param = worsening_param
        else:
            # 用户提供了参数，也要设置到session中
            session.improving_param = improving_param
            session.worsening_param = worsening_param

        # 这里可以添加矩阵查询逻辑
        # 暂时使用本地引擎生成解决方案

        # 创建AI请求（如果需要）
        if use_ai and ai_request:
            request = ai_request
        else:
            request = AIAnalysisRequest(
                problem=problem,
                improving_param=improving_param,
                worsening_param=worsening_param,
                solution_count=5,
            )

        # 生成解决方案
        if use_ai:
            # 从 ai_manager 获取 AI 客户端
            from ..ai.ai_client import get_ai_manager

            ai_manager = get_ai_manager()
            ai_client = ai_manager.get_client()
            if ai_client:
                response = await ai_client.generate_solutions(request)
            else:
                logger.warning("AI未启用，使用本地引擎")
                response = self.local_engine.generate_solutions_from_request(request)
        else:
            response = self.local_engine.generate_solutions_from_request(request)

        if response.success:
            session.solutions = response.solutions
            session.solution_count = len(response.solutions)
        else:
            logger.warning(f"生成解决方案失败: {response.error_message}")

        logger.info(
            f"问题分析完成: {problem[:50]}... -> {len(session.solutions)}个方案"
        )

        return session

    async def generate_solutions_iterative(
        self,
        problem: str,
        improving_param: str | None,
        worsening_param: str | None,
        principle_ids: list[int],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[Solution]:
        """
        遍历方式生成解决方案（每个原理单独调用AI）

        Args:
            problem: 问题描述
            improving_param: 改善参数
            worsening_param: 恶化参数
            principle_ids: 原理ID列表
            progress_callback: 进度回调函数 (current: int, total: int)

        Returns:
            解决方案列表
        """
        from ..ai.ai_client import get_ai_manager

        solutions: list[Solution] = []
        total = len(principle_ids)

        if total == 0:
            return solutions

        ai_manager = get_ai_manager()
        ai_client = ai_manager.get_client()

        if not ai_client:
            logger.warning("AI客户端不可用，使用本地引擎生成")
            return self.local_engine.generate_solutions(
                principle_ids=principle_ids, problem=problem, count=total
            )

        for i, principle_id in enumerate(principle_ids):
            # 报告进度
            if progress_callback:
                progress_callback(i + 1, total)

            # 为单个原理生成解决方案
            solution = await ai_client.generate_solution_for_principle(
                problem=problem,
                improving_param=improving_param or "",
                worsening_param=worsening_param or "",
                principle_id=principle_id,
            )

            if solution:
                solutions.append(solution)
            else:
                # 如果AI生成失败，使用本地引擎作为后备
                logger.warning(f"原理{principle_id}的AI生成失败，使用本地引擎")
                local_solutions = self.local_engine.generate_solutions(
                    principle_ids=[principle_id], problem=problem, count=1
                )
                if local_solutions:
                    solutions.append(local_solutions[0])

        logger.info(f"遍历生成完成: 共{len(solutions)}/{total}个解决方案")
        return solutions


# 全局TRIZ引擎实例
triz_engine = TRIZEngine()


def get_triz_engine() -> TRIZEngine:
    """获取全局TRIZ引擎"""
    return triz_engine
