# InnovateTRIZ - AI 增强的 TRIZ 创新工具

## 项目简介

InnovateTRIZ 是一款基于 **Flet** 框架开发的移动应用，提供 AI 增强的 TRIZ（发明问题解决理论）分析工具。集成 39×39 和 48×48 矛盾矩阵查询、40 项发明原理浏览以及 AI 头脑风暴功能，帮助工程师和创新者快速解决技术矛盾。

## 技术框架

| 类别 | 技术选型 |
|------|----------|
| **框架** | Flet (Python) |
| **语言** | Python 3.10+ |
| **平台** | Android / Web / Desktop |
| **数据存储** | SQLite + JSON 配置 |
| **AI 集成** | DeepSeek / OpenRouter (OpenAI 兼容接口) |

## 快速开始

### 运行应用

```bash
# 桌面窗口模式
python main.py --mode desktop

# Web 模式（开发调试）
python main.py --mode web --port 8550
```

### 构建 APK

```bash
# 需 JDK 17 + Android SDK
flet build apk
```

### 运行测试

```bash
uv run pytest tests/ -v
```

## 核心功能

### 1. 矛盾矩阵查询
- **39×39 矛盾矩阵**：1189 条经典 TRIZ 记录
- **48×48 矛盾矩阵**：2304 条完整矩阵数据
- 参数名称统一使用标准翻译（如"明亮度"而非"亮度"）

### 2. 40 项发明原理库
- 完整的 40 条发明原理浏览
- 每条原理配有详细说明和应用指导

### 3. AI 参数检测
- 可选 AI 分析，从用户问题描述中自动识别工程参数
- 支持 DeepSeek、OpenRouter 等多提供商
- AI 不可用时自动降级到本地引擎

### 4. AI 头脑风暴
- 基于查询到的发明原理，AI 自动生成创新解决方案
- 原理结果自动缓存，无需重复查询

## 创新点

1. **双矩阵支持**：同时内置 39×39 和 48×48 矛盾矩阵，兼容传统与扩展 TRIZ 方法
2. **AI 增强分析**：大语言模型辅助参数识别与方案生成，降低 TRIZ 学习门槛
3. **离线优先**：所有 TRIZ 数据内置于代码，无外部依赖，确保离线可用
4. **跨平台部署**：一份代码支持 Android、Web、Windows、macOS、Linux 多平台
5. **异步架构**：全面采用 async/await 异步编程，保证 UI 流畅响应
