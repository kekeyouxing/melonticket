import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置类，用于管理所有配置信息"""
    
    # Melon网站相关
    MELON_BASE_URL = "https://ticket.melon.com/performance/index.htm?prodId=211541"
    MELON_LOGIN_URL = "https://member.melon.com/muid/web/login/login_informM.htm"
    
    # 用户凭据
    MELON_USERNAME = os.getenv('MELON_USERNAME')
    MELON_PASSWORD = os.getenv('MELON_PASSWORD')
    PHONE = os.getenv('MELON_PHONE', '')
    
    # 浏览器设置（Docker容器环境）
    HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'true').lower() == 'true'
    
    # 用户代理
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # 预约开始时间
    RESERVATION_START_TIME = os.getenv('RESERVATION_START_TIME')
    

    
    @classmethod
    def validate(cls):
        """验证必需的配置项"""
        required_fields = [
            'MELON_USERNAME', 'MELON_PASSWORD', 
            'RESERVATION_START_TIME'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"缺少必需的配置项: {', '.join(missing_fields)}")
        
        # 验证时间格式
        try:
            datetime.strptime(cls.RESERVATION_START_TIME, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError("RESERVATION_START_TIME 格式错误，应为: YYYY-MM-DD HH:MM:SS")
    
    @classmethod
    def calculate_random_login_time(cls):
        """计算随机登录时间（预约时间前1-3分钟内的随机秒数）"""
        reservation_time = datetime.strptime(cls.RESERVATION_START_TIME, '%Y-%m-%d %H:%M:%S')
        # 随机选择1-3分钟内的随机秒数前登录
        seconds_before = random.randint(60, 180)  # 60秒(1分钟) 到 180秒(3分钟)
        login_time = reservation_time - timedelta(seconds=seconds_before)
        return login_time 