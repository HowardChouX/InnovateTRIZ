# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目定位

InnovateTRIZ 是一个基于 **Flet** 框架的 Android 移动应用，提供 AI 增强的 TRIZ（创新算法）分析工具。核心功能：39×39 矛盾矩阵查询、40 发明原理浏览、AI 头脑风暴。

## 常用命令

```bash
# Python 版本要求：3.10+

# 运行应用（开发调试首选）
python main.py --mode desktop    # 桌面窗口模式
python main.py --mode web --port 8550  # 浏览器测试

# 运行测试
uv run pytest tests/ -v
uv run pytest tests/test_core.py -v              # 单个文件
uv run pytest tests/ -k "matrix" -v              # 按名称过滤
uv run pytest tests/ -k "ai and not status" -v   # 组合过滤

# 代码质量检查
uv run black src/ tests/
uv run ruff check src/ tests/
uv run mypy src/

# 构建 Android APK（需 JDK 17 + Android SDK）
flet build apk
flet build apk --split-per-abi   # 按 ABI 分割

# 构建 AAB（用于 Play Store）
flet build aab
```

## Flet 规范参考

权威文档在 `docs_flet/` 目录（来源 https://flet.dev/docs/）。所有 Flet API 问题**以本地文档为准**。

| 文档 | 路径 |
|------|------|
| Android 发布 | `docs_flet/publish/android.md` |
| 异步编程 | `docs_flet/cookbook/async-apps.md` |
| 大列表优化 | `docs_flet/cookbook/large-lists.md` |

### Flet 关键规范

- 入口：`ft.run(TRIZApp().main, assets_dir="assets")`
- 异步优先：事件处理器应为 `async def`，刷新使用 `await page.update_async()`
- 大列表必须用 `ft.ListView(expand=True)` 而非 `ft.Column`
- 自定义控件：继承 Flet 控件或使用 `@ft.control` 装饰器
- 导航：`ft.NavigationBar` + `on_change` 事件处理 Tab 切换

## 架构概览

```
src/main.py → TRIZApp.main(page)              # 应用入口（pyproject.toml 指定 path="src"）
├── AppSettings.load()                        # 异步加载 config.json
├── LocalStorage.initialize()                  # SQLite 初始化
├── AIManager.initialize()                     # AI 客户端（可选）
├── page.run_task(_silent_test_ai_connection)  # 后台静默测试 AI 连接
└── TRIZAppShell.show()                        # 3-Tab 导航外壳
        ├── MatrixTab          # Tab1: 矛盾矩阵分析（主功能）
        ├── PrinciplesTab      # Tab2: 40 发明原理库
        └── SettingsTab        # Tab3: 全局设置 + 历史管理
```

### UI 层级

- `TRIZAppShell`（`src/ui/app_shell.py`）：管理 `ft.NavigationBar` + Tab 显隐切换
- `TabContent(ft.Column)` 是所有 Tab 的基类，`on_show()` 在 Tab 首次显示时调用
- `AIStateManager`（`src/ui/state/ai_state.py`）：观察者模式单例，广播 AI 启用/连接状态变更

### 全局单例模式

| 函数 | 模块 | 返回类型 |
|------|------|----------|
| `get_ai_manager()` | `src/ai/ai_client.py` | `AIManager` |
| `get_triz_engine()` | `src/core/triz_engine.py` | `TRIZEngine` |
| `get_matrix_manager()` | `src/core/matrix_selector.py` | `MatrixManager` |
| `get_storage()` | `src/data/local_storage.py` | `LocalStorage` |
| `get_app_settings()` | `src/config/settings.py` | `AppSettings` |
| `get_triz_logger()` | `src/utils/logger.py` | `TRIZLogger` |
| `get_ai_state_manager()` | `src/ui/state/ai_state.py` | `AIStateManager` |

### 矛盾矩阵

两个矩阵均已实现，内置于 `src/data/triz_constants.py`：

| 矩阵 | 参数数 | 记录数 | 说明 |
|------|--------|--------|------|
| 39 矛盾矩阵 | 39 | 1189 条 | 稀疏矩阵，原始数据 |
| 48 矛盾矩阵 | 48 | 2304 条 | 完整48×48，从triz48.xls导入 |

- 参数名统一使用 xls 标准翻译（如"明亮度"而非"亮度"）
- `ContradictionMatrix`（`matrix_selector.py`）：查询接口，`matrix_type` 属性区分 "39"/"48"
- `MatrixManager.get_matrix(matrix_type)`：获取指定类型矩阵实例
- `LocalTRIZEngine.detect_parameters()`：支持切换 `matrix_type="48"`

### 用户操作流程

```
输入问题 → (可选)AI分析参数 → 选择参数 → 点击"查询原理" → 点击"头脑风暴"
                                          ↓
                              原理缓存到 _current_matrix_principles
                                          ↓
                              头脑风暴使用缓存的原理，不再重新查询
```

**关键约束**：
1. 查询原理前必须先选择至少一个参数（改善或恶化）
2. 头脑风暴前必须先点击"查询原理"填充缓存

### 数据流

- **TRIZ 数据内置**：39 矩阵 + 48 矩阵 + 40 发明原理，全部在 `triz_constants.py` 中，无外部文件依赖
- `LocalStorage`（SQLite）存储分析会话，Android 下使用 DELETE 日志模式，桌面环境使用 WAL
- `AppSettings` 持久化到 `FLET_APP_STORAGE_DATA/config.json`，API Key 用 Base64 简单混淆
- `LocalStorage` 和 `AppSettings` 都优先使用 `FLET_APP_STORAGE_DATA` 环境变量目录

### AI 集成

- `AIClient` 封装 `AsyncOpenAI`，支持 DeepSeek（默认）、OpenRouter 等 OpenAI 兼容接口
- `AIManager` 管理连接状态：`is_enabled()` = 已配置，`is_connected()` = 实际可用
- 多提供商配置存储在 `config.json`，通过 `AppSettings.ai_providers_config` 管理
- **AI 参数检测**（`AIClient.detect_parameters`）：
  - 严格的 prompt 要求 AI 必须从 39 个工程参数中精确选择
  - temperature=0 确保确定性输出，最多重试 2 次
  - AI 不可用时自动降级到 `LocalTRIZEngine.detect_parameters`
- `PromptBuilder`（`src/ai/prompts/builder.py`）：只有 `build_solution_prompt` 和 `build_single_principle_solution_prompt` 两个方法

### 模块导入约定

- `PromptBuilder` 从 `data.triz_constants` 导入 `PRINCIPLE_NAMES`（原理名称，无"原理"后缀）
- `PrincipleService` 使用 `PRINCIPLE_NAMES` 作为原理显示名称
- `matrix_selector.py` 从 `data.triz_constants` 导入矩阵数据
- 测试文件需将 `src/` 目录加入 `sys.path`，参考 `tests/conftest.py`

## 待开发功能

| 功能 | 描述 | 相关文件 |
|------|------|---------|
| **物质-场分析** | 识别S1-S2-F模型并应用标准解 | `templates.py` |
| **76标准解应用** | 基于物质-场分析推荐标准解 | `templates.py` |
| **功能分析** | 分析技术系统的组件、功能和关系 | （规划中） |
| **物理矛盾求解** | 分离原理求解物理矛盾 | （规划中） |

> 注意：`builder.py` 中的 `build_function_analysis_prompt` 和 `build_physical_contradiction_prompt` 方法尚未实现

## 关键约束

1. **数据内置**：禁止依赖外部 Excel/CSV，所有数据在 Python 代码中
2. **AI 默认关闭**：用户必须主动开启
3. **纯 Python 依赖**：打包前确认所有二进制包有 Android wheel
4. **异步模式**：所有 Flet 事件处理器和页面更新都使用 `async/await`

## 调试技巧

```bash
# 快速验证数据完整性
uv run python -c "
from src.data.triz_constants import get_triz_data_loader
loader = get_triz_data_loader()
print(f'参数:{len(loader.get_all_params())}, 矩阵:{len(loader.get_contradiction_matrix())}, 原理:{len(loader.get_40_principles())}')
"

# 运行测试
uv run pytest tests/ -v

# 日志路径（按优先级）：
# 1. FLET_APP_STORAGE_DATA/logs/ （Flet 推荐）
# 2. ~/.config/triz-assistant/logs/ （桌面环境回退）
# 3. .triz_logs/ （Android 回退）
```

