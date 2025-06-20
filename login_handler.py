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
    
    async def load_cookies(self):
        """加载已保存的cookies"""
        if os.path.exists(Config.COOKIE_FILE):
            try:
                with open(Config.COOKIE_FILE, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    if cookies and self.page:
                        await self.page.setCookie(*cookies)
                        print("✅ 成功加载已保存的cookies")
                        return True
            except Exception as e:
                print(f"❌ 加载cookies失败: {e}")
        return False
        
    async def save_cookies(self):
        """保存cookies到本地文件"""
        if self.page:
            try:
                cookies = await self.page.cookies()
                with open(Config.COOKIE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                print(f"✅ cookies已保存到 {Config.COOKIE_FILE}")
            except Exception as e:
                print(f"❌ 保存cookies失败: {e}")
    
    async def login(self):
        """执行登录流程"""
        try:
            # 验证配置
            Config.validate()
            
            # 初始化页面
            if not self.page and self.browser:
                self.page = await self.browser.newPage()
                await self.page.setViewport({'width': 1920, 'height': 1080})
            
            # 首先尝试加载已保存的cookies
            cookies_loaded = await self.load_cookies()
            if cookies_loaded:
                print("🔄 尝试使用已保存的cookies...")
                # 直接访问基础URL检查cookies是否有效
                await self.page.goto(Config.MELON_BASE_URL)
                await asyncio.sleep(2)
                
                # 检查是否已经登录成功
                current_url = self.page.url
                print(f"🔍 当前URL: {current_url}")
                if "login" not in current_url.lower():
                    print("✅ 使用已保存的cookies登录成功")
                    return True
                else:
                    print("❌ 已保存的cookies已失效")
            
            # cookies无效或不存在，执行登录流程
            print("🔐 开始登录...")
            print(f"🔗 访问登录URL: {Config.MELON_LOGIN_URL}")
            
            # 添加重试机制处理网站访问延迟
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await self.page.goto(Config.MELON_LOGIN_URL)
                    await asyncio.sleep(3)  # 等待页面加载
                    
                    # 调试：截图当前登录页面状态
                    await self.take_debug_screenshot("login_page")
                    
                    current_url = self.page.url
                    print(f"🔍 实际访问的URL: {current_url}")
                    
                    # 检查页面内容，看是否遇到访问延迟页面
                    page_content = await self.page.content()
                    if "访问页面使用率过高" in page_content or "访问延迟" in page_content:
                        print(f"⚠️  网站访问量过高，等待后重试... (第{attempt + 1}次)")
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 30  # 递增等待时间
                            print(f"⏳ 等待 {wait_time} 秒...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print("❌ 多次重试仍无法访问登录页面，网站可能暂时不可用")
                            return False
                    
                    # 等待登录按钮元素出现，表示登录页面已加载
                    print("⏳ 等待登录按钮出现...")
                    await self.page.waitForSelector('#btnLogin', {'timeout': 15000})
                    print("✅ 登录页面加载成功")
                    break
                    
                except Exception as e:
                    print(f"❌ 访问登录页面失败 (第{attempt + 1}次): {e}")
                    if attempt < max_retries - 1:
                        print("🔄 30秒后重试...")
                        await asyncio.sleep(30)
                    else:
                        raise e
            
            # 输入用户名和密码
            print("🔑 输入登录凭据...")
            await self.page.type('#id', Config.USERNAME)
            await self.page.type('#pwd', Config.PASSWORD)
            
            # 点击登录按钮
            await self.page.click('#btnLogin')
            print("✅ 已点击登录按钮")
            
            # 等待页面跳转
            await asyncio.sleep(5)
            
            # 调试：登录后截图
            await self.take_debug_screenshot("after_login")
            
            # 检查登录结果
            current_url = self.page.url
            print(f"🔍 登录后URL: {current_url}")
            
            if "login" in current_url.lower():
                print(f"❌ 登录失败: {current_url}")
                return False
            else:
                print("✅ 登录成功")
                await self.save_cookies()
                return True
                
        except Exception as e:
            print(f"❌ 登录过程中发生错误: {e}")
            return False 