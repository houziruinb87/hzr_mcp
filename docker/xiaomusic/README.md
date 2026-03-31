# XiaoMusic Docker 部署

用于在极空间/NAS 上跑 [XiaoMusic](https://github.com/hanxi/xiaomusic)，让小爱播 NAS 音乐与故事。

## 使用前修改

编辑 `docker-compose.yml`：

1. **volumes**：把 `/path/to/your/music` 和 `/path/to/your/xiaomusic_conf` 改成你 NAS 上的真实路径（音乐目录、配置目录）。
2. **environment.XIAOMUSIC_HOSTNAME**：改成你 NAS 的局域网 IP（如 `192.168.1.100`），不要写端口。

## 启动

```bash
cd docker/xiaomusic
docker compose up -d
```

然后浏览器打开 **http://NAS的IP:58090**，在设置里填小米账号、密码、XIAOMUSIC_HOSTNAME、外网访问端口（58090），保存后选设备。

详细步骤见：**docs/极空间XiaoMusic安装实操步骤.md**。
