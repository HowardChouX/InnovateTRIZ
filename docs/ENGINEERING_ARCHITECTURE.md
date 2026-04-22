# TRIZ Android应用 - 工程架构设计

## 📋 需求分析总结

### 核心功能模块
1. **基础TRIZ分析**（本地，离线可用）
2. **AI智能增强**（可选，需要网络）
3. **矛盾矩阵选择器**（39矩阵 + 48矩阵规划）
4. **参数选择界面**（改善/恶化参数可视化选择）
5. **解决方案生成器**（基于40发明原理分类）
6. **本地记录系统**（完整流程记录）

### 用户交互流程
```
1. 问题输入 → 2. AI开关选择 → 3. 矩阵类型选择 → 
4. 参数选择（改善/恶化） → 5. 解决方案数量设置 → 
6. 分析执行 → 7. 解决方案展示（按原理分类） → 
8. 本地保存记录
```

## 🏗️ 系统架构设计

### 分层架构
```
┌─────────────────────────────────────────┐
│            Presentation Layer           │
│         (Flet UI Components)           │
├─────────────────────────────────────────┤
│            Business Logic Layer         │
│    (TRIZ Engine + AI Integration)      │
├─────────────────────────────────────────┤
│            Data Access Layer            │
│   (Local Storage + Configuration)      │
└─────────────────────────────────────────┘
```

### 模块划分
```
src/
├── core/                    # 核心业务逻辑
│   ├── triz_engine.py      # TRIZ引擎（本地分析）
│   ├── matrix_selector.py  # 矛盾矩阵选择器
│   ├── parameter_picker.py # 参数选择器
│   └── solution_generator.py # 解决方案生成器
├── ai/                     # AI集成模块
│   ├── ai_client.py        # AI客户端（DeepSeek）
│   ├── ai_enhancer.py      # AI增强逻辑
│   └── prompt_engineer.py  # 提示词工程
├── ui/                     # 界面组件
│   ├── main_flow.py        # 主流程界面
│   ├── matrix_ui.py        # 矛盾矩阵UI
│   ├── parameter_ui.py     # 参数选择UI
│   └── solution_ui.py      # 解决方案UI
├── data/                   # 数据管理
│   ├── local_storage.py    # 本地存储
│   ├── session_manager.py  # 会话管理
│   └── models.py           # 数据模型
└── config/                 # 配置管理
    ├── settings.py         # 应用设置
    └── constants.py        # 常量定义
```

## 🔧 详细设计

### 1. 矛盾矩阵系统

#### 数据结构
```python
class ContradictionMatrix:
    """矛盾矩阵基类"""
    def __init__(self, matrix_type: str = "39"):
        self.matrix_type = matrix_type  # "39" 或 "48"
        self.parameters = []  # 参数列表
        self.matrix = {}      # 矩阵数据
        
    def get_improving_params(self) -> List[str]:
        """获取所有可改善参数"""
        
    def get_worsening_params(self) -> List[str]:
        """获取所有可能恶化参数"""
        
    def find_solutions(self, improving: str, worsening: str) -> List[int]:
        """查找对应的发明原理编号"""
```

#### 矩阵实现
- **39矛盾矩阵**: 完整实现，包含39个工程参数
- **48矛盾矩阵**: 预留接口，UI可切换但功能暂不实现

### 2. 参数选择系统

#### 交互设计
```
参数选择流程：
1. 点击"选择改善参数"按钮
2. 弹出全屏参数选择界面
3. 显示所有可改善参数（滚动列表）
4. 用户选择1个参数（单选）
5. 返回主界面，显示已选参数
6. 同样流程选择恶化参数
```

#### UI组件
```python
class ParameterPicker:
    """参数选择器组件"""
    
    def show_improving_picker(self):
        """显示改善参数选择器"""
        # 全屏模态对话框
        # 搜索框 + 参数分类 + 滚动列表
        
    def show_worsening_picker(self):
        """显示恶化参数选择器"""
        # 基于已选的改善参数，智能推荐相关恶化参数
```

### 3. AI集成系统

#### 架构设计
```
AI系统工作流程：
1. 检查AI开关状态（默认关闭）
2. 如果开启：使用DeepSeek API分析
3. 如果关闭：使用本地TRIZ算法
4. 混合模式：本地分析 + AI优化建议
```

#### AI客户端
```python
class AIClient:
    """AI客户端（DeepSeek）"""
    
    def __init__(self, api_key: str = None):
        self.enabled = bool(api_key)
        self.client = OpenAI() if api_key else None
        
    async def enhance_analysis(self, 
                              problem: str,
                              improving: str = None,
                              worsening: str = None) -> Dict:
        """AI增强分析"""
        
    async def generate_solutions(self,
                                principles: List[int],
                                problem: str,
                                count: int = 5) -> List[Solution]:
        """基于发明原理生成AI解决方案"""
```

### 4. 解决方案系统

#### 生成流程
```
解决方案生成：
1. 矛盾矩阵查询 → 得到发明原理编号列表
2. 用户设置解决方案数量（0-∞）
3. 如果数量>0：
   - AI开启：调用AI生成详细方案
   - AI关闭：使用本地模板生成方案
4. 按40发明原理分类展示
```

#### 数据结构
```python
@dataclass
class Solution:
    """解决方案"""
    id: str
    principle_id: int          # 发明原理编号（1-40）
    principle_name: str        # 原理名称
    description: str           # 方案描述
    confidence: float          # 置信度（0-1）
    is_ai_generated: bool      # 是否AI生成
    category: str              # 分类（物理/化学等）
    examples: List[str]        # 应用示例
    created_at: datetime
    
@dataclass
class AnalysisSession:
    """分析会话记录"""
    id: str
    problem: str               # 问题描述
    matrix_type: str           # 矩阵类型（39/48）
    improving_param: Optional[str]  # 改善参数
    worsening_param: Optional[str]  # 恶化参数
    ai_enabled: bool           # AI是否启用
    solution_count: int        # 解决方案数量
    solutions: List[Solution]  # 生成的解决方案
    created_at: datetime
```

### 5. 本地记录系统

#### 存储设计
```python
class LocalStorage:
    """本地存储管理器"""
    
    def __init__(self):
        self.db_path = "triz_sessions.db"
        self.init_database()
        
    def save_session(self, session: AnalysisSession):
        """保存分析会话"""
        
    def get_sessions(self, limit: int = 50) -> List[AnalysisSession]:
        """获取历史会话"""
        
    def export_session(self, session_id: str, format: str = "json"):
        """导出会话数据"""
        
    def clear_old_sessions(self, days: int = 30):
        """清理旧会话"""
```

## 🎨 UI/UX设计

### 主界面布局
```
┌─────────────────────────────────────┐
│ 🚀 TRIZ创新助手                    │
│ [AI增强: ○ 关闭 ● 开启]           │
├─────────────────────────────────────┤
│ 1. 问题描述：___________________   │
│    [📝 输入您的问题...]           │
│                                    │
│ 2. 矛盾矩阵：[○ 39矩阵 ● 48矩阵]  │
│                                    │
│ 3. 参数选择：                     │
│    改善参数：[选择参数] → [ ]     │
│    恶化参数：[选择参数] → [ ]     │
│                                    │
│ 4. 解决方案数量：[5]              │
│    (0=不给方案，≥1=生成方案)      │
│                                    │
│ [🔍 开始分析] [📊 查看历史]       │
└─────────────────────────────────────┘
```

### 关键UI组件

#### 1. AI开关组件
```python
class AISwitch(ft.Row):
    """显眼的AI开关"""
    def __init__(self):
        self.switch = ft.Switch(
            label="AI智能增强",
            value=False,  # 默认关闭
            active_color=ft.colors.GREEN,
            thumb_color={True: ft.colors.WHITE, False: ft.colors.GREY},
            scale=1.2  # 放大显示
        )
        self.help_icon = ft.IconButton(
            icon=ft.icons.HELP_OUTLINE,
            on_click=self.show_help
        )
```

#### 2. 矩阵选择器
```python
class MatrixSelector(ft.Row):
    """矩阵类型选择器"""
    def __init__(self):
        self.matrix_39 = ft.Radio(value="39", label="39矛盾矩阵")
        self.matrix_48 = ft.Radio(
            value="48", 
            label="48矛盾矩阵（规划中）",
            disabled=True  # 暂时禁用
        )
```

#### 3. 参数选择按钮
```python
class ParameterButton(ft.ElevatedButton):
    """参数选择按钮"""
    def __init__(self, param_type: str):
        super().__init__(
            text=f"选择{param_type}参数",
            icon=ft.icons.ARROW_DROP_DOWN,
            on_click=self.open_picker
        )
```

#### 4. 解决方案数量输入
```python
class SolutionCountInput(ft.TextField):
    """解决方案数量输入"""
    def __init__(self):
        super().__init__(
            label="解决方案数量",
            value="5",
            keyboard_type=ft.KeyboardType.NUMBER,
            helper_text="0=不给方案，≥1=生成方案",
            width=150
        )
```

## 🔄 工作流程实现

### 步骤1：问题输入和配置
```python
async def start_analysis_flow(page: ft.Page):
    """开始分析流程"""
    
    # 1. 收集用户输入
    problem = problem_input.value
    ai_enabled = ai_switch.value
    matrix_type = matrix_selector.value
    improving_param = improving_picker.selected_param
    worsening_param = worsening_picker.selected_param
    solution_count = int(solution_count_input.value)
    
    # 2. 验证输入
    if not problem.strip():
        show_error("请输入问题描述")
        return
        
    if solution_count < 0:
        show_error("解决方案数量不能为负数")
        return
```

### 步骤2：矛盾矩阵查询
```python
async def query_contradiction_matrix():
    """查询矛盾矩阵"""
    
    # 1. 创建矩阵实例
    matrix = ContradictionMatrix(matrix_type)
    
    # 2. 如果用户未选择参数，使用AI或算法自动检测
    if not improving_param or not worsening_param:
        if ai_enabled:
            # 使用AI检测参数
            params = await ai_client.detect_parameters(problem)
            improving_param = params.get("improving")
            worsening_param = params.get("worsening")
        else:
            # 使用本地算法检测
            params = local_engine.detect_parameters(problem)
            improving_param = params.get("improving")
            worsening_param = params.get("worsening")
    
    # 3. 查询矩阵得到原理编号
    principle_ids = matrix.find_solutions(
        improving_param, 
        worsening_param
    )
    
    return principle_ids, improving_param, worsening_param
```

### 步骤3：生成解决方案
```python
async def generate_solutions():
    """生成解决方案"""
    
    solutions = []
    
    if solution_count == 0:
        # 用户选择不生成方案
        return solutions
        
    # 限制最大数量
    actual_count = min(solution_count, 20)
    
    if ai_enabled:
        # AI生成解决方案
        solutions = await ai_client.generate_solutions(
            principle_ids=principle_ids,
            problem=problem,
            count=actual_count
        )
    else:
        # 本地生成解决方案
        solutions = local_engine.generate_solutions(
            principle_ids=principle_ids,
            problem=problem,
            count=actual_count
        )
    
    # 按原理分类
    categorized = categorize_by_principle(solutions)
    
    return categorized
```

### 步骤4：保存记录
```python
async def save_analysis_session():
    """保存分析会话"""
    
    session = AnalysisSession(
        id=generate_uuid(),
        problem=problem,
        matrix_type=matrix_type,
        improving_param=improving_param,
        worsening_param=worsening_param,
        ai_enabled=ai_enabled,
        solution_count=solution_count,
        solutions=solutions,
        created_at=datetime.now()
    )
    
    # 保存到本地数据库
    storage.save_session(session)
    
    # 显示保存成功提示
    show_success("分析记录已保存")
```

## 📊 数据模型设计

### SQLite数据库表结构
```sql
-- 分析会话表
CREATE TABLE analysis_sessions (
    id TEXT PRIMARY KEY,
    problem TEXT NOT NULL,
    matrix_type TEXT CHECK(matrix_type IN ('39', '48')),
    improving_param TEXT,
    worsening_param TEXT,
    ai_enabled BOOLEAN DEFAULT 0,
    solution_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 解决方案表
CREATE TABLE solutions (
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
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(id)
);

-- 应用配置表
CREATE TABLE app_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 开发计划

### 阶段1：基础框架（1周）
- [ ] 项目结构和依赖配置
- [ ] 基础UI框架搭建
- [ ] 本地TRIZ引擎迁移
- [ ] SQLite数据库设计

### 阶段2：核心功能（2周）
- [ ] 矛盾矩阵39实现
- [ ] 参数选择界面
- [ ] AI开关和集成
- [ ] 解决方案生成器

### 阶段3：完整流程（1周）
- [ ] 完整分析流程串联
- [ ] 本地记录系统
- [ ] 历史查看功能
- [ ] 数据导出功能

### 阶段4：Android优化（1周）
- [ ] 移动端UI适配
- [ ] 触摸交互优化
- [ ] APK打包测试
- [ ] 性能优化

## 🧪 测试策略

### 单元测试
```python
# 测试矛盾矩阵
def test_contradiction_matrix():
    matrix = ContradictionMatrix("39")
    principles = matrix.find_solutions("速度", "能耗")
    assert len(principles) > 0
    
# 测试AI客户端
def test_ai_client():
    client = AIClient(api_key="test_key")
    assert client.enabled == True
    
# 测试本地存储
def test_local_storage():
    storage = LocalStorage()
    session = create_test_session()
    storage.save_session(session)
    retrieved = storage.get_sessions(limit=1)
    assert retrieved[0].id == session.id
```

### 集成测试
```python
# 测试完整分析流程
async def test_full_analysis_flow():
    # 模拟用户输入
    inputs = {
        "problem": "手机电池续航短",
        "ai_enabled": True,
        "matrix_type": "39",
        "solution_count": 3
    }
    
    # 执行分析
    result = await execute_analysis_flow(inputs)
    
    # 验证结果
    assert result["success"] == True
    assert len(result["solutions"]) == 3
    assert result["session_saved"] == True
```

### Android真机测试
1. **功能测试**: 所有核心功能在真机上运行
2. **性能测试**: 内存使用、响应时间、电池消耗
3. **兼容性测试**: Android 5.0-14 不同版本
4. **网络测试**: 离线/在线模式切换

## 📱 Android打包配置

### build.gradle配置
```gradle
android {
    compileSdkVersion 34
    defaultConfig {
        applicationId "com.innovatetriz.assistant"
        minSdkVersion 21
        targetSdkVersion 34
        versionCode 1
        versionName "0.2.0"
    }
    
    buildTypes {
        release {
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android.txt')
        }
    }
}
```

### AndroidManifest.xml
```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.innovatetriz.assistant">
    
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    
    <application
        android:label="TRIZ创新助手"
        android:icon="@mipmap/ic_launcher"
        android:theme="@style/AppTheme">
        
        <activity android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

## 🔍 监控和优化

### 性能监控点
1. **启动时间**: < 2秒
2. **分析响应时间**: < 10秒（AI模式）
3. **内存使用**: < 100MB
4. **数据库操作**: < 100ms

### 错误处理
```python
class ErrorHandler:
    """统一错误处理"""
    
    @staticmethod
    def handle_network_error(error: Exception):
        """处理网络错误"""
        if isinstance(error, TimeoutError):
            return "网络请求超时，请检查网络连接"
        elif isinstance(error, ConnectionError):
            return "网络连接失败，请检查网络设置"
        else:
            return f"网络错误: {str(error)}"
    
    @staticmethod  
    def handle_ai_error(error: Exception):
        """处理AI错误"""
        if "API key" in str(error):
            return "AI服务配置错误，请检查API密钥"
        elif "quota" in str(error):
            return "AI服务额度不足，请稍后重试"
        else:
            return f"AI服务错误: {str(error)}"
```

## 📈 成功指标

### 功能完成度
- [ ] 基础TRIZ分析（离线）
- [ ] AI增强开关（显眼位置）
- [ ] 39矛盾矩阵完整实现
- [ ] 参数可视化选择
- [ ] 解决方案按原理分类
- [ ] 本地记录保存

### 用户体验
- [ ] 移动端界面友好
- [ ] 分析流程清晰
- [ ] 错误提示明确
- [ ] 操作反馈及时

### 技术质量
- [ ] Android APK成功打包
- [ ] 代码覆盖率 > 70%
- [ ] 无内存泄漏
- [ ] 响应时间达标

---

**工程负责人**: Claude Code  
**最后更新**: 2026年4月  
**版本**: 0.2.0