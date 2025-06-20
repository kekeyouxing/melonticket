import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置类，用于管理所有配置信息"""
    
    # Melon网站相关
    MELON_BASE_URL = "https://ticket.melon.com/performance/index.htm?prodId=211358"
    MELON_LOGIN_URL = "https://member.melon.com/muid/web/login/login_informM.htm"
    
    # 用户凭据
    USERNAME = os.getenv('MELON_USERNAME', '')
    PASSWORD = os.getenv('MELON_PASSWORD', '')
    PHONE = os.getenv('MELON_PHONE', '')
    
    # 浏览器设置（Docker容器环境）
    HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'True').lower() == 'true'
    
    # 容器内文件路径
    SESSION_FILE = os.getenv('SESSION_FILE', '/app/data/session_data.json')
    COOKIE_FILE = os.getenv('COOKIE_FILE', '/app/data/cookies.json')
    
    # 用户代理
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # 定时预约设置（必填）
    RESERVATION_START_TIME = os.getenv('RESERVATION_START_TIME', '')
    LOGIN_TIME = os.getenv('LOGIN_TIME', '')
    
    @classmethod
    def validate(cls):
        """验证配置是否有效"""
        if not cls.USERNAME or not cls.PASSWORD:
            raise ValueError("请在环境变量中设置MELON_USERNAME和MELON_PASSWORD")
        if not cls.PHONE:
            raise ValueError("请在环境变量中设置MELON_PHONE")
        if not cls.RESERVATION_START_TIME:
            raise ValueError("请在环境变量中设置RESERVATION_START_TIME")
        if not cls.LOGIN_TIME:
            raise ValueError("请在环境变量中设置LOGIN_TIME")
        
        # 验证时间格式
        from datetime import datetime
        try:
            reservation_time = datetime.strptime(cls.RESERVATION_START_TIME, '%Y-%m-%d %H:%M:%S')
            login_time = datetime.strptime(cls.LOGIN_TIME, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError("时间格式错误，应为: YYYY-MM-DD HH:MM:SS")
        
        # 验证时间逻辑
        if login_time >= reservation_time:
            raise ValueError("LOGIN_TIME必须早于RESERVATION_START_TIME")
        
        return True 