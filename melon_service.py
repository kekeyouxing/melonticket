import asyncio
import os
import time
from datetime import datetime
import ddddocr
from pyppeteer import launch
from config import Config
from login_handler import LoginHandler
from reservation_handler import ReservationHandler

class MelonTicketService:
    """Melon票务定时服务"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.ocr = ddddocr.DdddOcr(show_ad=False)
        self.iframe_element = None
        self.is_logged_in = False
        self.service_running = True
        self.login_completed = False
        self.reservation_completed = False
        self._event_loop = None  # 共享事件循环
        
        # 计算随机登录时间
        self.login_time = Config.calculate_random_login_time()
        
        # 确保数据目录存在
        data_dir = "/app/data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
    
    def run_scheduler(self):
        """运行定时调度器"""
        # 验证时间是否已过期
        reservation_time = datetime.strptime(Config.RESERVATION_START_TIME, '%Y-%m-%d %H:%M:%S')
        current_time = datetime.now()
        
        if reservation_time <= current_time:
            print(f"❌ 预约时间 {Config.RESERVATION_START_TIME} 已过期")
            return
        
        if self.login_time <= current_time:
            print(f"❌ 计算的登录时间 {self.login_time.strftime('%Y-%m-%d %H:%M:%S')} 已过期")
            return
        
        login_executed = False
        reservation_executed = False
        
        while self.service_running:
            current_time = datetime.now()
            
            # 检查是否到了登录时间
            if not login_executed and current_time >= self.login_time:
                print(f"⏰ 登录时间到！开始执行登录任务... [{current_time.strftime('%Y-%m-%d %H:%M:%S')}]")
                self.execute_login_job()
                login_executed = True
            
            # 检查是否到了预约时间
            if not reservation_executed and current_time >= reservation_time:
                print(f"⏰ 预约时间到！开始执行预约任务... [{current_time.strftime('%Y-%m-%d %H:%M:%S')}]")
                self.execute_reservation_job()
                reservation_executed = True
                break  # 预约完成后退出循环
            
            time.sleep(1)  # 每秒检查一次
        
        print("🎉 所有任务执行完成")
    
    def execute_login_job(self):
        """执行登录任务"""
        try:
            if not self._event_loop or self._event_loop.is_closed():
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
            
            success = self._event_loop.run_until_complete(self.login_and_wait())
            
            if success:
                print("✅ 登录完成，浏览器保持在主页面等待预约...")
            else:
                print("❌ 登录失败")
                self._cleanup_and_stop()
        except Exception as e:
            print(f"❌ 登录任务异常: {e}")
            self._cleanup_and_stop()
    
    def execute_reservation_job(self):
        """执行预约任务"""
        try:
            if not self._event_loop or self._event_loop.is_closed():
                print("❌ 事件循环不可用")
                return
            
            success = self._event_loop.run_until_complete(self.refresh_and_reserve())
            
            if success:
                print("✅ 预约任务完成")
            else:
                print("❌ 预约任务失败")
                
            # 预约任务完成后清理所有资源并停止服务
            self._cleanup_and_stop()
        except Exception as e:
            print(f"❌ 预约任务异常: {e}")
            self._cleanup_and_stop()
    
    def _cleanup_and_stop(self):
        """清理资源并停止服务"""
        self.service_running = False
        
        if self._event_loop and not self._event_loop.is_closed():
            try:
                if self.browser:
                    self._event_loop.run_until_complete(self.browser.close())
                self._event_loop.close()
            except:
                pass
        print("🛑 服务已停止")
    
    async def login_and_wait(self):
        """登录并保持在主页面等待"""
        try:
            # 初始化浏览器
            await self.init_browser()
            self.page = await self.browser.newPage()
            await self.page.setViewport({'width': 1920, 'height': 1080})
            
            # 执行登录
            success = await self.login()
            if success:
                # 登录成功后导航到主页面并保持
                await self.page.goto(Config.MELON_BASE_URL)
                print(f"✅ 已导航到主页面: {Config.MELON_BASE_URL}")
                return True
            return False
        except Exception as e:
            print(f"❌ 登录和等待过程出错: {e}")
            return False
    
    async def refresh_and_reserve(self):
        """开始预约"""
        try:
            if not self.page:
                print("❌ 页面对象不可用")
                return False
            
            # 直接开始预约流程（刷新逻辑已在ReservationHandler中处理）
            return await self.start_reservation()
        except Exception as e:
            print(f"❌ 预约过程出错: {e}")
            return False
    
    async def login(self):
        """执行登录流程"""
        try:
            # 验证配置
            Config.validate()
            
            # 验证浏览器和页面是否已初始化
            if not self.browser or not self.page:
                print("❌ 浏览器未初始化")
                return False
            
            # 直接执行登录流程
            print("🔐 开始登录流程...")
            
            # 使用LoginHandler执行登录
            login_handler = LoginHandler(self.browser)
            login_handler.page = self.page  # 设置页面对象
            success = await login_handler.login()
            
            if success:
                print("✅ 登录成功")
                self.is_logged_in = True
                return True
            else:
                print("❌ 登录失败")
                return False
                
        except Exception as e:
            print(f"❌ 登录过程出错: {e}")
            return False

    async def start_reservation(self):
        """开始预约流程"""
        try:
            print("🎫 开始预约流程...")
            # 使用ReservationHandler执行完整预约流程
            reservation_handler = ReservationHandler(self.browser)
            reservation_handler.page = self.page  # 设置页面对象
            success = await reservation_handler.execute_reservation()
            
            if success:
                print("✅ 预约流程完成")
                return True
            else:
                print("❌ 预约流程失败")
                return False
                
        except Exception as e:
            print(f"❌ 预约流程执行失败: {e}")
            return False
    
    async def init_browser(self):
        """初始化浏览器（Docker环境）"""
        browser_args = [
            '--no-sandbox', 
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--window-size=1920,1080'
        ]
        
        executable_path = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
        
        self.browser = await launch(
            headless=False,  # 调试期间关闭无头模式以支持截图
            executablePath=executable_path,
            args=browser_args,
            defaultViewport=None
        )

def main():
    """主函数"""
    service = MelonTicketService()
    
    try:
        # 验证配置
        Config.validate()
        
        print("🚀 定时服务启动中...")
        print(f"⏰ 随机登录时间: {service.login_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎫 预约时间: {Config.RESERVATION_START_TIME}")
        
        # 运行定时服务
        service.run_scheduler()
        
        print("🐳 Docker容器运行完成，自动关闭...")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断操作")
        service._cleanup_and_stop()
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
    finally:
        print("👋 服务已关闭")

if __name__ == "__main__":
    main() 