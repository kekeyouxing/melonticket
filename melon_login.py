import asyncio
import json
import os
from pyppeteer import launch
from config import Config

class MelonLogin:
    """Melon自动登录类"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        
    async def init_browser(self):
        """初始化浏览器"""
        self.browser = await launch(
            headless=Config.HEADLESS_MODE,
            executablePath='/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
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
            
            # 初始化浏览器
            await self.init_browser()
            self.page = await self.browser.newPage()
            await self.page.setViewport({'width': 1366, 'height': 768})
            
            # 尝试加载已保存的cookies
            cookies_loaded = await self.load_cookies()
            
            if cookies_loaded:
                # 验证cookies是否有效
                print("🔍 验证已保存的登录状态...")
                await self.page.goto(Config.MELON_BASE_URL, {'waitUntil': 'domcontentloaded'})
                
                if "login" not in self.page.url.lower():
                    print("✅ 使用已保存的cookies登录成功！")
                    return True
                else:
                    print("⚠️ 已保存的cookies已失效，需要重新登录")
            
            # 执行登录流程
            print("🔐 开始登录流程...")
            await self.page.goto(Config.MELON_LOGIN_URL, {'waitUntil': 'domcontentloaded'})
            
            # 等待登录按钮加载
            await self.page.waitForSelector('#btnLogin', {'timeout': 10000})
            
            # 输入用户名和密码
            await self.page.type('#id', Config.USERNAME)
            print("✅ 已输入用户名")
            
            await self.page.type('#pwd', Config.PASSWORD)
            print("✅ 已输入密码")
            
            # 点击登录按钮
            await self.page.click('#btnLogin')
            print("🔄 正在登录...")
            
            # 等待页面跳转
            await asyncio.sleep(3)
            
            # 检查登录结果
            current_url = self.page.url
            if "login" in current_url.lower():
                print("❌ 登录失败，请检查用户名和密码")
                return False
            else:
                print("✅ 登录成功！")
                
                # 保存cookies
                await self.save_cookies()
                
                # 跳转到目标页面
                if Config.MELON_BASE_URL not in current_url:
                    print("🔗 正在跳转到目标页面...")
                    await self.page.goto(Config.MELON_BASE_URL, {'waitUntil': 'domcontentloaded'})
                    print("✅ 已跳转到目标页面")
                
                return True
                
        except Exception as e:
            print(f"❌ 登录过程中发生错误: {e}")
            return False
            
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()

async def main():
    """主函数"""
    login_manager = MelonLogin()
    
    try:
        success = await login_manager.login()
        
        if success:
            print("🎉 登录流程完成！")
            
            # 询问是否保持会话
            keep_alive = input("是否需要保持浏览器开启？(y/n): ").lower().strip()
            if keep_alive == 'y':
                input("按回车键关闭浏览器...")
        else:
            print("💔 登录失败")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断操作")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
    finally:
        await login_manager.close()
        print("👋 浏览器已关闭")

if __name__ == "__main__":
    asyncio.run(main()) 