# TRIZ AI 创新助手 (Flet移动应用版)

基于Flet框架的跨平台TRIZ创新工具，将AI增强的TRIZ方法论带到移动设备。

**当前版本**: v1.0.0 (开发中)
**开发进度**: 约60%完成
**主要功能**: 矛盾矩阵分析 + AI智能增强 + 本地记录

## 🚀 特性

### 核心功能
- **智能问题分析**: 基于40个TRIZ发明原理
- **AI增强**: DeepSeek/OpenRouter API集成（默认关闭）
- **矛盾矩阵**: 39个工程参数矩阵（48矩阵规划中）
- **头脑风暴**: 创意解决方案生成
- **本地记录**: 会话历史保存和导出

### 用户体验
- **响应式设计**: 手机、平板、桌面全适配
- **离线可用**: 核心TRIZ功能无需网络
- **双语支持**: 中文/English界面
- **本地存储**: 历史记录、收藏夹、配置

### 技术优势
- **纯Python**: 无需HTML/CSS/JavaScript
- **一次编写**: 多平台运行（Android/iOS/桌面）
- **现代架构**: MVVM模式 + 依赖注入
- **易于扩展**: 模块化设计

## 📱 支持的平台

### 移动设备
- **Android 5.0+** (API Level 21+)
- **iOS 13.0+** (需要macOS打包)

### 桌面系统
- **Windows 10/11**
- **macOS 10.15+**
- **Linux** (Ubuntu 20.04+, Fedora 32+)

## 🛠️ 技术栈

### 核心框架
- **Flet 0.25.0+**: 基于Flutter的Python GUI框架
- **Python 3.10+**: 运行时环境

### AI集成
- **DeepSeek API**: 默认AI提供商
- **OpenRouter API**: 兼容现有配置
- **本地TRIZ**: 离线回退模式

### 数据存储
- **SQLite**: 本地数据库
- **JSON**: 配置和导出文件

### 开发工具
- **pytest**: 单元测试
- **black**: 代码格式化
- **mypy**: 类型检查

## 📁 项目结构

```
triz-app/
├── src/                          # 源代码
│   ├── core/                    # TRIZ核心逻辑
│   ├── ui/                      # Flet界面组件
│   ├── data/                    # 数据管理
│   └── utils/                   # 工具函数
├── main.py                      # 应用入口
├── requirements.txt             # Python依赖
├── pyproject.toml              # 项目配置
├── android/                     # Android打包配置
├── tests/                       # 测试文件
└── docs/                        # 文档
```

## 🚦 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd triz-app

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行应用
```bash
# 桌面模式（默认）
python main.py

# Web模式（浏览器访问）
python main.py --web

# 指定端口
python main.py --port 8080
```

### 3. 配置AI密钥（可选）
```bash
# 创建.env文件
cp .env.example .env

# 编辑.env文件，添加你的DeepSeek API密钥
DEEPSEEK_API_KEY=your-api-key-here
```

## 📦 打包部署

### Android APK
```bash
# 安装Flet CLI
pip install flet-cli

# 打包APK
flet build apk

# 输出文件在 build/android/app-release.apk
```

### 桌面应用
```bash
# 使用PyInstaller
pip install pyinstaller

# 打包为可执行文件
pyinstaller --onefile --windowed main.py
```

## 🔧 开发指南

### 代码规范
- 使用类型注解
- 遵循PEP 8规范
- 编写文档字符串
- 添加单元测试

### 添加新功能
1. 在对应模块创建新类/函数
2. 编写单元测试
3. 更新UI组件
4. 更新文档

### 调试技巧
```python
# 启用调试模式
python main.py --debug

# 查看Flet日志
flet --verbose
```

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- **TRIZ理论创始人**: Genrich Altshuller
- **Flet框架团队**: 提供优秀的Python GUI解决方案
- **DeepSeek团队**: 提供高质量的AI API服务
- **所有贡献者**: 感谢你们的代码和反馈

## 📞 支持与反馈

- **问题报告**: [GitHub Issues](https://github.com/your-repo/issues)
- **功能请求**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **文档**: 查看 `docs/` 目录
- **邮件**: support@innovatetriz.com

---

**让创新变得更简单** 🚀