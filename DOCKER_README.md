# 🍈 Melon票务自动预约系统 - 精确定时服务版

基于Docker的Melon票务自动预约系统，采用专业定时调度库实现**精确到秒**的定时执行。

## 🚀 快速开始

### 1. 创建配置文件
创建 `.env` 文件并填入你的信息：

```bash
# Melon账户信息
MELON_USERNAME=你的用户名
MELON_PASSWORD=你的密码  
MELON_PHONE=你的手机号

# 精确定时设置（必填）
RESERVATION_START_TIME=2024-01-15 10:00:00
LOGIN_TIME=2024-01-15 09:55:00

# Docker环境设置
HEADLESS_MODE=true
SESSION_FILE=/app/data/session_data.json
COOKIE_FILE=/app/data/cookies.json
```

### 2. 一键启动
```bash
# 给脚本执行权限
chmod +x run-docker.sh

# 启动容器
./run-docker.sh
```

### 3. 查看运行状态
```bash
# 查看容器状态
docker ps

# 查看实时日志
docker logs -f melonticket-app
```

## ⏰ 精确定时服务

### 🎯 **核心特性**
- **秒级精确度**：使用 `schedule` 库实现精确到秒的定时执行
- **准点触发**：在指定时间点准确执行任务，不存在轮询延迟
- **服务化运行**：程序作为后台服务持续运行，直到任务完成

### 🕒 时间设置

```bash
RESERVATION_START_TIME=2024-01-15 10:00:00  # 预约开始时间
LOGIN_TIME=2024-01-15 09:55:00              # 登录时间
```

### 📅 执行流程
```
🍈 启动定时服务
📅 设置任务:
   - 09:55:00 → 登录任务
   - 10:00:00 → 预约任务
⏰ 服务运行中，等待执行时间...

⏰ 09:55:00 - 登录时间到！执行登录任务
✅ 登录任务执行完成

⏰ 10:00:00 - 预约时间到！执行预约任务  
✅ 预约任务执行完成
🎉 定时服务执行完成
```

### 🔧 **技术架构**
| 组件 | 旧版本 | 新版本 |
|------|--------|--------|
| **调度方式** | 手动循环轮询 | `schedule` 专业定时库 |
| **时间精度** | 10秒轮询 | **秒级精确** |
| **执行方式** | 等待 + 顺序执行 | **准点触发** |
| **服务模式** | 一次性脚本 | **持续后台服务** |

### ⚠️ 注意事项
- 预约时间已过期时，程序会直接退出
- LOGIN_TIME 必须早于 RESERVATION_START_TIME
- 时间格式必须为：`YYYY-MM-DD HH:MM:SS`
- 程序在指定时间**准确触发**，无延迟

## 🛠️ 容器管理

### 停止容器
```bash
docker stop melonticket-app
```

### 重启容器
```bash
docker restart melonticket-app
```

### 删除容器
```bash
docker stop melonticket-app
docker rm melonticket-app
```

### 查看日志
```bash
# 查看所有日志
docker logs melonticket-app

# 实时查看日志
docker logs -f melonticket-app

# 查看最近50行日志
docker logs --tail 50 melonticket-app
```

## 📂 数据持久化

容器会在宿主机创建以下目录来保存数据：
- `./data/` - 会话数据和cookies
- `./logs/` - 运行日志

即使删除容器，这些数据也会保留。

## 🔧 高级配置

### 环境变量说明
| 变量名 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| MELON_USERNAME | ✅ | Melon用户名 | `your_username` |
| MELON_PASSWORD | ✅ | Melon密码 | `your_password` |  
| MELON_PHONE | ✅ | 手机号 | `01012345678` |
| RESERVATION_START_TIME | ✅ | 预约开始时间 | `2024-01-15 10:00:00` |
| LOGIN_TIME | ✅ | 登录时间 | `2024-01-15 09:55:00` |
| HEADLESS_MODE | ❌ | 无头模式 | `true` |

## 🚨 故障排除

### 常见问题

1. **登录失败**
   - 检查用户名密码是否正确
   - 确认Melon账户状态正常

2. **容器启动失败** 
   - 检查`.env`文件是否存在
   - 确认Docker服务运行正常

3. **预约失败**
   - 检查网络连接
   - 确认预约时间设置正确

4. **时间已过期**
   - 更新`.env`中的时间设置
   - 重新启动容器

### 性能特性
- **内存占用低**：定时服务模式比轮询模式更节省资源
- **CPU使用率低**：只在指定时间点激活，平时处于等待状态
- **执行精确**：专业定时库保证时间精确度

### 获取帮助
如遇到问题，可以通过以下方式获取详细日志：
```bash
docker logs melonticket-app 2>&1 | tee debug.log
```

## 📁 目录结构

```
melonticket/
├── Dockerfile              # Docker镜像构建文件
├── .dockerignore           # Docker忽略文件
├── run-docker.sh           # 一键部署脚本
├── requirements.txt        # Python依赖
├── data/                   # 数据持久化目录
│   ├── session_data.json   # 会话数据
│   └── cookies.json        # Cookie数据
└── logs/                   # 日志目录
```

## 🔧 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `MELON_USERNAME` | Melon用户名 | 必填 |
| `MELON_PASSWORD` | Melon密码 | 必填 |
| `MELON_PHONE` | 手机号码 | 必填 |
| `HEADLESS_MODE` | 无头模式 | `true` |
| `RESERVATION_START_TIME` | 预约开始时间 | `2024-01-15 10:00:00` |
| `LOGIN_TIME` | 登录时间 | 必填 |

### Docker特性

- **容器化运行**：专为Docker容器环境优化
- **数据持久化**：session和cookie数据持久化到宿主机
- **无头模式**：容器中默认启用无头浏览器
- **安全运行**：使用非root用户运行应用
- **虚拟显示**：内置Xvfb支持图形界面

## 🐛 故障排除

### 常见问题

1. **权限问题**
   ```bash
   # 确保数据目录有正确权限
   sudo chmod -R 755 data logs
   ```

2. **内存不足**
   ```bash
   # 增加Docker容器内存限制
   docker run --memory=2g melonticket
   ```

3. **浏览器启动失败**
   - 检查Docker版本是否支持
   - 确保系统有足够内存

### 调试模式

使用调试参数启动：
```bash
# 调试模式（进入容器shell）
./run-docker.sh --debug
```

## 📝 日志查看

查看容器日志：
```bash
# 实时查看日志
docker logs -f melonticket-app

# 查看最近的日志
docker logs --tail=100 melonticket-app
```

## 🔄 更新应用

```bash
# 停止并删除容器
docker stop melonticket-app
docker rm melonticket-app

# 重新运行（会自动重新构建）
./run-docker.sh
```

## ⚠️ 注意事项

1. **账户安全**：请妥善保管 `.env` 文件，不要提交到版本控制
2. **资源占用**：容器运行时会占用一定CPU和内存资源
3. **网络稳定**：确保网络连接稳定，避免预约过程中断
4. **时区设置**：如需要可在Dockerfile中设置时区

## 📞 技术支持

如遇到问题，请检查：
1. 环境变量是否正确配置
2. Docker版本是否兼容
3. 系统资源是否充足
4. 网络连接是否正常 