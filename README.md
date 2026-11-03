# Via Safari

将 Via 国内版（`mark.via`）的桌面名称改为 **Safari**、使用 iOS 26 Safari 图标，并将原生检查更新的配置 URL 改到本项目的公开 JSON。非官方修改版，与 Via、Apple 无关。

## 自动更新

- 每周二、周五 UTC 04:27（北京时间 12:27）仅检查一次 [Via 官方 JSON](https://res.viayoo.com/v1/latest_cn.json)。
- 若对应的 GitHub Release 已存在，立即退出。只有上游有新版本时才下载 APK、反编译、重新打包、签名、发布。
- 获取 APK：[Via 官网下载地址](https://res.viayoo.com/v1/via-release-cn.apk)
- 本地更新 JSON：[latest_cn.json](https://raw.githubusercontent.com/Scluzlep/via-safari/main/latest_cn.json)（首次成功发布后生成）。
- 下载修改版：[Releases](../../releases)
- 手动触发：[Actions](../../actions/workflows/via-safari.yml) → Run workflow。

代码定位使用 URL 字符串，不依赖混淆类名。未来版本若找不到 URL 或启动器组件则直接构建失败，避免发布错误 APK。

## 必须配置的签名 Secrets

首次运行前需要在 [Actions secrets](../../settings/secrets/actions) 设置两个仓库密钥。生成的 keystore 不要提交到 Git：

```bash
# 需要 Java JDK、GitHub CLI (gh)，先登录：gh auth login
export SIGNING_PASSWORD='换成你自己的强密码'
keytool -genkeypair -keystore safari.p12 -storetype PKCS12 \
  -alias safari -keyalg RSA -keysize 3072 -validity 36500 \
  -storepass "$SIGNING_PASSWORD" -keypass "$SIGNING_PASSWORD" \
  -dname "CN=Via Safari Mod"
base64 -w0 safari.p12 | gh secret set SIGNING_KEYSTORE_BASE64 -R Scluzlep/via-safari
printf '%s' "$SIGNING_PASSWORD" | gh secret set SIGNING_PASSWORD -R Scluzlep/via-safari
unset SIGNING_PASSWORD
```

macOS 的 `base64` 若不支持 `-w0`，可改用 `base64 < safari.p12 | tr -d '\n'`。请离线备份 `safari.p12` 和密码，所有后续更新必须用同一把私钥签名。核心破解可能允许覆盖签名不同的 APK，但是否成功取决于设备，不应据此每次更换签名。

## 设计

通过 Apktool 3.0.3 修改 Launcher 相关的 Manifest 图标与名称、更新配置地址及 APK versionCode。构建后采用 `zipalign` 和 `apksigner` 验证。Release 先发布，成功后才更新公开的 `latest_cn.json`（APK 链接及 MD5 都指向魔改版）。

图标文件 `assets/safari26.png` 来自 [kkkik/iOS26](https://github.com/kkkik/iOS26) 的 `com.apple.mobilesafari-large.png` 提取版。相关商标及图标归原权利人所有。请备份原 Via 浏览器的数据再进行覆盖安装。
