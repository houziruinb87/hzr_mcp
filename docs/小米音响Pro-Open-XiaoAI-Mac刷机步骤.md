# 小米音响 Pro（OH2P）Open-XiaoAI 刷机步骤（macOS）

> 官方说明：刷机有风险，可能失去保修、变砖，请自行评估。仅适用于 **小米智能音箱 Pro（OH2P）** 和 **小爱音箱 Pro（LX06）**。

你这台电脑（Mac）**可以进行刷机**，使用项目提供的 macOS 专用刷机工具即可。

**本地环境已就绪**：刷机工具和固件已放在 **`/Users/houzirui/Documents/xiaomi`**，使用说明见该目录下的 `README.md`。下面为完整步骤说明。

---

## 一、准备

### 0. 前置条件（本机仅需做一次）

- **同意 Xcode 许可**（若从未做过）：终端执行 `sudo xcodebuild -license accept`（需输入本机密码）。
- **安装 USB 依赖**：`brew install libusb-compat`。

### 1. 硬件

- **小米智能音箱 Pro（OH2P）**
- **Type-C 数据线**：必须能传数据（不能只是充电线），用音响底部 Type-C 口连到 Mac
- 电源：音响需接电源

### 2. 固件

- 已下载到本地：**`/Users/houzirui/Documents/xiaomi/OH2P_1.58.6_patched.squashfs`**
- 若需其他版本，可到 [Releases](https://github.com/idootop/open-xiaoai/releases) 下载对应 `*_patched.squashfs`，并替换下面命令中的路径。

> 若你音箱系统版本不是 1.58.6，请先让音箱升级到该版本再刷。跨版本刷机有变砖风险。

### 3. 依赖（仅 Mac 刷机需要）

```bash
brew install libusb-compat
```

---

## 二、刷机工具（本机执行）

本地已准备好：**`/Users/houzirui/Documents/xiaomi/open-xiaoai/packages/flash-tool`**。**所有 `./flash` 命令必须在该目录下执行**：

```bash
cd /Users/houzirui/Documents/xiaomi/open-xiaoai/packages/flash-tool
./flash help
```

---

## 三、刷机步骤（顺序执行）

### 第 1 步：连接设备（关键：1 秒窗口 + 数据线）

**重要**：音箱一插电，约 **1 秒内** 会进入正常开机，刷机工具就再也扫不到设备。必须在这 1 秒内让工具执行一次 `identify`，所以**时机**和**数据线**非常关键。

1. **先确认数据线能传数据**  
   很多 Type-C 线只能充电。建议用「连手机到 Mac 能传文件」的线，或换一根明确支持数据的线。  
   （有人反馈：五芯线也不一定是数据线，换一根老的数据线后一次就成功。）

2. 音响用该 **Type-C 线** 连到 Mac，**先不要插音响电源**。

3. 在终端执行（让脚本开始循环检测）：
   ```bash
   cd /Users/houzirui/Documents/xiaomi/open-xiaoai/packages/flash-tool
   ./flash connect
   ```
   终端会不断提示「等待设备连接…」。

4. **拔掉音响电源** → 等 1～2 秒 → **立刻再插上音响电源**。  
   插电的瞬间，脚本下一次检测有可能在 1 秒内扫到设备，就会显示「✅ 设备已连接」。

5. 若一直 `can not find device`：  
   - **多试几次**：重复「拔电 → 等 1～2 秒 → 插电」，试 10～20 次，总有一次会卡准时机。  
   - **换线**：换一根确定能传数据的 Type-C 线。  
   - **换口**：Mac 有多个 USB/Type-C 口时，换一个口（优先 USB 2.0 或直连机身的口）。  
   - **关其它 USB**：关掉会占 USB 的软件（手机助手、虚拟机等），再试。

### 第 2 步：设置启动延时

```bash
./flash delay 15
```

### 第 3 步：切换启动分区

```bash
./flash switch boot0
```

### 第 4 步：刷入固件

使用本地已下载的固件路径：

```bash
./flash system system0 /Users/houzirui/Documents/xiaomi/OH2P_1.58.6_patched.squashfs
```

若报错可多试几次，有时是连接不稳定。

---

## 四、常见问题：`can not find device` / `No [WorldCup Device] device after scan`

说明：刷机工具在插电后约 **1 秒** 内才能扫到设备，超过 1 秒音箱会正常开机，工具就扫不到了。

**建议按顺序做：**

1. **先让 `./flash connect` 跑起来**（不要先插电再运行命令）。脚本会每隔约 1 秒执行一次检测。
2. **反复做「拔电 → 等 1～2 秒 → 插电」**，每次插电后看终端是否在当次检测里识别到设备。多试 10～20 次，总有一次会卡在 1 秒窗口内。
3. **确认是数据线**：用这根线连手机和 Mac，看能否传文件。只能充电的线一定会失败，可换一根确认能传数据的 Type-C 线。
4. **换 USB 口**：换到 Mac 上另一个口（若有 USB 2.0 或直连机身的口可优先试）。
5. **关掉占用 USB 的软件**：如手机助手、虚拟机等，再试。

更多同类反馈见：[open-xiaoai #6](https://github.com/idootop/open-xiaoai/issues/6)。

---

## 五、刷机完成后

1. **拔掉数据线和电源**，再重新插电开机。
2. 若开机无反应：拔电等几分钟再上电；仍不行可再刷一次，或把启动分区改为 `boot1` 恢复原系统（见官方文档）。
3. 刷机成功后，固件默认开启 **SSH**，密码：`open-xiaoai`  
   同网段下可连接（示例，IP 改成你音箱的）：
   ```bash
   ssh -o HostKeyAlgorithms=+ssh-rsa root@音箱的局域网IP
   ```

---

## 六、让音箱连到你 NAS 上的 Open-XiaoAI Server（必做，否则「小智同学」无反应）

刷机后固件**默认不会**连你的 NAS，需要你在**音箱里**写上 NAS 的地址，否则说「小智同学」会没反应。

### 6.1 确认音箱和 NAS 在同一 WiFi，并查到音箱 IP

- 在路由器管理页或 NAS 的「客户端列表」里找到音箱的 IP（设备名可能为 `MiAiSoundbox-OH2P` 等）。
- 若 NAS 和音箱同网段，也可在 NAS 上执行：`arp -a` 或 `ping MiAiSoundbox-OH2P.local`（以实际主机名为准）辅助确认。

### 6.2 在音箱上配置 NAS 地址（SSH）

1. 用 Mac 连到和音箱同一 WiFi，在终端执行（把 `音箱IP` 换成上一步查到的 IP）：
   ```bash
   ssh -o HostKeyAlgorithms=+ssh-rsa root@音箱IP
   ```
   密码：`open-xiaoai`。

2. 登录到音箱后执行（把下面的 `192.168.1.100` 换成你 NAS 的局域网 IP，端口 4399 不变）：
   ```bash
   mkdir -p /data/open-xiaoai
   echo 'ws://192.168.1.100:4399' > /data/open-xiaoai/server.txt
   ```

### 6.3 在音箱上安装并运行 Client（必做，否则唤醒词无反应）

官方说明：**仅刷机 + 写 server.txt 不够**，必须在小爱音箱上**安装并运行 Rust Client**，由 Client 把麦克风音频推到 NAS 的 Server，Server 才能做唤醒词识别。否则只有「小爱同学」有反应，「小智同学」/ 自定义唤醒词都不会有反应。

在已 SSH 登录到音箱的前提下，在音箱上执行：

1. **安装并启动 Client（会从 Gitee 下载 client 二进制，并读取 server.txt 连接 NAS）**：
   ```bash
   curl -sSfL https://gitee.com/idootop/artifacts/releases/download/open-xiaoai-client/init.sh | sh
   ```
   执行后终端会保持运行、Client 会连上 NAS；可先试一下说「爸爸最帅」是否有反应。

2. **开机自启（推荐）**：让音箱每次重启后自动连上 NAS，在音箱上执行：
   ```bash
   curl -L -o /data/init.sh https://gitee.com/idootop/artifacts/releases/download/open-xiaoai-client/boot.sh
   reboot
   ```
   重启后 Client 会自动启动并读取 `server.txt` 连接 NAS。

配置并运行 Client 后，音箱才会把音频发到 NAS，NAS 上的唤醒词（如「爸爸最帅」）才会生效。

### 6.4 与 xiaozhi README 一致的其他说明

以下内容对应 [Open-XiaoAI x 小智 AI 说明](https://github.com/idootop/open-xiaoai/blob/main/examples/xiaozhi/README.md)：

- **打断小智回答**：直接说「小爱同学」即可打断当前 AI 回答。
- **Server 刚启动**：Docker 启动后需加载 VAD/KWS 模型，约 **30 秒** 后再试唤醒词更稳。
- **唤醒词不灵敏**：可在 NAS 的 `config.py` 里把 `vad.threshold` 调低（如 `0.05`），重启 Open-XiaoAI Server 容器后再试。
- **用自建 xiaozhi-esp32-server**：若不用小智云、改走自己 NAS 上的小智后端，需在 `config.py` 里改 `OTA_URL`、`WEBSOCKET_URL` 为你的服务地址（例如 `ws://NAS_IP:8000/xiaozhi/v1/` 等），并重启容器。
- **模型文件**：若自己编译运行 Server 需从 [Release VAD+KWS 模型](https://github.com/idootop/open-xiaoai/releases/tag/vad-kws-models) 下载并解压到 `xiaozhi/models`；用 Docker 镜像 `idootop/open-xiaoai-xiaozhi` 一般已内置，无需单独下载。

---

## 参考链接

- **xiaozhi 示例说明（必读）**：<https://github.com/idootop/open-xiaoai/blob/main/examples/xiaozhi/README.md>
- Client 端安装（Rust 补丁）：<https://github.com/idootop/open-xiaoai/blob/main/packages/client-rust/README.md>
- 官方刷机文档：<https://github.com/idootop/open-xiaoai/blob/main/docs/flash.md>
- Mac 刷机工具说明：<https://github.com/idootop/open-xiaoai/blob/main/packages/flash-tool/README.md>
- 连接不上设备时的排查：<https://github.com/idootop/open-xiaoai/issues/6#issuecomment-2815632879>
