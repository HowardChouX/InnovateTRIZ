# TRIZ Android应用 - API文档

## 概述

本文档描述TRIZ Android应用中各模块的API接口。

---

## 1. AI模块 (`src/ai/ai_client.py`)

### AIClient 类

#### 构造函数
```python
AIClient(api_key: Optional[str] = None, provider: str = "deepseek")
```

#### 主要方法

##### `is_available() -> bool`
检查AI客户端是否可用。

##### `async test_connection() -> bool`
测试API连接是否正常。

##### `async detect_parameters(problem: str) -> Dict[str, str]`
使用AI检测技术参数。

**参数**:
- `problem`: 问题描述

**返回**:
```python
{
    "improving": "改善参数名称",
    "worsening": "恶化参数名称",
    "explanation": "矛盾解释"
}
```

##### `async generate_solutions(request: AIAnalysisRequest) -> AIAnalysisResponse`
生成AI解决方案。

**参数**:
- `request`: AI分析请求

**返回**:
```python
AIAnalysisResponse(
    success: bool,
    solutions: List[Solution],
    error_message: Optional[str],
    processing_time: Optional[float]
)
```

---

## 2. 矛盾矩阵模块 (`src/core/matrix_selector.py`)

### ContradictionMatrix 类

#### 构造函数
```python
ContradictionMatrix(matrix_type: str = "39")
```

#### 主要方法

##### `get_improving_params() -> List[str]`
获取所有可改善参数列表。

##### `get_worsening_params() -> List[str]`
获取所有可能恶化参数列表。

##### `find_solutions(improving: str, worsening: str) -> List[int]`
查找对应的发明原理编号。

**参数**:
- `improving`: 改善参数名称
- `worsening`: 恶化参数名称

**返回**: 发明原理编号列表

##### `query_matrix(improving: Optional[str], worsening: Optional[str]) -> MatrixQueryResult`
查询矛盾矩阵。

##### `suggest_worsening_params(improving: str) -> List[str]`
根据改善参数建议可能的恶化参数。

### MatrixManager 类

全局矩阵管理器。

```python
matrix_manager = MatrixManager()
matrix = matrix_manager.get_matrix("39")
```

---

## 3. TRIZ引擎模块 (`src/core/triz_engine.py`)

### LocalTRIZEngine 类

本地TRIZ引擎（无需网络）。

#### 主要方法

##### `detect_parameters(problem: str) -> Dict[str, str]`
本地算法检测技术参数。

##### `generate_solutions(principle_ids: List[int], problem: str, count: int) -> List[Solution]`
本地生成解决方案。

##### `categorize_solutions(solutions: List[Solution]) -> Dict[str, List[Solution]]`
按原理分类解决方案。

### TRIZEngine 类

统一TRIZ引擎（整合本地和AI）。

```python
triz_engine = TRIZEngine()
session = triz_engine.analyze_problem(
    problem="手机需要更大电池但要保持轻薄",
    improving_param=None,  # 自动检测
    worsening_param=None,  # 自动检测
    use_ai=True,
    ai_request=None
)
```

---

## 4. 数据模型 (`src/data/models.py`)

### Solution 数据类

```python
@dataclass
class Solution:
    id: str                          # 唯一标识
    principle_id: int               # 原理编号（1-40）
    principle_name: str             # 原理名称
    description: str                # 方案描述
    confidence: float               # 置信度（0-1）
    is_ai_generated: bool          # 是否AI生成
    category: str                   # 分类（物理/化学等）
    examples: List[str]             # 应用示例
    created_at: datetime           # 创建时间
```

### AnalysisSession 数据类

```python
@dataclass
class AnalysisSession:
    id: str                         # 唯一标识
    problem: str                    # 问题描述
    matrix_type: str                # 矩阵类型（39/48）
    improving_param: Optional[str]  # 改善参数
    worsening_param: Optional[str]  # 恶化参数
    ai_enabled: bool                # AI是否启用
    solution_count: int            # 解决方案数量
    solutions: List[Solution]       # 解决方案列表
    created_at: datetime            # 创建时间
```

### AIAnalysisRequest 数据类

```python
@dataclass
class AIAnalysisRequest:
    problem: str                     # 问题描述
    improving_param: Optional[str]   # 改善参数
    worsening_param: Optional[str]   # 恶化参数
    principle_ids: Optional[List[int]]  # 原理编号列表
    solution_count: int              # 解决方案数量
    language: str                   # 语言（zh/en）
```

---

## 5. 本地存储模块 (`src/data/local_storage.py`)

### LocalStorage 类

#### 构造函数
```python
LocalStorage(db_path: str = "triz_sessions.db")
```

#### 主要方法

##### `initialize()`
初始化数据库连接。

##### `save_session(session: AnalysisSession) -> bool`
保存分析会话。

##### `get_session(session_id: str) -> Optional[AnalysisSession]`
获取指定会话。

##### `get_sessions(limit: int = 50, offset: int = 0) -> List[AnalysisSession]`
获取会话列表。

##### `get_session_summaries(limit: int = 50) -> List[Dict[str, Any]]`
获取会话摘要列表（性能优化）。

##### `delete_session(session_id: str) -> bool`
删除指定会话。

##### `export_session(session_id: str, format: str = "json") -> Optional[str]`
导出会话数据。

##### `get_statistics() -> Dict[str, Any]`
获取存储统计信息。

---

## 6. 配置管理模块 (`src/config/settings.py`)

### AppSettings 类

#### 主要属性

```python
settings = AppSettings()

# AI配置
settings.ai_api_key       # API密钥
settings.ai_provider     # 提供商（deepseek/openrouter）
settings.is_ai_configured()  # 是否已配置

# 应用配置
settings.language         # 界面语言（zh/en）
settings.theme            # 主题模式（light/dark/auto）
settings.default_solution_count  # 默认解决方案数量
settings.enable_history   # 启用历史记录
```

#### 主要方法

##### `async load()`
加载设置。

##### `async save()`
保存设置。

##### `get(key: str, default=None) -> Any`
获取设置值。

##### `set(key: str, value: Any)`
设置值。

##### `update(updates: Dict[str, Any])`
批量更新设置。

---

## 7. 常量定义 (`src/config/constants.py`)

### 主要常量

```python
# 39个工程参数
ENGINEERING_PARAMETERS_39 = [
    "运动物体的重量", "静止物体的重量", "运动物体的长度",
    # ... 共39个
]

# 40个发明原理
INVENTIVE_PRINCIPLES = {
    1: "分割原理",
    2: "抽取原理",
    # ... 共40个
}

# 原理分类
PRINCIPLE_CATEGORIES = {
    "物理": [1, 2, 3, ...],
    "化学": [35, 36, 38, 39, 40],
    # ...
}
```

### 矩阵类型

```python
MATRIX_39 = "39"  # 39矛盾矩阵
MATRIX_48 = "48"  # 48矛盾矩阵（规划中）
```

---

## 8. 应用入口 (`main.py`)

### TRIZApp 类

```python
class TRIZApp:
    async def main(self, page: ft.Page):
        """主函数"""
        # 初始化页面
        # 初始化组件
        # 显示主界面
```

### 运行方式

```bash
# 桌面模式
python main.py

# Web模式（测试用）
python main.py --web

# 指定端口
python main.py --port 8080
```

---

## 使用示例

### 基本分析流程

```python
import flet as ft
from src.data.local_storage import LocalStorage
from src.core.triz_engine import get_triz_engine
from src.ai.ai_client import get_ai_manager
from src.config.settings import AppSettings

async def main(page: ft.Page):
    # 初始化组件
    storage = LocalStorage()
    storage.initialize()

    settings = AppSettings()
    await settings.load()

    ai_manager = get_ai_manager()
    if settings.ai_api_key:
        ai_manager.initialize(api_key=settings.ai_api_key)

    triz_engine = get_triz_engine()

    # 执行分析
    session = triz_engine.analyze_problem(
        problem="手机需要更大电池但要保持轻薄设计",
        improving_param="移动物体用的能源",  # 可选
        worsening_param="运动物体的体积",       # 可选
        use_ai=ai_manager.is_enabled()
    )

    # 保存会话
    storage.save_session(session)

    # 显示结果
    print(f"生成 {len(session.solutions)} 个解决方案")

ft.app(target=main)
```

---

## 错误处理

所有API方法都会记录日志并返回适当的错误信息。

```python
try:
    solutions = await ai_client.generate_solutions(request)
except Exception as e:
    logger.error(f"生成解决方案失败: {e}")
    # 返回默认解决方案或错误信息
```
