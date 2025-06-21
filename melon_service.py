import asyncio
import os
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from config import Config
from login_handler import LoginHandler
from reservation_handler import ReservationHandler
import schedule
import random

class MelonTicketService:
    """Melon票务定时服务"""
    
    def __init__(self):
        self.browser = None
        self.page = None
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
        
        if self.browser:
            self.browser.quit()
        if self._event_loop and not self._event_loop.is_closed():
            try:
                self._event_loop.close()
            except:
                pass
        print("🛑 服务已停止")
    
    async def login_and_wait(self):
        """登录并保持在主页面等待"""
        try:
            # 初始化浏览器
            self.browser = await self.init_browser()
            
            # 执行登录
            success = await self.login()
            if success:
                # 登录成功后导航到主页面并保持
                self.browser.get(Config.MELON_BASE_URL)
                print(f"✅ 已导航到主页面: {Config.MELON_BASE_URL}")
                return True
            return False
        except Exception as e:
            print(f"❌ 登录和等待过程出错: {e}")
            return False
    
    async def refresh_and_reserve(self):
        """开始预约"""
        try:
            if not self.browser:
                print("❌ 浏览器对象不可用")
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
            if not self.browser:
                print("❌ 浏览器未初始化")
                return False
            
            # 直接执行登录流程
            print("🔐 开始登录流程...")
            
            # 使用LoginHandler执行登录
            login_handler = LoginHandler(self.browser)
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
            reservation_handler = ReservationHandler(self.browser)
            print("🎫 开始预约流程...")
            try:
                mono_start_time = time.monotonic()
                start_dt = datetime.now()
                print(f"🚀 预约开始时间: {start_dt.strftime('%Y-%m-%d %H:%M:%S.%f')}")

                success = await reservation_handler.execute_reservation()

                mono_end_time = time.monotonic()
                end_dt = datetime.now()
                print(f"🏁 预约结束时间: {end_dt.strftime('%Y-%m-%d %H:%M:%S.%f')}")
                
                duration = mono_end_time - mono_start_time
                print(f"⏱️ 预约任务总耗时: {duration:.2f} 秒")

                if success:
                    print("✅ 预约流程成功")
                else:
                    print("❌ 预约流程失败")
                return success
            except Exception as e:
                print(f"❌ 预约流程执行失败: {e}")
            return False
            
        except Exception as e:
            print(f"❌ 预约流程执行失败: {e}")
            return False

    async def init_browser(self):
        """初始化浏览器（Docker环境）"""
        print("🚀 初始化Selenium WebDriver...")
        options = ChromeOptions()
        
        # 从您的示例代码中借鉴，无头模式在Docker中是必需的
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f"user-agent={Config.USER_AGENT}")

        try:
            # 明确指定chromedriver路径，禁用自动版本管理
            service = ChromeService(executable_path='/usr/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ Selenium WebDriver 初始化成功")
            return driver
        except Exception as e:
            print(f"❌ Selenium WebDriver 初始化失败: {e}")
            print("🤔 请确保chromedriver已安装并且路径正确。")
        return None
    
    async def run_immediately(self):
        """立即执行登录和预约流程，用于测试"""
        print("⚡️ 立即执行模式启动...")
        try:
            # 1. 初始化浏览器
            self.browser = await self.init_browser()
            if not self.browser:
                print("❌ 浏览器初始化失败，测试终止。")
                return

            # 2. 执行登录
            login_handler = LoginHandler(self.browser)
            login_success = await login_handler.login()
            if not login_success:
                print("❌ 登录失败，测试终止。")
                return

            print("✅ 登录成功，立即开始预约流程...")
            
            # 3. 导航到目标页面
            self.browser.get(Config.MELON_BASE_URL)
            print(f"✅ 已导航到主页面: {Config.MELON_BASE_URL}")
            
            # 4. 执行预约
            reservation_handler = ReservationHandler(self.browser)
            reservation_success = await reservation_handler.execute_reservation()

            if reservation_success:
                print("🎉 立即执行模式：预约成功！")
            else:
                print("❌ 立即执行模式：预约失败。")
                
        except Exception as e:
            print(f"❌ 立即执行模式出错: {e}")
        finally:
            print("🛑 立即执行模式结束，正在清理资源...")
            if self.browser:
                self.browser.quit()
                
def main():
    """主函数"""
    service = MelonTicketService()
    
    try:
        # 验证配置
        Config.validate()
        
        # 立即执行测试流程
        asyncio.run(service.run_immediately())

    except Exception as e:
        print(f"❌ 服务启动失败: {e}")

if __name__ == "__main__":
    main() 