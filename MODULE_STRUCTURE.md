# 模块化结构说明

## 文件结构

现在代码已经分解为以下模块：

### 核心文件
- `melon_service.py` - 主服务文件（原melon_login.py）
- `login_handler.py` - 登录处理模块
- `reservation_handler.py` - 预约座位处理模块  
- `captcha_handler.py` - 验证码处理模块
- `config.py` - 配置文件

### Docker文件
- `Dockerfile` - 容器配置（已更新为使用melon_service.py）
- `run-docker.sh` - 一键启动脚本

## 模块职责

### 1. MelonTicketService (melon_service.py)
- 主服务调度器
- 时间管理和定时任务
- 浏览器初始化
- 模块协调

### 2. LoginHandler (login_handler.py)
- Cookie管理
- 登录流程处理
- 登录重试机制
- 调试截图（仅登录相关）

### 3. ReservationHandler (reservation_handler.py)
- 票务预约流程
- 弹窗页面处理
- iframe处理
- 座位选择
- 支付流程

### 4. CaptchaHandler (captcha_handler.py) 
- 验证码识别
- OCR处理
- 验证码重试机制

## 优势

1. **代码分离** - 每个模块职责单一，易于维护
2. **调试方便** - 可以单独测试登录或预约功能
3. **代码复用** - 模块可以独立使用
4. **易于扩展** - 新功能可以作为独立模块添加

## 运行方式

运行方式保持不变：
```bash
./run-docker.sh
```

调试时只会截图登录过程的关键步骤，避免产生过多截图文件。 