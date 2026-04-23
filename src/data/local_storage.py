"""
本地存储管理
使用SQLite数据库存储分析会话和解决方案
"""

import json
import logging
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .models import AnalysisSession, Solution

logger = logging.getLogger(__name__)


def _is_android() -> bool:
    """检测是否运行在Android环境"""
    if sys.platform == "android":
        return True
    if "ANDROID" in os.environ.get("ANDROID_ROOT", ""):
        return True
    if "ANDROID_DATA" in os.environ:
        return True
    if os.getenv("FLET_PLATFORM") == "android":
        return True
    return False


def _get_storage_dir() -> Path:
    """获取存储目录（Flet统一管理，所有平台使用FLET_APP_STORAGE_DATA）"""
    app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
    if app_data_path:
        storage_dir = Path(app_data_path)
    else:
        # 防御性fallback：使用临时目录（平台通用）
        import tempfile
        storage_dir = Path(tempfile.gettempdir()) / "triz-assistant" / "data"

    try:
        storage_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"无法创建存储目录 {storage_dir}: {e}")
    return storage_dir


class LocalStorage:
    """本地存储管理器"""

    def __init__(self, db_path: str | None = None):
        # 使用统一的存储路径
        if db_path is None:
            storage_dir = _get_storage_dir()
            db_path = str(storage_dir / "triz_sessions.db")
        self.db_path = db_path
        self.conn: sqlite3.Connection | None = None
        self.max_history_items = 100  # 最大历史记录数量

    def initialize(self) -> None:
        """初始化数据库"""
        try:
            # 确保数据库目录存在
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # 启用行工厂

            # 启用外键约束
            self.conn.execute("PRAGMA foreign_keys = ON")

            # Android上使用DELETE模式更稳定，桌面环境可用WAL
            if _is_android():
                self.conn.execute("PRAGMA journal_mode = DELETE")
                logger.info("使用DELETE日志模式(Android优化)")
            else:
                self.conn.execute("PRAGMA journal_mode = WAL")
                logger.info("使用WAL日志模式")

            self._create_tables()
            logger.info(f"数据库初始化完成: {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"数据库初始化失败: {e}")
            raise

    def _create_tables(self) -> None:
        """创建数据库表"""
        assert self.conn is not None, "数据库未初始化"
        cursor = self.conn.cursor()

        # 分析会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_sessions (
                id TEXT PRIMARY KEY,
                problem TEXT NOT NULL,
                matrix_type TEXT CHECK(matrix_type IN ('39', '48')),
                improving_param TEXT,
                worsening_param TEXT,
                ai_enabled BOOLEAN DEFAULT 0,
                solution_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 解决方案表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS solutions (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                principle_id INTEGER,
                principle_name TEXT,
                description TEXT,
                confidence REAL CHECK(confidence >= 0 AND confidence <= 1),
                is_ai_generated BOOLEAN DEFAULT 0,
                category TEXT,
                examples TEXT,  -- JSON数组
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                -- 4字段结构化输出（头脑风暴专用）
                technical_solution TEXT DEFAULT '',
                innovation_point TEXT DEFAULT '',
                cross_domain_cases TEXT DEFAULT '[]',  -- JSON数组
                expected_effect TEXT DEFAULT '',
                FOREIGN KEY (session_id) REFERENCES analysis_sessions(id) ON DELETE CASCADE
            )
        """)

        # 如果表已存在，尝试添加新列（兼容旧数据库）
        try:
            cursor.execute(
                "ALTER TABLE solutions ADD COLUMN technical_solution TEXT DEFAULT ''"
            )
            cursor.execute(
                "ALTER TABLE solutions ADD COLUMN innovation_point TEXT DEFAULT ''"
            )
            cursor.execute(
                "ALTER TABLE solutions ADD COLUMN cross_domain_cases TEXT DEFAULT '[]'"
            )
            cursor.execute(
                "ALTER TABLE solutions ADD COLUMN expected_effect TEXT DEFAULT ''"
            )
        except sqlite3.OperationalError:
            pass  # 列已存在

        # 应用配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_created ON analysis_sessions(created_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_solutions_session ON solutions(session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_solutions_principle ON solutions(principle_id)"
        )

        self.conn.commit()
        logger.info("数据库表创建完成")

    def save_session(self, session: AnalysisSession) -> bool:
        """
        保存分析会话

        Args:
            session: 分析会话

        Returns:
            是否保存成功
        """
        if not self.conn:
            logger.error("数据库未初始化")
            return False

        try:
            cursor = self.conn.cursor()

            # 使用显式事务确保原子性
            cursor.execute("BEGIN TRANSACTION")

            # 插入会话
            cursor.execute(
                """
                INSERT INTO analysis_sessions
                (id, problem, matrix_type, improving_param, worsening_param, ai_enabled, solution_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session.id,
                    session.problem,
                    session.matrix_type,
                    session.improving_param,
                    session.worsening_param,
                    1 if session.ai_enabled else 0,
                    len(session.solutions),
                    session.created_at.isoformat(),
                ),
            )

            # 插入解决方案
            for solution in session.solutions:
                cursor.execute(
                    """
                    INSERT INTO solutions
                    (id, session_id, principle_id, principle_name, description,
                     confidence, is_ai_generated, category, examples, created_at,
                     technical_solution, innovation_point, cross_domain_cases, expected_effect)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        solution.id,
                        session.id,
                        solution.principle_id,
                        solution.principle_name,
                        solution.description,
                        solution.confidence,
                        1 if solution.is_ai_generated else 0,
                        solution.category,
                        json.dumps(solution.examples, ensure_ascii=False),
                        solution.created_at.isoformat(),
                        # 4字段结构化输出
                        getattr(solution, "technical_solution", "") or "",
                        getattr(solution, "innovation_point", "") or "",
                        json.dumps(
                            getattr(solution, "cross_domain_cases", []) or [],
                            ensure_ascii=False,
                        ),
                        getattr(solution, "expected_effect", "") or "",
                    ),
                )

            cursor.execute("COMMIT")
            logger.info(
                f"会话保存成功: {session.id}, {len(session.solutions)}个解决方案"
            )
            return True

        except sqlite3.Error as e:
            logger.error(f"保存会话失败: {e}")
            try:
                cursor.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            return False

    def get_session(self, session_id: str) -> AnalysisSession | None:
        """
        获取分析会话

        Args:
            session_id: 会话ID

        Returns:
            分析会话，如果不存在则返回None
        """
        if not self.conn:
            return None

        try:
            cursor = self.conn.cursor()

            # 获取会话信息
            cursor.execute(
                "SELECT * FROM analysis_sessions WHERE id = ?", (session_id,)
            )
            session_row = cursor.fetchone()

            if not session_row:
                return None

            # 获取解决方案
            cursor.execute(
                "SELECT * FROM solutions WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            )
            solution_rows = cursor.fetchall()

            # 构建解决方案列表
            solutions = []
            for row in solution_rows:
                # 转换为字典以支持 .get() 方法
                row_dict = dict(row)
                examples = (
                    json.loads(row_dict["examples"]) if row_dict["examples"] else []
                )
                # 尝试获取4字段数据（新增字段，兼容旧数据）
                cross_domain_cases: list[Any] = []
                try:
                    cross_domain_cases = (
                        json.loads(row_dict.get("cross_domain_cases", "[]"))
                        if row_dict.get("cross_domain_cases")
                        else []
                    )
                except (json.JSONDecodeError, TypeError):
                    cross_domain_cases = []

                solution = Solution(
                    id=row_dict["id"],
                    principle_id=row_dict["principle_id"],
                    principle_name=row_dict["principle_name"],
                    description=row_dict["description"],
                    confidence=row_dict["confidence"],
                    is_ai_generated=bool(row_dict["is_ai_generated"]),
                    category=row_dict["category"],
                    examples=examples,
                    created_at=datetime.fromisoformat(row_dict["created_at"]),
                    # 4字段结构化输出（新增字段）
                    technical_solution=row_dict.get("technical_solution", "") or "",
                    innovation_point=row_dict.get("innovation_point", "") or "",
                    cross_domain_cases=cross_domain_cases,
                    expected_effect=row_dict.get("expected_effect", "") or "",
                )
                solutions.append(solution)

            # 转换为字典
            session_row_dict = dict(session_row)
            # 构建会话
            session = AnalysisSession(
                id=session_row_dict["id"],
                problem=session_row_dict["problem"],
                matrix_type=session_row_dict["matrix_type"],
                improving_param=session_row_dict["improving_param"],
                worsening_param=session_row_dict["worsening_param"],
                ai_enabled=bool(session_row_dict["ai_enabled"]),
                solution_count=session_row_dict["solution_count"],
                solutions=solutions,
                created_at=datetime.fromisoformat(session_row_dict["created_at"]),
            )

            return session

        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"获取会话失败: {e}")
            return None

    def find_session_by_problem(self, problem: str) -> str | None:
        """
        根据问题文本查找已存在的会话ID（精确匹配）

        Args:
            problem: 问题文本

        Returns:
            会话ID，如果不存在则返回None
        """
        if not self.conn:
            logger.error("find_session_by_problem: conn is None")
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id FROM analysis_sessions WHERE problem = ? ORDER BY created_at DESC LIMIT 1",
                (problem,),
            )
            row = cursor.fetchone()
            result = row["id"] if row else None
            logger.info(
                f"find_session_by_problem: problem={problem[:30]}..., result={result}"
            )
            return result
        except sqlite3.Error as e:
            logger.error(f"查找会话失败: {e}")
            return None

    def append_solutions(self, session_id: str, solutions: list) -> bool:
        """
        追加解决方案到已有会话

        Args:
            session_id: 会话ID
            solutions: 解决方案列表

        Returns:
            是否成功
        """
        if not self.conn or not solutions:
            return False

        try:
            cursor = self.conn.cursor()

            # 插入新解决方案
            for solution in solutions:
                # 生成新ID
                solution_id = str(uuid.uuid4())
                now = datetime.now().isoformat()

                # 序列化列表字段
                examples_json = json.dumps(solution.examples, ensure_ascii=False)
                cross_domain_cases_json = json.dumps(
                    (
                        solution.cross_domain_cases
                        if hasattr(solution, "cross_domain_cases")
                        else []
                    ),
                    ensure_ascii=False,
                )

                cursor.execute(
                    """
                    INSERT INTO solutions
                    (id, session_id, principle_id, principle_name, description,
                     confidence, is_ai_generated, category, examples,
                     technical_solution, innovation_point, cross_domain_cases,
                     expected_effect, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        solution_id,
                        session_id,
                        solution.principle_id,
                        solution.principle_name,
                        solution.description,
                        solution.confidence,
                        solution.is_ai_generated,
                        solution.category,
                        examples_json,
                        getattr(solution, "technical_solution", "") or "",
                        getattr(solution, "innovation_point", "") or "",
                        cross_domain_cases_json,
                        getattr(solution, "expected_effect", "") or "",
                        now,
                    ),
                )

            # 更新会话的解决方案数量
            cursor.execute(
                """
                UPDATE analysis_sessions
                SET solution_count = solution_count + ?
                WHERE id = ?
            """,
                (len(solutions), session_id),
            )

            self.conn.commit()
            logger.info(f"成功追加 {len(solutions)} 个解决方案到会话 {session_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"追加解决方案失败: {e}")
            self.conn.rollback()
            return False

    def get_sessions(self, limit: int = 50, offset: int = 0) -> list[AnalysisSession]:
        """
        获取分析会话列表（使用JOIN优化，避免N+1查询）

        Args:
            limit: 最大数量
            offset: 偏移量

        Returns:
            分析会话列表
        """
        sessions: list[AnalysisSession] = []

        if not self.conn:
            return sessions

        try:
            cursor = self.conn.cursor()

            # 使用JOIN一次性获取所有数据，避免N+1查询
            cursor.execute("""
                SELECT
                    s.id, s.problem, s.matrix_type, s.improving_param,
                    s.worsening_param, s.ai_enabled, s.solution_count, s.created_at,
                    sol.id as sol_id, sol.principle_id, sol.principle_name,
                    sol.description, sol.confidence, sol.is_ai_generated,
                    sol.category, sol.examples, sol.created_at as sol_created_at,
                    sol.technical_solution, sol.innovation_point,
                    sol.cross_domain_cases, sol.expected_effect
                FROM analysis_sessions s
                LEFT JOIN solutions sol ON s.id = sol.session_id
                ORDER BY s.created_at DESC
            """)

            # 按会话ID分组
            session_map: dict[str, AnalysisSession] = {}
            for row in cursor.fetchall():
                session_id = row["id"]

                if session_id not in session_map:
                    # 创建新会话
                    session_map[session_id] = AnalysisSession(
                        id=session_id,
                        problem=row["problem"],
                        matrix_type=row["matrix_type"],
                        improving_param=row["improving_param"],
                        worsening_param=row["worsening_param"],
                        ai_enabled=bool(row["ai_enabled"]),
                        solution_count=row["solution_count"],
                        solutions=[],
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )

                # 添加解决方案（如果有）
                if row["sol_id"]:
                    try:
                        examples = (
                            json.loads(row["examples"]) if row["examples"] else []
                        )
                        cross_domain_cases = (
                            json.loads(row["cross_domain_cases"])
                            if row["cross_domain_cases"]
                            else []
                        )
                    except (json.JSONDecodeError, TypeError):
                        examples = []
                        cross_domain_cases = []

                    # sqlite3.Row 不支持 .get()，需要转换为 dict
                    row_dict = dict(row)
                    solution = Solution(
                        id=row["sol_id"],
                        principle_id=row["principle_id"],
                        principle_name=row["principle_name"],
                        description=row["description"],
                        confidence=row["confidence"],
                        is_ai_generated=bool(row["is_ai_generated"]),
                        category=row["category"],
                        examples=examples,
                        created_at=datetime.fromisoformat(row["sol_created_at"]),
                        technical_solution=row_dict.get("technical_solution") or "",
                        innovation_point=row_dict.get("innovation_point") or "",
                        cross_domain_cases=cross_domain_cases,
                        expected_effect=row_dict.get("expected_effect") or "",
                    )
                    session_map[session_id].solutions.append(solution)

            # 应用分页
            sessions = list(session_map.values())[offset : offset + limit]
            logger.info(f"获取 {len(sessions)} 个会话")

        except sqlite3.Error as e:
            logger.error(f"获取会话列表失败: {e}")

        return sessions

    def get_session_summaries(
        self, limit: int = 20, offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        获取会话摘要列表（性能优化版本，支持分页）

        Args:
            limit: 最大数量，默认20
            offset: 偏移量，默认0

        Returns:
            会话摘要列表
        """
        summaries: list[dict[str, Any]] = []

        if not self.conn:
            return summaries

        try:
            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    problem,
                    matrix_type,
                    improving_param,
                    worsening_param,
                    ai_enabled,
                    solution_count,
                    created_at
                FROM analysis_sessions
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            )

            for row in cursor.fetchall():
                summary = {
                    "id": row["id"],
                    "problem_preview": row["problem"][:50]
                    + ("..." if len(row["problem"]) > 50 else ""),
                    "matrix_type": row["matrix_type"],
                    "improving_param": row["improving_param"],
                    "worsening_param": row["worsening_param"],
                    "ai_enabled": bool(row["ai_enabled"]),
                    "solution_count": row["solution_count"],
                    "created_at": datetime.fromisoformat(row["created_at"]).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                }
                summaries.append(summary)

        except sqlite3.Error as e:
            logger.error(f"获取会话摘要失败: {e}")

        return summaries

    def get_session_count(self) -> int:
        """
        获取会话总数

        Returns:
            会话总数
        """
        if not self.conn:
            return 0

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM analysis_sessions")
            row = cursor.fetchone()
            return row["count"] if row else 0
        except sqlite3.Error as e:
            logger.error(f"获取会话总数失败: {e}")
            return 0

    def delete_session(self, session_id: str) -> bool:
        """
        删除分析会话

        Args:
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        if not self.conn:
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM analysis_sessions WHERE id = ?", (session_id,))
            self.conn.commit()

            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"会话删除成功: {session_id}")
            else:
                logger.warning(f"会话不存在: {session_id}")

            return deleted

        except sqlite3.Error as e:
            logger.error(f"删除会话失败: {e}")
            self.conn.rollback()
            return False

    def delete_all_sessions(self) -> int:
        """
        删除所有会话

        Returns:
            删除的会话数量
        """
        if not self.conn:
            return 0

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM analysis_sessions")
            count = cursor.fetchone()["count"]

            cursor.execute("DELETE FROM solutions")
            cursor.execute("DELETE FROM analysis_sessions")
            self.conn.commit()

            logger.info(f"已删除所有 {count} 个会话")
            return int(count)

        except sqlite3.Error as e:
            logger.error(f"删除所有会话失败: {e}")
            self.conn.rollback()
            return 0

    def close(self) -> None:
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("数据库连接已关闭")

    def __del__(self) -> None:
        """析构函数，确保连接关闭"""
        self.close()


# 全局存储实例
_storage: LocalStorage | None = None


def get_storage() -> LocalStorage:
    """获取全局存储实例"""
    global _storage
    if _storage is None:
        _storage = LocalStorage()
        _storage.initialize()
    return _storage
