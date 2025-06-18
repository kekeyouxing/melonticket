import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置类，用于管理所有配置信息"""
    
    # Melon网站相关
    MELON_BASE_URL = "https://ticket.melon.com/performance/index.htm?prodId=211506"
    MELON_LOGIN_URL = "https://member.melon.com/muid/web/login/login_informM.htm"
    
    # 用户凭据
    USERNAME = os.getenv('MELON_USERNAME', '')
    PASSWORD = os.getenv('MELON_PASSWORD', '')
    
    # 浏览器设置
    HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'False').lower() == 'true'
    WAIT_TIMEOUT = int(os.getenv('WAIT_TIMEOUT', 10))
    IMPLICIT_WAIT = int(os.getenv('IMPLICIT_WAIT', 5))
    
    # 文件路径
    SESSION_FILE = os.getenv('SESSION_FILE', 'session_data.json')
    COOKIE_FILE = os.getenv('COOKIE_FILE', 'cookies.json')
    
    # 用户代理
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    @classmethod
    def validate(cls):
        """验证配置是否有效"""
        if not cls.USERNAME or not cls.PASSWORD:
            raise ValueError("请在环境变量中设置MELON_USERNAME和MELON_PASSWORD")
        return True 