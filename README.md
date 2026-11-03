# Via Safari

将 **Via 浏览器国内版（`mark.via`）** 的桌面名称和图标改成 Safari，同时保留 Via 的原生更新界面，并把更新检测地址定向到本仓库维护的版本 JSON。

> 非 Via / Apple 官方项目。仅修改应用标识、Launcher 图标、更新配置 URL 和版本码；不保证所有未来上游版本继续兼容。

## 发布流程

- 每周二、周五 UTC 04:27（北京时间 12:27）运行一次**轻量检查**，从 Via 官方读取 `latest_cn.json`。
- 如果同版本的 Release 已经存在，立即退出，不下载 APK、不启动反编译/签名流程。
- 有新版本时从 **Via 官网** 下载 `via-release-cn.apk`，用 Apktool 反编译、重设 Launcher 名称/图标、修改更新源、同步版本码。
- 使用你的固定 APK 签名密钥签名，并验证 APK 包名和安装包；发布 `Safari.apk` 到 GitHub Releases。
- 发布完成后才更新仓库根目录的 `latest_cn.json`，让现有 Via Safari 原生检查更新界面提示你安装新版。
- 也支持在 [Actions](../../actions/workflows/via-safari.yml) 中手动运行；没有新版本时不会重复构建。

上游更新配置： https://res.viayoo.com/v1/latest_cn.json  
官方 APK： https://res.viayoo.com/v1/via-release-cn.apk  
本项目更新配置： https://raw.githubusercontent.com/Scluzlep/via-safari/main/latest_cn.json

## 首次使用：设置签名

**固定签名很重要**：不能每次 Action 生成新的随机证书。生成一次 PKCS#12 密钥，并把它以 GitHub Actions Secrets 形式保存（绝对不要把私钥上传到公开仓库）。

在安装 Java JDK、GitHub CLI 并登录 `gh auth login` 后执行：

```bash
# 把下方密码改成自己的、只保存在本地的强密码
export SIGNING_PASSWORD='替换为自己的强密码'
keytool -genkeypair -v -keystore safari.p12 -storetype PKCS12 \
  -alias safari -keyalg RSA -keysize 3072 -validity 36500 \
  -storepass "$SIGNING_PASSWORD" -keypass "$SIGNING_PASSWORD" \
  -dname "CN=Via Safari Mod"
base64 -w0 safari.p12 | gh secret set SIGNING_KEYSTORE_BASE64 -R Scluzlep/via-safari
printf %s "$SIGNING_PASSWORD" | gh secret set SIGNING_PASSWORD -R Scluzlep/via-safari
unset SIGNING_PASSWORD
```

macOS 的 `base64` 如不支持 `-w0`，改为 `base64 < safari.p12 | tr -d '\\n' | gh secret set ...`。

需要在仓库 Actions 的 Secrets 中存在：
- `SIGNING_KEYSTORE_BASE64`：PKCS#12 文件的单行 Base64 内容
- `SIGNING_PASSWORD`：密钥库和 `safari` 别名私钥密码（两者相同）

密钥应在你自己的离线环境备份。由于用户的系统可能利用核心破解绕过系统签名校验，覆盖官方 Via 是否成功取决于设备配置；**不建议仅依赖该绕过机制替代固定签名**。首次安装前请备份书签和设置。

## 图标来源

`assets/safari26.png` 为 [kkkik/iOS26](https://github.com/kkkik/iOS26) 提供的 iOS 26 Safari 图标提取版（来自其 `com.apple.mobilesafari-large.png`）。相关商标和图标权利属于其原权利人。本项目并非 Apple 的产品。

## 设计与防护

- 修改代码使用 **smali 中固定更新 URL** 定位，不绑定混淆类名；如果官方改变接口，直接拒绝发布而不是输出不受控包。
- 构建后检查 URL 替换、manifest 的 Launcher 标签与版本码、APK 签名，并校验原版下载的 MD5（若官方配置提供）。
- 更新 JSON 的 `url` 指向已发布版本的 Release APK，`md5` 是 **修改后的 APK** 的摘要。
- 不提交第三方 APK 到 Git 历史；生成的二进制仅存在于 Release。
- `latest_cn.json` 只有在成功发布 Release 后才更新；如果发布失败，用户仍会继续收到上一个可用版本。
