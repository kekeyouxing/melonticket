import asyncio
import json
import os
from datetime import datetime
from config import Config

class LoginHandler:
    """登录处理器"""
    
    def __init__(self, browser=None):
        self.browser = browser
        self.page = None
    
    async def take_debug_screenshot(self, filename_prefix):
        """调试用截图函数"""
        try:
            if self.page:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"/app/data/{filename_prefix}_{timestamp}.png"
                await self.page.screenshot({'path': screenshot_path, 'fullPage': True})
                print(f"📸 截图已保存: {screenshot_path}")
                return screenshot_path
        except Exception as e:
            print(f"❌ 截图失败: {e}")
        return None
    
    async def login(self):
        """执行登录流程"""
        try:
            # 验证配置
            Config.validate()
            
            # 初始化页面
            if not self.page and self.browser:
                self.page = await self.browser.newPage()
                await self.page.setViewport({'width': 1920, 'height': 1080})
            
            # 直接执行登录流程（删除cookie逻辑）
            print("🔐 开始登录...")
            print(f"🔗 访问登录URL: {Config.MELON_LOGIN_URL}")
            
            # 直接访问登录页面
            await self.page.goto(Config.MELON_LOGIN_URL)
            await asyncio.sleep(3)  # 等待页面加载
            
            # 调试：截图当前登录页面状态
            await self.take_debug_screenshot("login_page")
            
            current_url = self.page.url
            print(f"🔍 实际访问的URL: {current_url}")
            
            # 等待登录按钮元素出现，表示登录页面已加载
            await self.page.waitForSelector('#btnLogin', {'timeout': 15000})
            
            # 输入用户名和密码
            await self.page.type('#id', Config.MELON_USERNAME)
            await self.page.type('#pwd', Config.MELON_PASSWORD)
            
            # 点击登录按钮
            await self.page.click('#btnLogin')
            print("✅ 已点击登录按钮")
            
            # 等待页面跳转
            await asyncio.sleep(5)
            
            # 调试：登录后截图
            await self.take_debug_screenshot("after_login")
            
            # 检查登录结果
            current_url = self.page.url
            
            if "login" in current_url.lower():
                print(f"❌ 登录失败: {current_url}")
                return False
            else:
                print("✅ 登录成功")
                return True
                
        except Exception as e:
            print(f"❌ 登录过程中发生错误: {e}")
            return False 