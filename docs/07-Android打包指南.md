# Android 打包指南（Vue + FastAPI）

> 目标：在 `feature/mobile-packaging` 分支上完成 Android APK 打包，包含前端 Vue 页面与后端 FastAPI 服务。

## 1. 分支准备
在仓库根目录执行：

```bash
git checkout feature/mobile-packaging
git merge --no-ff feature/windows-packaging
```

如果提示已合并（`Already up to date`）即可进入下一步。

## 2. 环境要求
- Node.js 20+
- Python 3.11+
- Android Studio（建议 Giraffe/Koala 及以上）
- Android SDK（建议 API 34）
- JDK 21

如果使用 Clash（`127.0.0.1:7890`），在构建前先设置：

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7890"
$env:HTTPS_PROXY="http://127.0.0.1:7890"
$env:ALL_PROXY="socks5://127.0.0.1:7890"
$env:GRADLE_OPTS="-Dhttp.proxyHost=127.0.0.1 -Dhttp.proxyPort=7890 -Dhttps.proxyHost=127.0.0.1 -Dhttps.proxyPort=7890"
```

也可以在 `frontend/` 目录一键写入当前用户环境变量（持久化）：

```bash
npm run mobile:env:setup
```

并确保 Android SDK 路径已配置（`frontend/android/local.properties`）：

```properties
sdk.dir=C:\\Users\\<你的用户名>\\AppData\\Local\\Android\\Sdk
```

若文件不存在，可在 `frontend/android/` 下手动创建。

## 3. 前端打包为 Android 容器（Capacitor）

在 `frontend/` 目录执行：

```bash
npm install
npm install @capacitor/core @capacitor/cli @capacitor/android --save-dev
npx cap init PomodoroTable com.pomodorotable.app --web-dir=app-dist
npx cap add android
```

然后使用项目脚本构建并同步：

```bash
npm run mobile:sync
npm run mobile:open
```

说明：
- `npm run mobile:sync` 会按顺序执行：前端构建 -> 后端 Python 同步 -> Python 依赖同步 -> Capacitor 同步。
- 后端同步脚本：`frontend/scripts/sync-mobile-backend.cjs`。
- Python 依赖同步脚本：`frontend/scripts/sync-mobile-deps.cjs`（写入 `frontend/android/app/src/main/python/vendor`）。

## 4. 将 FastAPI 内嵌进 Android 应用

推荐方式：在 `frontend/android` 工程内使用 Chaquopy 运行 Python，再启动 Uvicorn。

### 4.1 安装 Chaquopy（Gradle）
本仓库已在以下文件完成配置：
- `frontend/android/build.gradle`
- `frontend/android/app/build.gradle`
- `frontend/android/app/src/main/java/com/pomodorotable/app/MainActivity.java`
- `frontend/android/app/src/main/python/mobile_server.py`
- `frontend/requirements-mobile.txt`

建议 Python 依赖最小集合：
- `fastapi`
- `uvicorn`
- `pydantic`

业务代码会由脚本自动复制到 Android Python 源目录：
- 来源：`backend/main.py` 与 `backend/app/*.py`
- 目标：`frontend/android/app/src/main/python/`

### 4.2 Android 启动时拉起 FastAPI
在 Android 启动逻辑（`MainActivity` 或 Application）中：
1. 启动 Python runtime。
2. 以子线程方式运行 `uvicorn.run(app, host="127.0.0.1", port=8000)`。
3. 等待服务可访问后再加载 WebView 页面。

### 4.3 前端 API 地址
保持前端请求地址为：
- `http://127.0.0.1:8000`

这样 WebView 与内嵌 FastAPI 可在同一设备内通信。

## 5. Android 打包（Debug / Release）

在 Android Studio 中：
1. 选择 `Build > Build Bundle(s) / APK(s) > Build APK(s)` 生成 debug APK。
2. 选择 `Build > Generate Signed Bundle / APK` 生成签名 release APK/AAB。

命令行方式（在 `frontend/`）：

```bash
npm run mobile:sync
npm run mobile:build:debug
npm run mobile:build:release
npm run mobile:bundle:release
```

若本机默认 Java 不是 21，请先在当前终端设置：

```powershell
$env:JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-21.0.10.7-hotspot"
$env:Path="$env:JAVA_HOME\bin;$env:Path"
```

产物路径：
- Debug APK：`frontend/android/app/build/outputs/apk/debug/app-debug.apk`
- Release APK：`frontend/android/app/build/outputs/apk/release/app-release.apk`
- Release AAB：`frontend/android/app/build/outputs/bundle/release/app-release.aab`

### 5.1 生成“可分发安装包”（签名 Release）
如果你们要给团队外部直接安装，建议使用签名后的 `app-release.apk`：

1. 在 `frontend/android/` 目录创建 keystore：

```powershell
New-Item -ItemType Directory -Force -Path .\keystore
keytool -genkeypair -v -keystore .\keystore\pomodoro-release.jks -alias pomodoro -keyalg RSA -keysize 2048 -validity 10000
```

2. 复制 `frontend/android/keystore.properties.example` 为 `frontend/android/keystore.properties`，填写真实密码。

3. 重新打包：

```bash
npm run mobile:build:release
```

完成后得到可分发安装包：
- `frontend/android/app/build/outputs/apk/release/app-release.apk`

若 Gradle 下载慢，可先设置代理再打包（PowerShell）：

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7890"
$env:HTTPS_PROXY="http://127.0.0.1:7890"
npm run mobile:build:debug
```

## 6. 发布前检查清单（Android）
- 应用启动后可访问 `http://127.0.0.1:8000/` 并返回健康检查。
- 待办新增、番茄钟倒计时、统计页更新正常。
- 锁屏页在 Android UI 下全屏展示且不出现背景滚动。
- 离线模式下（无公网）核心本地功能可用。
- Release 包签名正确，可安装到真机。

## 7. Android 包测试方式（推荐）

### 7.1 用 Android Studio 测试（推荐）
可以，推荐优先使用 Android Studio：
1. 执行 `npm run mobile:sync`。
2. 执行 `npm run mobile:open` 打开 Android 工程。
3. 连接真机（USB 调试）或启动模拟器。
4. 在 Android Studio 点击 Run，安装并启动应用。
5. 验证：待办新增、倒计时、统计页、`http://127.0.0.1:8000/` 健康检查。

### 7.2 用 adb 直接安装 APK
先确认设备在线：

```bash
adb devices
```

安装 debug 包：

```bash
adb install -r frontend/android/app/build/outputs/apk/debug/app-debug.apk
```

安装 release 包：

```bash
adb install -r frontend/android/app/build/outputs/apk/release/app-release.apk
```

## 8. 常见问题

### 7.1 启动后前端请求不到后端
- 检查 Android 端 Python 服务是否已启动。
- 确认监听地址是 `127.0.0.1:8000`。
- 确认网络安全策略允许应用访问本地回环地址。

### 7.2 打包时 Python 依赖安装失败
- 优先精简依赖，先只保留 FastAPI 主链路。
- 对 AI 相关依赖（如 LangChain/OpenAI）建议改为云端调用，不强制内嵌到 APK。
