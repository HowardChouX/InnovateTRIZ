# Android打包模块交接文档

**模块**: `android/` - Android应用打包配置
**创建日期**: 2025-04-18
**前置状态**: 核心逻辑+UI+测试完成后
**后续状态**: 部署发布

---

## 📋 任务概述

配置Android打包环境，生成可安装的APK文件。

---

## 📁 Android配置结构

```
triz-app/android/
├── README.md                   # 打包说明
├── build.gradle               # Gradle构建配置
├── AndroidManifest.xml       # Android清单
├── res/                       # 资源文件
│   ├── mipmap-hdpi/         # 应用图标（不同分辨率）
│   ├── mipmap-mdpi/
│   ├── mipmap-xhdpi/
│   ├── mipmap-xxhdpi/
│   ├── mipmap-xxxhdpi/
│   └── values/
│       ├── strings.xml       # 字符串资源
│       ├── colors.xml        # 颜色定义
│       └── themes.xml        # 主题
└── keystore/                # 签名密钥（发布时需要）
    └── app.keystore
```

---

## 🎯 打包前准备

### 1. 环境要求

```bash
# 检查Python版本
python --version  # 需要 Python 3.10+

# 检查Flet CLI
flet --version  # 需要 flet >= 0.25.0

# 如果未安装Flet CLI
pip install flet-cli

# 检查Flutter SDK（Android打包必需）
flutter --version

# 如果未安装Flutter，需要安装
# 参考：https://flutter.dev/docs/get-started/install
```

### 2. Android SDK配置

```bash
# 设置环境变量
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools

# 检查Android SDK
echo $ANDROID_HOME  # 确认路径存在
```

### 3. 安装依赖

```bash
cd triz-app
pip install -r requirements.txt

# 安装打包工具
pip install flet-cli pyinstaller
```

---

## 📝 build.gradle配置

```gradle
android {
    namespace "com.innovatetriz.assistant"
    compileSdk 34

    defaultConfig {
        applicationId "com.innovatetriz.assistant"
        minSdk 21
        targetSdk 34
        versionCode 1
        versionName "0.2.0"

        // 支持多CPU架构
        ndk {
            abiFilters 'armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64'
        }
    }

    buildTypes {
        release {
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
        debug {
            minifyEnabled false
            debuggable true
        }
    }

    signingConfigs {
        release {
            // 发布签名配置（需要keystore文件）
            storeFile file("keystore/app.keystore")
            storePassword "your_password"
            keyAlias "triz-app"
            keyPassword "your_password"
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }

    kotlinOptions {
        jvmTarget = '1.8'
    }
}

flutter {
    source '../..'
}

dependencies {
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
}
```

---

## 📝 AndroidManifest.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.innovatetriz.assistant">

    <!-- 网络权限（AI功能必需） -->
    <uses-permission android:name="android.permission.INTERNET" />

    <!-- 存储权限（数据导出可能需要） -->
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

    <application
        android:label="TRIZ创新助手"
        android:name=".Application"
        android:icon="@mipmap/ic_launcher"
        android:allowBackup="true"
        android:fullBackupContent="@xml/backup_rules"
        android:dataExtractionRules="@xml/data_extraction_rules"
        android:theme="@style/LaunchTheme"
        android:supportsRtl="true"
        android:usesCleartextTraffic="true">

        <!-- 主Activity -->
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize">

            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <!-- Google Play应用签名 -->
        <meta-data
            android:name="com.google.android.gms.version"
            android:value="@integer/google_play_services_version" />
    </application>
</manifest>
```

---

## 📝 strings.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">TRIZ创新助手</string>
    <string name="app_description">AI增强的TRIZ创新工具</string>

    <!-- 主界面 -->
    <string name="ai_enhancement">AI智能增强</string>
    <string name="ai_disabled">关闭</string>
    <string name="ai_enabled">开启</string>
    <string name="problem_input_hint">描述您的技术问题...</string>
    <string name="matrix_39">39矛盾矩阵</string>
    <string name="matrix_48">48矛盾矩阵（规划中）</string>
    <string name="select_improving_param">选择改善参数</string>
    <string name="select_worsening_param">选择恶化参数</string>
    <string name="solution_count">解决方案数量</string>
    <string name="start_analysis">开始分析</string>
    <string name="view_history">查看历史</string>

    <!-- 结果 -->
    <string name="analysis_result">分析结果</string>
    <string name="no_solution">未生成解决方案</string>
    <string name="confidence">置信度</string>
    <string name="ai_generated">AI生成</string>

    <!-- 错误 -->
    <string name="error_network">网络连接失败</string>
    <string name="error_api_key">API密钥配置错误</string>
    <string name="error_unknown">发生未知错误</string>

    <!-- 按钮 -->
    <string name="btn_retry">重试</string>
    <string name="btn_export">导出</string>
    <string name="btn_save">保存</string>
    <string name="btn_close">关闭</string>
</resources>
```

---

## 🎨 应用图标

### 图标规格

| 分辨率 | 尺寸 | 用途 |
|--------|------|------|
| mdpi | 48x48 | 低密度屏幕 |
| hdpi | 72x72 | 高密度屏幕 |
| xhdpi | 96x96 | 超高密度屏幕 |
| xxhdpi | 144x144 | 超超高密度屏幕 |
| xxxhdpi | 192x192 | 超超超高密度屏幕 |

### 图标设计要求

- 尺寸：512x512 PNG（原始尺寸）
- 格式：PNG（推荐）或 WebP
- 背景：透明或纯色
- 主元素：大脑/灯泡/TRIZ相关图标
- 颜色：使用APP的主题色（蓝色 #2196F3）

### 生成命令
```bash
# 使用ImageMagick调整图标大小
convert original_icon.png -resize 48x48 android/res/mipmap-mdpi/ic_launcher.png
convert original_icon.png -resize 72x72 android/res/mipmap-hdpi/ic_launcher.png
convert original_icon.png -resize 96x96 android/res/mipmap-xhdpi/ic_launcher.png
convert original_icon.png -resize 144x144 android/res/mipmap-xxhdpi/ic_launcher.png
convert original_icon.png -resize 192x192 android/res/mipmap-xxxhdpi/ic_launcher.png
```

---

## 🚀 打包命令

### 开发版APK（调试）

```bash
cd triz-app

# 方法1：使用Flet CLI
flet build apk --dev

# 方法2：指定输出目录
flet build apk --output ./dist/

# 方法3：指定包名和版本
flet build apk \
  --package-name com.innovatetriz.assistant \
  --build-number 1 \
  --build-name 0.2.0
```

### 发布版APK（签名）

```bash
# 1. 创建keystore（如果不存在）
keytool -genkey -v -keystore android/keystore/app.keystore \
  -alias triz-app \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000

# 2. 打包发布版
flet build apk --release \
  --keystore=android/keystore/app.keystore \
  --keystore-password=your_password \
  --key-alias=triz-app \
  --key-password=your_password

# 3. 验证签名
jarsigner -verify -verbose -certs dist/app-release.apk
```

### 查看打包输出

```bash
# 查看生成的APK
ls -la build/android/app/build/outputs/apk/*/app-*.apk

# 查看APK信息
aapt dump badging build/android/app/build/outputs/apk/debug/app-debug.apk
```

---

## 🔧 常见问题处理

### 1. Flutter SDK未安装
```
Error: Flutter SDK not found
```
**解决方案**:
```bash
# 安装Flutter SDK
cd ~
wget https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.24.0-stable.tar.xz
tar xf flutter_linux_3.24.0-stable.tar.xz
export PATH="$PATH:$HOME/flutter/bin"

# 配置Android SDK路径
flutter config --android-sdk=$ANDROID_HOME
```

### 2. Android SDK未找到
```
Error: Android SDK not found at /path/to/sdk
```
**解决方案**:
```bash
# 设置Android SDK路径
export ANDROID_HOME=$HOME/Android/Sdk
flutter config --android-sdk=$ANDROID_HOME

# 接受许可协议
yes | $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --licenses
```

### 3. 打包超时
```
Error: Build timeout
```
**解决方案**:
```bash
# 增加超时时间
flet build apk --timeout 600

# 清除缓存重新打包
rm -rf build/
flet build apk
```

### 4. 内存不足
```
Error: Out of memory
```
**解决方案**:
```bash
# 增加Gradle内存
echo "org.gradle.jvmargs=-Xmx2048m -XX:MaxMetaspaceSize=512m" >> android/gradle.properties

# 使用较少资源进行打包
flet build apk --no-tree-shake
```

---

## 📊 打包检查清单

### 打包前检查
- [ ] Python环境版本正确（3.10+）
- [ ] Flet CLI已安装
- [ ] Flutter SDK已安装（如果是Android打包）
- [ ] Android SDK已安装
- [ ] 环境变量配置正确
- [ ] 应用图标已准备

### 打包后验证
- [ ] APK文件生成成功
- [ ] APK文件大小合理（<100MB）
- [ ] APK可以安装到设备
- [ ] 应用可以启动
- [ ] 核心功能正常运行

### 发布前检查
- [ ] 使用发布签名
- [ ] 混淆配置已启用
- [ ] 版本号已更新
- [ ] 应用名称正确
- [ ] 图标清晰

---

## 📞 交接给下一个Agent

当Android打包完成后，请创建`Android打包完成.md`，包含：
1. APK文件位置
2. 打包过程记录
3. 签名信息
4. 测试结果
5. 发布指南

---

**前置模块**: 测试模块完成后
**后续状态**: 部署发布
**预计工时**: 1-2小时（包含环境配置）

---

## 附录：快速参考命令

```bash
# 环境检查
python --version
pip show flet
flutter --version
echo $ANDROID_HOME

# 开发打包
cd triz-app
flet build apk --dev

# 发布打包
flet build apk --release \
  --keystore=android/keystore/app.keystore \
  --keystore-password=password \
  --key-alias=triz-app \
  --key-password=password

# 查看APK
ls -la build/android/app/build/outputs/apk/
```