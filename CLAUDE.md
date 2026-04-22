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

# 也可使用 flet CLI（需先安装 flet-cli）
uv run flet run          # 桌面模式
uv run flet run --web     # Web 模式

# 运行测试
pytest tests/ -v
pytest tests/test_core.py -v                       # 单个文件
pytest tests/ -k "matrix" -v                       # 按名称过滤
pytest tests/ -k "ai and not status" -v           # 组合过滤

# 代码质量检查
black src/ tests/
ruff check src/ tests/
mypy src/

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
根目录 main.py → TRIZApp.main(page)           # 应用入口（注意：不是 src/main.py）
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
- `TabContent(ft.Column)` 是所有 Tab 的基类，`on_show()` 在 Tab 首次显示时调用，`on_hide()` 在 Tab 隐藏时调用
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

### 数据流

- 所有 TRIZ 数据**内置于** `src/data/triz_constants.py`（1189 条矩阵记录），无外部文件依赖
- `LocalStorage`（SQLite）存储分析会话，Android 下使用 DELETE 日志模式，桌面环境使用 WAL
- `AppSettings` 持久化到 `FLET_APP_STORAGE_DATA/config.json`，API Key 用 Base64 简单混淆
- `LocalStorage` 和 `AppSettings` 都优先使用 `FLET_APP_STORAGE_DATA` 环境变量目录

### AI 集成

- `AIClient` 封装 `AsyncOpenAI`，支持 DeepSeek（默认）、OpenRouter 等 OpenAI 兼容接口
- `AIManager` 管理连接状态：`is_enabled()` = 已配置，`is_connected()` = 实际可用
- 多提供商配置存储在 `config.json`，通过 `AppSettings.ai_providers_config` 管理
- `LocalTRIZEngine.detect_parameters()` 用关键词权重匹配作为 AI 的降级方案
- **头脑风暴遍历注入**：`TRIZEngine.generate_solutions_iterative()` 遍历每个原理单独调用 AI

### 矛盾矩阵

- **39 矛盾矩阵**：完整实现，1189 条记录
- **48 矛盾矩阵**：预留接口，UI 可切换但功能未实现

### 提示词系统

- `PromptBuilder`（`src/ai/prompts/builder.py`）：构建各类提示词
- `PromptLoader`（`src/ai/prompts/loader.py`）：加载40发明原理详情

## 关键约束

1. **数据内置**：禁止依赖外部 Excel/CSV，所有数据在 `triz_constants.py` 的 Python 代码中
2. **AI 默认关闭**：用户必须主动开启
3. **纯 Python 依赖**：打包前确认所有二进制包有 Android wheel
4. **异步模式**：所有 Flet 事件处理器和页面更新都使用 `async/await`

## 调试技巧

```bash
# 桌面模式运行时日志同时输出到控制台和文件
# 日志路径（按优先级）：
# 1. FLET_APP_STORAGE_DATA/logs/ （Flet 推荐，平台预创建）
# 2. ~/.config/triz-assistant/logs/ （桌面环境回退）
# 3. .triz_logs/ （Android 回退）

# 快速验证数据完整性
python -c "
from src.data.triz_constants import get_triz_data_loader
loader = get_triz_data_loader()
print(f'参数:{len(loader.get_all_params())}, 矩阵:{len(loader.get_contradiction_matrix())}, 原理:{len(loader.get_40_principles())}')
"
```
