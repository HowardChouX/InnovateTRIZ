"""
AI客户端模块
支持DeepSeek API，兼容OpenRouter API
"""

import logging
from typing import Optional, List, Dict, Any, cast
from datetime import datetime

from openai import AsyncOpenAI, APIError, APITimeoutError, APIConnectionError

from ..data.models import AIAnalysisRequest, AIAnalysisResponse, Solution
from ..config.constants import (
    DEFAULT_AI_MODEL,
    DEEPSEEK_API_BASE,
    OPENROUTER_API_BASE,
    INVENTIVE_PRINCIPLES,
    PRINCIPLE_CATEGORIES,
    ENGINEERING_PARAMETERS_39,
)

logger = logging.getLogger(__name__)


def fuzzy_match_param(param: str, param_list: list) -> str:
    """将参数名模糊匹配到参数列表

    Args:
        param: 待匹配的参数名
        param_list: 参数列表

    Returns:
        匹配到的参数名，如果无匹配则返回原参数
    """
    param_lower = param.lower().strip()

    if not param_lower:
        return param

    # 精确匹配
    for p in param_list:
        if p.lower() == param_lower:
            return p

    # 包含匹配
    for p in param_list:
        if param_lower and (param_lower in p.lower() or p.lower() in param_lower):
            return p

    # 别名映射
    aliases = {
        "能量": "移动物体用的能源",
        "能源": "移动物体用的能源",
        "功率": "功率",
        "速度": "速度",
        "力": "力",
        "重量": "移动物体的重量",
        "体积": "移动物体的体积",
        "长度": "移动物体的长度",
        "面积": "移动物体的面积",
        "形状": "形状",
        "稳定性": "物体的稳定性",
        "强度": "强度",
        "温度": "温度",
        "亮度": "亮度",
        "可靠性": "可靠性",
        "复杂性": "设备的复杂性",
        "时间": "时间的浪费",
        "浪费": "能源的浪费",
    }
    for alias, full_name in aliases.items():
        if alias in param_lower and full_name in param_list:
            return full_name

    # 关键词匹配
    keywords_map = {
        "能量": ["能源", "能量消耗"],
        "功率": ["功率"],
        "速度": ["速度"],
        "重量": ["重量"],
        "体积": ["体积"],
        "长度": ["长度"],
        "面积": ["面积"],
        "形状": ["形状"],
        "稳定": ["稳定性"],
        "强度": ["强度"],
        "温度": ["温度"],
        "亮度": ["亮度"],
        "可靠": ["可靠性"],
        "复杂": ["复杂性"],
        "时间": ["时间"],
        "浪费": ["浪费"],
        "生产": ["产能"],
        "自动": ["自动化"],
        "控制": ["控制"],
        "适应": ["适应性"],
        "修复": ["修复性"],
        "便利": ["便利性"],
        "制造": ["制造性"],
    }
    for keyword, candidates in keywords_map.items():
        if keyword in param_lower:
            for candidate in candidates:
                for p in param_list:
                    if keyword in p.lower():
                        return p

    return param


class AIClient:
    """AI客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "deepseek",
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        初始化AI客户端

        Args:
            api_key: API密钥
            provider: AI提供商，"deepseek" 或 "openrouter"
            base_url: 自定义API地址
            model: 模型名称
        """
        self.api_key = api_key
        self.provider = provider
        self.enabled = bool(api_key)
        self.client = None
        self.model = model or DEFAULT_AI_MODEL
        self.base_url = base_url

        if self.enabled:
            self._init_client()

    def _init_client(self):
        """初始化OpenAI客户端"""
        try:
            if self.base_url:
                base_url = self.base_url
            else:
                base_url = (
                    DEEPSEEK_API_BASE
                    if self.provider == "deepseek"
                    else OPENROUTER_API_BASE
                )

            self.client = AsyncOpenAI(api_key=self.api_key, base_url=base_url)

            # 如果没有指定模型，根据提供商设置默认模型
            if not self.model or self.model == DEFAULT_AI_MODEL:
                if self.provider == "deepseek":
                    self.model = "deepseek-chat"
                elif self.provider == "openrouter":
                    self.model = "nvidia/nemotron-3-super-120b-a12b:free"
                else:
                    self.model = "deepseek/deepseek-chat"

            logger.info(
                f"AI客户端初始化成功，提供商: {self.provider}, 模型: {self.model}, URL: {base_url}"
            )

        except Exception as e:
            logger.error(f"AI客户端初始化失败: {e}")
            self.enabled = False
            self.client = None

    def is_available(self) -> bool:
        """检查AI是否可用"""
        return self.enabled and self.client is not None

    async def test_connection(self) -> bool:
        """测试API连接"""
        if not self.is_available():
            return False

        try:
            # 发送一个简单的测试请求
            client = cast(AsyncOpenAI, self.client)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
            )

            success = response.choices[0].message.content is not None
            logger.info(f"API连接测试: {'成功' if success else '失败'}")
            return success

        except Exception as e:
            logger.error(f"API连接测试失败: {e}")
            return False

    async def detect_parameters(self, problem: str) -> Dict[str, Any]:
        """
        使用AI检测技术参数

        Args:
            problem: 问题描述

        Returns:
            包含改善和恶化参数的字典
        """
        if not self.is_available():
            logger.warning("AI不可用，无法检测参数")
            return {"improving": "", "worsening": ""}

        # 使用constants中正确定义的39工程参数
        params_39 = ENGINEERING_PARAMETERS_39
        params_str = "\n".join([f"{i+1}. {p}" for i, p in enumerate(params_39)])

        prompt = f"""你是一个TRIZ专家。从以下39个工程参数中选择多个改善参数和多个恶化参数。

问题：{problem}

39个工程参数：
{params_str}

要求：
1. 改善参数：你希望改善/提高/增加的目标（可能多个）
2. 恶化参数：改善过程中可能带来的负面影响（可能多个）
3. 尽量选择最相关的2-3个参数

直接用JSON返回，只返回这一个JSON对象：
```json
{{
  "improving": ["参数1", "参数2"],
  "worsening": ["参数1", "参数2"],
  "explanation": "一句话解释矛盾"
}}
```"""

        system_prompt = """你是一个TRIZ专家。请严格按照JSON格式输出参数选择，不要包含任何其他文字。

JSON格式：
{"improving": ["参数1", "参数2"], "worsening": ["参数1", "参数2"], "explanation": "解释"}

重要：
- improving和worsening必须是数组格式
- 只输出JSON，不要输出其他文字
- 改善参数应该是"能量"、"功率"、"速度"、"强度"等正向参数
- 恶化参数应该是"重量"、"体积"、"长度"、"损失"等负向参数"""

        try:
            start_time = datetime.now()

            client = cast(AsyncOpenAI, self.client)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=300,
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            content = response.choices[0].message.content or ""
            logger.info(f"AI原始响应: {content}")

            # 尝试解析JSON
            import json

            try:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    result = json.loads(json_str)
                    logger.info(f"参数检测成功: {result}, 耗时: {processing_time:.2f}s")

                    # 验证并标准化返回格式
                    improving = result.get("improving", [])
                    worsening = result.get("worsening", [])

                    # 确保是列表格式
                    if isinstance(improving, str):
                        improving = [improving] if improving else []
                    if isinstance(worsening, str):
                        worsening = [worsening] if worsening else []

                    # 过滤掉不在39参数列表中的值
                    improving = [p for p in improving if p in params_39]
                    worsening = [p for p in worsening if p in params_39]

                    return {
                        "improving": improving,
                        "worsening": worsening,
                        "explanation": result.get("explanation", ""),
                    }
                else:
                    logger.warning(f"未找到JSON: {content}")

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}, 原始响应: {content}")

            # 如果JSON解析失败，使用备用提取
            improving = self._extract_multiple_from_response(
                content, "improving", params_39
            )
            worsening = self._extract_multiple_from_response(
                content, "worsening", params_39
            )

            if improving or worsening:
                logger.info(
                    f"备用提取成功: improving={improving}, worsening={worsening}"
                )
                return {
                    "improving": improving,
                    "worsening": worsening,
                    "explanation": "从AI响应中提取",
                }

            return {"improving": "", "worsening": "", "explanation": "AI未返回有效参数"}

        except APITimeoutError:
            logger.error("AI请求超时")
            return {"improving": "", "worsening": "", "error": "请求超时"}
        except APIConnectionError:
            logger.error("AI连接错误")
            return {"improving": "", "worsening": "", "error": "连接错误"}
        except APIError as e:
            logger.error(f"API错误: {e}")
            return {"improving": "", "worsening": "", "error": str(e)}
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return {"improving": "", "worsening": "", "error": str(e)}

    def _extract_from_response(
        self, content: str, param_type: str, param_list: list
    ) -> str:
        """从AI响应中提取参数"""
        content_lower = content.lower()

        # 找所有在内容中的参数（精确匹配）
        found_params = []
        for param in param_list:
            if param.lower() in content_lower:
                found_params.append(param)

        # 模糊匹配：AI可能返回近似参数名
        # 例如："能量消耗" -> "能量"，"运动物体用" -> "运动物体"
        if not found_params:
            # 从content中提取可能匹配的片段（取150字符窗口）
            for i, param in enumerate(param_list):
                param_lower = param.lower()
                idx = content_lower.find(param_lower)
                if idx != -1:
                    found_params.append(param)
                    continue

                # 尝试去后缀匹配
                suffixes = ["消耗", "用", "问题", "率", "性"]
                for suffix in suffixes:
                    if param_lower.endswith(suffix):
                        base = param_lower[: -len(suffix)]
                        if base in content_lower:
                            found_params.append(param)
                            logger.info(f"模糊匹配: '{param}' (base: '{base}')")
                            break

        logger.info(f"找到的参数: {found_params}")

        if not found_params:
            return ""

        unique_params = list(dict.fromkeys(found_params))  # 去重保持顺序

        # 如果只有一个参数，根据参数类型推断另一个
        if len(unique_params) == 1:
            single = unique_params[0]
            if "能量消耗" in single or "能量" in single:
                if param_type == "improving":
                    return single
                else:
                    for p in ["重量", "体积", "长度"]:
                        for param in param_list:
                            if p in param:
                                return param
            elif "重量" in single or "体积" in single:
                if param_type == "worsening":
                    return single
                else:
                    for p in ["能量消耗"]:
                        for param in param_list:
                            if p in param:
                                return param
            return single

        # 多个参数时，根据上下文匹配
        # 优先参数类型映射
        if param_type == "improving":
            # 改善参数优先选择：能量、功率、速度等正向参数
            priority_keywords = [
                "能量",
                "功率",
                "速度",
                "强度",
                "可靠性",
                "精度",
                "效率",
            ]
            for keyword in priority_keywords:
                for param in unique_params:
                    if keyword in param:
                        return param
            return unique_params[0]
        else:
            # 恶化参数优先选择：重量、体积、复杂性等负向参数
            priority_keywords = [
                "重量",
                "体积",
                "长度",
                "面积",
                "复杂性",
                "损失",
                "时间",
            ]
            for keyword in priority_keywords:
                for param in unique_params:
                    if keyword in param:
                        return param
            return unique_params[-1]

    def _extract_multiple_from_response(
        self, content: str, param_type: str, param_list: list
    ) -> List[str]:
        """从AI响应中提取多个参数"""
        content_lower = content.lower()

        # 定义参数类型映射
        improving_keywords = [
            "能量",
            "功率",
            "速度",
            "强度",
            "可靠性",
            "精度",
            "效率",
            "生产率",
            "面积",
            "稳定性",
        ]
        worsening_keywords = [
            "重量",
            "长度",
            "复杂性",
            "损失",
            "时间",
            "应力",
            "压力",
            "有害因素",
            "体积",
        ]

        # 找所有在内容中的参数
        param_positions = []  # (param, position, context)
        for param in param_list:
            param_lower = param.lower()
            start = 0
            while True:
                idx = content_lower.find(param_lower, start)
                if idx == -1:
                    break
                # 获取上下文（前后100字符）
                context_start = max(0, idx - 100)
                context_end = min(len(content), idx + 100)
                context = content_lower[context_start:context_end]
                param_positions.append((param, idx, context))
                start = idx + 1

        if not param_positions:
            return []

        # 分析上下文，判断参数属于改善还是恶化
        improving_candidates = []
        worsening_candidates = []

        for param, pos, context in param_positions:
            # 检查上下文中是否有改善/恶化的标记
            improving_markers = [
                "improve",
                "increase",
                "increase",
                "提高",
                "增加",
                "改善",
                "更多",
                "larger",
                "bigger",
                "more",
            ]
            worsening_markers = [
                "decrease",
                "reduce",
                "reduce",
                "降低",
                "减少",
                "恶化",
                "less",
                "smaller",
                "low",
                "keep",
                "avoid",
                "重量",
                "体积",
                "长度",
            ]

            is_improving = False
            is_worsening = False

            for marker in improving_markers:
                if marker in context:
                    is_improving = True
                    break

            for marker in worsening_markers:
                if marker in context:
                    is_worsening = True
                    break

            # 根据关键词本身判断
            for kw in improving_keywords:
                if kw in param and "损失" not in param:
                    is_improving = True
                    break

            for kw in worsening_keywords:
                if kw in param:
                    is_worsening = True
                    break

            if is_improving and param not in improving_candidates:
                improving_candidates.append(param)
            if is_worsening and param not in worsening_candidates:
                worsening_candidates.append(param)

        # 根据请求类型返回对应的参数
        if param_type == "improving":
            # 优先返回能量相关的正向参数
            result = []
            for kw in ["能量", "功率", "速度", "强度"]:
                for p in improving_candidates:
                    if kw in p and p not in result:
                        result.append(p)
            # 添加其他改善参数
            for p in improving_candidates:
                if p not in result:
                    result.append(p)
            return result[:3] if result else []
        else:
            # 恶化参数：选择负向参数，排除能量类
            result = []
            for kw in [
                "重量",
                "体积",
                "长度",
                "复杂性",
                "损失",
                "时间",
                "应力",
                "压力",
                "有害因素",
            ]:
                for p in worsening_candidates:
                    if kw in p and p not in result:
                        # 排除能量类参数，它们应该是改善参数
                        if "能量" not in p and "功率" not in p and "速度" not in p:
                            result.append(p)
            return result[:3] if result else []

    async def generate_solutions(
        self, request: AIAnalysisRequest
    ) -> AIAnalysisResponse:
        """
        生成AI解决方案

        Args:
            request: AI分析请求

        Returns:
            AI分析响应
        """
        if not self.is_available():
            return AIAnalysisResponse(
                success=False, solutions=[], error_message="AI服务不可用"
            )

        # 构建提示词
        prompt = self._build_solution_prompt(request)

        try:
            start_time = datetime.now()

            client = cast(AsyncOpenAI, self.client)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # 稍高的温度以获得创造性
                max_tokens=2000,
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            content = response.choices[0].message.content

            # 解析解决方案
            solutions = self._parse_solutions(
                content or "", request.principle_ids or []
            )

            logger.info(
                f"生成 {len(solutions)} 个解决方案，耗时: {processing_time:.2f}s"
            )

            return AIAnalysisResponse(
                success=True, solutions=solutions, processing_time=processing_time
            )

        except APITimeoutError:
            error_msg = "AI请求超时，请检查网络连接"
            logger.error(error_msg)
            return AIAnalysisResponse(
                success=False, solutions=[], error_message=error_msg, processing_time=0
            )
        except APIConnectionError:
            error_msg = "AI连接错误，请检查网络设置"
            logger.error(error_msg)
            return AIAnalysisResponse(
                success=False, solutions=[], error_message=error_msg, processing_time=0
            )
        except APIError as e:
            error_msg = f"AI服务错误: {str(e)}"
            logger.error(error_msg)
            return AIAnalysisResponse(
                success=False, solutions=[], error_message=error_msg, processing_time=0
            )
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.error(error_msg)
            return AIAnalysisResponse(
                success=False, solutions=[], error_message=error_msg, processing_time=0
            )

    async def generate_solution_for_principle(
        self,
        problem: str,
        improving_param: str,
        worsening_param: str,
        principle_id: int
    ) -> Optional[Solution]:
        """为单个原理生成解决方案"""
        if not self.is_available():
            logger.warning("AI服务不可用，无法生成解决方案")
            return None

        from .prompts.builder import PromptBuilder

        builder = PromptBuilder()
        prompt = builder.build_single_principle_solution_prompt(
            problem=problem,
            improving_param=improving_param,
            worsening_param=worsening_param,
            principle_id=principle_id
        )

        try:
            client = cast(AsyncOpenAI, self.client)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500,
            )

            content = response.choices[0].message.content or ""

            # 移除思考标签
            import re as regex_module
            content = regex_module.sub(r'<think>.*?</think>', '', content, flags=regex_module.DOTALL)

            # 解析解决方案
            solutions = self._parse_solutions(content, [principle_id])

            if solutions:
                return solutions[0]
            return None

        except Exception as e:
            logger.error(f"为原理{principle_id}生成解决方案失败: {e}")
            return None

    def _build_solution_prompt(self, request: AIAnalysisRequest) -> str:
        """构建解决方案提示词（集成丰富的TRIZ知识）"""
        from .prompts.builder import PromptBuilder

        builder = PromptBuilder()
        return builder.build_solution_prompt(
            problem=request.problem,
            improving_param=request.improving_param or "",
            worsening_param=request.worsening_param or "",
            principles=request.principle_ids or [],
            solution_count=request.solution_count,
        )

    def _parse_solutions(
        self, content: str, principle_ids: List[int]
    ) -> List[Solution]:
        """解析AI返回的解决方案"""
        solutions = []

        try:
            import json
            import re

            logger.info(f"AI原始响应长度: {len(content)}")
            logger.info(f"AI原始响应: {content[:1500]}")

            # 策略1: 尝试直接解析整个JSON数组
            json_start = content.find("[")
            json_end = content.rfind("]") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]

                # 清理常见问题
                json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)  # 尾随逗号
                json_str = re.sub(r"\s+", " ", json_str)  # 压缩空白

                try:
                    data = json.loads(json_str)
                    if isinstance(data, list):
                        logger.info(f"策略1成功: 直接解析{len(data)}个解决方案")
                        for item in data:
                            sol = self._parse_single_solution(item, principle_ids)
                            if sol:
                                solutions.append(sol)
                        if solutions:
                            return solutions
                except json.JSONDecodeError as e:
                    logger.warning(f"策略1失败: {e}, 尝试修复截断...")
                    # 检测是否在数组中间截断
                    truncated, fixed_json = self._try_fix_truncated_json(json_str)
                    if truncated and fixed_json:
                        try:
                            data = json.loads(fixed_json)
                            if isinstance(data, list):
                                logger.info(f"截断修复成功: 解析{len(data)}个解决方案")
                                for item in data:
                                    sol = self._parse_single_solution(
                                        item, principle_ids
                                    )
                                    if sol:
                                        solutions.append(sol)
                                if solutions:
                                    return solutions
                        except json.JSONDecodeError:
                            logger.warning("截断修复失败")

            # 策略2: 逐个提取JSON对象
            logger.info("尝试策略2: 逐个提取JSON对象")
            # 匹配 { ... } 模式
            pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
            matches = re.findall(pattern, content)

            for match in matches:
                try:
                    # 尝试解析单个对象
                    cleaned = re.sub(r",(\s*[}\]])", r"\1", match)
                    item = json.loads(cleaned)
                    if isinstance(item, dict) and "principle_id" in item:
                        sol = self._parse_single_solution(item, principle_ids)
                        if sol:
                            solutions.append(sol)
                except (json.JSONDecodeError, Exception):
                    continue

            if solutions:
                logger.info(f"策略2成功: 提取了{len(solutions)}个解决方案")
                return solutions

            # 策略3: 使用eval作为最后手段（仅处理简单情况）
            logger.warning("策略3: 使用保守的文本提取作为最后手段")
            solutions = self._fallback_parse(content, principle_ids)

            # 如果仍无解决方案，返回默认方案
            if not solutions:
                logger.warning("策略3未提取到解决方案，使用默认方案")
                solutions = self._create_default_solutions(principle_ids)

            logger.info(f"最终解析结果: {len(solutions)}个解决方案")
            return solutions

        except Exception as e:
            logger.error(f"解析解决方案时出错: {e}")
            return self._create_default_solutions(principle_ids)

    def _try_fix_truncated_json(self, json_str: str) -> tuple:
        """尝试修复被截断的JSON字符串

        Returns:
            (是否修复成功, 修复后的JSON字符串)
        """
        if json_str.startswith("[") and not json_str.strip().endswith("]"):
            last_obj_end = json_str.rfind("},")
            if last_obj_end > 0:
                fixed = json_str[: last_obj_end + 1] + "]"
                logger.info(f"JSON被截断，尝试修复为{len(fixed)}字符")
                return True, fixed
        return False, None

    def _parse_single_solution(
        self, item: dict, principle_ids: List[int]
    ) -> Optional[Solution]:
        """解析单个解决方案对象"""
        import json
        from ..config.constants import INVENTIVE_PRINCIPLES, PRINCIPLE_CATEGORIES

        try:
            principle_id = item.get("principle_id", 1)
            principle_name = item.get("principle_name", "")

            if not principle_name and principle_id in INVENTIVE_PRINCIPLES:
                principle_name = INVENTIVE_PRINCIPLES[principle_id]

            category = "物理"
            for cat, pids in PRINCIPLE_CATEGORIES.items():
                if principle_id in pids:
                    category = cat
                    break

            technical_solution = item.get("technical_solution", "")
            innovation_point = item.get("innovation_point", "")
            cross_domain_cases = item.get("cross_domain_cases", [])
            expected_effect = item.get("expected_effect", "")

            if not technical_solution:
                technical_solution = item.get("description", "")

            return Solution(
                principle_id=principle_id,
                principle_name=principle_name,
                description=technical_solution,
                confidence=min(max(item.get("confidence", 0.8), 0.0), 1.0),
                is_ai_generated=True,
                category=category,
                examples=cross_domain_cases or item.get("examples", []),
                technical_solution=technical_solution,
                innovation_point=innovation_point,
                cross_domain_cases=(
                    cross_domain_cases if isinstance(cross_domain_cases, list) else []
                ),
                expected_effect=expected_effect,
            )
        except Exception as e:
            logger.warning(f"解析单个解决方案失败: {e}")
            return None

    def _fallback_parse(self, content: str, principle_ids: List[int]) -> List[Solution]:
        """最后的备选解析方法 - 文本提取"""
        import re

        solutions = []
        from .prompts.templates import INVENTIVE_PRINCIPLES

        # 尝试提取原则编号和名称
        id_pattern = r'"principle_id"\s*:\s*(\d+)'
        name_pattern = r'"principle_name"\s*:\s*"([^"]+)"'
        tech_pattern = r'"technical_solution"\s*:\s*"([^"]{20,})"'

        ids = re.findall(id_pattern, content)
        names = re.findall(name_pattern, content)
        techs = re.findall(tech_pattern, content)

        for i, pid in enumerate(ids[:5]):
            pid_int = int(pid)
            name = (
                str(names[i])
                if i < len(names)
                else INVENTIVE_PRINCIPLES.get(pid_int, f"原理{pid_int}")
            )
            tech = techs[i] if i < len(techs) else ""

            if tech and len(tech) > 20:
                solutions.append(
                    Solution(
                        principle_id=pid_int,
                        principle_name=name,  # type: ignore
                        description=tech[:200],
                        technical_solution=tech[:200],
                        confidence=0.7,
                        is_ai_generated=True,
                        category="物理",
                    )
                )

        return solutions

    def _create_default_solutions(self, principle_ids: List[int]) -> List[Solution]:
        """创建默认解决方案（当AI解析失败时）"""
        solutions = []

        for pid in principle_ids[:5]:  # 最多5个
            if pid in INVENTIVE_PRINCIPLES:
                principle_name = INVENTIVE_PRINCIPLES[pid]

                # 确定分类
                category = "物理"
                for cat, pids in PRINCIPLE_CATEGORIES.items():
                    if pid in pids:
                        category = cat
                        break

                solution = Solution(
                    principle_id=pid,
                    principle_name=principle_name,
                    description=f"应用{principle_name}来解决技术问题",
                    confidence=0.7,
                    is_ai_generated=True,
                    category=category,
                    examples=[f"{principle_name}的典型应用案例"],
                )

                solutions.append(solution)

        return solutions


class AIManager:
    """AI管理器"""

    def __init__(self):
        self.client = None
        self.config = {"provider": "deepseek", "api_key": None, "enabled": False}
        self._is_connected = False  # 缓存实际连接状态

    def initialize(
        self,
        api_key: Optional[str] = None,
        provider: str = "deepseek",
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """初始化AI管理器"""
        if api_key:
            self.config["api_key"] = api_key
            self.config["provider"] = provider
            self.config["enabled"] = True

            self.client = AIClient(
                api_key=api_key, provider=provider, base_url=base_url, model=model
            )
            logger.info(f"AI管理器初始化，提供商: {provider}, 模型: {model}")
        else:
            self.config["enabled"] = False
            self.client = None
            logger.info("AI管理器初始化，AI功能禁用")

    def is_enabled(self) -> bool:
        """检查AI是否启用"""
        return (
            self.config["enabled"]
            and self.client is not None
            and self.client.is_available()
        )

    def is_connected(self) -> bool:
        """检查AI是否已连接"""
        return self._is_connected

    def set_connected(self, connected: bool):
        """设置连接状态"""
        self._is_connected = connected

    def get_client(self) -> Optional[AIClient]:
        """获取AI客户端"""
        return self.client if self.is_enabled() else None

    async def test_ai_connection(self) -> bool:
        """测试AI连接"""
        if not self.is_enabled():
            return False

        try:
            client = cast(AIClient, self.client)
            return await client.test_connection()
        except Exception as e:
            logger.error(f"测试AI连接失败: {e}")
            return False


# 全局AI管理器实例
ai_manager = AIManager()


def get_ai_manager() -> AIManager:
    """获取全局AI管理器"""
    return ai_manager

