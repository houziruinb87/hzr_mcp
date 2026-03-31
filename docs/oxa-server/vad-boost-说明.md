# VAD boost 配置说明（小爱录音音量放大）

## 配置项

在 `config.py` 的 `APP_CONFIG["vad"]` 中增加：

```py
"vad": {
    # 小爱录音音量较小，需放大（见 GitHub Issue 反馈）
    "boost": 150,
    "threshold": 0.10,
    "min_speech_duration": 250,
    "min_silence_duration": 500,
}
```

## 来源说明

- **社区/文档**：多处反馈小爱音箱录音音量偏小，导致唤醒或识别不佳，建议在配置中增加 `boost`（如 150）做放大。
- **idootop/open-xiaoai**：当前主仓库 [examples/xiaozhi](https://github.com/idootop/open-xiaoai/tree/main/examples/xiaozhi) 的 `xiaozhi/services/audio/vad/__init__.py` 只读取 `threshold`、`min_speech_duration`、`min_silence_duration`，**未读取 `boost`**；README 与常见问题中未单独提及 boost。
- **oxa-server**：[pu-007/oxa-server](https://github.com/pu-007/oxa-server) 等增强配置中推荐包含类似选项。
- **结论**：保留 `"boost": 150` 与注释「小爱录音音量较小，需放大（见 GitHub Issue 反馈）」作为推荐配置；若后续官方或 Docker 镜像支持该参数即可生效，当前未支持时不会报错（多出的 key 会被忽略）。

## 已同步位置

- 本地仓库：`xiaomi/open-xiaoai/examples/xiaozhi/config.py` 已加入上述 `boost` 与注释。
- 部署用：`gitlab_hzr/hzr_mcp/docs/oxa-server/config_official_boost.py` 与 NAS 上使用的 `config.py` 保持一致（含 boost）。
