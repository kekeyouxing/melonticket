# 🍈 Melon票务定时预约系统

基于Docker的Melon票务自动预约系统，支持定时预约、无头运行。

## ⚠️ 重要声明

本项目仅用于**学习和研究目的**，请遵守以下原则：

- 🚫 **不得用于抢票或其他违法用途**
- 📜 **遵守网站使用条款和服务协议**
- 🤝 **尊重网站的反自动化措施**
- 📚 **仅用于技术学习和个人自动化需求**

## 🎯 功能特性

### 核心功能
- ⏰ **定时预约**: 设定预约时间，系统自动执行
- 🔐 **智能登录**: 提前5分钟自动登录，确保预约时已准备就绪
- 🎫 **全流程自动化**: 验证码识别、座位选择、支付配置全自动
- 🤖 **无人值守**: 完全后台运行，无需人工干预
- 💾 **会话保持**: 自动保存和恢复登录状态

### 技术特性
- 🐳 **Docker容器化**: 完全容器化部署，环境隔离
- 🖥️ **无头模式**: 后台运行，无需图形界面
- 🎯 **精确定时**: 支持秒级精确的定时执行
- 📊 **实时日志**: 详细的执行日志和状态监控
- 🛡️ **错误恢复**: 完善的异常处理和重试机制

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd melonticket
```

### 2. 配置环境变量
```bash
# 创建并编辑配置文件
vim .env
```

配置内容示例：
```env
# 账户信息
MELON_USERNAME=你的用户名
MELON_PASSWORD=你的密码
MELON_PHONE=010-1234-5678

# 定时设置（重要！）
RESERVATION_START_TIME=2024-01-15 10:00:00
LOGIN_ADVANCE_MINUTES=5

# 系统设置
HEADLESS_MODE=true
```

### 3. 启动定时预约
```bash
# 一键启动（后台运行）
./run-docker.sh

# 前台运行（查看日志）
./run-docker.sh --foreground

# 调试模式
./run-docker.sh --debug
```

## 📁 项目结构

```
melonticket/
├── 🐳 Docker配置
│   ├── Dockerfile              # 镜像构建文件
│   ├── .dockerignore           # 构建忽略
│   └── run-docker.sh           # 一键部署脚本
├── ⚙️ 配置文件
│   ├── config.py               # 应用配置
│   └── requirements.txt        # Python依赖
├── 🎫 核心应用
│   └── melon_login.py          # 主程序
├── 📖 文档
│   ├── README.md               # 主文档
│   └── DOCKER_README.md        # Docker使用指南
└── 💾 数据目录
    ├── data/                   # 持久化数据
    └── logs/                   # 日志文件
```

## ⚙️ 配置选项

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MELON_USERNAME` | - | Melon用户名(必需) |
| `MELON_PASSWORD` | - | Melon密码(必需) |
| `MELON_PHONE` | - | 手机号码(必需) |
| `RESERVATION_START_TIME` | - | 预约开始时间 |
| `LOGIN_ADVANCE_MINUTES` | `5` | 提前登录分钟数 |
| `HEADLESS_MODE` | `true` | 无头模式运行 |

## 🔍 工作原理

### 定时执行流程
1. **时间计算**: 根据预约时间计算提前登录时间
2. **等待登录**: 到达登录时间前保持等待状态
3. **提前登录**: 预约前5分钟自动开始登录
4. **等待预约**: 登录成功后等待到预约时间
5. **开始预约**: 精确到预约时间开始抢票

### 自动化流程
- **验证码识别**: 自动识别并输入验证码
- **智能选座**: 按前排中间优先选择座位
- **支付配置**: 自动配置支付方式和银行信息
- **会话保持**: 自动保存和恢复登录状态

### 容器特性
- **虚拟显示**: 使用Xvfb提供虚拟图形环境
- **无头运行**: 后台运行，无需物理显示器
- **数据持久化**: 会话和日志数据持久化存储
- **环境隔离**: 完全独立的运行环境

## 🐛 故障排除

### 常见问题

**Q: 容器启动失败**
```bash
# 检查Docker状态
docker ps

# 查看容器日志
docker logs melonticket-app
```

**Q: 预约时间设置错误**
```bash
# 时间格式必须为: YYYY-MM-DD HH:MM:SS
RESERVATION_START_TIME=2024-01-15 10:00:00
```

**Q: 验证码识别失败**
```bash
# 查看日志，验证码识别有重试机制
docker logs -f melonticket-app
```

**Q: 网络连接问题**
```bash
# 确保Docker容器网络正常
docker exec melonticket-app ping baidu.com
```

### 调试模式
使用调试参数启动:
```bash
# 进入容器调试
./run-docker.sh --debug

# 前台运行查看日志
./run-docker.sh --foreground
```

## 📄 许可证

本项目仅供学习研究使用，请勿用于商业用途或违法行为。

## ⚠️ 免责声明

- 本工具仅用于技术学习和研究目的
- 使用者需自行承担使用风险和法律责任
- 开发者不对任何滥用行为负责
- 请遵守相关网站的使用条款和法律法规

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目。

## 📞 支持

如有问题，请在GitHub上提交Issue。 