# Android打包配置目录

本目录用于存放Android应用打包相关的配置和资源文件。

## 目录结构

```
android/
├── build.gradle          # Gradle构建配置
├── AndroidManifest.xml   # Android清单文件
├── res/                  # 资源文件
│   ├── mipmap-xxxhdpi/  # 应用图标
│   └── values/          # 字符串和样式
└── keystore/            # 签名密钥（发布时需要）
```

## 打包命令

### 开发版APK（调试）
```bash
flet build apk --dev
```

### 发布版APK
```bash
flet build apk --release \
  --keystore=android/keystore/triz-app.keystore \
  --keystore-password=your_password \
  --key-alias=triz-app \
  --key-password=your_password
```

### 自定义包名
```bash
flet build apk --package-name com.innovatetriz.assistant
```

### 指定版本信息
```bash
flet build apk \
  --build-number 1 \
  --build-name 1.0.0 \
  --version-code 1 \
  --version-name 1.0.0
```

## 注意事项

1. **Android SDK**: 打包需要安装Android SDK和Flutter SDK
2. **API级别**: 最低支持Android 5.0 (API Level 21)
3. **签名密钥**: 发布版本需要签名密钥，开发版本使用默认调试密钥

## 环境要求

- Android SDK 21+
- Flutter SDK (Flet需要)
- Python 3.10+

## 参考文档

- [Flet Android打包文档](https://flet.qiannianlu.com/zh/docs/publish/android)
- [Android应用签名](https://developer.android.com/studio/publish/app-signing)