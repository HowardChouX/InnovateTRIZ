---
name: build-android-apk
description: Use when asked to build the Android APK for InnovateTRIZ app, including debug and release builds.
---

## Prerequisites

- JDK 17+ (installed automatically by Flet to `~/java/` on first build)
- Android SDK (configured via environment or Flet defaults)
- All Python dependencies installed

## Build Commands

### Debug APK (recommended for testing)

```bash
cd /home/chou/triz-app && flet build apk
```

### Debug APK with ABI split (smaller file size)

```bash
cd /home/chou/triz-app && flet build apk --split-per-abi
```

### Release AAB (for Play Store)

```bash
cd /home/chou/triz-app && flet build aab
```

## Output Location

- Android APK: `build/app/outputs/flutter-apk/`
- Android AAB: `build/app/outputs/bundle/`

## Build Options

| Flag | Purpose |
|------|---------|
| `--split-per-abi` | Split APK by ABI (arm64-v8a, armeabi-v7a, x86_64) |
| `--android-signing-key-store <path>` | Specify signing keystore |
| `--android-signing-key-alias <alias>` | Key alias |
| `--flutter-sdk <path>` | Use specific Flutter SDK |

## Verification

After build:
1. Check APK size: `ls -lh build/app/outputs/flutter-apk/`
2. Install on device: `adb install build/app/outputs/flutter-apk/app-debug.apk`
3. Verify all 3 tabs work (Matrix, Principles, Settings)

## Troubleshooting

| Issue | Solution |
|-------|---------|
| Build fails | Verify JDK 17: `java -version` |
| Missing wheel | Binary package lacks Android wheel, see `docs_flet/publish/android.md` |
| Signing issues | Debug builds use debug key; release needs keystore |
| First build slow | Auto-downloads JDK/Android SDK, be patient |

## Reference

- Flet Android publishing guide: `/home/chou/triz-app/docs_flet/publish/android.md`
