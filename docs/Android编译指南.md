# TRIZ Android 应用编译指南

## 环境要求

### 推荐环境
- **操作系统**：Windows 11（推荐）或 macOS
- **Flutter SDK**：3.10.x - 3.20.x（LTS 版本）
- **Android SDK**：Android Studio 自带或独立安装
- **Python**：3.10+

### 注意事项
- Arch Linux 等 Linux 发行版可能存在 Flutter SDK 版本兼容性问题
- 推荐使用官方支持的 Windows/macOS 环境进行打包

---

## Windows 11 编译步骤

### 第一步：安装 Flutter SDK

1. 下载 Flutter SDK（推荐 3.10.5 LTS）：
   ```
   https://docs.flutter.dev/release/archive?tab=windows
   ```

2. 解压到合适位置（如 `C:\flutter`）

3. 添加到系统环境变量：
   - `PATH` 添加 `C:\flutter\bin`

4. 验证安装：
   ```cmd
   flutter --version
   ```

### 第二步：配置 Android SDK

**方案 A：使用 Android Studio（推荐）**
1. 下载 Android Studio：https://developer.android.com/studio
2. 安装时勾选 "Android SDK"
3. 配置环境变量：
   ```cmd
   set ANDROID_HOME=C:\Users\<用户名>\AppData\Local\Android\Sdk
   ```

**方案 B：独立安装 Android SDK**
1. 下载 Command Line Tools：https://developer.android.com/studio#command-line-tools-only
2. 安装必要的组件：
   ```cmd
   sdkmanager --install "platform-tools" "platforms;android-34" "build-tools;34.0.0"
   ```

### 第三步：安装 Python 依赖

```cmd
cd triz-app
pip install flet==0.84.0
```

### 第四步：编译 APK

```cmd
flet build apk
```

或指定输出目录：
```cmd
flet build apk --output ./dist
```

### 第五步：验证 APK

编译成功后，APK 文件位于：
```
build/flutter/app/outputs/flutter-apk/app-debug.apk
```

---

## 命令行完整流程

```cmd
# 1. 克隆项目（如果需要）
git clone <仓库地址>
cd triz-app

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
set ANDROID_HOME=C:\Users\<用户名>\AppData\Local\Android\Sdk

# 4. 编译 Debug 版本
flet build apk

# 5. 编译 Release 版本（需要签名）
flet build apk --release
```

---

## 发布版 APK 签名配置

### 生成签名密钥

```cmd
keytool -genkey -v -keystore app.keystore -alias triz-app -keyalg RSA -keysize 2048 -validity 10000
```

### 编译带签名的 Release APK

```cmd
flet build apk --release \
  --keystore=app.keystore \
  --keystore-password=<密码> \
  --key-alias=triz-app \
  --key-password=<密码>
```

---

## 常见问题

### Q1: flutter 命令找不到
**解决**：将 Flutter SDK 的 bin 目录添加到 PATH 环境变量

### Q2: Android SDK 未检测到
**解决**：确保 ANDROID_HOME 环境变量正确设置

### Q3: 编译失败，提示 SDK 版本问题
**解决**：使用 Flutter 3.10-3.20 版本，避免使用最新的 stable 版本

### Q4: 依赖安装失败
**解决**：使用国内镜像
```cmd
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 项目结构

```
triz-app/
├── main.py                 # 应用入口
├── requirements.txt         # Python 依赖
├── src/                    # 源代码
│   ├── ai/                 # AI 客户端
│   ├── config/             # 配置
│   ├── core/               # 核心逻辑
│   ├── data/               # 数据层
│   └── ui/                 # UI 组件
├── tests/                  # 测试文件
└── build/                  # 编译输出
    └── flutter/
        └── app/
            └── outputs/
                └── flutter-apk/
                    └── app-debug.apk
```

---

## 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| Flutter | 3.10-3.20 | SDK 框架 |
| Flet | 0.84.0 | Python GUI 框架 |
| Python | 3.10+ | 运行时 |
| Android SDK | 34+ | Android 编译目标 |
