# TRIZ-APP 重构测试规划

## 一、问题汇总分析

### AI模块问题 (优先级: P0)
| 问题 | 文件 | 描述 | 影响 |
|------|------|------|------|
| SDK版本过宽 | requirements.txt | `openai>=1.0.0` 应锁定主版本 | 潜在版本不兼容 |
| API Base URL配置不一致 | settings.py | URL多了`/v1`后缀 | DeepSeek API调用失败 |
| 39参数混用列表和字典 | constants.py vs templates.py | constants用列表,templates用字典 | AI参数检测/生成可能不一致 |
| 循环导入风险 | connectivity.py | 在函数内部导入ai_client | 模块加载顺序问题 |

### 核心模块问题 (优先级: P1)
| 问题 | 文件 | 描述 | 影响 |
|------|------|------|------|
| N+1查询问题 | local_storage.py:583 | `export_all_sessions`一次加载10000条 | 性能瓶颈 |
| 矩阵复制开销 | triz_constants.py:1265 | 每次调用`get_contradiction_matrix()`复制1189条 | 内存浪费 |
| 无缓存单例 | principle_service.py:666-696 | 每次实例化重载658行数据 | 启动慢 |
| 未使用矩阵结果 | triz_engine.py:547-548 | 注释代码，未实现矩阵查询 | 功能缺失 |
| 矩阵匹配重复 | matrix_selector.py vs triz_constants.py | 两者都有find_solutions逻辑 | 代码重复 |

### UI模块问题 (优先级: P2)
| 问题 | 文件 | 描述 | 影响 |
|------|------|------|------|
| 624行遗留代码 | main_flow.py | 全文件624行未使用 | 维护负担 |
| history_list占位符 | history_list.py | 所有方法为空 | 功能缺失 |
| 重复卡片/对话框 | principles_list.py vs matrix_page.py | 相同实现多次 | 代码冗余 |
| 重复_get_category_color | 两处定义相同 | principles_list.py:220, matrix_page.py:1408 | 代码重复 |
| duplicate loading_indicator | matrix_page.py | 两处声明(行242,257) | 潜在bug |

---

## 二、重构顺序 (按依赖关系排序)

```
Phase 1: 依赖与配置修复 (P0)
  ├─ 1.1 锁定 openai SDK 版本
  ├─ 1.2 修复 API Base URL 配置
  └─ 1.3 统一39参数格式 (列表/字典二选一)

Phase 2: 核心性能优化 (P1)
  ├─ 2.1 triz_constants 缓存优化
  ├─ 2.2 principle_service 单例缓存
  ├─ 2.3 local_storage N+1 查询修复
  └─ 2.4 triz_engine 矩阵查询集成

Phase 3: 代码重复消除 (P2)
  ├─ 3.1 提取共享 _get_category_color
  ├─ 3.2 消除 matrix_selector 与 triz_constants 重复
  └─ 3.3 UI重复组件抽象

Phase 4: 清理占位符 (P2)
  ├─ 4.1 实现 history_list.py 或确认集成到matrix_tab
  └─ 4.2 删除 main_flow.py 遗留代码或确认是否使用
```

---

## 三、详细修改方案

### Phase 1.1: 锁定 openai SDK 版本

**问题**: requirements.txt 中 `openai>=1.0.0` 版本过宽

**修改文件**: `requirements.txt`, `pyproject.toml`

**当前**:
```
openai>=1.0.0
```

**修改为**:
```
openai>=1.12.0,<2.0.0
```

**验证方法**:
```bash
pip install openai>=1.12.0,<2.0.0
python -c "from openai import AsyncOpenAI; print(AsyncOpenAI.__version__)"
```

---

### Phase 1.2: 修复 API Base URL 配置

**问题**: settings.py 的 Base URL 格式与实际API不匹配

**修改文件**: `src/config/settings.py`

**分析**:
- constants.py: `DEEPSEEK_API_BASE = "https://api.deepseek.com"` (无v1后缀)
- settings.py: 若配置URL带`/v1`后缀则多余

**修改方案**:
在 `AppSettings.ai_base_url` setter 中 normalize URL:
```python
@ai_base_url.setter
def ai_base_url(self, value: str):
    # 移除多余的 /v1 后缀(如果存在)
    if value and value.endswith('/v1'):
        value = value[:-3]
    self.config.ai_base_url = value
```

**验证方法**:
```python
settings = AppSettings()
settings.ai_base_url = "https://api.deepseek.com/v1"  # 带v1
assert settings.ai_base_url == "https://api.deepseek.com"  # 应被normalize
```

---

### Phase 1.3: 统一39参数格式

**问题**: constants.py 用列表，templates.py 用字典

**修改文件**: 
- `src/config/constants.py`
- `src/ai/prompts/templates.py`
- `src/ai/ai_client.py`

**分析**:
- constants.py: `ENGINEERING_PARAMETERS_39` 是 List[str]
- templates.py: `ENGINEERING_PARAMETERS_39` 是 Dict[int, str] (键为1-39索引)

**修改方案**:
统一使用 `constants.py` 的列表格式，templates.py 引用 constants

**修改 templates.py**:
```python
# 删除本地的 ENGINEERING_PARAMETERS_39 字典
# 从 constants 导入
from src.config.constants import ENGINEERING_PARAMETERS_39

# 添加索引映射供内部使用
_ENGINEERING_PARAMS_WITH_INDEX = {
    i+1: param for i, param in enumerate(ENGINEERING_PARAMETERS_39)
}
```

**验证方法**:
```python
# 确保 AI 参数检测使用相同参数源
from src.config.constants import ENGINEERING_PARAMETERS_39
from src.ai.ai_client import AIClient

client = AIClient()
params = client._get_39_params()  # 新增方法
assert params == ENGINEERING_PARAMETERS_39
```

---

### Phase 2.1: triz_constants 缓存优化

**问题**: `get_contradiction_matrix()` 每次调用返回 `.copy()` 创建新字典

**修改文件**: `src/data/triz_constants.py`

**当前代码** (行1262-1266):
```python
def get_contradiction_matrix(self) -> Dict[Tuple[str, str], List[int]]:
    if self._matrix_data is None:
        self._matrix_data = MATRIX_39.copy()
    return self._matrix_data
```

**问题**: 调用者可能修改返回的字典，影响后续调用

**修改方案**:
1. 返回只读视图或深拷贝(保护内部状态)
2. 或文档说明返回引用，调用者不应修改

**推荐修改**:
```python
def get_contradiction_matrix(self) -> Dict[Tuple[str, str], List[int]]:
    if self._matrix_data is None:
        self._matrix_data = MATRIX_39.copy()
    # 返回深拷贝以防止意外修改
    return {k: v.copy() for k, v in self._matrix_data.items()}
```

**验证方法**:
```python
loader = TRIZDataLoader()
matrix1 = loader.get_contradiction_matrix()
matrix2 = loader.get_contradiction_matrix()
# 验证修改matrix1不影响matrix2
matrix1[('test','test')] = [999]
assert ('test','test') not in matrix2
```

---

### Phase 2.2: principle_service 单例缓存

**问题**: `PrincipleService.__init__` 每次实例化调用 `get_triz_data_loader()` 重载数据

**修改文件**: `src/core/principle_service.py`

**当前代码** (行664-698):
```python
class PrincipleService:
    def __init__(self):
        self._principles: Dict[int, InventivePrinciple] = {}
        self._load_principles()  # 每次都加载

    def _load_principles(self):
        triz_loader = get_triz_data_loader()  # 获取单例
        triz_principles = triz_loader.get_40_principles()
        # ... 遍历填充原理详情
```

**修改方案**: 已在使用全局单例 `_principle_service`，但检查 `__init__` 是否被多次调用

**验证方法**:
```python
# 验证全局单例只加载一次
from src.core.principle_service import get_principle_service

ps1 = get_principle_service()
ps2 = get_principle_service()
assert ps1 is ps2  # 同一实例

# 验证数据完整
assert len(ps1.get_all_principles()) == 40
```

---

### Phase 2.3: local_storage N+1 查询修复

**问题**: `export_all_sessions` 使用 `get_sessions(limit=10000)` 导致N+1查询

**修改文件**: `src/data/local_storage.py`

**当前代码** (行573-583):
```python
def export_all_sessions(self, format: str = "json") -> Optional[str]:
    sessions = self.get_sessions(limit=10000, offset=0)
    # get_sessions 内部逐个调用 get_session(session_id)
```

**修改方案**: 添加批量导出方法，直接用JOIN查询

```python
def export_all_sessions_optimized(self, format: str = "json") -> Optional[str]:
    """优化版导出，使用单一查询"""
    if not self.conn:
        return None
    
    cursor = self.conn.cursor()
    cursor.execute("""
        SELECT s.*, 
               GROUP_CONCAT(json_object(
                   'principle_id', sol.principle_id,
                   'principle_name', sol.principle_name,
                   'description', sol.description
               ), '|||') as solutions_json
        FROM analysis_sessions s
        LEFT JOIN solutions sol ON s.id = sol.session_id
        GROUP BY s.id
        LIMIT 10000
    """)
    # ... 处理结果
```

**验证方法**:
```python
# 性能测试
import time
storage = LocalStorage()
storage.initialize()

start = time.time()
result = storage.export_all_sessions()
elapsed = time.time() - start

assert result is not None
# 验证导出数据完整性
data = json.loads(result)
assert data['total_sessions'] > 0
```

---

### Phase 2.4: triz_engine 矩阵查询集成

**问题**: triz_engine.py 行547-548 有注释代码，未使用矩阵查询结果

**修改文件**: `src/core/triz_engine.py`

**当前代码** (行545-560):
```python
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
        solution_count=5
    )
```

**修改方案**:
```python
# 使用矩阵查询获取推荐的发明原理
from ..core.matrix_selector import get_matrix_manager
matrix_manager = get_matrix_manager()
matrix = matrix_manager.get_current_matrix()

# 查询矛盾矩阵获取推荐原理
matrix_result = matrix.query_matrix(
    improving=improving_param,
    worsening=worsening_param
)

# 生成解决方案
if use_ai and ai_request:
    request = ai_request
    # 合并矩阵推荐的原理和请求中的原理
    if matrix_result.principle_ids and not request.principle_ids:
        request.principle_ids = matrix_result.principle_ids
else:
    request = AIAnalysisRequest(
        problem=problem,
        improving_param=improving_param,
        worsening_param=worsening_param,
        principle_ids=matrix_result.principle_ids,  # 使用矩阵推荐原理
        solution_count=5
    )
```

**验证方法**:
```python
# 集成测试
from src.core.triz_engine import TRIZEngine

engine = TRIZEngine()
session = await engine.analyze_problem(
    problem="如何让汽车更快但更省油",
    improving_param="速度",
    worsening_param="能源的浪费"
)
# 验证session包含矩阵查询到的原理
assert session.solution_count > 0
```

---

### Phase 3.1: 提取共享 _get_category_color

**问题**: `_get_category_color` 在 principles_list.py:220 和 matrix_page.py:1408 两处定义相同

**修改文件**: 
- `src/ui/principles_tab/principles_list.py`
- `src/ui/matrix_tab/matrix_page.py`
- `src/ui/app_shell.py` (新增共享模块)

**修改方案**:
在 `src/ui/app_shell.py` 或新建 `src/ui/shared.py`:
```python
def get_category_color(category: str) -> str:
    """获取原理分类对应的颜色"""
    category_colors = {
        "物理": "#2196F3",   # 蓝色
        "化学": "#4CAF50",   # 绿色
        "几何": "#FF9800",   # 橙色
        "时间": "#9C27B0",   # 紫色
        "系统": "#00BCD4",   # 青色
        "其他": "#757575",   # 灰色
    }
    return category_colors.get(category, "#757575")
```

**验证方法**:
```python
from src.ui.shared import get_category_color

assert get_category_color("物理") == "#2196F3"
assert get_category_color("化学") == "#4CAF50"
assert get_category_color("未知") == "#757575"  # 默认值
```

---

### Phase 3.2: 消除 matrix_selector 与 triz_constants 重复

**问题**: 两者都有 `find_solutions` 逻辑

**修改文件**:
- `src/core/matrix_selector.py`
- `src/data/triz_constants.py`

**修改方案**:
`ContradictionMatrix` 直接委托给 `TRIZDataLoader`:
```python
class ContradictionMatrix:
    def __init__(self, matrix_type: str = "39"):
        self.matrix_type = matrix_type
        self._triz_loader = None
        self._init_matrix()

    def _init_matrix(self):
        if self.matrix_type == "39":
            self._triz_loader = get_triz_data_loader()
        # ... 其他初始化

    def find_solutions(self, improving: str, worsening: str) -> List[int]:
        # 直接委托给 loader
        if self._triz_loader:
            return self._triz_loader.get_principle_ids(improving, worsening)
        return [1, 10, 15, 19, 35]  # 默认
```

**验证方法**:
```python
from src.core.matrix_selector import get_matrix_manager

manager = get_matrix_manager()
matrix = manager.get_matrix("39")

# 验证结果一致性
result1 = matrix.find_solutions("速度", "能耗")
result2 = matrix._triz_loader.get_principle_ids("速度", "能耗")
assert result1 == result2
```

---

### Phase 3.3: 修复 duplicate loading_indicator

**问题**: matrix_page.py 行242和257两处声明 `self.loading_indicator`

**修改文件**: `src/ui/matrix_tab/matrix_page.py`

**当前代码**:
```python
# 行242
self.loading_indicator = ft.ProgressBar(visible=False, width=200)
# ...
# 行257  
self.loading_indicator = ft.ProgressBar(visible=False, width=200)
```

**修改方案**: 删除重复声明，保留一个引用

**验证方法**:
```python
# 确认只有一处初始化
tab = MatrixTab(page, storage)
assert tab.loading_indicator is not None
# 验证状态切换正常
tab.loading_indicator.visible = True
assert tab.loading_indicator.visible == True
```

---

### Phase 4.1: history_list.py 处理

**问题**: 所有方法为空，为占位符实现

**修改文件**: `src/ui/history_tab/history_list.py`

**决策**: 
1. 如果历史功能已在 matrix_tab 实现，确认 history_list.py 不会被import
2. 如果需要独立HistoryTab，实现基本功能
3. 如果确定不使用，删除整个 history_tab 模块

**验证方法**:
```python
# 确认无import错误
from src.ui.history_tab.history_list import HistoryTab

# 如果保留占位符，验证返回空列表
tab = HistoryTab(page, storage)
assert tab.get_sessions() == []
assert tab.delete_session("test") == False
```

---

### Phase 4.2: main_flow.py 遗留代码处理

**问题**: 624行代码未使用

**修改文件**: `src/ui/main_flow.py`

**决策**:
1. 搜索所有 import 确认 main_flow 是否被使用
2. 如果未使用，删除或移至 deprecated 目录
3. 如果被部分使用，清理未使用代码

**验证方法**:
```bash
grep -r "MainFlowUI\|main_flow" /home/chou/InnovateTRIZ/triz-app/src/ --include="*.py"
```

---

## 四、测试验证方法

### 4.1 单元测试
```bash
# 运行现有测试
cd /home/chou/InnovateTRIZ/triz-app
pytest tests/test_core.py -v

# 新增测试验证重构
pytest tests/test_matrix_query.py -v
pytest tests/test_ai_client.py -v
```

### 4.2 集成测试
```bash
# 端到端测试
pytest tests/test_integration.py -v
pytest tests/test_brainstorm_flow.py -v
```

### 4.3 性能测试
```python
# local_storage 导出性能
import time
storage = LocalStorage()
storage.initialize()

start = time.time()
result = storage.export_all_sessions()
elapsed = time.time() - start
print(f"导出耗时: {elapsed:.3f}s")
assert elapsed < 5.0  # 5秒内完成
```

### 4.4 功能验证检查清单
- [ ] AI连接测试通过 (deepseek/openrouter)
- [ ] 参数检测返回有效39参数
- [ ] 矩阵查询返回1-40原理编号
- [ ] 解决方案生成包含推荐原理
- [ ] UI正常显示，无duplicate widget警告

---

## 五、回归预防措施

### 5.1 测试驱动重构
```bash
# 每个模块重构前先运行测试
pytest tests/test_core.py -v --tb=short

# 重构后再次运行确保通过
pytest tests/ -v -x  # 遇到第一个失败则停止
```

### 5.2 Git分支策略
```bash
# 为每个Phase创建分支
git checkout -b refactor/phase1-dependencies
# 完成Phase1后合并
git checkout main
git merge refactor/phase1-dependencies
```

### 5.3 自动化检查
```bash
# 运行所有测试
pytest tests/ -v --tb=short

# 代码质量检查
ruff check src/ --select=E,W,F,I
black --check src/
mypy src/
```

---

## 六、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| SDK版本锁定导致兼容性问题 | 高 | 先在测试环境验证Python 3.10-3.12 |
| URL修改影响现有配置 | 中 | 添加配置迁移逻辑 |
| 矩阵查询逻辑修改 | 高 | 保留原有fallback逻辑 |
| UI组件重构 | 中 | 逐步重构，每步验证UI正常 |

---

## 七、执行时间估算

| Phase | 任务 | 估计时间 |
|-------|------|----------|
| 1.1 | SDK版本锁定 | 15分钟 |
| 1.2 | URL配置修复 | 30分钟 |
| 1.3 | 参数格式统一 | 1小时 |
| 2.1 | triz_constants缓存 | 30分钟 |
| 2.2 | principle_service缓存 | 20分钟 |
| 2.3 | local_storage优化 | 1小时 |
| 2.4 | triz_engine集成 | 1小时 |
| 3.1 | 共享color函数 | 30分钟 |
| 3.2 | 矩阵重复消除 | 1小时 |
| 3.3 | duplicate修复 | 15分钟 |
| 4.1 | history_list处理 | 30分钟 |
| 4.2 | main_flow处理 | 30分钟 |

**总计**: 约8小时 (可分阶段执行)

---

## 八、关键文件清单

需重点关注的文件 (按重构顺序):

1. `/home/chou/InnovateTRIZ/triz-app/requirements.txt` - SDK版本
2. `/home/chou/InnovateTRIZ/triz-app/src/config/settings.py` - URL配置
3. `/home/chou/InnovateTRIZ/triz-app/src/config/constants.py` - 参数定义
4. `/home/chou/InnovateTRIZ/triz-app/src/ai/prompts/templates.py` - 参数格式
5. `/home/chou/InnovateTRIZ/triz-app/src/data/triz_constants.py` - 数据加载
6. `/home/chou/InnovateTRIZ/triz-app/src/core/principle_service.py` - 单例缓存
7. `/home/chou/InnovateTRIZ/triz-app/src/data/local_storage.py` - N+1查询
8. `/home/chou/InnovateTRIZ/triz-app/src/core/triz_engine.py` - 矩阵集成
9. `/home/chou/InnovateTRIZ/triz-app/src/core/matrix_selector.py` - 重复消除
10. `/home/chou/InnovateTRIZ/triz-app/src/ui/app_shell.py` - 共享组件
11. `/home/chou/InnovateTRIZ/triz-app/src/ui/matrix_tab/matrix_page.py` - UI重复
12. `/home/chou/InnovateTRIZ/triz-app/src/ui/principles_tab/principles_list.py` - UI重复
