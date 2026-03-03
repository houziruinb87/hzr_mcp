# 小爱 + NAS 完整部署指南：先 XiaoMusic，再 MiGPT-Next

按顺序完成：**第一步部署 XiaoMusic**（小爱播 NAS 音乐/故事、续播），**第二步部署 MiGPT-Next**（小爱语音控制加湿器、新风机等，调用 hzr_mcp/bridge_server）。

适用设备：**小米音响 Pro（OH2P）**；NAS 以**极空间**为例，其他 NAS 可对照调整路径与界面。

---

# 第一步：部署 XiaoMusic（播 NAS 音乐与故事）

## 1.1 能做什么

- **音乐**：语音「播放歌曲 xxx」→ 本地音乐库或 yt-dlp 下载后播放。
- **本地故事/听书**：把 mp3/m4a 等放进音乐库（或单独子文件夹当「专辑」），说「播放歌曲 小猪佩奇的故事」或「播放歌单 睡前故事」即可；官方推荐听书用 [epub2mp3](https://github.com/hanxi/epub2mp3) 把 epub 转成 mp3 再放进 music 目录。
- **续播（继续播放）**：在设置里开启「启用继续播放」后，会**按播放列表（歌单）记录上次播到哪一首**，下次说「播放歌单 某某」时从上次那首继续，而不是从头。注意：这是**列表级**续播（记住第几首），不是单曲内的「断点到某一秒」。
- **专辑/文件夹当歌单**：music 目录下的**子文件夹名**会变成「歌单名」，可以说「播放歌单 睡前故事」「播放歌单 收藏」。

## 1.2 极空间 Docker 部署（详细步骤）

### 1.2.1 拉取镜像

- **有科学上网**：Docker → 镜像 → 搜索 `hanxi/xiaomusic` → 选第一个 → 下载，版本选 `latest`。
- **国内**：Docker → 镜像 → 自定义拉取，输入 `m.daocloud.io/docker.io/hanxi/xiaomusic` 或 `docker.hanxi.cc/hanxi/xiaomusic` → 拉取。

### 1.2.2 创建容器并挂载目录

1. 在极空间里先建好两个目录（示例）：
   - 音乐库：如 `存储池/音乐` 或 `存储池/docker/xiaomusic/music`（把你现有的音乐/故事 mp3 放这里）。
   - 配置目录：如 `存储池/docker/xiaomusic/conf`（给 xiaomusic 存配置和数据库，持久化）。
2. 本地镜像里找到 `hanxi/xiaomusic`，**单击选中** → **添加到容器**。
3. 在「创建容器」里：
   - **文件夹路径**：只配置这两项，**不要**添加主题目录等多余映射。
     - 宿主机「音乐」目录 → 装载路径 **`/app/music`**
     - 宿主机「配置」目录 → 装载路径 **`/app/conf`**
   - **端口**：本地端口改成与极空间不冲突的，例如 **58090**（容器端口保持 8090 不变）。
   - **环境**：添加 `XIAOMUSIC_HOSTNAME` = **极空间的局域网 IP**（如 `192.168.1.100`），不要写端口。不要在这里填账号密码。
4. 应用并启动容器。

### 1.2.3 Web 端首次配置

1. 关闭本机代理，浏览器打开 **http://极空间IP:58090**（例如 `http://192.168.1.100:58090`）。
2. 进入 **设置**，必填：
   - **小米账号**、**小米密码**（与音箱绑定的账号；账号是小米 ID，非手机号，在手机 设置-个人中心 可查）。
   - **XIAOMUSIC_HOSTNAME(IP或域名)**：填极空间 IP，**不要带端口**。
   - **外网访问端口**：填你映射的端口，如 **58090**（与上面本地端口一致）。
3. 保存后应出现**设备列表**，选择你的**小米音响 Pro（OH2P）**。
4. 回到首页，确认设备已选，即可用语音或网页试播。

**常见问题**：设备不出现时，确认绑定音箱的是**创建者**账号而非家庭管理员；网络用 bridge 即可；若提示 hostname/端口不匹配，检查设置里 IP 与端口是否与访问地址一致。详见 [极空间安装教程 #297](https://github.com/hanxi/xiaomusic/issues/297)、[FAQ #99](https://github.com/hanxi/xiaomusic/issues/99)。

## 1.3 本地故事与专辑续播

- **故事/听书**：在 music 下建子文件夹，如 `睡前故事`，把每集的 mp3/m4a 放进去。对小爱说「播放歌单 睡前故事」即可；说「播放歌曲 小猪佩奇的故事」会走搜索（本地或 yt-dlp）。若用 epub 听书，可用 [epub2mp3](https://github.com/hanxi/epub2mp3) 转成 mp3 再放入 music 某文件夹。
- **续播**：在 Web 设置里打开 **「启用继续播放」**。之后每个「歌单」（即每个子文件夹/列表）会记住上次播到哪一首，下次「播放歌单 xxx」会从该首继续。部分机型可能存在兼容问题，若有异常可先关闭该选项。
- **刷新列表**：新增或删除文件后，可说「小爱同学，刷新列表」，或在设置里开启「文件监控」自动刷新。

---

# 第二步：部署 MiGPT-Next（小爱控制加湿器、新风机等）

## 2.1 作用

MiGPT-Next 拦截小爱的对话：当你说「小爱同学，请 xxx」时，请求会发到 MiGPT-Next，可在 **onMessage** 里识别「打开加湿器」「关新风机」等，然后请求你 NAS 上的 **bridge_server**（或直接调脚本），从而执行 hzr_mcp 里的控制逻辑。小爱用 TTS 播报回复。

## 2.2 前置条件

- **bridge_server** 已在 NAS 上运行（见 `homeassistant/bridge_server.py`），并已提供例如：
  - `http://NAS的IP:8765/jiashiqi/on`、`/jiashiqi/off`
  - 新风机：`/xinfengji/on`、`/xinfengji/off`、`/xinfengji/toggle`（内部执行 airproce 脚本，后台运行，立即返回）。
- NAS 与小米音响在同一局域网，小爱已能联网。

**若提示「本次登录需要验证码，请使用 passToken 重新登录」**：在 `config.js` 的 `speaker` 里增加 `passToken`。获取方式：Chrome 打开 https://account.xiaomi.com 登录小米账号 → F12 → Application → Cookies → 找到 `passToken` 复制其值填入配置；passToken 相当于密码，请勿泄露。详见 [MiGPT-Next #4](https://github.com/idootop/migpt-next/issues/4)。

## 2.3 部署方式（二选一）

### 方式 A：Docker 运行（推荐）

**一键脚本（本机与 NAS 同网时）**：在仓库根目录执行 `bash docs/deploy_migpt_next_on_nas.sh`，会在 NAS 的 `/data_n003/data/udata/real/18510411307/docker/MiGPT-Next` 下创建目录、上传 `config.js`、拉镜像并启动容器。完成后到 NAS 上编辑该目录下的 `config.js` 填写小米账号与设备名，并执行 `sg docker -c 'docker restart migpt-next'`。

**手动步骤**：

1. 克隆 MiGPT-Next：
   ```bash
   git clone https://github.com/idootop/migpt-next.git
   cd migpt-next/apps/example
   ```
2. 复制并编辑配置：
   ```bash
   cp config.js.example config.js   # 若无 example 则参考仓库内 config 示例
   ```
3. 编辑 `config.js`，至少填写：
   - `speaker.userId`、`speaker.password`（小米 ID 与密码，与音箱绑定）
   - `speaker.did`：设备名，与米家/小爱里显示的**一致**（如「小米音响 Pro」或你改过的名字）
   - 若登录报「需要验证码」，在 `speaker` 中增加 `passToken`（从 account.xiaomi.com 的 Cookies 中复制，见上节说明）
   - `openai`：若要用大模型回复，填 apiKey、baseURL、model；若只做设备控制可先不配或随便填一个占位
4. 在 **onMessage** 里加入「设备控制」逻辑，见下节。
5. 启动容器（在 `apps/example` 目录）：
   ```bash
   docker run -it --rm -v $(pwd)/config.js:/app/config.js idootop/migpt-next:latest
   ```
   若在极空间用 Docker 图形界面：创建容器时挂载 `config.js` 到 `/app/config.js`，镜像 `idootop/migpt-next:latest`，保持与 XiaoMusic 不同端口（MiGPT-Next 本身不占 HTTP 端口，只是连小米服务）。

### 方式 B：Node.js 直接运行

```bash
cd migpt-next
pnpm install
# 编辑 apps/example/config.js 后：
pnpm run dev   # 或按仓库说明启动 example
```

## 2.4 onMessage 里调用 bridge_server（示例）

在 `config.js` 的 **onMessage** 中，根据用户文字匹配关键词，请求你 NAS 上的 bridge_server：

```javascript
async onMessage(engine, msg) {
  const text = (msg.text || '').trim();
  const NAS_IP = '192.168.1.100';  // 改成你极空间 IP
  const BRIDGE = `http://${NAS_IP}:8765`;

  // 加湿器
  if (/打开加湿器|开启加湿器|加湿器开/.test(text)) {
    try {
      await fetch(`${BRIDGE}/jiashiqi/on`, { method: 'POST' });
      return { text: '好的，已打开加湿器。' };
    } catch (e) {
      return { text: '加湿器控制失败，请稍后再试。' };
    }
  }
  if (/关闭加湿器|加湿器关/.test(text)) {
    try {
      await fetch(`${BRIDGE}/jiashiqi/off`, { method: 'POST' });
      return { text: '好的，已关闭加湿器。' };
    } catch (e) {
      return { text: '加湿器控制失败，请稍后再试。' };
    }
  }

  // 新风机（bridge_server 已提供 /xinfengji/on、/xinfengji/off，内部为同一脚本「点击开关」切换状态）
  if (/打开新风机|开启新风|开新风机/.test(text)) {
    try {
      await fetch(`${BRIDGE}/xinfengji/on`, { method: 'POST' });
      return { text: '好的，已发送新风机控制指令，正在执行，请稍候。' };
    } catch (e) {
      return { text: '新风机控制失败，请稍后再试。' };
    }
  }
  if (/关闭新风机|关闭新风|关新风机/.test(text)) {
    try {
      await fetch(`${BRIDGE}/xinfengji/off`, { method: 'POST' });
      return { text: '好的，已发送关闭新风机指令，正在执行，请稍候。' };
    } catch (e) {
      return { text: '新风机控制失败，请稍后再试。' };
    }
  }

  // 其他交给 AI 或默认回复
  return null;  // 返回 null 表示不拦截，走原有逻辑
}
```

注意：Node 环境里用 `fetch` 需要 Node 18+；若在旧环境可用 `axios` 或 `http.request`。把 `NAS_IP` 和端口改成你实际值。新风机接口已在 bridge_server 中实现（`/xinfengji/on`、`/xinfengji/off`），会后台执行 airproce 脚本，小爱会立即得到回复。

## 2.5 与 XiaoMusic 并存

- XiaoMusic 和 MiGPT-Next 使用**不同唤醒/触发方式**：XiaoMusic 响应「播放歌曲」「播放歌单」等；MiGPT-Next 响应「小爱同学，请 xxx」。同一台音箱可同时配置两个服务（两个应用连同一台设备），一般不会互相抢话。若遇抢答，可把 MiGPT-Next 的触发词设成「请」或固定句式，减少与点歌口令重叠。

---

# 小结

| 步骤 | 容器/服务 | 作用 |
|------|-----------|------|
| 第一步 | **XiaoMusic** | 小爱播 NAS 音乐与本地故事，支持按歌单续播、专辑文件夹当歌单 |
| 第二步 | **MiGPT-Next** | 小爱说「请打开加湿器」等 → onMessage 调 bridge_server → 执行 hzr_mcp 脚本（加湿器、新风机等） |

- 本地故事：music 目录下建文件夹放 mp3，说「播放歌单 文件夹名」；续播在设置里开「启用继续播放」即可按列表续播。
- 详细 XiaoMusic 说明见：`docs/小爱播放NAS音乐-XiaoMusic部署.md`。
- bridge_server 与 HA 用法见：`homeassistant/README.md`。
