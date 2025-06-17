# Melon 自动登录程序

一个基于Python + Selenium的Melon网站自动登录和会话管理工具。

## ⚠️ 重要声明

本项目仅用于**学习和研究目的**，请遵守以下原则：

- 🚫 **不得用于抢票或其他违法用途**
- 📜 **遵守网站使用条款和服务协议**
- 🤝 **尊重网站的反自动化措施**
- 📚 **仅用于技术学习和个人自动化需求**

## 🎯 功能特性

### 核心功能
- ✅ **智能登录检测**: 自动检测当前登录状态
- 🔄 **会话复用**: 保存和恢复登录会话，避免重复登录
- 🔐 **安全存储**: 使用文件保存cookies和会话数据
- 🕒 **会话保持**: 自动保持会话活跃状态
- 🎭 **人类行为模拟**: 随机延时，模拟真实用户操作

### 技术特性
- 🌐 **跨平台支持**: 支持 Windows、macOS、Linux
- ⚙️ **自动驱动管理**: 自动下载和管理ChromeDriver
- 🎛️ **灵活配置**: 支持环境变量和配置文件
- 📊 **详细日志**: 提供详细的操作日志和状态信息
- 🛡️ **错误处理**: 完善的异常处理和错误恢复

## 📦 安装依赖

### 1. 克隆项目
```bash
git clone <repository-url>
cd melonticket
```

### 2. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 3. 安装Chrome浏览器
确保系统已安装Google Chrome浏览器。程序会自动下载匹配的ChromeDriver。

## 🔧 配置

### 方式1: 环境变量
```bash
export MELON_USERNAME="your_username"
export MELON_PASSWORD="your_password"
export HEADLESS_MODE="False"  # 可选: 是否使用无头模式
export WAIT_TIMEOUT="10"      # 可选: 等待超时时间(秒)
```

### 方式2: .env文件
创建 `.env` 文件:
```env
MELON_USERNAME=your_username
MELON_PASSWORD=your_password
HEADLESS_MODE=False
WAIT_TIMEOUT=10
IMPLICIT_WAIT=5
SESSION_FILE=session_data.json
COOKIE_FILE=cookies.json
```

## 🚀 使用方法

### 基础使用
```bash
python main.py
```

### 编程使用
```python
from melon_automation import MelonAutomation

# 使用上下文管理器
with MelonAutomation() as automation:
    if automation.login():
        print("登录成功!")
        # 保持会话30分钟
        automation.keep_session_alive(30)
```

### 高级使用
```python
from melon_automation import MelonAutomation
from session_manager import SessionManager

automation = MelonAutomation()

# 检查是否有有效会话
if automation.session_manager.is_session_valid():
    print("发现有效会话")
    
# 执行登录
if automation.login():
    print("登录成功")
    
    # 自定义会话数据
    custom_data = {'user_id': '12345', 'preferences': {}}
    automation.session_manager.save_session_data(custom_data)
    
    # 保持会话
    automation.keep_session_alive(60)  # 60分钟

# 清理资源
automation.close()
```

## 📁 项目结构

```
melonticket/
├── main.py                 # 主程序入口
├── example.py              # 使用示例
├── melon_automation.py     # 核心自动化类
├── session_manager.py      # 会话管理器
├── config.py               # 配置管理
├── requirements.txt        # 依赖包列表
├── README.md              # 项目说明
├── .env.example           # 环境变量示例
├── session_data.json      # 会话数据文件(运行时生成)
└── cookies.json           # Cookie数据文件(运行时生成)
```

## ⚙️ 配置选项

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `MELON_USERNAME` | - | Melon用户名(必需) |
| `MELON_PASSWORD` | - | Melon密码(必需) |
| `HEADLESS_MODE` | `False` | 是否使用无头模式 |
| `WAIT_TIMEOUT` | `10` | 元素等待超时时间(秒) |
| `IMPLICIT_WAIT` | `5` | 隐式等待时间(秒) |
| `SESSION_FILE` | `session_data.json` | 会话数据文件路径 |
| `COOKIE_FILE` | `cookies.json` | Cookie文件路径 |

## 🔍 工作原理

### 登录流程
1. **检查现有会话**: 首先检查是否有有效的保存会话
2. **会话恢复**: 如果有效会话存在，加载cookies并验证
3. **凭据登录**: 如果会话无效，使用用户名密码登录
4. **保存会话**: 登录成功后保存cookies和会话数据

### 会话管理
- **自动保存**: 登录成功后自动保存会话信息
- **过期检查**: 检查会话是否在24小时内有效
- **定期更新**: 在保持会话期间定期更新cookies
- **安全清理**: 提供清理会话数据的方法

### 反检测措施
- **用户代理**: 使用真实的浏览器用户代理
- **随机延时**: 在操作间添加随机延时
- **隐藏特征**: 隐藏webdriver检测特征
- **人类行为**: 模拟真实的键盘输入模式

## 🐛 故障排除

### 常见问题

**Q: 无法找到ChromeDriver**
```
A: 程序会自动下载ChromeDriver，确保网络连接正常
```

**Q: 登录失败**
```
A: 检查用户名密码是否正确，是否需要验证码
```

**Q: 会话过期**
```
A: 会话有效期为24小时，过期后需要重新登录
```

**Q: 元素查找失败**
```
A: 网站结构可能已更改，需要更新选择器
```

### 调试模式
设置环境变量启用详细日志:
```bash
export HEADLESS_MODE="False"  # 显示浏览器窗口
export WAIT_TIMEOUT="30"      # 增加等待时间
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