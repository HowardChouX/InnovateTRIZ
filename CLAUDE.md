# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目定位

InnovateTRIZ 是一个基于 **Flet** 框架的 Android 移动应用，提供 AI 增强的 TRIZ（创新算法）分析工具。核心功能：39×39 矛盾矩阵查询、40 发明原理浏览、AI 头脑风暴。

## 常用命令

```bash
# 桌面模式运行（开发调试首选）
python main.py --mode desktop

# Web 模式运行（浏览器测试）
python main.py --mode web --port 8550

# 运行所有测试
pytest tests/ -v

# 运行单个测试文件
pytest tests/test_core.py -v

# 代码格式化与检查
black src/ tests/
ruff check src/ tests/
mypy src/

# 构建 Android APK（需 JDK 17 + Android SDK）
flet build apk
flet build apk --split-per-abi   # 按 ABI 分割，减小包体积

# 构建 AAB（推荐用于 Play Store）
flet build aab
```

## Flet 规范参考

**权威文档**：`docs_flet/` 目录（来源 https://flet.dev/docs/）。所有 Flet API 问题**以本地文档为准**。

| 文档 | 路径 |
|------|------|
| Android 发布 | `docs_flet/publish/android.md` |
| 异步编程 | `docs_flet/cookbook/async-apps.md` |
| 导航与路由 | `docs_flet/cookbook/navigation-and-routing.md` |
| 主题系统 | `docs_flet/cookbook/theming.md` |
| 大列表优化 | `docs_flet/cookbook/large-lists.md` |
| 自定义控件 | `docs_flet/extend/` |
| 客户端存储 | `docs_flet/cookbook/client-storage.md` |

### Flet 关键规范（当前版本 v0.84.0）

- 入口：`ft.app(target=async_main, assets_dir="assets")`
- 异步优先：事件处理器应为 `async def`，刷新使用 `await page.update_async()`
- 大列表必须用 `ft.ListView(expand=True)` 而非 `ft.Column`，避免性能问题
- 自定义控件用 `@ft.control` 装饰器或继承 Flet 控件加 `@dataclass`
- 主题：`page.theme = ft.Theme(color_scheme_seed=...)` 或 `ft.ColorScheme(...)`
- 导航：`ft.NavigationBar` + `page.on_route_change` 处理路由变更

### Android 打包约束

- 仅支持**纯 Python 包**或有 Android 预编译 wheel 的二进制包（见 `docs_flet/publish/android.md`）
- `sqlalchemy`、`pydantic-core` 等二进制包需确认 Android wheel 存在
- 构建需要 JDK 17，首次运行 `flet build` 会自动安装（安装在 `~/java/`）
- APK 签名：不提供 keystore 时使用 debug key，无法上传 Play Store

## 架构概览

```
main.py → TRIZApp.main(page)
            ├── AppSettings.load()          # 异步加载设置（config.json）
            ├── LocalStorage.initialize()    # SQLite 初始化
            ├── AIManager.initialize()       # AI 客户端（可选）
            ├── check_ai_connectivity()      # 联通性检测，结果缓存
            └── TRIZAppShell.show()          # 3-Tab 导航外壳
                    ├── MatrixTab            # Tab1: 矛盾矩阵分析（主功能，~1400 行）
                    ├── PrinciplesTab        # Tab2: 40 发明原理库
                    └── SettingsTab          # Tab3: 全局设置 + 历史管理
```

### UI 层级

- `TRIZAppShell`（`src/ui/app_shell.py`）：管理 `ft.NavigationBar` + Tab 显隐切换
- `TabContent(ft.Column)` 是所有 Tab 的基类，提供 `on_show()` / `on_hide()` 延迟构建钩子
- `AIStateManager`（`src/ui/state/ai_state.py`）：观察者模式单例，广播 AI 启用/连接状态变更，`MatrixTab` 通过 `subscribe()` 同步 AI 按钮状态

### 全局单例模式

所有核心服务通过模块级工厂函数返回单例，避免重复初始化：

| 函数 | 模块 | 返回类型 |
|------|------|------|
| `get_ai_manager()` | `src/ai/ai_client.py` | `AIManager` |
| `get_triz_engine()` | `src/core/triz_engine.py` | `TRIZEngine` |
| `get_matrix_manager()` | `src/core/matrix_selector.py` | `MatrixManager` |
| `get_storage()` | `src/data/local_storage.py` | `LocalStorage` |
| `get_app_settings()` | `src/config/settings.py` | `AppSettings` |
| `get_triz_logger()` | `src/utils/logger.py` | `TRIZLogger` |

### 数据流

- 所有 TRIZ 数据（参数、矩阵、原理）**内置于** `src/data/excel_loader.py`（1189 条矩阵记录），无外部文件依赖
- `LocalStorage`（`src/data/local_storage.py`）：SQLite 直接存储分析会话，Android 下自动从 WAL 模式切换为 DELETE 模式
- `AppSettings` 持久化到 `~/.config/triz-assistant/config.json`（Android: `/data/data/com.example.triz/files/config.json`），API Key 用 Base64 简单混淆存储

### AI 集成

- `AIClient` 封装 `AsyncOpenAI`，通过 `openai` 兼容 SDK 调用 DeepSeek（默认）或 OpenRouter
- `AIManager`（单例）管理连接状态：`is_enabled()` = 已配置，`is_connected()` = 实际可用
- `LocalTRIZEngine.detect_parameters()` 用关键词权重匹配（带 `@lru_cache`）作为 AI 的降级方案

## 关键约束

1. **数据内置**：禁止依赖外部 Excel/CSV，所有数据在 `excel_loader.py` 的 Python 代码中
2. **AI 默认关闭**：`ai_enabled = False`，用户必须主动开启
3. **Android 专一**：不考虑 iOS，路径和存储已针对 Android 环境特殊处理
4. **纯 Python 依赖**：打包前确认所有二进制包有 Android wheel
5. **异步模式**：所有 Flet 事件处理器和页面更新都使用 `async/await`

## 调试技巧

```bash
# 查看实时日志
tail -f logs/triz_app.log

# 快速验证数据完整性
python -c "
from src.data.excel_loader import get_triz_data_loader
loader = get_triz_data_loader()
print(f'参数:{len(loader.get_all_params())}, 矩阵:{len(loader.get_contradiction_matrix())}, 原理:{len(loader.get_40_principles())}')
"
```
