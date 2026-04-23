"""
TRIZ引擎模块
提供本地和AI增强的TRIZ分析功能
"""

import logging
import random
from collections.abc import Callable
from datetime import datetime
from functools import lru_cache
from typing import Any

from config.constants import (
    ENGINEERING_PARAMETERS_39,
    INVENTIVE_PRINCIPLES,
    PRINCIPLE_CATEGORIES,
)
from data.models import (
    AIAnalysisRequest,
    AIAnalysisResponse,
    AnalysisSession,
    Solution,
)
from data.triz_constants import ENGINEERING_PARAMETERS_48

logger = logging.getLogger(__name__)

# 参数名称映射：从param_keywords使用的简写名称到ENGINEERING_PARAMETERS_39完整名称
_PARAM_SHORT_TO_FULL = {
    "重量": "移动物体的重量",
    "亮度": "明亮度",
    "能源的浪费": "能量的浪费",
    "信息的流失": "信息的遗漏",
    "物质的总量": "物质的数量",
    "测量的准度": "测量的准确度",
    "制造的准度": "制造的准确度",
    "制造性": "可制造性",
    "物体的稳定性": "结构的稳定性",
    "移动物体的持久性": "移动物体的耐久性",
    "静止物体的持久性": "静止物体的耐久性",
    "移动物体用的能源": "移动物体消耗的能量",
    "非移动物体用的能源": "静止物体消耗的能量",
    "产能/生产力": "生产率",
    "作用于物体的有害因素": "外来有害因素",
    "设备的复杂性": "装置的复杂性",
    "能耗": "能量的浪费",  # 能耗 -> 能量的浪费
    "复杂性": "装置的复杂性",  # 简写 -> 完整
}


def _map_param_name(param: str) -> str:
    """将简写参数名映射到完整参数名（与MATRIX_39键匹配）"""
    return _PARAM_SHORT_TO_FULL.get(param, param)


@lru_cache(maxsize=256)
def _cached_detect_parameters(problem: str) -> tuple:
    """
    增强版参数检测算法（39矩阵）
    策略1: "太X"上下文检测 - 识别问题参数
    策略2: 双向关键词评分 - 统计正负面词汇
    策略3: Trade-off配对 - 常见矛盾组合

    Args:
        problem: 问题描述

    Returns:
        (improving_param, worsening_param, explanation) 元组
    """
    text = problem.strip()
    text_lower = text.lower()

    # ===== 策略1: "太X"/"X不好"上下文模式检测 =====
    # 识别"太X"、"X太"、"X不好"、"X差"等结构，确定问题参数
    # 当检测到"太X"时，X是用户想要改善的参数
    context_problem_params: dict[str, str] = {
        "重": "重量",
        "沉": "重量",
        "快": "速度",
        "慢": "速度",
        "贵": "成本",
        "热": "温度",
        "大": "功率",  # 功率大
        "强": "强度",
        "弱": "强度",
        "复杂": "复杂性",
        "耗电": "能耗",
        "费电": "能耗",
        "差": "产能/生产力",  # 效率差
        "不好": None,  # 需要特殊处理
        "兼容性不好": "兼容性/连通性",
        "稳定性差": "物体的稳定性",
        "寿命短": "移动物体的持久性",
        "效率低": "产能/生产力",
        "质量差": "强度",
        "不可靠": "可靠性",
        "不安全": "安全性",
    }

    # 从"太X"模式中识别问题参数
    problem_param_from_context: str | None = None

    # 检测"太+字"或"+字太"模式 - 但排除"成本高"这类
    for neg_word, param in context_problem_params.items():
        if neg_word == "高" or neg_word == "低":
            continue  # 跳过单独的高/低，避免误匹配
        if f"太{neg_word}" in text_lower or f"{neg_word}太" in text_lower:
            problem_param_from_context = param
            break

    # 特殊处理"X太高"/"X太低"模式 - 针对特定参数
    if not problem_param_from_context:
        if "温度太高" in text_lower or "温度太低" in text_lower:
            problem_param_from_context = "温度"
        elif "成本太高" in text_lower or "成本太低" in text_lower:
            problem_param_from_context = "成本"
        elif "重量太高" in text_lower or "重量太低" in text_lower:
            problem_param_from_context = "重量"
        elif "功率太高" in text_lower or "功率太低" in text_lower:
            problem_param_from_context = "功率"
        elif "速度太高" in text_lower or "速度太低" in text_lower:
            problem_param_from_context = "速度"
        elif "强度太高" in text_lower or "强度太低" in text_lower:
            problem_param_from_context = "强度"

    # 特殊处理"X不好"模式
    if not problem_param_from_context:
        for param in ENGINEERING_PARAMETERS_39:
            if f"{param}不好" in text_lower or f"{param}差" in text_lower or f"{param}低" in text_lower:
                problem_param_from_context = param
                break

    # ===== 策略2: 双向关键词评分 =====
    # 参数 → (正面词列表, 负面词列表, 权重)
    param_keywords: dict[str, tuple[list[str], list[str], float]] = {
        "速度": (["快", "高速", "加速", "快速", "提速", "高速度", "迅速度", "迅捷"], ["慢", "缓慢", "低速", "减速", "延迟", "耗时"], 1.2),
        "重量": (["轻", "轻量", "轻便", "轻巧", "减重", "轻盈"], ["重", "沉重", "笨重", "过重", "笨拙"], 1.3),
        "强度": (["强", "坚固", "牢固", "耐用", "高强度", "坚固", "结实"], ["弱", "脆弱", "易损", "不耐用", "强度低"], 1.1),
        "可靠性": (["可靠", "稳定", "信赖", "稳妥", "耐用", "持久"], ["故障", "失效", "损坏", "失灵", "不稳定", "易坏"], 1.2),
        "能耗": (["省电", "节能", "低功耗", "高效能", "省能", "节能型", "油耗低", "省油"], ["耗电", "费电", "高功耗", "能耗高", "耗能", "油耗高", "费油"], 1.3),
        "成本": (["便宜", "省钱", "经济", "廉价", "低成本", "实惠", "划算"], ["贵", "昂贵", "高成本", "费用高", "价高"], 1.2),
        "安全性": (["安全", "保险", "防护", "安心", "安保", "无危险"], ["危险", "不安全", "有风险", "隐患", "风险"], 1.2),
        "温度": (["冷却", "散热", "低温", "降温", "凉爽", "耐热"], ["热", "高温", "过热", "发烫", "升温", "炎热"], 1.0),
        "功率": (["大功率", "高功率", "强劲", "马力足", "动力强", "高性能"], ["功率低", "动力不足", "马力小"], 1.1),
        "精度": (["精确", "准确", "精密", "高精", "精准", "无误", "精密"], ["误差大", "不精确", "偏差大", "粗糙"], 1.1),
        "复杂性": (["简单", "简易", "简化", "简洁", "精简"], ["复杂", "繁琐", "繁杂", "结构复杂", "麻烦"], 1.1),
        "产能/生产力": (["高效", "高产", "高产能", "高效率", "增产", "提升效率"], ["低效", "低产", "效率低", "产能低", "慢"], 1.2),
        "自动化程度": (["自动", "自动化", "智能", "无人", "省力"], ["手动", "人工", "繁琐", "复杂"], 1.1),
        "制造的准度": (["精密", "精细", "光洁", "平滑", "高品质"], ["粗糙", "毛刺", "精度低", "误差大"], 1.0),
        "测量的准度": (["精确", "精准", "高灵敏度", "精确测量"], ["误差", "偏差", "不准", "粗糙"], 1.0),
        "修复性": (["易维修", "易修复", "易保养", "好维护", "易维护"], ["难维修", "难修复", "难保养", "维护困难"], 1.0),
        "适应性": (["适应", "灵活", "通用", "多变", "可调", "自适应"], ["僵硬", "死板", "单一", "固定"], 1.0),
        "使用的便利性": (["易用", "简便", "简单", "方便", "人性化", "直观"], ["难用", "复杂", "繁琐", "不方便"], 1.0),
        "设备的复杂性": (["简单", "简洁", "紧凑", "小型化"], ["复杂", "庞大", "庞大", "繁杂"], 1.0),
        "控制的复杂性": (["易控制", "简单控制", "直观"], ["难控制", "复杂控制", "难调节"], 1.0),
        "时间的浪费": (["省时", "快速", "高效", "节省时间"], ["耗时", "费时", "时间长", "缓慢"], 1.1),
        "物质的浪费": (["省材", "节约", "减少损耗", "节省材料"], ["浪费", "损耗", "消耗大", "材料消耗"], 1.0),
        "信息的流失": (["信息完整", "数据可靠", "保真"], ["丢失", "失真", "信息丢失", "损失"], 1.0),
        "有害的副作用": (["环保", "无害", "绿色", "清洁"], ["污染", "危害", "有害", "危险", "副作用"], 1.0),
        "亮度": (["亮", "明亮", "高亮度", "照亮", "清晰"], ["暗", "昏暗", "亮度低", "模糊"], 1.0),
        "形状": (["美观", "好看", "漂亮", "流线型", "合理形状"], ["丑陋", "变形", "畸形", "形状不合理"], 0.9),
        "移动物体的持久性": (["耐用", "持久", "寿命长", "经久耐用"], ["易损", "不耐用", "寿命短"], 1.0),
        "静止物体的持久性": (["耐久", "持久", "长寿", "稳定"], ["易老化", "退化", "不稳定"], 1.0),
        "张力/压力": (["抗压", "强度高", "耐压"], ["易变形", "不耐压", "压力下失效"], 1.0),
        "移动物体用的能源": (["新能源", "清洁能源", "省能"], ["污染", "高能耗", "化石能源"], 1.0),
        "非移动物体用的能源": (["节能", "低能耗", "高效"], ["高能耗", "浪费能源"], 1.0),
    }

    # 评分计算
    improving_scores: dict[str, float] = {}
    worsening_scores: dict[str, float] = {}

    for param, (pos_kws, neg_kws, weight) in param_keywords.items():
        # 正面得分
        pos_matches = sum(1 for kw in pos_kws if kw in text_lower)
        improving_scores[param] = pos_matches * weight

        # 负面得分
        neg_matches = sum(1 for kw in neg_kws if kw in text_lower)
        worsening_scores[param] = neg_matches * weight

    # 如果检测到"太X"上下文，将对应参数标记为问题参数（需要改善）
    if problem_param_from_context:
        # 如果问题参数不在高分列表中，给它一个基础分
        if problem_param_from_context not in improving_scores or improving_scores[problem_param_from_context] == 0:
            improving_scores[problem_param_from_context] = 0.5

    # ===== 策略3: Trade-off常见矛盾配对 =====
    # 当检测到特定参数时，优先考虑其对应的矛盾参数
    tradeoff_pairs = {
        "速度": "重量",  # 高速往往伴随重量增加
        "重量": "强度",  # 轻量化往往降低强度
        "精度": "复杂性",  # 高精度往往伴随结构复杂
        "能耗": "功率",  # 大功率往往高能耗
        "成本": "可靠性",  # 降低成本往往降低可靠性
        "安全性": "复杂性",  # 高安全性往往伴随复杂设计
        "自动化程度": "复杂性",  # 高自动化往往复杂
        "亮度": "能耗",  # 高亮度往往高能耗
    }

    # 检测到改善参数时，顺带提升其tradeoff参数的恶化可能性
    for param, (pos_kws, neg_kws, weight) in param_keywords.items():
        pos_matches = sum(1 for kw in pos_kws if kw in text_lower)
        if pos_matches > 0 and param in tradeoff_pairs:
            tradeoff_param = tradeoff_pairs[param]
            worsening_scores[tradeoff_param] = worsening_scores.get(tradeoff_param, 0) + 0.5

    # ===== 综合决策 =====
    # 优先使用上下文检测到的参数（仅当参数在39矩阵中时）
    if problem_param_from_context and problem_param_from_context in ENGINEERING_PARAMETERS_39:
        improving_param = problem_param_from_context
    else:
        # 从关键词评分选择
        if improving_scores:
            improving_param = max(improving_scores, key=improving_scores.get)
            # 如果最高分为0，使用默认
            if improving_scores[improving_param] == 0:
                improving_param = "速度"
        else:
            improving_param = "速度"

    if worsening_scores:
        worsening_param = max(worsening_scores, key=worsening_scores.get)
        if worsening_scores[worsening_param] == 0:
            worsening_param = "能耗" if improving_param != "能耗" else "成本"
    else:
        worsening_param = "能耗" if improving_param != "能耗" else "成本"

    # 避免相同参数或同类参数（当上下文检测到问题时）
    similar_params = {
        "重量": ["移动物体的重量", "静止物体的重量"],
        "速度": ["移动物体的重量"],  # 速度与重量有关联
        "温度": ["移动物体用的能源", "非移动物体用的能源"],
    }

    if improving_param == worsening_param or (
        problem_param_from_context and worsening_param in similar_params.get(improving_param, [])
    ):
        # 找第一个不同的参数
        candidates = [p for p in ENGINEERING_PARAMETERS_39 if p != improving_param and p not in similar_params.get(improving_param, [])]
        if candidates:
            worsening_param = candidates[0]
        else:
            worsening_param = "能耗" if improving_param != "能耗" else "设备的复杂性"

    return (_map_param_name(improving_param), _map_param_name(worsening_param), "本地算法自动检测")


@lru_cache(maxsize=256)
def _cached_detect_parameters_48(problem: str) -> tuple:
    """
    增强版参数检测算法（48矩阵）
    包含39矩阵所有参数 + 9个扩展参数

    Args:
        problem: 问题描述

    Returns:
        (improving_param, worsening_param, explanation) 元组
    """
    text = problem.strip()
    text_lower = text.lower()

    # 48矩阵新增的9个参数关键词
    param_keywords_48: dict[str, tuple[list[str], list[str], float]] = {
        "物质的数量": (["多", "量大", "批量", "数量多", "丰富"], ["少", "量少", "稀缺", "不足", "短缺"], 1.0),
        "信息的数量": (["信息多", "数据多", "丰富", "详尽", "全面"], ["信息少", "数据少", "稀缺", "缺失", "不完整"], 1.0),
        "移动物体的耐久性": (["耐用", "耐久", "寿命长", "经久", "持久"], ["不耐用", "易损", "寿命短", "老化快"], 1.1),
        "结构的稳定性": (["稳定", "稳固", "牢固", "结实", "抗震"], ["不稳定", "晃动", "松动", "易倒", "脆弱"], 1.2),
        "明亮度": (["亮", "明亮", "照亮", "清晰", "高亮度"], ["暗", "昏暗", "阴暗", "模糊", "不清晰"], 1.0),
        "运行效率": (["高效", "高效率", "省时", "快速", "性能高"], ["低效", "效率低", "缓慢", "性能低"], 1.2),
        "兼容性/连通性": (["兼容", "通用", "互联", "互通", "适配"], ["不兼容", "隔离", "孤立", "封闭"], 1.1),
        "安全性": (["安全", "保险", "防护", "安心", "无危险"], ["危险", "不安全", "有风险", "隐患", "事故"], 1.2),
        "美观": (["美观", "漂亮", "好看", "优雅", "精致"], ["丑陋", "难看", "粗糙", "廉价感"], 0.8),
    }

    # 先用39参数算法
    improving_param, worsening_param, _ = _cached_detect_parameters(problem)

    # 检查是否匹配48新增参数
    new_scores_improving: dict[str, float] = {}
    new_scores_worsening: dict[str, float] = {}

    for param, (pos_kws, neg_kws, weight) in param_keywords_48.items():
        pos_matches = sum(1 for kw in pos_kws if kw in text_lower)
        neg_matches = sum(1 for kw in neg_kws if kw in text_lower)
        new_scores_improving[param] = pos_matches * weight
        new_scores_worsening[param] = neg_matches * weight

    # 如果48新增参数得分更高，替换结果
    if new_scores_improving:
        best_new_improving = max(new_scores_improving.items(), key=lambda x: x[1])
        # 只有当得分 > 1时才替换（避免太低置信度）
        if best_new_improving[1] > 1 and best_new_improving[0] != improving_param:
            improving_param = best_new_improving[0]

    if new_scores_worsening:
        best_new_worsening = max(new_scores_worsening.items(), key=lambda x: x[1])
        if best_new_worsening[1] > 1 and best_new_worsening[0] != worsening_param:
            worsening_param = best_new_worsening[0]

    # 如果改善和恶化相同，尝试从48新增参数中找一个不同的
    if improving_param == worsening_param:
        candidates = [p for p in ENGINEERING_PARAMETERS_48 if p != improving_param]
        if candidates:
            worsening_param = candidates[0]
        else:
            worsening_param = "物质的数量" if improving_param != "物质的数量" else "兼容性/连通性"

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

    def detect_parameters(self, problem: str, matrix_type: str = "39") -> dict[str, Any]:
        """
        本地算法检测技术参数（支持39/48矩阵）

        Args:
            problem: 问题描述
            matrix_type: 矩阵类型，"39" 或 "48"

        Returns:
            包含改善和恶化参数的字典
        """
        if matrix_type == "48":
            improving, worsening, explanation = _cached_detect_parameters_48(problem)
        else:
            improving, worsening, explanation = _cached_detect_parameters(problem)
        logger.info(f"本地参数检测({matrix_type}矩阵): 改善={improving}, 恶化={worsening}")
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
            improving_param: 改善参数（可选，未提供则自动检测）
            worsening_param: 恶化参数（可选，未提供则自动检测）
            use_ai: 是否使用AI
            ai_request: AI请求参数（可选）

        Returns:
            分析会话
        """
        # 创建会话
        session = AnalysisSession(problem=problem, ai_enabled=use_ai)

        # 如果任一参数未提供，自动检测缺失的参数
        if not improving_param or not worsening_param:
            detected = self.local_engine.detect_parameters(problem)
            # 只填充未提供的参数，保留用户提供的
            improving_param = improving_param or detected["improving"]
            worsening_param = worsening_param or detected["worsening"]

        session.improving_param = improving_param
        session.worsening_param = worsening_param

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
            from ai.ai_client import get_ai_manager

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
        from ai.ai_client import get_ai_manager

        solutions: list[Solution] = []
        total = len(principle_ids)

        if total == 0:
            return solutions

        ai_manager = get_ai_manager()
        ai_client = ai_manager.get_client()

        # AI不可用时，直接使用本地引擎批量生成
        if not ai_client:
            logger.info("AI客户端不可用，使用本地引擎生成")
            solutions = self.local_engine.generate_solutions(
                principle_ids=principle_ids, problem=problem, count=total
            )
            return solutions

        # AI可用时，逐个原理生成
        failed_count = 0
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
                # AI生成失败，使用本地引擎作为后备
                failed_count += 1
                logger.debug(f"原理{principle_id}的AI生成失败，使用本地引擎")
                local_solutions = self.local_engine.generate_solutions(
                    principle_ids=[principle_id], problem=problem, count=1
                )
                if local_solutions:
                    solutions.append(local_solutions[0])

        if failed_count > 0:
            logger.warning(f"遍历生成完成: {failed_count}/{total}个使用本地引擎回退")

        return solutions


# 全局TRIZ引擎实例
triz_engine = TRIZEngine()


def get_triz_engine() -> TRIZEngine:
    """获取全局TRIZ引擎"""
    return triz_engine
