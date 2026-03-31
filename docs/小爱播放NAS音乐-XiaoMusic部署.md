# 小爱播放 NAS 音乐：XiaoMusic 容器部署

不刷机情况下，让**小爱音箱 / 小米音响 Pro（OH2P）** 用语音播放你 NAS 上的音乐库，并支持「没有就自动下载」的玩法。

推荐在 NAS 上跑 **XiaoMusic** 容器：[hanxi/xiaomusic](https://github.com/hanxi/xiaomusic)。

---

## 一、XiaoMusic 能做什么

- **语音点歌**：对小爱说「播放歌曲 周杰伦 晴天」→ 优先从 NAS 音乐库找，没有则用 yt-dlp 下载后播放。
- **本地音乐库**：支持 mp3、flac、wav、ape、ogg、m4a，音乐文件放在 NAS 挂载目录即可。
- **本地故事 / 听书**：把故事、有声书 mp3/m4a 放进音乐库（或子文件夹），说「播放歌曲 小猪佩奇的故事」或「播放歌单 睡前故事」即可。听书推荐配合 [epub2mp3](https://github.com/hanxi/epub2mp3) 把 epub 转成 mp3 再放入 music 目录。
- **续播（继续播放）**：在 Web 设置里开启 **「启用继续播放」** 后，会**按播放列表（歌单）记录上次播到哪一首**，下次说「播放歌单 xxx」时从上次那首继续。这是**列表级**续播（记住第几首），不是单曲内的「断点到某一秒」；部分机型可能有兼容问题，可先试再决定是否长期开启。
- **专辑/文件夹当歌单**：music 目录下的**子文件夹名**即「歌单名」，可说「播放歌单 睡前故事」「播放歌单 收藏」。适合把某张专辑或某套故事放在一个文件夹里连续播、续播。
- **歌单 / 收藏**：播放歌单、收藏歌单、上一首/下一首、单曲循环/全部循环/随机播放。
- **你的设备**：OH2P（XIAOMI 智能音箱 Pro）在[官方支持列表](https://github.com/hanxi/xiaomusic#-设备支持)内。

---

## 二、在 NAS 上跑什么容器

就一个：**XiaoMusic**。

| 项目 | 说明 |
|------|------|
| **镜像** | `hanxi/xiaomusic`（国内可用 `docker.hanxi.cc/hanxi/xiaomusic`） |
| **端口** | 宿主机 58090 → 容器 8090，浏览器访问 `http://NAS的IP:58090` 做配置 |
| **挂载** | 两个目录：音乐目录、配置目录 |

无需再单独跑 DLNA；若你只想「手机选歌投送到小爱」可以额外跑 DLNA，但语音直接点 NAS 歌用 XiaoMusic 更合适。

---

## 三、极空间 Docker 部署示例

在极空间上创建目录（按你实际存储改路径，例如 `docker/xiaomusic`），再建 `docker-compose.yml`：

```yaml
services:
  xiaomusic:
    image: hanxi/xiaomusic
    # 国内拉不动可改为: docker.hanxi.cc/hanxi/xiaomusic
    container_name: xiaomusic
    restart: unless-stopped
    ports:
      - 58090:8090
    volumes:
      - /path/to/your/music:/app/music    # NAS 上的音乐库目录
      - /path/to/your/xiaomusic_conf:/app/conf  # 配置与数据库，持久化
```

**请把路径改成你极空间上的实际路径**，例如：

- 音乐库：极空间里你存音乐的共享文件夹，如 `/volume1/音乐` 或你 Docker 里挂载的路径。
- 配置目录：单独一个给 xiaomusic 用的目录，如 `/volume1/docker/xiaomusic/conf`。

若极空间 Docker 用的是「卷」或「存储空间」的路径，按界面里显示的挂载路径写即可。

启动：

```bash
cd /path/to/docker/xiaomusic
docker compose up -d
```

然后浏览器打开 **http://极空间IP:58090**。

---

## 四、首次配置（Web 页面）

1. 打开 **http://NAS的IP:58090**。
2. 在设置页填写**小米账号、密码**（与小爱音箱绑定的账号），保存后会自动拉取设备列表。
3. 选择要使用的小爱设备（你的 OH2P）。
4. 音乐目录已在 compose 里挂载为 `/app/music`，把 NAS 上的音乐放进对应宿主机目录即可被扫描。
5. 若需「没有就下载」，在设置里开启相关选项（依赖 yt-dlp，镜像内一般已带）。
6. **打开【语音口令】/【获取对话记录】**：设置页或主页有「语音口令」或「获取对话记录」开关，**必须打开**语音点歌才会走 XiaoMusic；关掉时只有网页/后台点播有效。首次在后台保存设备（did）后建议**重启一次容器**。

带 `*` 的为必填，其余可保持默认。详细说明见 [XiaoMusic 文档](https://xdocs.hanxi.cc/)、[FAQ](https://github.com/hanxi/xiaomusic/issues/99)。

---

## 五、常用语音口令（对小爱说）

**⚠️ 语音必须带「播放歌曲」才会走 XiaoMusic**：对小爱说「播放 xxx」或「播放音乐」不会走本地/ NAS，会被小爱自带音乐（如 QQ 音乐）处理。**必须说「播放歌曲 + 歌名」**，例如「小爱同学，播放歌曲 誓要入刀山」。口令前缀可在 XiaoMusic 设置里改，默认是【播放歌曲】。

| 口令示例 | 说明 |
|----------|------|
| **播放歌曲** 誓要入刀山 / 周杰伦 晴天 | 按歌名搜索并播放（本地或自动下载），**「播放歌曲」不能省** |
| 播放歌曲 小猪佩奇的故事 | 按名称搜故事/听书（本地或自动下载） |
| 播放歌单 睡前故事 | 播放 music 下「睡前故事」文件夹（专辑/故事集），可续播 |
| 上一首 / 下一首 | 切歌 |
| 播放歌单 收藏 | 播放收藏歌单 |
| 单曲循环 / 全部循环 / 随机播放 | 播放模式 |
| 加入收藏 / 取消收藏 | 收藏当前曲目 |
| 小爱同学，刷新列表 | 刷新音乐库（新增/删除文件后可用） |
| 关机 / 停止播放 | 停止播放 |

更多见 [README 功能特性](https://github.com/hanxi/xiaomusic#-功能特性)。

---

## 五.1 同名多首、按歌手区分

当 music 里有多首同歌名不同歌手（如 `刘德华_誓要入刀山.mp3` 和 `郑少秋_誓要入刀山.mp3`）时，**在口令里同时说出歌手和歌名**，有助于命中正确那一首。例如：

- **「小爱同学，播放歌曲 郑少秋 誓要入刀山」**
- 或 **「小爱同学，播放歌曲 郑少秋演唱的誓要入刀山」**

XiaoMusic 会按关键词在本地列表里做匹配；文件名或元数据里同时包含「郑少秋」和「誓要入刀山」的那条更容易被选中。若仍播错，可：
- **用文件夹区分**：如 `music/郑少秋/誓要入刀山.mp3`、`music/刘德华/誓要入刀山.mp3`，说「播放歌曲 郑少秋 誓要入刀山」或「播放歌单 郑少秋」再选；
- **补全 ID3 标签**：用 Music Tag 等工具把 MP3 的「歌手(Artist)」「标题(Title)」写对，部分版本会按元数据搜索，识别更准。

---

## 五.2 本地故事与续播说明

- **本地故事**：在 music 下建子文件夹（如 `睡前故事`、`西游记`），把每集 mp3/m4a 放进去。说「播放歌单 睡前故事」即按列表播放；说「播放歌曲 某某故事」会按歌名搜索（本地或 yt-dlp）。epub 听书可用 [epub2mp3](https://github.com/hanxi/epub2mp3) 转 mp3 再放入目录。
- **续播**：设置里打开 **「启用继续播放」**。每个歌单（子文件夹或列表）会记住**上次播到第几首**，下次「播放歌单 xxx」从该首继续。不是单曲内的「断点到第几秒」。
- **刷新**：新增或删除文件后，可说「小爱同学，刷新列表」，或开启设置中的「文件监控」自动刷新。

---

## 六、与 hzr_mcp / 其他容器

- XiaoMusic 独立运行，不依赖 hzr_mcp。
- 可与 MiGPT-Next、Home Assistant、bridge_server 等一起跑在同一台 NAS 上，各用各的端口即可。
- 若要做「小爱播完某首歌后触发脚本」等联动，可看 XiaoMusic 的插件/API 或 Webhook 能力（见官方文档与 Issues）。

---

## 七、链接与后续

- 项目与支持型号：[hanxi/xiaomusic](https://github.com/hanxi/xiaomusic)
- 文档：[xdocs.hanxi.cc](https://xdocs.hanxi.cc/)
- 常见问题：[FAQ #99](https://github.com/hanxi/xiaomusic/issues/99)
- 极空间图文教程：[xiaomusic 极空间安装 #297](https://github.com/hanxi/xiaomusic/issues/297)
- **先 XiaoMusic 再 MiGPT-Next 的完整步骤**（小爱控制加湿器、新风机等）：见同目录 **`小爱与NAS完整部署指南-XiaoMusic与MiGPT-Next.md`**。
