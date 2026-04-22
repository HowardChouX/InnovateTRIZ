"""
AI客户端模块
支持DeepSeek API，兼容OpenRouter API
"""

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openai import AsyncOpenAI

try:
    from openai import (  # type: ignore[import-not-found]
        APIConnectionError,
        APIError,
        APITimeoutError,
        AsyncOpenAI,
    )
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    APIConnectionError = Exception
    APIError = Exception
    APITimeoutError = Exception
    AsyncOpenAI = None

from config.constants import (
    DEEPSEEK_API_BASE,
    DEFAULT_AI_MODEL,
    ENGINEERING_PARAMETERS_39,
    INVENTIVE_PRINCIPLES,
    OPENROUTER_API_BASE,
    PRINCIPLE_CATEGORIES,
)
from data.models import AIAnalysisRequest, AIAnalysisResponse, Solution

logger = logging.getLogger(__name__)


class AIClient:
    """AI客户端"""

    def __init__(
        self,
        api_key: str | None = None,
        provider: str = "deepseek",
        base_url: str | None = None,
        model: str | None = None,
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

    def _init_client(self) -> None:
        """初始化OpenAI客户端"""
        if not _OPENAI_AVAILABLE:
            logger.warning("openai 模块未安装，AI功能不可用")
            self.enabled = False
            self.client = None
            return

        # Type narrowing: AsyncOpenAI is not None when _OPENAI_AVAILABLE is True
        assert AsyncOpenAI is not None

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

        assert self.client is not None
        try:
            # 发送一个简单的测试请求
            response = await self.client.chat.completions.create(
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

    async def detect_parameters(self, problem: str) -> dict[str, Any]:
        """
        使用AI检测技术参数

        Args:
            problem: 问题描述

        Returns:
            包含改善和恶化参数的字典
        """
        if not self.is_available():
            logger.warning("AI不可用，降级到本地引擎")
            return self._local_detect_parameters(problem)

        assert self.client is not None
        # 使用constants中正确定义的39工程参数
        params_39 = ENGINEERING_PARAMETERS_39
        params_str = "\n".join([f"{i+1}. {p}" for i, p in enumerate(params_39)])

        system_prompt = f"""你是一个TRIZ专家。你的任务是从用户问题中识别出TRIZ改善参数和恶化参数。

【强制要求】
1. improving和worsening数组中的每一个参数必须完全匹配下面的39个参数之一，不多不少
2. 不要自己创造、缩写、修改任何参数名，只使用列表中存在的参数
3. 如果不确定某个参数是否匹配，请从列表中选择最接近的一个
4. 只输出JSON，不要输出任何其他文字

39个工程参数列表：
{params_str}

JSON格式（严格按照这个格式）：
{{"improving": ["参数1", "参数2"], "worsening": ["参数1"], "explanation": "解释"}}"""

        user_prompt = f"""问题：{problem}

请分析这个TRIZ问题，找出：
1. 改善参数：你希望改善、提高、增强的目标（选择1-2个）
2. 恶化参数：改善过程中可能带来的负面影响（选择1-2个）

注意：参数名必须从39个工程参数列表中精确选择，不要自己创造参数名！"""

        max_retries = 2
        for attempt in range(max_retries):
            try:
                start_time = datetime.now()

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0,
                    max_tokens=300,
                )

                processing_time = (datetime.now() - start_time).total_seconds()

                content = response.choices[0].message.content or ""
                logger.info(f"AI原始响应(尝试{attempt + 1}): {content}")

                # 解析JSON
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start < 0 or json_end <= json_start:
                    logger.warning(f"未找到JSON，尝试{attempt + 1}/{max_retries}")
                    continue

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

                # 严格验证：只保留在39参数列表中的参数
                improving = [p for p in improving if p in params_39]
                worsening = [p for p in worsening if p in params_39]

                # 如果参数为空，让AI重新思考
                if not improving and not worsening:
                    logger.warning(f"AI返回参数为空，尝试{attempt + 1}/{max_retries}")
                    continue

                return {
                    "improving": improving,
                    "worsening": worsening,
                    "explanation": result.get("explanation", ""),
                }

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}, 尝试{attempt + 1}/{max_retries}")
            except APITimeoutError:
                logger.error("AI请求超时")
                return self._local_detect_parameters(problem)
            except APIConnectionError:
                logger.error("AI连接错误")
                return self._local_detect_parameters(problem)
            except APIError as e:
                logger.error(f"API错误: {e}")
                return self._local_detect_parameters(problem)
            except Exception as e:
                logger.error(f"未知错误: {e}")
                return self._local_detect_parameters(problem)

        # 所有重试都失败，降级到本地引擎
        logger.warning("AI参数检测失败，降级到本地引擎")
        return self._local_detect_parameters(problem)

    def _local_detect_parameters(self, problem: str) -> dict[str, Any]:
        """本地引擎参数检测（降级方案）"""
        try:
            from ..core.triz_engine import get_triz_engine
            engine = get_triz_engine()
            result = engine.local_engine.detect_parameters(problem)
            logger.info(f"本地引擎参数检测结果: {result}")
            return result
        except Exception as e:
            logger.error(f"本地引擎参数检测失败: {e}")
            return {"improving": "", "worsening": "", "explanation": "参数检测失败"}

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

        assert self.client is not None
        # 构建提示词
        prompt = self._build_solution_prompt(request)

        try:
            start_time = datetime.now()

            response = await self.client.chat.completions.create(
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
        principle_id: int,
    ) -> Solution | None:
        """为单个原理生成解决方案"""
        if not self.is_available():
            logger.warning("AI服务不可用，无法生成解决方案")
            return None

        assert self.client is not None
        from .prompts.builder import PromptBuilder

        builder = PromptBuilder()
        prompt = builder.build_single_principle_solution_prompt(
            problem=problem,
            improving_param=improving_param,
            worsening_param=worsening_param,
            principle_id=principle_id,
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500,
            )

            content = response.choices[0].message.content or ""

            # 移除思考标签
            import re as regex_module

            content = regex_module.sub(
                r"<think>.*?</think>", "", content, flags=regex_module.DOTALL
            )

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
        self, content: str, principle_ids: list[int]
    ) -> list[Solution]:
        """解析AI返回的解决方案"""
        solutions = []

        try:
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
                            # 如果item是字符串，尝试再次解析
                            if isinstance(item, str):
                                try:
                                    item = json.loads(item)
                                except json.JSONDecodeError:
                                    continue
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
                                    # 如果item是字符串，尝试再次解析
                                    if isinstance(item, str):
                                        try:
                                            item = json.loads(item)
                                        except json.JSONDecodeError:
                                            continue
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
        self, item: dict, _principle_ids: list[int]
    ) -> Solution | None:
        """解析单个解决方案对象"""
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

    def _fallback_parse(
        self, content: str, _principle_ids: list[int]
    ) -> list[Solution]:
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

    def _create_default_solutions(self, principle_ids: list[int]) -> list[Solution]:
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

    def __init__(self) -> None:
        self.client: AIClient | None = None
        self.config: dict[str, Any] = {
            "provider": "deepseek",
            "api_key": None,
            "enabled": False,
        }
        self._is_connected = False  # 缓存实际连接状态

    def initialize(
        self,
        api_key: str | None = None,
        provider: str = "deepseek",
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
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
        return bool(
            self.config["enabled"]
            and self.client is not None
            and self.client.is_available()
        )

    def is_connected(self) -> bool:
        """检查AI是否已连接"""
        return self._is_connected

    def set_connected(self, connected: bool) -> None:
        """设置连接状态"""
        self._is_connected = connected

    def get_client(self) -> AIClient | None:
        """获取AI客户端"""
        return self.client if self.is_enabled() else None

    async def test_ai_connection(self) -> bool:
        """测试AI连接"""
        if not self.is_enabled():
            return False

        assert self.client is not None
        try:
            return await self.client.test_connection()
        except Exception as e:
            logger.error(f"测试AI连接失败: {e}")
            return False


# 全局AI管理器实例
ai_manager = AIManager()


def get_ai_manager() -> AIManager:
    """获取全局AI管理器"""
    return ai_manager
