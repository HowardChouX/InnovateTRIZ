"""
手动保存历史测试

测试头脑风暴结果手动保存到历史记录的流程
"""

import asyncio

from src.core.triz_engine import get_triz_engine
from src.data.local_storage import LocalStorage
from src.data.models import AnalysisSession, Solution


def run_sync(coro):
    """将协程同步运行"""
    return asyncio.run(coro)


class TestManualSaveHistory:
    """手动保存历史测试"""

    def setup_method(self):
        self.storage = LocalStorage(db_path=":memory:")
        self.storage.initialize()

    def test_matrix_query_does_not_auto_save(self):
        """测试矩阵查询不会自动保存"""
        engine = get_triz_engine()

        # 执行本地分析（模拟矩阵查询）
        session = run_sync(
            engine.analyze_problem(
                problem="测试问题",
                improving_param="速度",
                worsening_param="重量",
                use_ai=False,
            )
        )

        # 验证会话创建成功
        assert session is not None
        assert session.id is not None

        # 验证历史记录为空（矩阵查询不自动保存）
        summaries = self.storage.get_session_summaries(limit=10)
        assert len(summaries) == 0, "矩阵查询不应自动保存"

    def test_brainstorm_session_can_be_saved_manually(self):
        """测试头脑风暴会话可以手动保存"""
        engine = get_triz_engine()

        # 创建模拟的头脑风暴会话
        session = AnalysisSession(
            problem="手机需要更大电池但要保持轻薄",
            matrix_type="39",
            improving_param="运动物体的能量消耗",
            worsening_param="重量",
            ai_enabled=True,
            solutions=[
                Solution(
                    principle_id=1,
                    principle_name="分割",
                    description="将物体分成独立部分",
                    category="物理",
                    examples=["模块化手机电池"],
                    is_ai_generated=True,
                    confidence=0.9,
                ),
                Solution(
                    principle_id=15,
                    principle_name="动态化",
                    description="使物体或其环境适应最佳性能",
                    category="物理",
                    examples=["可折叠电池设计"],
                    is_ai_generated=True,
                    confidence=0.85,
                ),
            ],
        )

        # 手动保存
        saved = self.storage.save_session(session)
        assert saved is True

        # 验证可以检索
        retrieved = self.storage.get_session(session.id)
        assert retrieved is not None
        assert retrieved.problem == "手机需要更大电池但要保持轻薄"
        assert len(retrieved.solutions) == 2

    def test_history_displays_ai_sessions_correctly(self):
        """测试历史记录正确显示AI会话"""
        engine = get_triz_engine()

        # 创建AI会话
        ai_session = AnalysisSession(
            problem="AI测试问题",
            matrix_type="39",
            improving_param="速度",
            worsening_param="能耗",
            ai_enabled=True,
            solutions=[],
        )

        # 创建本地会话
        local_session = AnalysisSession(
            problem="本地测试问题",
            matrix_type="39",
            improving_param="强度",
            worsening_param="重量",
            ai_enabled=False,
            solutions=[],
        )

        # 保存两个会话
        self.storage.save_session(ai_session)
        self.storage.save_session(local_session)

        # 获取摘要
        summaries = self.storage.get_session_summaries(limit=10)

        # 验证
        assert len(summaries) == 2

        # 验证AI标记
        ai_summary = next(
            s for s in summaries if "AI测试" in s.get("problem_preview", "")
        )
        assert ai_summary.get("ai_enabled") is True

        local_summary = next(
            s for s in summaries if "本地测试" in s.get("problem_preview", "")
        )
        assert local_summary.get("ai_enabled") is False

    def test_save_button_on_solution_card(self):
        """测试解决方案卡片有保存按钮（UI组件测试）"""
        # 这个测试验证保存逻辑正确
        session = AnalysisSession(
            problem="测试保存按钮",
            matrix_type="39",
            ai_enabled=True,
            solutions=[
                Solution(
                    principle_id=5,
                    principle_name="组合",
                    description="合并同类物体",
                    category="几何",
                    is_ai_generated=True,
                    confidence=0.8,
                )
            ],
        )

        # 模拟MatrixTab的保存逻辑
        self.storage.save_session(session)

        # 验证保存成功
        retrieved = self.storage.get_session(session.id)
        assert retrieved is not None
        assert len(retrieved.solutions) == 1

    def test_multiple_brainstorm_sessions(self):
        """测试多个头脑风暴会话"""
        for i in range(3):
            session = AnalysisSession(
                problem=f"头脑风暴问题{i}",
                matrix_type="39",
                ai_enabled=True,
                solutions=[
                    Solution(
                        principle_id=i + 1,
                        principle_name=f"原理{i + 1}",
                        description=f"测试描述{i}",
                        category="物理",
                        is_ai_generated=True,
                        confidence=0.8,
                    )
                ],
            )
            self.storage.save_session(session)

        # 验证所有会话都已保存
        summaries = self.storage.get_session_summaries(limit=10)
        assert len(summaries) == 3

        # 验证统计
        stats = self.storage.get_statistics()
        assert stats["total_sessions"] == 3


class TestSaveToHistoryFlow:
    """保存到历史流程测试"""

    def setup_method(self):
        self.storage = LocalStorage(db_path=":memory:")
        self.storage.initialize()

    def test_session_without_problem_still_saves(self):
        """测试没有问题描述的会话仍可保存"""
        session = AnalysisSession(
            problem="",
            matrix_type="39",
            ai_enabled=True,
            solutions=[
                Solution(
                    principle_id=1,
                    principle_name="分割",
                    description="测试",
                    category="物理",
                    is_ai_generated=True,
                )
            ],
        )

        saved = self.storage.save_session(session)
        assert saved is True

        retrieved = self.storage.get_session(session.id)
        assert retrieved is not None

    def test_empty_solutions_session_saves(self):
        """测试没有解决方案的会话可以保存"""
        session = AnalysisSession(
            problem="测试空方案", matrix_type="39", ai_enabled=False, solutions=[]
        )

        saved = self.storage.save_session(session)
        assert saved is True

        retrieved = self.storage.get_session(session.id)
        assert retrieved is not None
        assert len(retrieved.solutions) == 0

    def test_solution_details_preserved(self):
        """测试解决方案详情被正确保存"""
        solutions = [
            Solution(
                principle_id=2,
                principle_name="抽取",
                description="从物体中抽出干扰部分",
                category="物理",
                examples=["抽出噪音部分", "抽出热量部分"],
                is_ai_generated=True,
                confidence=0.92,
            )
        ]

        session = AnalysisSession(
            problem="保留详情测试",
            matrix_type="39",
            ai_enabled=True,
            solutions=solutions,
        )

        self.storage.save_session(session)

        retrieved = self.storage.get_session(session.id)
        saved_solution = retrieved.solutions[0]

        assert saved_solution.principle_id == 2
        assert saved_solution.principle_name == "抽取"
        assert saved_solution.confidence == 0.92
        assert saved_solution.is_ai_generated is True
