# airproce

通过 adb 操作 Android 手机的测试脚本。

## 使用

```bash
# 使用默认设备 192.168.1.100:5555（或通过环境变量 ADB_DEVICE_IP 覆盖）
python ensure_connect_and_select.py

# 指定 IP
python ensure_connect_and_select.py 192.168.1.100

# 指定 IP 和端口
python ensure_connect_and_select.py 192.168.1.100 5555
```

环境变量：
- `ADB_DEVICE_IP`：默认设备 IP，不传参数时使用
- `ADB_DEVICE_PORT`：默认端口，默认 5555
